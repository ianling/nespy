import pyglet
from pyglet.gl import *

from nespy.apu import APU
from nespy.cpu import CPU
from nespy.enum import ROMFormat, Mapper
from nespy.exceptions import InvalidROM, UnsupportedMapper
from nespy.ppu import PPU


class NES:
    """
    Args:
        resolution(tuple): in the form (int, int). Render resolution.
            if set to None, the emulator can still run, but no video will be drawn to the screen.
            Controller inputs and other manipulations can be performed via the API.
    """
    def __init__(self, resolution=(512, 480)):
        if resolution:
            # overrides pyglet default filtering behavior from GL_LINEAR to GL_NEAREST
            # GL_LINEAR creates really bad blurriness
            pyglet.image.Texture.default_min_filter = GL_NEAREST
            pyglet.image.Texture.default_mag_filter = GL_NEAREST
            # initialize graphics
            self._main_window = pyglet.window.Window(*resolution, caption="NESpy - Main Window")
            self._width_scale = self._main_window.width / 256  # NES native width is 256 pixels
            self._height_scale = self._main_window.height / 240  # NES native height is 240 pixels
            # use main window's scale factor for debug window scale factor
            self._debug_window_ppu = pyglet.window.Window(int(256 * self._width_scale), int(128 * self._height_scale),
                                                          caption="NESpy - Debug (PPU)", visible=False)
            self._render_batch_ppu_debug = pyglet.graphics.Batch()

        self._memory = [0] * 0x10000  # 64KiB
        self._cpu = CPU(self._memory)
        self._ppu = PPU(self, self._memory)
        self._apu = APU(self._memory)

        self._mapper = None
        self._rom = None
        self._rom_format = None

    def load_rom(self, path, reset=True):
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

            rom_chr_bytes = rom_bytes[rom_prg_end:rom_prg_end + 0x2000]  # CHR ROM is 0x2000 bytes long
            memory_pointer = 0
            for byte in rom_chr_bytes:
                self._ppu._memory[memory_pointer] = byte
                memory_pointer += 1
        else:
            raise UnsupportedMapper(f"The mapper {self._mapper} for ROM {path} is not supported.")

        if reset:
            self._cpu.reset()
            self._ppu.reset()

        self._rom = path

    def tick(self, dt):
        self._cpu.emulate_cycle()
        self._ppu.emulate_cycle()

    @staticmethod
    def _toggle_window(window):
        window.set_visible(not window.visible)

    def toggle_window_debug_ppu(self):
        self._toggle_window(self._debug_window_ppu)

    def run(self):
        pyglet.clock.schedule_interval(self.tick, interval=1/60.0)  # 60 FPS

        @self._main_window.event
        def on_close():
            """
            exit program when the main window is closed
            """
            pyglet.app.exit()

        @self._main_window.event
        def on_key_press(symbol, modifiers):
            if symbol == pyglet.window.key.F11:
                self.toggle_window_debug_ppu()

        @self._debug_window_ppu.event
        def on_draw():
            self._debug_window_ppu.clear()
            self._ppu.generate_debug_sprites()
            self._render_batch_ppu_debug.draw()

        pyglet.app.run()
