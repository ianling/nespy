from nespy.functions import to_signed_int, to_unsigned_int, to_hex
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
        self.opcodes = {'69': self.adc, '65': self.adc, '75': self.adc, '6D': self.adc,
                        '7D': self.adc, '79': self.adc, '61': self.adc, '71': self.adc,
                        '29': self._and, '25': self._and, '35': self._and, '2D': self._and,
                        '3D': self._and, '39': self._and, '21': self._and, '31': self._and,
                        '0A': self.asl, '06': self.asl, '16': self.asl, '0E': self.asl,
                        '1E': self.asl,
                        '90': self.bcc,
                        'B0': self.bcs,
                        'F0': self.beq,
                        '24': self.bit, '2C': self.bit,
                        '30': self.bmi,
                        'D0': self.bne,
                        '10': self.bpl,
                        '00': self.brk,
                        '50': self.bvc,
                        '70': self.bvs,
                        '18': self.clc,
                        'D8': self.cld,
                        '58': self.cli,
                        'B8': self.clv,
                        'C9': self.cmp, 'C5': self.cmp, 'D5': self.cmp, 'CD': self.cmp,
                        'DD': self.cmp, 'D9': self.cmp, 'C1': self.cmp, 'D1': self.cmp,
                        'E0': self.cpx, 'E4': self.cpx, 'EC': self.cpx,
                        'C0': self.cpy, 'C4': self.cpy, 'CC': self.cpy,
                        'C6': self.dec, 'D6': self.dec, 'CE': self.dec, 'DE': self.dec,
                        'CA': self.dex,
                        '88': self.dey,
                        '49': self.eor, '45': self.eor, '55': self.eor, '4D': self.eor,
                        '5D': self.eor, '59': self.eor, '41': self.eor, '51': self.eor,
                        'E6': self.inc, 'F6': self.inc, 'EE': self.inc, 'FE': self.inc,
                        'E8': self.inx,
                        'C8': self.iny,
                        '4C': self.jmp, '6C': self.jmp,
                        '20': self.jsr,
                        'A9': self.lda, 'A5': self.lda, 'B5': self.lda, 'AD': self.lda,
                        'BD': self.lda, 'B9': self.lda, 'A1': self.lda, 'B1': self.lda,
                        'A2': self.ldx, 'A6': self.ldx, 'B6': self.ldx, 'AE': self.ldx,
                        'BE': self.ldx,
                        'A0': self.ldy, 'A4': self.ldy, 'B4': self.ldy, 'AC': self.ldy,
                        'BC': self.ldy,
                        '4A': self.lsr, '46': self.lsr, '56': self.lsr, '4E': self.lsr,
                        '5E': self.lsr,
                        'EA': self.nop,
                        '09': self.ora, '05': self.ora, '15': self.ora, '0D': self.ora,
                        '1D': self.ora, '19': self.ora, '01': self.ora, '11': self.ora,
                        '48': self.pha,
                        '08': self.php,
                        '68': self.pla,
                        '28': self.plp,
                        '2A': self.rol, '26': self.rol, '36': self.rol, '2E': self.rol,
                        '3E': self.rol,
                        '6A': self.ror, '66': self.ror, '76': self.ror, '6E': self.ror,
                        '7E': self.ror,
                        '40': self.rti,
                        '60': self.rts,
                        'E9': self.sbc, 'E5': self.sbc, 'F5': self.sbc, 'ED': self.sbc,
                        'FD': self.sbc, 'F9': self.sbc, 'E1': self.sbc, 'F1': self.sbc,
                        '38': self.sec,
                        'F8': self.sed,
                        '78': self.sei,
                        '85': self.sta, '95': self.sta, '8D': self.sta, '9D': self.sta,
                        '99': self.sta, '81': self.sta, '91': self.sta,
                        '86': self.stx, '96': self.stx, '8E': self.stx,
                        '84': self.sty, '94': self.sty, '8C': self.sty,
                        'AA': self.tax,
                        'A8': self.tay,
                        'BA': self.tsx,
                        '8A': self.txa,
                        '9A': self.txs,
                        '98': self.tya}

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

    # pushes one byte onto the stack
    def push(self, byte):
        self.memory[0x100 | self.sp] = byte
        self.sp -= 1

    # pops one byte off of the stack
    def pop(self):
        self.sp += 1
        value = self.memory[0x100 | self.sp]
        return to_unsigned_int(value)

    # pushes two bytes onto the stack
    def push16(self):
        pass

    # pops two bytes off of the stack
    def pop16(self):
        pass

    def push_pc(self):
        pc_hex = to_hex(self.pc).zfill(4)  # ex: "0C28"
        pc_msb = pc_hex[0:2]
        pc_lsb = pc_hex[2:]
        self.push(pc_msb)
        self.push(pc_lsb)

    def emulate_cycle(self):
        self.opcode = str(self.memory[self.pc])
        print('running: ' + self.opcode + ' at 0x' + to_hex(self.pc))
        try:
            self.opcodes[self.opcode]()
        except KeyError:
            raise InvalidOpcode(f"Encountered invalid opcode: {self.opcode}")

    # ADC - Add with Carry
    # Flags: carry, zero, overflow, negative
    def adc(self):
        # immediate
        if self.opcode == '69':
            value = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == '65':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # zero page, x
        elif self.opcode == '75':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute
        elif self.opcode == '6D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, x
        elif self.opcode == '7D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, y
        elif self.opcode == '79':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # indirect, x
        elif self.opcode == '61':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # indirect, y (opcode 71)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == '29':
            value = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == '25':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # zero page, x
        elif self.opcode == '35':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute
        elif self.opcode == '2D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, x
        elif self.opcode == '3D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, y
        elif self.opcode == '39':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # indirect, x
        elif self.opcode == '21':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # indirect, y (opcode 31)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == '0A':
            old_value = self.a
            value = old_value << 1
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '06':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value << 1
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '16':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value << 1
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == '0E':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value << 1
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 1E)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            old_value = to_unsigned_int(self.memory[memory_location])
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
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.c == 0:
            self.pc += offset

    # BCS - Branch if Carry Set (B0)
    # Branch to relative offset if carry flag is not set
    def bcs(self):
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.c == 1:
            self.pc += offset

    # BEQ - Branch if Equal (F0)
    # Branch to relative offset if zero flag is set
    def beq(self):
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.z == 1:
            self.pc += offset

    # BIT - Bit Test
    # The value in memory is AND'd with the Accumulator to set the Zero flag, and then the result is discarded.
    # Bit 6 of that same value in memory is used to set the Overflow flag, and bit 7 is used for the Negative flag
    # Flags: zero, overflow, negative
    def bit(self):
        # zero page
        if self.opcode == '24':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute (opcode 2C)
        else:
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        self.z = 0
        self.v = value >> 6 & 1
        self.n = value >> 7 & 1
        if self.a & value == 0:
            self.z = 1

    # BMI - Branch if Minus (30)
    # Branch to relative offset if negative flag is set
    def bmi(self):
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.n == 1:
            self.pc += offset

    # BNE - Branch if Not Equal (D0)
    # Branch to relative offset if zero flag is not set
    def bne(self):
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.z == 0:
            self.pc += offset

    # BPL - Branch if Positive (10)
    # Branch to relative offset if negative flag is not set
    def bpl(self):
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.n == 0:
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
        irq_interrupt_location = to_unsigned_int(self.memory[0xFFFF] + self.memory[0xFFFE])
        self.pc = irq_interrupt_location

    # BVC - Branch if Overflow Clear (50)
    # Branch to relative offset if overflow flag is not set
    def bvc(self):
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.v == 0:
            self.pc += offset

    # BVS - Branch if Overflow Set (70)
    # Branch to relative offset if overflow flag is set
    def bvs(self):
        offset = to_signed_int(self.memory[self.pc + 1])
        self.pc += 2
        if self.v == 1:
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
        if self.opcode == 'C9':
            value = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'C5':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'D5':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute
        elif self.opcode == 'CD':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, x
        elif self.opcode == 'DD':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, y
        elif self.opcode == 'D9':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # indirect, x
        elif self.opcode == 'C1':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # indirect y (opcode D1)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == 'E0':
            value = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'E4':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute (opcode EC)
        else:
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == 'C0':
            value = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'C4':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute (opcode CC)
        else:
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == 'C6':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'D6':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 'CE':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x (opcode DE)
        else:
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        self.z = 0
        self.n = 0
        value = to_unsigned_int(self.memory[value_location]) - 1 & 0xFF
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
        if self.opcode == '49':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == '45':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page, x
        elif self.opcode == '55':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '4D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x
        elif self.opcode == '5D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        # absolute, y
        elif self.opcode == '59':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            self.pc += 3
        # indirect, x
        elif self.opcode == '41':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            self.pc += 2
        # indirect, y (opcode 51)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            self.pc += 2
        self.z = 0
        self.n = 0
        value = to_unsigned_int(self.memory[value_location])
        self.a = self.a ^ value
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # INC - Increment Memory
    # Flags: zero, negative
    def inc(self):
        # zero page
        if self.opcode == 'E6':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'F6':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 'EE':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x (opcode FE)
        else:
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        self.z = 0
        self.n = 0
        value = to_unsigned_int(self.memory[value_location]) + 1 & 0xFF
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
        if self.opcode == '4C':
            # TODO: might be implemented incorrectly
            location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # indirect (opcode 6C)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            location = indirect_address + 1 << 8 | indirect_address
            self.pc += 3
        self.pc = location

    # JSR - Jump to Subroutine (20)
    # Store PC-1 in stack (RTS adds 1 when it returns), then jump to absolute address of subroutine
    def jsr(self):
        subroutine_loc = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
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
        if self.opcode == 'A9':
            value = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'A5':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # zero page,x
        elif self.opcode == 'B5':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute
        elif self.opcode == 'AD':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute,x
        elif self.opcode == 'BD':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute,y
        elif self.opcode == 'B9':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # indirect,x
        elif self.opcode == 'A1':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # indirect,y (opcode B1)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == 'A2':
            data_to_load = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'A6':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            data_to_load = to_unsigned_int(self.memory[memory_location])
            self.pc += 2
        # zero page,y
        elif self.opcode == 'B6':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.y & 0xFF
            data_to_load = to_unsigned_int(self.memory[memory_location])
            self.pc += 2
        # absolute
        elif self.opcode == 'AE':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            data_to_load = to_unsigned_int(self.memory[memory_location])
            self.pc += 3
        # absolute,y (opcode BE)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            data_to_load = to_unsigned_int(self.memory[memory_location])
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
        if self.opcode == 'A0':
            data_to_load = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'A4':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            data_to_load = to_unsigned_int(self.memory[memory_location])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'B4':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            data_to_load = to_unsigned_int(self.memory[memory_location])
            self.pc += 2
        # absolute
        elif self.opcode == 'AC':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            data_to_load = to_unsigned_int(self.memory[memory_location])
            self.pc += 3
        # absolute, x (opcode BC)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            data_to_load = to_unsigned_int(self.memory[memory_location])
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
        if self.opcode == '4A':
            old_value = self.a
            value = old_value >> 1
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '46':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '56':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == '4E':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 5E)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 3
        self.c = old_value & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1

    # NOP - No Operation (EA)
    def nop(self):
        self.pc += 1

    # ORA - Logical Inclusive OR
    # Performs a bitwise OR on the Accumulator using a byte from memory
    # Flags: zero, negative
    def ora(self):
        # immediate
        if self.opcode == '09':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == '05':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page, x
        elif self.opcode == '15':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '0D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x
        elif self.opcode == '1D':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        # absolute, y
        elif self.opcode == '19':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            self.pc += 3
        # indirect, x
        elif self.opcode == '01':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            self.pc += 2
        # indirect, y (opcode 11)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            self.pc += 2
        self.z = 0
        self.n = 0
        value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == '2A':
            old_value = self.a
            value = old_value << 1 | self.c
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '26':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value << 1 | self.c
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '36':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value << 1 | self.c
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == '2E':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value << 1 | self.c
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 3E)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            old_value = to_unsigned_int(self.memory[memory_location])
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
        if self.opcode == '6A':
            old_value = self.a
            value = old_value >> 1 | self.c << 7
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '66':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '76':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 2
        # absolute
        elif self.opcode == '6E':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            old_value = to_unsigned_int(self.memory[memory_location])
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 3
        # absolute, x (opcode 7E)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            old_value = to_unsigned_int(self.memory[memory_location])
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
        if self.opcode == 'E9':
            value = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'E5':
            value_location = to_unsigned_int(self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'F5':
            value_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # absolute
        elif self.opcode == 'ED':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, x
        elif self.opcode == 'FD':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # absolute, y
        elif self.opcode == 'F9':
            value_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 3
        # indirect, x
        elif self.opcode == 'E1':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            value_location = indirect_address + 1 << 8 | indirect_address
            value = to_unsigned_int(self.memory[value_location])
            self.pc += 2
        # indirect, y (opcode F1)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            value_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            value = to_unsigned_int(self.memory[value_location])
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
        if self.opcode == '85':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page,x
        elif self.opcode == '95':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '8D':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute,x
        elif self.opcode == '9D':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        # absolute,y
        elif self.opcode == '99':
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            self.pc += 3
        # indirect,x
        elif self.opcode == '81':
            indirect_address = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            memory_location = indirect_address + 1 << 8 | indirect_address
            self.pc += 2
        # indirect,y (opcode 91)
        else:
            indirect_address = to_unsigned_int(self.memory[self.pc + 1])
            memory_location = (indirect_address + 1 << 8 | indirect_address) + self.y
            self.pc += 2
        self.memory[memory_location] = self.a

    # STX - Store X Register
    # Store the X register at the specified location in memory
    def stx(self):
        # zero page
        if self.opcode == '86':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page, y
        elif self.opcode == '96':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.y & 0xFF
            self.pc += 2
        # absolute (opcode 8E)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        self.memory[memory_location] = self.x

    # STY - Store Y Register
    # Store the Y register at the specified location in memory
    def sty(self):
        # zero page
        if self.opcode == '84':
            memory_location = to_unsigned_int(self.memory[self.pc + 1])
            self.pc += 2
        # zero page, x
        elif self.opcode == '94':
            memory_location = to_unsigned_int(self.memory[self.pc + 1]) + self.x & 0xFF
            self.pc += 2
        # absolute (opcode 8C)
        else:
            memory_location = to_unsigned_int(self.memory[self.pc + 2] + self.memory[self.pc + 1])
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
