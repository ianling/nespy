cdef class PPU:
    cdef list _cpu_memory
    cdef list _memory
    cdef dict _sprites
    cdef dict _debug_sprites
    cdef int _scan_line
    cdef int _cycle
    cdef bint _odd_frame
    cdef int _max_cycle_count
    cdef int _max_scan_line

    #cpdef set_memory(self, location, value)