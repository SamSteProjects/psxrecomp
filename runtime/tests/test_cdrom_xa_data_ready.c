/* Execute the production CD controller/ADPCM decoder with a synthetic disc.
 * The only replacements are external disc, SPU output and diagnostic edges.
 * PSX-SPX CDROM / Playing XA-ADPCM Sectors: INT1 is for non-ADPCM sectors
 * when XA playback or filtering is enabled, regardless of host muting.
 */
#include <assert.h>
#ifndef CDROM_TEST_SOURCE
#define CDROM_TEST_SOURCE "../src/cdrom.c"
#endif
#include CDROM_TEST_SOURCE

uint32_t i_stat, g_debug_current_func_addr, g_debug_last_store_pc;
uint64_t psx_cycle_count, s_frame_count;
static uint8_t test_sectors[3][RAW_SECTOR_SIZE];
static uint64_t audio_frames;
static int test_dma_active;
int iso_read_raw_sector(void *handle, uint32_t lba, uint8_t *data, int size) {
    assert(handle == (void*)1 && lba < 3 && size == RAW_SECTOR_SIZE);
    memcpy(data, test_sectors[lba], size); return 1;
}
int iso_read_sector(void *h, uint32_t lba, uint8_t *data, int size) {
    (void)h;(void)lba;(void)data;(void)size;assert(0);return 0;
}
int iso_read_subq(void *h,uint32_t lba,uint8_t *data,int size,int *valid) {
    (void)h;(void)lba;(void)data;(void)size;(void)valid;assert(0);return 0;
}
void spu_cd_audio_push(const int16_t *samples,int frames) {
    assert(samples && frames > 0);audio_frames += (unsigned)frames;
}
void psx_irq_raise(uint32_t bit,uint32_t detail) { (void)detail;i_stat |= 1u << bit; }
void event_ring_record(uint16_t kind,uint8_t detail) { (void)kind;(void)detail; }
void event_ring_record_aux(uint16_t kind,uint8_t detail,uint32_t aux) {
    (void)kind;(void)detail;(void)aux;
}
void audio_trace_event(uint16_t kind,uint32_t a,uint32_t b) {
    (void)kind;(void)a;(void)b;
}
/* Unused controller entry points remain linked by some Windows linkers.
 * Abort if this focused fixture accidentally reaches those external services. */
int psx_netplay_is_resimulating(void) { abort(); }
int psx_netplay_cd_bisect_active(void) { abort(); }
uint32_t psx_netplay_sim_tick(void) { abort(); }
uint32_t interrupts_get_cycles_since_vblank(void) { abort(); }
void spu_cd_audio_reset(void) { abort(); }
int dma_cdrom_transfer_active(void) { return test_dma_active; }
void *iso_open(const char *p) { (void)p;abort(); }
void iso_close(void *h) { (void)h;abort(); }
int iso_has_subq_replacements(void *h) { (void)h;abort(); }
uint32_t iso_sector_count(void *h) { (void)h;abort(); }
int iso_track_count(void *h) { (void)h;abort(); }
uint32_t iso_track_start_lba(void *h,int t) { (void)h;(void)t;abort(); }
uint32_t iso_track_pregap_lba(void *h,int t) { (void)h;(void)t;abort(); }
int iso_track_is_audio(void *h,int t) { (void)h;(void)t;abort(); }

static void setup(uint8_t mode,int mute,int mismatch,int coding,int realtime) {
    memset(test_sectors,0,sizeof(test_sectors));
    for(int i=0;i<3;i++) {
        test_sectors[i][15]=2;
        test_sectors[i][16]=1;
        test_sectors[i][17]=2;
        test_sectors[i][18]=i==1 ? (uint8_t)(XA_SUBMODE_AUDIO | (realtime?XA_SUBMODE_REALTIME:0)) : 0x08;
        test_sectors[i][19]=(uint8_t)coding;
        memcpy(test_sectors[i]+20,test_sectors[i]+16,4);
        if(i!=1) test_sectors[i][24]=(uint8_t)(0x41+i);
    }
    clear_sector_buffer();iso_handle=(void*)1;subq_replacements_active=0;
    mode_reg=mode;cd_muted=mute;filter_file=mismatch?9:1;filter_channel=2;
    read_min=0;read_sec=2;read_sect=0;reading=1;read_cmd=0x1b;
    irq_enable=7;irq_flag=0;request_reg=0;stat_reg=CDSTAT_READ;
    pending_dataready=0;xa_data_end_pending=0;audio_frames=0;
    test_dma_active=0;s_warm_route_active=0;
    xa_reset_decode();
}
static uint32_t drain_header(void) {
    request_reg=CDROM_REQUEST_BFRD;
    /* The guest drains the 12-byte raw-sector prefix before its header. */
    if(mode_reg&0x20) for(int i=0;i<3;i++) { assert(cdrom_dma_ready());cdrom_dma_read(); }
    assert(cdrom_dma_ready());return cdrom_dma_read();
}
static void sequence(uint8_t mode,int mute,int mismatch,int coding,int realtime,
                     int audio_only,int expect_audio) {
    setup(mode,mute,mismatch,coding,realtime);
    uint64_t arrivals=s_telemetry_sectors_total, irqs=s_dataready_fires;
    assert(deliver_read_sector()==1);assert(irq_flag==CDIRQ_DATA_READY);
    assert(drain_header()==0x41);irq_flag=0;
    int old_read=s_ring_read,old_write=s_ring_write,old_pos=RB_.pos;
    uint32_t generation=cdrom_irq_generation;
    assert(deliver_read_sector()==!audio_only);
    assert(read_sect==2); /* physical drive and decoder advance even without INT1 */
    assert((audio_frames>0)==expect_audio);
    if(audio_only) {
        assert(irq_flag==0 && cdrom_irq_generation==generation);
        assert(s_ring_read==old_read && s_ring_write==old_write && RB_.pos==old_pos);
        assert(s_dataready_fires==irqs+1 && !pending_dataready);
    } else {
        assert(irq_flag==CDIRQ_DATA_READY && cdrom_irq_generation==generation+1);
        assert(drain_header()==0);irq_flag=0;
    }
    assert(deliver_read_sector()==1);assert(irq_flag==CDIRQ_DATA_READY);
    assert(drain_header()==0x43); /* next data payload, never previous header */
    assert(s_telemetry_sectors_total==arrivals+3);
    assert(s_dataready_fires==irqs+(audio_only?2:3));
}
int main(void) {
    sequence(0xe0,0,0,1,1,1,1); /* ReadS raw + XA, no filter */
    sequence(0xe8,0,0,1,1,1,1); /* matching XA filter */
    sequence(0xe8,0,1,1,1,1,0); /* filtered audio must not become data */
    sequence(0xe0,1,0,1,1,1,0); /* muted audio must not become data */
    sequence(0xe0,0,0,0x31,1,1,0); /* unsupported decoder coding still routed as XA */
    sequence(0xa8,0,0,1,1,1,0); /* filter on, audio decoder off */
    sequence(0xa0,0,0,1,1,0,0); /* both off: sector visible to CPU */
    sequence(0xe0,0,0,1,0,0,0); /* audio flag without realtime is data */
    sequence(0xc0,0,0,1,1,1,1); /* data-only sector size leaves XA route unchanged */
    setup(0xe0,0,0,1,1);assert(deliver_read_sector()==1);drain_header();
    int rd=s_ring_read,wr=s_ring_write,pos=RB_.pos;
    assert(deliver_read_sector_without_irq()==0); /* in-flight/pended path */
    assert(s_ring_read==rd && s_ring_write==wr && RB_.pos==pos && audio_frames>0);
    for(int path=0;path<3;path++) {
        setup(0xe0,0,0,1,1);assert(deliver_read_sector()==1);drain_header();
        irq_flag=path?CDIRQ_DATA_READY:0;test_dma_active=path==2;
        uint64_t pended=s_int1_pended,lost=s_int1_lost,fires=s_dataready_fires;
        uint32_t generation=cdrom_irq_generation;
        rd=s_ring_read;wr=s_ring_write;pos=RB_.pos;read_delay=0;
        process_read_stream(1); /* immediate, pending and active-DMA branches */
        assert(read_sect==2 && audio_frames>0 && read_delay>0);
        assert(s_ring_read==rd && s_ring_write==wr && RB_.pos==pos);
        assert(s_int1_pended==pended && s_int1_lost==lost && !pending_dataready);
        assert(s_dataready_fires==fires && cdrom_irq_generation==generation);
    }
    puts("PASS production data/XA/data: no duplicate INT1 or FIFO header; audio and drive advance");
    return 0;
}
