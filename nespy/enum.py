class ROMFormat:
    INES = 0
    INES2_0 = 1


class Mapper:
    """
    Maps mapper names to mapper values found in iNES ROMs
    """
    NROM = 0
    MMC1 = 1
    UXROM = 2
    CNROM = 3
    MMC3 = 4
    AXROM = 7
    MMC2 = 9


class PPURegister:
    PPUCTRL = 0x2000
    PPUMASK = 0x2001
    PPUSTATUS = 0x2002
    OAMADDR = 0x2003
    OAMDATA = 0x2004
    PPUSCROLL = 0x2005
    PPUADDR = 0x2006
    PPUDATA = 0x2007
