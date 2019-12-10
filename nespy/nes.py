import pygame

from nespy.apu import APU
from nespy.cpu import CPU
from nespy.exceptions import InvalidROM
from nespy.functions import to_unsigned_int
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
            pygame.init()
            pygame.display.set_caption('NESPy')
            self._display = pygame.display.set_mode(resolution)
            self._clock = pygame.time.Clock()

        # initialize memory
        # see http://nemulator.com/files/nes_emu.txt for memory and ROM info
        self._memory = ['00'] * 0x10000  # 16KiB of RAM

        self._cpu = CPU(self._memory)
        self._ppu = PPU(self._memory)
        self._apu = APU(self._memory)

    def load_rom(self, path):
        # read rom into memory
        rom = open(path, "rb")
        rom_bytes = []
        while True:
            byte = rom.read(1)
            if not byte:
                break
            rom_bytes.append(byte.hex().upper())
        rom_header = rom_bytes[0:16]
        # parse ROM header
        if rom_header[0:4] != ['4E', '45', '53', '1A']:  # first 3 bytes should be 'NES\x1A'
            raise InvalidROM(f'Invalid ROM header: {rom_header}')
        prg_banks = to_unsigned_int(rom_header[4])
        chr_banks = to_unsigned_int(rom_header[5])
        flags6 = to_unsigned_int(rom_header[6])
        flags7 = to_unsigned_int(rom_header[7])
        prg_ram_size = to_unsigned_int(rom_header[8])
        flags9 = to_unsigned_int(rom_header[9])
        flags10 = to_unsigned_int(rom_header[10])
        # bits 11-15 of the header are unused

        if flags6 & 0b00000100 != 0:  # bit 2 of flags6 indicates whether a trainer is present
            rom_has_trainer = 1
        else:
            rom_has_trainer = 0

        rom_prg_start = 0x10 + (0x200 * rom_has_trainer)  # trainer is 0x200 bytes long
        rom_prg_end = rom_prg_start + (0x4000 * prg_banks)  # each prgBank is 0x4000 bytes long
        memory_pointer = 0x8000  # prg_banks get written to memory starting at 0x8000
        rom_prg_bytes = rom_bytes[rom_prg_start:rom_prg_end]
        if prg_banks == 2:
            for byte in rom_prg_bytes:
                self._memory[memory_pointer] = byte
                memory_pointer += 1
        elif prg_banks == 1:  # if there's only one PRG bank on the ROM, it gets duplicated to the 2nd area in memory
            for byte in rom_bytes[rom_prg_start:rom_prg_end]:
                self._memory[memory_pointer] = byte
                self._memory[memory_pointer + 0x4000] = byte
                memory_pointer += 1

        # set pc to RESET vector (0xFFFC-0xFFFD)
        reset_interrupt = self._memory[0xFFFC:0xFFFE]
        reset_interrupt = reset_interrupt[1] + reset_interrupt[0]  # reverse them since NES is little-endian
        self._cpu.set_pc(to_unsigned_int(reset_interrupt))
        print(f"set PC to {self._cpu.get_pc()} == {reset_interrupt}")

    def run(self, block=True):
        # debug
        loop_iterations = 0
        # main loop
        while True:
            # make sure the screen only updates at 60FPS max
            self._clock.tick(60)
            pygame.display.update()
            # check if the player has tried to close the window
            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                exit()
            pygame.event.clear()  # we don't use pygame events
            self._cpu.emulate_cycle()

            # debug
            loop_iterations += 1
            if loop_iterations > 60:
                break
