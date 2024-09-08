from . import Mapper


class NROM(Mapper):
    def __init__(self, rom_bytes: list[int], num_prg_banks: int, rom_has_trainer: bool):
        self.rom_bytes = rom_bytes
        self.num_prg_banks = num_prg_banks
        self.rom_has_trainer = rom_has_trainer
        self._bank_size = 0x4000
        self.rom_prg_start = 0x8000  # PRG banks start at 0x8000
        self.rom_prg_start += 0x200 * self.rom_has_trainer  # trainer is 0x200 bytes long, if present
        self.rom_prg_end = self.rom_prg_start + (self._bank_size * self.num_prg_banks)

    def reset(self):
        # no reset necessary for NROM
        pass

    def ppu_set(self, rom_data: list[int], vram: list[int]) -> None:
        rom_chr_bytes = rom_data[self.rom_prg_end:self.rom_prg_end + 0x2000]  # CHR ROM is 0x2000 bytes long
        memory_pointer = 0
        for byte in rom_chr_bytes:
            vram[memory_pointer] = byte
            memory_pointer += 1

    def cpu_set(self, rom_data: list[int], ram: list[int]) -> None:
        print("i don't think this is supposed to happen in NROM")

    def cpu_get(self, address: int, size: int) -> list[int]:
        address -= self.rom_prg_start
        if address >= self._bank_size:
            # if there's only one PRG bank in the ROM, it gets mirrored starting at 0xC000 (0x8000+0x4000)
            address -= 0x4000
        return self.rom_bytes[address:address+size]
