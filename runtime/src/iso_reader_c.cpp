/*
 * iso_reader_c.cpp — C wrapper for the C++ ISOReader class
 *
 * Provides iso_open() / iso_read_sector() / iso_close() for use by cdrom.c
 */

#include "iso_reader.h"
#include "mod_runtime.h"
#include <cstdio>

using ISOHandle=std::shared_ptr<PS1::ISOReader>;
static PS1::ISOReader* current_reader(void* handle) {
    if(!handle)return nullptr;
    const auto& reader=*static_cast<ISOHandle*>(handle);
    return PSXRecompV4::mod_runtime_iso_reader_current(reader)?reader.get():nullptr;
}

extern "C" {

void* iso_open(const char* path) {
    if(!path)return nullptr;
    ISOHandle reader;std::string error;
    if(!PSXRecompV4::mod_runtime_open_iso_reader(path,reader,&error)) {
        std::fprintf(stderr,"psxrecomp: disc reader open rejected: %s\n",error.c_str());return nullptr;
    }
    return new ISOHandle(std::move(reader));
}

int iso_read_sector(void* handle, uint32_t lba, uint8_t* buffer, int size) {
    auto* reader = current_reader(handle);
    if (!reader || size<2048) return 0;
    if (!reader->ReadSector(lba, buffer)) return 0;
    mod_runtime_patch_disc_sector(lba, 0, buffer, 2048);
    return 1;
}

int iso_read_raw_sector(void* handle, uint32_t lba, uint8_t* buffer, int size) {
    auto* reader = current_reader(handle);
    if (!reader || size < 2352) return 0;
    if (!reader->ReadRawSector(lba, buffer)) return 0;
    mod_runtime_patch_disc_sector(lba, 1, buffer, 2352);
    return 1;
}

int iso_read_subq(void* handle, uint32_t lba, uint8_t* buffer, int size,
                  int* valid) {
    auto* reader=current_reader(handle);
    if (!reader || !buffer || size < 12 || !valid) return 0;
    bool crc_valid = false;
    if (!reader->ReadSubChannelQ(
            lba, buffer, &crc_valid)) return 0;
    *valid = crc_valid ? 1 : 0;
    return 1;
}

int iso_has_subq_replacements(void* handle) {
    auto* reader=current_reader(handle);
    return reader && reader->HasSubChannelReplacements();
}

uint32_t iso_sector_count(void* handle) {
    auto* reader = current_reader(handle);
    return reader?reader->GetSectorCount():0;
}

/* CD-track TOC accessors (multi-track / CD-DA support). track is 1-based. */
int iso_track_count(void* handle) {
    if (!handle) return 1;
    auto* reader=current_reader(handle);
    return reader?reader->TrackCount():0;
}

uint32_t iso_track_start_lba(void* handle, int track) {
    auto* reader=current_reader(handle);
    return reader?reader->TrackStartLBA(track):0;
}

uint32_t iso_track_pregap_lba(void* handle, int track) {
    auto* reader = current_reader(handle);
    return reader ? reader->TrackPregapLBA(track) : 0;
}

int iso_track_is_audio(void* handle, int track) {
    auto* reader=current_reader(handle);
    return reader && reader->TrackIsAudio(track)?1:0;
}

void iso_close(void* handle) {
    if (!handle) return;
    delete static_cast<ISOHandle*>(handle);
}

} /* extern "C" */
