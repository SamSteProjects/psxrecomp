"""Read-only logical ISO view of a grown PROT, without exporting a disc image."""
from hashlib import sha256

from .core import ImportError, Mode2Image, MODE2_SECTOR, USER_SIZE
from .iso_relocation import collect_metadata_relocation


class RelocatedLogicalDisc(Mode2Image):
    """Borrow an already-open source image; caller retains its lifetime/ownership.

    Source sectors after PROT map to their shifted logical positions. Replacement
    PROT and relocated ISO metadata supply only logical Form-1 user data. Raw CD,
    subchannel and runtime sector-count integration are deliberately separate.
    """

    def __init__(self, source, replacement, expected_prot_sha256):
        if not isinstance(replacement, bytes) or not replacement or len(replacement) % USER_SIZE:
            raise ImportError('Logical PROT replacement requires whole sectors')
        if type(source.size) is not int or source.size <= 0 or source.size % MODE2_SECTOR:
            raise ImportError('Logical source requires a whole-sector disc extent')
        prot = source.find('PROT.DAT')
        if (prot.is_dir or type(prot.extent_lba) is not int or prot.extent_lba < 0
                or not prot.size or prot.size % USER_SIZE or len(replacement) < prot.size
                or prot.extent_lba+prot.size//USER_SIZE > source.size//MODE2_SECTOR):
            raise ImportError('Logical PROT ownership or replacement size changed')
        digest = sha256()
        for lba in range(prot.extent_lba, prot.extent_lba+prot.size//USER_SIZE):
            sector = source.user_sector(lba)
            if not isinstance(sector, bytes) or len(sector) != USER_SIZE:
                raise ImportError('Logical source PROT sector is truncated')
            digest.update(sector)
        if digest.hexdigest() != expected_prot_sha256:
            raise ImportError('Logical source PROT hash changed')
        growth = (len(replacement)-prot.size)//USER_SIZE
        metadata, metadata_audit = collect_metadata_relocation(source, growth)
        self.source, self.replacement = source, replacement
        self.prot_lba, self.old_prot_bytes = prot.extent_lba, prot.size
        self.insertion_lba = prot.extent_lba+prot.size//USER_SIZE
        self.growth_sectors = growth
        self.size = source.size+growth*MODE2_SECTOR
        self.metadata = {}
        sectors = []
        for old_lba,payload in sorted(metadata.items()):
            if prot.extent_lba <= old_lba < self.insertion_lba:
                raise ImportError('Logical ISO metadata overlaps PROT ownership')
            new_lba = old_lba+(growth if old_lba >= self.insertion_lba else 0)
            self.metadata[new_lba] = payload
            sectors.append(dict(source_lba=old_lba, proposed_lba=new_lba,
                source_sha256=sha256(source.user_sector(old_lba)).hexdigest(),
                proposed_sha256=sha256(payload).hexdigest()))
        self.root = self._directory_record(self.user_sector(16), 156)
        reopened = self.find('PROT.DAT')
        if reopened.extent_lba != prot.extent_lba or reopened.size != len(replacement):
            raise ImportError('Logical reopened ISO PROT ownership disagrees with replacement')
        self.audit = dict(schema_version='legaia.relocated-logical-disc.v1',
            source_sector_count=source.size//MODE2_SECTOR, proposed_sector_count=self.size//MODE2_SECTOR,
            prot_lba=self.prot_lba, source_prot_bytes=prot.size, proposed_prot_bytes=len(replacement),
            source_prot_sha256=expected_prot_sha256, proposed_prot_sha256=sha256(replacement).hexdigest(),
            insertion_lba=self.insertion_lba, growth_sectors=growth,
            metadata=metadata_audit, metadata_sectors=sectors, reopened_iso_prot_verified=True,
            runtime_connected=False, build_ready=False, gameplay_verified=False)

    def user_sector(self, lba):
        if type(lba) is not int or not 0 <= lba < self.size//MODE2_SECTOR:
            raise ImportError('Relocated logical LBA is outside disc bounds')
        if lba in self.metadata:
            return self.metadata[lba]
        relative = lba-self.prot_lba
        if 0 <= relative < len(self.replacement)//USER_SIZE:
            return self.replacement[relative*USER_SIZE:(relative+1)*USER_SIZE]
        old_lba = lba-(self.growth_sectors if lba >= self.insertion_lba+self.growth_sectors else 0)
        return self.source.user_sector(old_lba)

    def _raw_sector(self, _lba):
        raise ImportError('Relocated logical view does not supply raw CD sectors')

    def close(self):
        """The borrowed source is never closed by this view."""
