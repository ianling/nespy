from nespy.apu cimport APU
from nespy.clock cimport Clock
from nespy.cpu cimport CPU
from nespy.ppu cimport PPU


cdef class NES:
    cdef int _memory[0x10000]
    cdef list memory
    cdef double _width_scale, _height_scale
    cdef object _main_window, _debug_window_ppu
    cdef CPU _cpu
    cdef PPU _ppu
    cdef APU _apu
    cdef Clock _master_clock
    cdef str _rom
    cdef int _rom_format
    cdef int _mapper