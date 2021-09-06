from OpenGL.GL import *
from OpenGL.GLUT import *
from typing import Optional

from nespy.apu import APU
from nespy.clock import Clock
from nespy.cpu import CPU
from nespy.enum import ROMFormat, Mapper
from nespy.exceptions import InvalidROM, UnsupportedMapper
from nespy.ppu import PPU


def square():
    glBegin(GL_QUADS)
    glVertex2f(100, 100)
    glVertex2f(200, 100)
    glVertex2f(200, 200)
    glVertex2f(100, 200)
    glEnd()


def iterate():
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    iterate()
    glColor3f(1.0, 0.0, 3.0)
    square()
    glutSwapBuffers()


class NES:
    """
    Args:
        resolution(tuple): in the form (int, int). Render resolution.
            if set to None, the emulator can still run, but no video will be drawn to the screen.
            Controller inputs and other manipulations can be performed via the API.
    """
    def __init__(self, resolution: Optional[tuple[int, int]] = (512, 480), disassemble: Optional[bool] = False) -> None:
        if resolution:
            self._width_scale = resolution[0] / 256  # NES native width is 256 pixels
            self._height_scale = resolution[1] / 240  # NES native height is 240 pixels
            # overrides opengl's default filtering behavior from GL_LINEAR to GL_NEAREST
            # GL_LINEAR creates really bad blurriness
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            # initialize graphics
            glutInit()
            glutInitDisplayMode(GLUT_RGBA)
            glutInitWindowSize(*resolution)
            glutInitWindowPosition(0, 0)
            self._main_window = glutCreateWindow("NESpy - Main Window")
            glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_GLUTMAINLOOP_RETURNS)
            glutInitWindowSize(int(256 * self._width_scale), int(128 * self._height_scale))
            self._debug_window_ppu = glutCreateWindow("NESpy - Debug (PPU)")
            glutHideWindow()
            #glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_CONTINUE_EXECUTION)
            #self._render_batch_ppu_debug = pyglet.graphics.Batch()
        self._memory = [0] * 0x10000  # 64KiB
        self._cpu = CPU(self._memory, disassemble=disassemble)
        self._ppu = PPU(self._memory)
        self._apu = APU(self._memory)
        self._master_clock = Clock(21477272)  # NTSC NES master clock frequency is ~21.477272 MHz
        self._master_clock.add_child(12, self._cpu.emulate_cycle)  # CPU clock frequency is master / 12
        self._master_clock.add_child(4, self._ppu.emulate_cycle)  # PPU clock frequency is master / 4

        self._mapper = -1
        self._rom_format = -1

    def load_rom(self, path: str, reset: bool = True) -> None:
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
        if rom_header[0:4] != [0x4E, 0x45, 0x53, 0x1A]:  # first 4 bytes should be 'NES\x1A'
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
                self._ppu.set_memory(memory_pointer, byte)
                memory_pointer += 1
        else:
            raise UnsupportedMapper(f"The mapper {self._mapper} for ROM {path} is not supported.")

        if reset:
            self._cpu.reset()
            self._ppu.reset()

        self._rom = path

    def update_display(self) -> None:
        pass

    def keyboard_handler(self) -> None:
        pass

    def run(self) -> None:
        """
        glutDisplayFunc(self.update_display)
        glutKeyboardFunc(self.keyboard_handler)
        glutIdleFunc(self._master_clock.tick)

        glutMainLoop()
        """
        self._master_clock.start()
