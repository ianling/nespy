from OpenGL.GL import glBegin, glVertex2f, glEnd, glViewport, glMatrixMode, glLoadIdentity, glOrtho, glClear, \
    glColor3f, glTexParameteri, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, \
    GL_TEXTURE_MAG_FILTER, GL_NEAREST, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_QUADS, GL_PROJECTION, GL_MODELVIEW
from OpenGL.GLUT import glutInit, glutInitDisplayMode, glutInitWindowSize, glutInitWindowPosition, glutCreateWindow, \
    glutSwapBuffers, glutSetOption, glutHideWindow, GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_GLUTMAINLOOP_RETURNS, \
    GLUT_RGBA
from typing import Optional

from .apu import APU
from .cartridge import Cartridge
from .clock import Clock
from .cpu import CPU
from .ppu import PPU


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


def show_screen():
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
    def __init__(self, resolution: Optional[tuple[int, int]] = (512, 480), disassemble: bool = False) -> None:
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
            # glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_CONTINUE_EXECUTION)
            # self._render_batch_ppu_debug = pyglet.graphics.Batch()
        self._cartridge = Cartridge()
        self._cpu = CPU(self._cartridge, disassemble=disassemble)
        self._ppu = PPU(self._cartridge)
        self._apu = APU()
        self._master_clock = Clock(21477272)  # NTSC NES master clock frequency is ~21.477272 MHz
        self._master_clock.add_child(12, self._cpu.emulate_cycle)  # CPU clock frequency is master / 12
        self._master_clock.add_child(4, self._ppu.emulate_cycle)  # PPU clock frequency is master / 4

        # kludge: grant the CPU direct access to the PPU registers
        self._cpu.ppu_registers = self._ppu.registers
        # kludge: grant the PPU direct access to the CPU for the purpose of setting the nmi_active bool
        self._ppu._cpu = self._cpu

    def insert_cartridge(self, path: str, reset: bool = True) -> None:
        self._cartridge = Cartridge(path)
        # kludge: swap out the cartridge in the CPU and PPU
        self._cpu.cartridge = self._cartridge
        self._ppu.cartridge = self._cartridge

        if reset:
            self.reset()

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

    def reset(self) -> None:
        self._cpu.reset()
        self._ppu.reset()
        self._cartridge.reset()
