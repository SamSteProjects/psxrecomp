#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include "../src/dma.c"

static unsigned begins, ends, prepasses, ranks;
void gpu_ws_begin_linked_list(void) { begins++; }
void gpu_ws_end_linked_list(void) { ends++; }
void gpu_ws_prepass_linked_list(uint32_t addr) { (void)addr; prepasses++; }
void gpu_ws_restore_linked_list_rank(uint32_t rank) { (void)rank; ranks++; }

static void seed_provenance(void) {
    for (int i = 0; i < 7; i++) s_dma_ch_initiator_pc[i] = 0x80010000u + i * 4u;
    g_dma_initiator_pc = 0x80012340u;
    g_dma_exec_depth = 1; g_dma_cur_ch = 2;
    g_dma_cur_madr = 0x12000; g_dma_cur_bcr = 32;
}

static void check_cleared(void) {
    for (int i = 0; i < 7; i++) assert(s_dma_ch_initiator_pc[i] == 0);
    assert(g_dma_initiator_pc == 0 && g_dma_exec_depth == 0);
    assert(g_dma_cur_ch == -1 && g_dma_cur_madr == 0 && g_dma_cur_bcr == 0);
}

int main(void) {
    seed_provenance(); dma_init(); check_cleared();
    uint8_t *wire = malloc(dma_snapshot_bytes());
    assert(wire);
    channels[2].madr = 0x1000;
    dma_snapshot_write(wire);
    seed_provenance();
    assert(!dma_snapshot_read(wire, dma_snapshot_bytes() - 1));
    assert(g_dma_initiator_pc == 0x80012340u && g_dma_exec_depth == 1);
    assert(s_dma_ch_initiator_pc[2] == 0x80010008u);
    channels[2].madr = 0x2000;
    assert(dma_snapshot_read(wire, dma_snapshot_bytes()));
    check_cleared();
    assert(channels[2].madr == 0x1000);
    assert(!begins && !ends && !prepasses && !ranks);
    gpu_linked_list.active = 1;
    gpu_linked_list.start_addr = 0x1000;
    gpu_linked_list.empty_rank = 7;
    dma_snapshot_write(wire);
    seed_provenance();
    assert(dma_snapshot_read(wire, dma_snapshot_bytes()));
    check_cleared();
    assert(gpu_linked_list.active && gpu_linked_list.empty_rank == 7);
    assert(begins == 1 && ends == 1 && prepasses == 1 && ranks == 1);
    free(wire);
    puts("dma_provenance_restore: PASS");
    return 0;
}
