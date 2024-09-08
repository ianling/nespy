cdef class CPU:
    cdef:
        list memory
        bint disassemble, nmi_low, irq_low
        dict opcodes
        int c, z, i, d, b, u, v, n, a, x, y, pc, sp, opcode
    #cpdef int fetch_uint16(self, int length=*, int address=*)
    #cpdef list fetch_memory(self, int length=*, int address=*)
    #cpdef void write_memory(self, int address, int value)
    #cpdef emulate_cycle(self)
