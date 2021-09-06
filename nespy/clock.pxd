import cython


#ctypedef void (*EMULATE_CYCLE_FUNCTION)()

cdef class Clock:
    cdef int frequency
    cdef int cycle
    cdef bint ticking
    cdef double nanoseconds_per_tick
    cdef double last_cycle_time
    cdef double last_print_time
    cdef list children
    cdef int speed
    cdef double start_time

    #cpdef void start(self)
    #cpdef void stop(self)

    #@cython.locals(delta=cython.double)
    #cpdef void tick(self)

    #cdef void add_child(self, int divisor, void (*func)())

cdef class ChildClock:
    cdef int divisor
    cdef object func
    #cpdef void tick(self)
    #cpdef int get_divisor(self)