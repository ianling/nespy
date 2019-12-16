import pyglet

from nespy.apu import APU
from nespy.cpu import CPU
from nespy.enum import ROMFormat, Mapper
from nespy.exceptions import InvalidROM, UnsupportedMapper
from nespy.ppu import PPU


class NES:
    """
    Args:
        resolution(tuple): in the form (int, int). Render resolution. NES native resolution is 256x240.
            if set to None, the emulator will still run, but
    """
    def __init__(self, resolution=(256, 240)):
        if resolution:
            # initialize graphics
            self._main_window = pyglet.window.Window()

        # initialize memory
        # see http://nemulator.com/files/nes_emu.txt for memory and ROM info
        self._memory = [0] * 0x10000  # 64KiB of RAM

        self._cpu = CPU(self._memory)
        self._ppu = PPU(self._memory)
        self._apu = APU(self._memory)

        self._mapper = None
        self._rom = None
        self._rom_format = None

    def load_rom(self, path):
        # read rom into memory
        rom = open(path, "rb")
        rom_bytes = []
        while True:
            byte = rom.read(1)
            if not byte:
                break
            rom_bytes.append(int.from_bytes(byte, byteorder='little'))
        rom_header = rom_bytes[0:16]
        # parse ROM header
        if rom_header[0:4] != [0x4E, 0x45, 0x53, 0x1A]:  # first 3 bytes should be 'NES\x1A'
            raise InvalidROM(f'Invalid ROM header: {rom_header}')
        prg_banks = rom_header[4]
        chr_banks = rom_header[5]
        flags6 = rom_header[6]
        flags7 = rom_header[7]

        # ROM is NES2.0 if 3rd bit of flags7 is set, and 2nd bit is clear
        if flags7 & 0b1100 == 0b1000:
            self._rom_format = ROMFormat.INES2_0
            flags8 = rom_header[8]
            self._mapper = ((flags6 & 0b11110000) >> 4) | (flags7 & 0b11110000) | ((flags8 & 0b11110000) << 4)
        else:
            self._rom_format = ROMFormat.INES
            self._mapper = ((flags6 & 0b11110000) >> 4) | (flags7 & 0b11110000)
            prg_ram_size = rom_header[8]
        flags9 = rom_header[9]
        flags10 = rom_header[10]
        # bits 11-15 of the header are unused

        rom_has_trainer = (flags6 & 0b00000100 != 0)  # bit 2 of flags6 indicates whether a trainer is present

        if self._mapper == Mapper.NROM:
            rom_prg_start = 0x10 + (0x200 * rom_has_trainer)  # trainer is 0x200 bytes long
            rom_prg_end = rom_prg_start + (0x4000 * prg_banks)  # each prgBank is 0x4000 bytes long
            memory_pointer = 0x8000  # prg_banks get written to memory starting at 0x8000
            rom_prg_bytes = rom_bytes[rom_prg_start:rom_prg_end]
            for byte in rom_prg_bytes:
                self._memory[memory_pointer] = byte
                if prg_banks == 1:  # if there's only one PRG bank on the ROM, it gets duplicated to the 2nd area in memory
                    self._memory[memory_pointer + 0x4000] = byte
                memory_pointer += 1
        else:
            raise UnsupportedMapper(f"The mapper {self._mapper} for ROM {path} is not supported.")

        # set pc to RESET vector (0xFFFC-0xFFFD)
        reset_interrupt = self._memory[0xFFFC:0xFFFE]
        reset_interrupt = (reset_interrupt[1] << 8) | reset_interrupt[0]  # reverse them since NES is little-endian
        self._cpu.set_pc(reset_interrupt)
        self._rom = path

    def run(self):
        pyglet.clock.schedule_interval(self.tick, interval=1/60.0)  # 60 FPS
        pyglet.app.run()

    def tick(self, dt):
        self._cpu.emulate_cycle()
        print(f"PPU registers: 2000 - 2007: {self._memory[0x2000:0x2008]}")
