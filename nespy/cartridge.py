from typing import Optional

from .exceptions import InvalidROM, UnsupportedMapper
from .enums import ROMFormat, MapperNumbers
from .mappers.nrom import NROM

Mappers = {
    MapperNumbers.NROM: NROM,
}


class Cartridge:
    def __init__(self, path: Optional[str] = None) -> None:
        if not path:
            return

        # read rom into memory
        self.rom_bytes: list[int] = []
        with open(path, "rb") as rom:
            while byte := rom.read(1):
                self.rom_bytes.append(int.from_bytes(byte, byteorder='little'))

        # parse ROM header
        rom_header = self.rom_bytes[0:16]
        if rom_header[0:4] != [0x4E, 0x45, 0x53, 0x1A]:  # first 4 bytes should be 'NES\x1A'
            raise InvalidROM(f'Invalid ROM header: {rom_header}')

        self.num_prg_banks = rom_header[4]
        self.num_chr_banks = rom_header[5]
        self.flags6 = rom_header[6]
        self.flags7 = rom_header[7]

        # ROM is NES2.0 if 3rd bit of flags7 is set, and 2nd bit is clear
        if self.flags7 & 0b1100 == 0b1000:
            self.rom_format = ROMFormat.INES2_0
            self.flags8 = rom_header[8]
            self._mapper_number = (((self.flags6 & 0b11110000) >> 4) |
                                   (self.flags7 & 0b11110000) |
                                   ((self.flags8 & 0b11110000) << 4))
        else:
            self.rom_format = ROMFormat.INES
            self._mapper_number = ((self.flags6 & 0b11110000) >> 4) | (self.flags7 & 0b11110000)
            self.prg_ram_size = rom_header[8]
        self.flags9 = rom_header[9]
        self.flags10 = rom_header[10]
        # bytes 11-15 of the header are unused

        self.has_trainer = (self.flags6 & 0b00000100 != 0)  # bit 2 of flags6 indicates whether a trainer is present

        # remove rom header before passing bytes to mapper
        self.rom_bytes = self.rom_bytes[16:]

        try:
            self.mapper = Mappers[self._mapper_number](self.rom_bytes, self.num_prg_banks, self.has_trainer)
        except KeyError:
            raise UnsupportedMapper(f"Unsupported mapper number: {self._mapper_number}")

    def cpu_get(self, address: int, size: int) -> list[int]:
        """
        Returns the value at the given memory location, mapped assuming the CPU is the caller.
        """
        return self.mapper.cpu_get(address, size)

    def cpu_set(self, address: int, value: int) -> None:
        """
        Sets the value at the given memory location, mapped assuming the CPU is the caller.
        """
        return self.mapper.cpu_set(address, value)

    def ppu_get(self, address: int, size: int) -> int:
        """
        Returns the value at the given memory location, mapped assuming the PPU is the caller.
        """
        return self.mapper.ppu_get(address, size)

    def ppu_set(self, address: int, value: int) -> None:
        """
        Sets the value at the given memory location, mapped assuming the PPU is the caller.
        """
        return self.mapper.ppu_set(address, value)

    def reset(self) -> None:
        """
        Performs any reset routines necessary for the cartridge's mapper.
        """
        self.mapper.reset()
