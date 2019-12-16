from nespy.functions import to_signed_int, to_hex
from nespy.exceptions import InvalidOpcode


class CPU:
    def __init__(self, memory):
        # initialize registers and stuff
        self.memory = memory
        self.sp = 0xFF  # stack pointer
        self.c = 0  # carry
        self.z = 0  # zero
        self.i = 0  # interrupt disable
        self.d = 0  # decimal mode
        self.b = 0  # break command
        self.u = 0  # unused
        self.v = 0  # overflow
        self.n = 0  # negative
        self.a = 0  # accumulator
        self.x = 0  # x and y are general purpose registers
        self.y = 0
        self.pc = 0x8000  # program counter
        self.opcode = None  # the current opcode being executed
        # set up opcode map
        self.opcodes = {0x69: self.adc, 0x65: self.adc, 0x75: self.adc, 0x6D: self.adc,
                        0x7D: self.adc, 0x79: self.adc, 0x61: self.adc, 0x71: self.adc,
                        0x29: self._and, 0x25: self._and, 0x35: self._and, 0x2D: self._and,
                        0x3D: self._and, 0x39: self._and, 0x21: self._and, 0x31: self._and,
                        0x0A: self.asl, 0x06: self.asl, 0x16: self.asl, 0x0E: self.asl,
                        0x1E: self.asl,
                        0x90: self.bcc,
                        0xB0: self.bcs,
                        0xF0: self.beq,
                        0x24: self.bit, 0x2C: self.bit,
                        0x30: self.bmi,
                        0xD0: self.bne,
                        0x10: self.bpl,
                        0x0: self.brk,
                        0x50: self.bvc,
                        0x70: self.bvs,
                        0x18: self.clc,
                        0xD8: self.cld,
                        0x58: self.cli,
                        0xB8: self.clv,
                        0xC9: self.cmp, 0xC5: self.cmp, 0xD5: self.cmp, 0xCD: self.cmp,
                        0xDD: self.cmp, 0xD9: self.cmp, 0xC1: self.cmp, 0xD1: self.cmp,
                        0xE0: self.cpx, 0xE4: self.cpx, 0xEC: self.cpx,
                        0xC0: self.cpy, 0xC4: self.cpy, 0xCC: self.cpy,
                        0xC6: self.dec, 0xD6: self.dec, 0xCE: self.dec, 0xDE: self.dec,
                        0xCA: self.dex,
                        0x88: self.dey,
                        0x49: self.eor, 0x45: self.eor, 0x55: self.eor, 0x4D: self.eor,
                        0x5D: self.eor, 0x59: self.eor, 0x41: self.eor, 0x51: self.eor,
                        0xE6: self.inc, 0xF6: self.inc, 0xEE: self.inc, 0xFE: self.inc,
                        0xE8: self.inx,
                        0xC8: self.iny,
                        0x4C: self.jmp, 0x6C: self.jmp,
                        0x20: self.jsr,
                        0xA9: self.lda, 0xA5: self.lda, 0xB5: self.lda, 0xAD: self.lda,
                        0xBD: self.lda, 0xB9: self.lda, 0xA1: self.lda, 0xB1: self.lda,
                        0xA2: self.ldx, 0xA6: self.ldx, 0xB6: self.ldx, 0xAE: self.ldx,
                        0xBE: self.ldx,
                        0xA0: self.ldy, 0xA4: self.ldy, 0xB4: self.ldy, 0xAC: self.ldy,
                        0xBC: self.ldy,
                        0x4A: self.lsr, 0x46: self.lsr, 0x56: self.lsr, 0x4E: self.lsr,
                        0x5E: self.lsr,
                        0xEA: self.nop, 0x1A: self.nop, 0x3A: self.nop, 0x5A: self.nop,
                        0x7A: self.nop, 0xDA: self.nop, 0xFA: self.nop,
                        0x80: self.nop_immediate, 0x82: self.nop_immediate, 0x89: self.nop_immediate,
                        0xC2: self.nop_immediate, 0xE2: self.nop_immediate,
                        0x09: self.ora, 0x05: self.ora, 0x15: self.ora, 0x0D: self.ora,
                        0x1D: self.ora, 0x19: self.ora, 0x01: self.ora, 0x11: self.ora,
                        0x48: self.pha,
                        0x08: self.php,
                        0x68: self.pla,
                        0x28: self.plp,
                        0x2A: self.rol, 0x26: self.rol, 0x36: self.rol, 0x2E: self.rol,
                        0x3E: self.rol,
                        0x6A: self.ror, 0x66: self.ror, 0x76: self.ror, 0x6E: self.ror,
                        0x7E: self.ror,
                        0x40: self.rti,
                        0x60: self.rts,
                        0xE9: self.sbc, 0xE5: self.sbc, 0xF5: self.sbc, 0xED: self.sbc,
                        0xFD: self.sbc, 0xF9: self.sbc, 0xE1: self.sbc, 0xF1: self.sbc,
                        0x38: self.sec,
                        0xF8: self.sed,
                        0x78: self.sei,
                        0x85: self.sta, 0x95: self.sta, 0x8D: self.sta, 0x9D: self.sta,
                        0x99: self.sta, 0x81: self.sta, 0x91: self.sta,
                        0x86: self.stx, 0x96: self.stx, 0x8E: self.stx,
                        0x84: self.sty, 0x94: self.sty, 0x8C: self.sty,
                        0xAA: self.tax,
                        0xA8: self.tay,
                        0xBA: self.tsx,
                        0x8A: self.txa,
                        0x9A: self.txs,
                        0x98: self.tya}

    def get_pc(self):
        return self.pc

    def set_pc(self, pc):
        self.pc = pc

    # the 6502 has a very particular order that the flags are arranged in: (little endian)
    # N V U B D I Z C
    def get_flags(self):
        flags = 0
        flags |= self.c << 0
        flags |= self.z << 1
        flags |= self.i << 2
        flags |= self.d << 3
        flags |= self.b << 4
        flags |= self.u << 5
        flags |= self.v << 6
        flags |= self.n << 7
        return flags

    def set_flags(self, flags):
        self.c = flags >> 0 & 1
        self.z = flags >> 1 & 1
        self.i = flags >> 2 & 1
        self.d = flags >> 3 & 1
        self.b = flags >> 4 & 1
        self.u = flags >> 5 & 1
        self.v = flags >> 6 & 1
        self.n = flags >> 7 & 1

    def push(self, byte):
        """
        Pushes one byte onto the stack

        Args:
            byte(int): one byte of data
        """
        self.memory[0x100 | self.sp] = byte
        self.sp -= 1

    def pop(self):
        """
        Returns:
            int: one byte from the top of the stack
        """
        self.sp += 1
        value = self.memory[0x100 | self.sp]
        return value

    def push16(self, data):
        """
        Pushes two bytes onto the stack

        Args:
            data(int): two bytes of data
        """
        lsb = data & 0xFF
        msb = data >> 8
        self.push(lsb)
        self.push(msb)

    def pop16(self):
        """
        Returns:
            int: two bytes from the top of the stack
        """
        pass  # TODO

    def push_pc(self):
        self.push16(self.pc)

    def emulate_cycle(self):
        self.opcode = self.memory[self.pc]
        # DEBUG
        print(f'running: {to_hex(self.opcode)} at 0x{to_hex(self.pc)}')
        try:
            self.opcodes[self.opcode]()
        except KeyError:
            raise InvalidOpcode(f"Encountered invalid opcode: {self.opcode}")

    # ADC - Add with Carry
    # Flags: carry, zero, overflow, negative
    def adc(self):
        # immediate
        if self.opcode == 0x69:
            value = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0x65:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x75:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            value = self.memory[value_location]
            self.pc += 2
        # absolute
        elif self.opcode == 0x6D:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        # absolute, x
        elif self.opcode == 0x7D:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.x
            value = self.memory[value_location]
            self.pc += 3
        # absolute, y
        elif self.opcode == 0x79:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.y
            value = self.memory[value_location]
            self.pc += 3
        # indirect, x
        elif self.opcode == 0x61:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = self.memory[value_location]
            self.pc += 2
        # indirect, y (opcode 71)
        else:
            indirect_address = self.memory[self.pc + 1]
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = self.memory[value_location]
            self.pc += 2
        self.z = 0
        self.n = 0
        self.v = 0
        old_accumulator = self.a
        self.a += value + self.c
        if self.a > 255:
            self.c = 1
        else:
            self.c = 0
        if self.a == 0:
            self.z = 1
        elif old_accumulator >> 7 & 1 != self.a >> 7 & 1:
            self.v = 1
        if self.a >> 7 & 1 == 1:
            self.n = 1
        self.a = self.a & 0xFF

    # AND - Logical AND
    # Flags: zero, negative
    def _and(self):
        # immediate
        if self.opcode == 0x29:
            value = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0x25:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x35:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            value = self.memory[value_location]
            self.pc += 2
        # absolute
        elif self.opcode == 0x2D:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        # absolute, x
        elif self.opcode == 0x3D:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.x
            value = self.memory[value_location]
            self.pc += 3
        # absolute, y
        elif self.opcode == 0x39:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.y
            value = self.memory[value_location]
            self.pc += 3
        # indirect, x
        elif self.opcode == 0x21:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = self.memory[value_location]
            self.pc += 2
        # indirect, y (opcode 31)
        else:
            indirect_address = self.memory[self.pc + 1]
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = self.memory[value_location]
            self.pc += 2
        self.z = 0
        self.n = 0
        self.a = self.a & value
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # ASL - Arithmetic Shift Left
    # Bitwise shift left by one bit. Bit 7 is shifted into the Carry flag. Bit 0 is set to zero.
    # Flags: carry, zero, negative
    def asl(self):
        # accumulator
        if self.opcode == 0x0A:
            old_value = self.a
            value = old_value << 1
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == 0x06:
            memory_location = self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value << 1
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x16:
            memory_location = self.memory[self.pc + 1] + self.x & 0xFF
            old_value = self.memory[memory_location]
            value = old_value << 1
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == 0x0E:
            memory_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value << 1
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 1E)
        else:
            memory_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.x
            old_value = self.memory[memory_location]
            value = old_value << 1
            self.memory[memory_location] = value
            self.pc += 3
        self.c = old_value >> 7 & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1
        if value > 127:
            self.n = 1

    # BCC - Branch if Carry Clear (90)
    # Branch to relative offset if carry flag is not set
    def bcc(self):
        self.pc += 2
        if self.c == 0:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # BCS - Branch if Carry Set (B0)
    # Branch to relative offset if carry flag is not set
    def bcs(self):
        self.pc += 2
        if self.c == 1:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # BEQ - Branch if Equal (F0)
    # Branch to relative offset if zero flag is set
    def beq(self):
        self.pc += 2
        if self.z == 1:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # BIT - Bit Test
    # The value in memory is AND'd with the Accumulator to set the Zero flag, and then the result is discarded.
    # Bit 6 of that same value in memory is used to set the Overflow flag, and bit 7 is used for the Negative flag
    # Flags: zero, overflow, negative
    def bit(self):
        # zero page
        if self.opcode == 0x24:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # absolute (opcode 2C)
        else:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        self.z = 0
        self.v = value >> 6 & 1
        self.n = value >> 7 & 1
        if self.a & value == 0:
            self.z = 1

    # BMI - Branch if Minus (30)
    # Branch to relative offset if negative flag is set
    def bmi(self):
        self.pc += 2
        if self.n == 1:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # BNE - Branch if Not Equal (D0)
    # Branch to relative offset if zero flag is not set
    def bne(self):
        self.pc += 2
        if self.z == 0:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # BPL - Branch if Positive (10)
    # Branch to relative offset if negative flag is not set
    def bpl(self):
        self.pc += 2
        if self.n == 0:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # BRK - Force Interrupt (00)
    # Push PC onto stack. Set Break flag. Push processor flags onto stack. Set Interrupt flag. Jump to IRQ Interrupt
    def brk(self):
        self.pc += 1
        self.pc += 1
        self.push_pc()
        self.b = 1
        self.push(self.get_flags())
        self.i = 1
        irq_interrupt_location = self.memory[0xFFFF] + self.memory[0xFFFE]
        self.pc = irq_interrupt_location

    # BVC - Branch if Overflow Clear (50)
    # Branch to relative offset if overflow flag is not set
    def bvc(self):
        self.pc += 2
        if self.v == 0:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # BVS - Branch if Overflow Set (70)
    # Branch to relative offset if overflow flag is set
    def bvs(self):
        self.pc += 2
        if self.v == 1:
            offset = to_signed_int(self.memory[self.pc + 1])
            self.pc += offset

    # CLC - Clear Carry Flag (18)
    def clc(self):
        self.c = 0
        self.pc += 1

    # CLD - Clear Decimal Mode Flag (D8)
    def cld(self):
        self.d = 0
        self.pc += 1

    # CLI - Clear Interrupt Disable Flag (58)
    def cli(self):
        self.i = 0
        self.pc += 1

    # CLV - Clear Overflow Flag (B8)
    def clv(self):
        self.v = 0
        self.pc += 1

    # CMP - Compare
    # Compares A with a value in memory. Set Carry if A>=M, set Zero if A==M, set Negative if A-M<0
    # Flags: carry, zero, negative
    def cmp(self):
        # immediate
        if self.opcode == 0xC9:
            value = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0xC5:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0xD5:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            value = self.memory[value_location]
            self.pc += 2
        # absolute
        elif self.opcode == 0xCD:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        # absolute, x
        elif self.opcode == 0xDD:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.x
            value = self.memory[value_location]
            self.pc += 3
        # absolute, y
        elif self.opcode == 0xD9:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.y
            value = self.memory[value_location]
            self.pc += 3
        # indirect, x
        elif self.opcode == 0xC1:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = self.memory[value_location]
            self.pc += 2
        # indirect y (opcode D1)
        else:
            indirect_address = self.memory[self.pc + 1]
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = self.memory[value_location]
            self.pc += 2
        self.c = 0
        self.z = 0
        self.n = 0
        if self.a >= value:
            self.c = 1
        result = self.a - value
        if result == 0:
            self.z = 1
        elif result < 0:
            self.n = 1

    # CPX - Compare X Register
    # Compares X with a value in memory. Set Carry if X>=M, set Zero if X==M, set Negative if X-M<0
    # Flags: carry, zero, negative
    def cpx(self):
        # immediate
        if self.opcode == 0xE0:
            value = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0xE4:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # absolute (opcode EC)
        else:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        self.c = 0
        self.z = 0
        self.n = 0
        if self.x >= value:
            self.c = 1
        result = self.x - value
        if result == 0:
            self.z = 1
        elif result < 0:
            self.n = 1

    # CPY - Compare Y Register
    # Compares Y with a value in memory. Set Carry if Y>=M, set Zero if Y==M, set Negative if Y-M<0
    # Flags: carry, zero, negative
    def cpy(self):
        # immediate
        if self.opcode == 0xC0:
            value = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0xC4:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # absolute (opcode CC)
        else:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        self.c = 0
        self.z = 0
        self.n = 0
        if self.y >= value:
            self.c = 1
        result = self.y - value
        if result == 0:
            self.z = 1
        elif result < 0:
            self.n = 1

    # DEC - Decrement Memory
    # Flags: zero, negative
    def dec(self):
        # zero page
        if self.opcode == 0xC6:
            value_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0xD6:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 0xCE:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            self.pc += 3
        # absolute, x (opcode DE)
        else:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.x
            self.pc += 3
        self.z = 0
        self.n = 0
        value = self.memory[value_location] - 1 & 0xFF
        self.memory[value_location] = value
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1

    # DEX - Decrement X Register (CA)
    # Flags: negative, zero
    def dex(self):
        self.n = 0
        self.z = 0
        self.x = self.x - 1 & 0xFF
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1

    # DEY - Decrement Y Register (88)
    # Flags: negative, zero
    def dey(self):
        self.n = 0
        self.z = 0
        self.y = self.y - 1 & 0xFF
        if self.y == 0:
            self.z = 1
        elif self.y > 127:
            self.n = 1

    # EOR - Exclusive OR
    # Performs an Exclusive OR on the Accumulator using a byte from memory
    # Flags: zero, negative
    def eor(self):
        # immediate
        if self.opcode == 0x49:
            value_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0x45:
            value_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x55:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 0x4D:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            self.pc += 3
        # absolute, x
        elif self.opcode == 0x5D:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.x
            self.pc += 3
        # absolute, y
        elif self.opcode == 0x59:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.y
            self.pc += 3
        # indirect, x
        elif self.opcode == 0x41:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            self.pc += 2
        # indirect, y (opcode 51)
        else:
            indirect_address = self.memory[self.pc + 1]
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            self.pc += 2
        self.z = 0
        self.n = 0
        value = self.memory[value_location]
        self.a = self.a ^ value
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # INC - Increment Memory
    # Flags: zero, negative
    def inc(self):
        # zero page
        if self.opcode == 0xE6:
            value_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0xF6:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 0xEE:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            self.pc += 3
        # absolute, x (opcode FE)
        else:
            value_location = self.memory[self.pc + 2] + self.memory[self.pc + 1] + self.x
            self.pc += 3
        self.z = 0
        self.n = 0
        value = self.memory[value_location] + 1 & 0xFF
        self.memory[value_location] = value
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1

    # INX - Increment X Register (E8)
    # Flags: negative, zero
    def inx(self):
        self.n = 0
        self.z = 0
        self.x = self.x + 1 & 0xFF
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1

    # INY - Increment Y Register (C8)
    # Flags: negative, zero
    def iny(self):
        self.n = 0
        self.z = 0
        self.y = self.y + 1 & 0xFF
        if self.y == 0:
            self.z = 1
        elif self.y > 127:
            self.n = 1

    # JMP - Jump
    # Set PC to specified address
    def jmp(self):
        # absolute
        if self.opcode == 0x4C:
            # TODO: might be implemented incorrectly
            location = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            self.pc += 3
        # indirect (opcode 6C)
        else:
            indirect_address = self.memory[self.pc + 2] + self.memory[self.pc + 1]
            location = indirect_address + 1 << 8 | indirect_address
            self.pc += 3
        self.pc = location

    # JSR - Jump to Subroutine (20)
    # Store PC-1 in stack (RTS adds 1 when it returns), then jump to absolute address of subroutine
    def jsr(self):
        print(f"DEBUG: JSR {self.memory[self.pc + 2]} {self.memory[self.pc + 1]}")
        subroutine_loc = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        self.push_pc()
        self.pc = subroutine_loc

    # LDA - Load Accumulator (A9, A5, B5, AD, BD, B9, A1, B1)
    # Load a byte into the accumulator.
    # Flags: negative, zero
    def lda(self):
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 0xA9:
            value = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0xA5:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # zero page,x
        elif self.opcode == 0xB5:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            value = self.memory[value_location]
            self.pc += 2
        # absolute
        elif self.opcode == 0xAD:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        # absolute,x
        elif self.opcode == 0xBD:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            value = self.memory[value_location]
            self.pc += 3
        # absolute,y
        elif self.opcode == 0xB9:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.y
            value = self.memory[value_location]
            self.pc += 3
        # indirect,x
        elif self.opcode == 0xA1:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = self.memory[value_location]
            self.pc += 2
        # indirect,y (opcode B1)
        else:
            indirect_address = self.memory[self.pc + 1]
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = self.memory[value_location]
            self.pc += 2
        self.a = value
        if value < 0:
            self.n = 1
        elif value == 0:
            self.z = 1

    # LDX - Load X Register
    # Load a byte into the X register.
    # Flags: negative, zero
    def ldx(self):
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 0xA2:
            data_to_load = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0xA6:
            memory_location = self.memory[self.pc + 1]
            data_to_load = self.memory[memory_location]
            self.pc += 2
        # zero page,y
        elif self.opcode == 0xB6:
            memory_location = self.memory[self.pc + 1] + self.y & 0xFF
            data_to_load = self.memory[memory_location]
            self.pc += 2
        # absolute
        elif self.opcode == 0xAE:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            data_to_load = self.memory[memory_location]
            self.pc += 3
        # absolute,y (opcode BE)
        else:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.y
            data_to_load = self.memory[memory_location]
            self.pc += 3
        self.x = data_to_load
        if data_to_load == 0:
            self.z = 1
        elif data_to_load < 0:
            self.n = 1

    # LDY - Load Y Register
    # Load a byte into the Y register.
    # Flags: negative, zero
    def ldy(self):
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 0xA0:
            data_to_load = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0xA4:
            memory_location = self.memory[self.pc + 1]
            data_to_load = self.memory[memory_location]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0xB4:
            memory_location = self.memory[self.pc + 1] + self.x & 0xFF
            data_to_load = self.memory[memory_location]
            self.pc += 2
        # absolute
        elif self.opcode == 0xAC:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            data_to_load = self.memory[memory_location]
            self.pc += 3
        # absolute, x (opcode BC)
        else:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            data_to_load = self.memory[memory_location]
            self.pc += 3
        self.y = data_to_load
        if data_to_load == 0:
            self.z = 1
        elif data_to_load < 0:
            self.n = 1

    # LSR - Logical Shift Right
    # Bitwise shift right by one bit. Bit 0 is shifted into the Carry flag. Bit 7 is set to zero.
    # Flags: carry, zero, negative
    def lsr(self):
        # accumulator
        if self.opcode == 0x4A:
            old_value = self.a
            value = old_value >> 1
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == 0x46:
            memory_location = self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x56:
            memory_location = self.memory[self.pc + 1] + self.x & 0xFF
            old_value = self.memory[memory_location]
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == 0x4E:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 5E)
        else:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            old_value = self.memory[memory_location]
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 3
        self.c = old_value & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1

    # NOP - No Operation (1 byte)
    def nop(self):
        self.pc += 1

    def nop_immediate(self):
        """
        Unofficial opcode for NOP. Reads an immediate byte and ignores the value.
        """
        self.pc += 2

    # ORA - Logical Inclusive OR
    # Performs a bitwise OR on the Accumulator using a byte from memory
    # Flags: zero, negative
    def ora(self):
        # immediate
        if self.opcode == 0x09:
            value_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0x05:
            value_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x15:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 0x0D:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            self.pc += 3
        # absolute, x
        elif self.opcode == 0x1D:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            self.pc += 3
        # absolute, y
        elif self.opcode == 0x19:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.y
            self.pc += 3
        # indirect, x
        elif self.opcode == 0x01:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            self.pc += 2
        # indirect, y (opcode 11)
        else:
            indirect_address = self.memory[self.pc + 1]
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            self.pc += 2
        self.z = 0
        self.n = 0
        value = self.memory[value_location]
        self.a = self.a | value
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # PHA - Push Accumulator (48)
    def pha(self):
        self.push(self.a)
        self.pc += 1

    # PHP - Push Processor Status (08)
    def php(self):
        self.push(self.get_flags())
        self.pc += 1

    # PLA - Pull Accumulator (68)
    # Flags: negative, zero
    def pla(self):
        self.n = 0
        self.z = 0
        self.a = self.pop()
        if self.a == 0:
            self.z = 1
        elif self.a < 0:
            self.n = 1
        self.pc += 1

    # PLP - Pull Processor Status (28)
    # Flags: all
    def plp(self):
        self.set_flags(self.pop())
        self.pc += 1

    # ROL - Rotate Left
    # Flags: carry, zero, negative
    def rol(self):
        # accumulator
        if self.opcode == 0x2A:
            old_value = self.a
            value = old_value << 1 | self.c
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == 0x26:
            memory_location = self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value << 1 | self.c
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x36:
            memory_location = self.memory[self.pc + 1] + self.x & 0xFF
            old_value = self.memory[memory_location]
            value = old_value << 1 | self.c
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == 0x2E:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value << 1 | self.c
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 3E)
        else:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            old_value = self.memory[memory_location]
            value = old_value << 1 | self.c
            self.memory[memory_location] = value
            self.pc += 3
        self.c = 0
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1
        if old_value > 127:
            self.c = 1

    # ROR - Rotate Right
    # Flags: carry, zero, negative
    def ror(self):
        # accumulator
        if self.opcode == 0x6A:
            old_value = self.a
            value = old_value >> 1 | self.c << 7
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == 0x66:
            memory_location = self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x76:
            memory_location = self.memory[self.pc + 1] + self.x & 0xFF
            old_value = self.memory[memory_location]
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == 0x6E:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            old_value = self.memory[memory_location]
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 7E)
        else:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            old_value = self.memory[memory_location]
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 3
        self.c = old_value & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1

    # RTI - Return from Interrupt (40)
    # Pop processor flags from stack, followed by the program counter
    def rti(self):
        self.set_flags(self.pop())
        return_loc_lsb = self.pop()
        return_loc_msb = self.pop() << 8
        return_loc = return_loc_msb | return_loc_lsb
        self.pc = return_loc

    # RTS - Return from Subroutine (60)
    # Pop return address (minus 1) from stack and jump to it
    def rts(self):
        return_loc_lsb = self.pop()
        return_loc_msb = self.pop() << 8
        return_loc = return_loc_msb | return_loc_lsb
        self.pc = return_loc
        self.pc += 1

    # SBC - Subtract with Carry
    # Flags: carry, zero, overflow, negative
    def sbc(self):
        # immediate
        if self.opcode == 0xE9:
            value = self.memory[self.pc + 1]
            self.pc += 2
        # zero page
        elif self.opcode == 0xE5:
            value_location = self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0xF5:
            value_location = self.memory[self.pc + 1] + self.x & 0xFF
            value = self.memory[value_location]
            self.pc += 2
        # absolute
        elif self.opcode == 0xED:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            value = self.memory[value_location]
            self.pc += 3
        # absolute, x
        elif self.opcode == 0xFD:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            value = self.memory[value_location]
            self.pc += 3
        # absolute, y
        elif self.opcode == 0xF9:
            value_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.y
            value = self.memory[value_location]
            self.pc += 3
        # indirect, x
        elif self.opcode == 0xE1:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = self.memory[value_location]
            self.pc += 2
        # indirect, y (opcode F1)
        else:
            indirect_address = self.memory[self.pc + 1]
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = self.memory[value_location]
            self.pc += 2
        self.z = 0
        self.n = 0
        self.v = 0
        old_accumulator = self.a
        self.a -= value - (1 - self.c)
        if self.a < 0:
            self.c = 1
        else:
            self.c = 0
        if self.a == 0:
            self.z = 1
        elif old_accumulator >> 7 & 1 != self.a >> 7 & 1:
            self.v = 1
        if self.a >> 7 & 1 == 1:
            self.n = 1
        self.a = self.a & 0xFF

    # SEC - Set Carry (38)
    def sec(self):
        self.c = 1
        self.pc += 1

    # SED - Set Decimal (F8)
    def sed(self):
        self.d = 1
        self.pc += 1

    # SEI - Set Interrupt Disable (78)
    def sei(self):
        self.i = 1
        self.pc += 1

    # STA - Store Accumulator
    # Store the accumulator at the specified location in memory
    def sta(self):
        # zero page
        if self.opcode == 0x85:
            memory_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page,x
        elif self.opcode == 0x95:
            memory_location = self.memory[self.pc + 1] + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 0x8D:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            self.pc += 3
        # absolute,x
        elif self.opcode == 0x9D:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.x
            self.pc += 3
        # absolute,y
        elif self.opcode == 0x99:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1] + self.y
            self.pc += 3
        # indirect,x
        elif self.opcode == 0x81:
            indirect_address = self.memory[self.pc + 1] + self.x & 0xFF
            memory_location = indirect_address + 1 << 8 | indirect_address
            self.pc += 2
        # indirect,y (opcode 91)
        else:
            indirect_address = self.memory[self.pc + 1]
            memory_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            self.pc += 2
        self.memory[memory_location] = self.a

    # STX - Store X Register
    # Store the X register at the specified location in memory
    def stx(self):
        # zero page
        if self.opcode == 0x86:
            memory_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page, y
        elif self.opcode == 0x96:
            memory_location = self.memory[self.pc + 1] + self.y & 0xFF
            self.pc += 2
        # absolute (opcode 8E)
        else:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            self.pc += 3
        self.memory[memory_location] = self.x

    # STY - Store Y Register
    # Store the Y register at the specified location in memory
    def sty(self):
        # zero page
        if self.opcode == 0x84:
            memory_location = self.memory[self.pc + 1]
            self.pc += 2
        # zero page, x
        elif self.opcode == 0x94:
            memory_location = self.memory[self.pc + 1] + self.x & 0xFF
            self.pc += 2
        # absolute (opcode 8C)
        else:
            memory_location = (self.memory[self.pc + 2] << 8) | self.memory[self.pc + 1]
            self.pc += 3
        self.memory[memory_location] = self.y

    # TAX - Transfer Accumulator to X (AA)
    # Flags: zero, negative
    def tax(self):
        self.z = 0
        self.n = 0
        self.x = self.a
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1
        self.pc += 1

    # TAY - Transfer Accumulator to Y (A8)
    # Flags: zero, negative
    def tay(self):
        self.z = 0
        self.n = 0
        self.y = self.a
        if self.y == 0:
            self.z = 1
        elif self.y > 127:
            self.n = 1
        self.pc += 1

    # TSX - Transfer Stack Pointer to X (BA)
    # Flags: zero, negative
    def tsx(self):
        self.z = 0
        self.n = 0
        self.x = self.sp
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1
        self.pc += 1

    # TXA - Transfer X to Accumulator (8A)
    # Flags: zero, negative
    def txa(self):
        self.z = 0
        self.n = 0
        self.a = self.x
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1
        self.pc += 1

    # TXS - Transfer X to Stack Pointer (9A)
    def txs(self):
        self.sp = self.x
        self.pc += 1

    # TYA - Transfer Y to Accumulator(98)
    # Flags: zero, negative
    def tya(self):
        self.z = 0
        self.n = 0
        self.a = self.y
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1
        self.pc += 1
