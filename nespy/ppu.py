# import pyglet
from nespy.enum import PPURegister

"""
TODO: clear vblank any time 0x2002 (PPUSTATUS) is read
"""


class PPU:
    # TODO: rename cpu_memory?
    def __init__(self, cpu_memory: list[int]) -> None:
        self._cpu_memory = cpu_memory
        # TODO: verify PPU startup and reset states
        self._memory = [0] * 0x4000  # 16KiB of RAM
        self._sprites = {}
        self._debug_sprites = {}
        self._scan_line = 261
        self._cycle = 0
        self._odd_frame = False
        self._max_cycle_count = 340
        self._max_scan_line = 261
        self.reset()

    def reset(self) -> None:
        self._memory = [0] * 0x4000  # 16KiB of RAM
        self._sprites = {}
        self._debug_sprites = {}
        self._scan_line = 261
        self._cycle = 0
        self._odd_frame = False
        self._max_cycle_count = 340
        self._max_scan_line = 261
        self._cpu_memory[PPURegister.PPUCTRL] = 0
        self._cpu_memory[PPURegister.PPUMASK] = 0
        self._cpu_memory[PPURegister.PPUSTATUS] = 0b10100000
        self._cpu_memory[PPURegister.PPUSCROLL] = 0
        self._cpu_memory[PPURegister.PPUDATA] = 0

    def set_memory(self, location: int, value: int) -> None:
        self._memory[location] = value

    """
    def generate_debug_sprites(self) -> None:
        # temp palette until palettes are implemented
        color_map = [(0, 0, 0),
                     (255, 0, 0),
                     (0, 255, 0),
                     (255, 255, 255)]
        if self._debug_sprites != {}:
            return
        # pattern tables stored in PPU memory from 0x0 to 0x2000
        for tile_offset in range(0, 0x2000, 0x10):
            tile1 = self._memory[0x0 + tile_offset: 0x8 + tile_offset]
            tile2 = self._memory[0x8 + tile_offset: 0x10 + tile_offset]
            imagemap = [[0 for x in range(8)] for y in range(8)]
            for row, byte in enumerate(tile1):
                for column in range(8):
                    if byte & 2**column:
                        imagemap[row][column] |= 0b00000001
            for row, byte in enumerate(tile2):
                for column in range(8):
                    if byte & 2**column:
                        imagemap[row][column] |= 0b00000010

            encoded_image_data = b""
            for y, row in enumerate(imagemap):
                for x, pixel in enumerate(row):
                    encoded_image_data = bytes(color_map[pixel]) + encoded_image_data
            image = pyglet.image.ImageData(8, 8, "RGB", encoded_image_data, pitch=24)
            sprite = pyglet.sprite.Sprite(image, batch=self._nes._render_batch_ppu_debug)
            self._debug_sprites[tile_offset] = sprite

        sprite_height = 8 * self._nes._height_scale
        sprite_width = 8 * self._nes._width_scale
        sprites_per_line = 16  # also sprites_per_column (it's a square)
        total_sprites = 512
        for sprite_number, sprite in enumerate(self._debug_sprites.values()):
            sprite.update(scale_x=self._nes._width_scale, scale_y=self._nes._height_scale)
            sprite.x = sprite_width * (sprite_number % sprites_per_line)
            sprite.y = (self._nes._debug_window_ppu.height - sprite_height) - sprite_height * (sprite_number // sprites_per_line)
            if sprite_number >= total_sprites / 2:
                # halfway through the sprite list, start drawing at the top of the right half of the window
                sprite.x += sprite_width * sprites_per_line
                sprite.y += self._nes._debug_window_ppu.height
    """

    def emulate_cycle(self) -> None:
        self._tick()

    def _tick(self) -> None:
        if 0 <= self._scan_line <= 239:
            pass
        elif self._scan_line == 240:
            pass
        elif self._scan_line == 241 and self._cycle == 1:
            # set the vblank flag
            self._cpu_memory[PPURegister.PPUSTATUS] |= 0b10000000
        elif self._scan_line == 261 and self._cycle == 1:
            # unset the vblank, sprite 0 hit, and overflow flags
            self._cpu_memory[PPURegister.PPUSTATUS] = 0

        self._cycle += 1
        if self._cycle > self._max_cycle_count:
            self._cycle = 0
            self._scan_line += 1
            if self._scan_line > self._max_scan_line:
                self._scan_line = 0
                self._odd_frame = not self._odd_frame
