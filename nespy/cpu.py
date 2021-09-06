import logging

from nespy.util import to_signed_int, to_uint16, to_hex
from nespy.enum import AddressingMode, AddressingModeDisasmFormat, InstructionAddressingModeMap,\
    InstructionMnemonicMap, InstructionDisasmExtras, InstructionLengthMap


class CPU:
    def __init__(self, memory: list[int], disassemble: bool = False) -> None:
        self.memory = memory
        self.disassemble = disassemble
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
        self.sp = 0xFD  # stack pointer, 0xFD at power-on
        self.c = 0  # carry
        self.z = 0  # zero
        self.i = 1  # interrupt disable, set at power-on
        self.d = 0  # decimal mode
        self.b = 1  # break command, set at power-on
        self.u = 1  # unused, set at power-on
        self.v = 0  # overflow
        self.n = 0  # negative
        self.a = 0  # accumulator
        self.x = 0  # x and y are general purpose registers
        self.y = 0
        self.pc = 0x8000  # program counter
        self.opcode = 0x00  # the current instruction being executed
        self.irq_low = False
        self.nmi_low = False

        self.reset()

    def reset(self) -> None:
        self.sp = self.sp - 3 & 0xFF  # 3 is subtracted from SP on reset
        self.c = 0
        self.z = 0
        self.i = 1  # set on reset
        self.d = 0
        self.b = 1  # set on reset
        self.u = 1  # set on reset
        self.v = 0
        self.n = 0
        self.a = 0
        self.x = 0
        self.y = 0
        self.pc = 0x8000
        self.opcode = 0x00
        self.irq_low = False
        self.nmi_low = False

        # set pc to RESET vector (0xFFFC-0xFFFD)
        reset_interrupt = self.fetch_uint16(2, address=0xFFFC)
        self.pc = reset_interrupt

    # the 6502 has a very particular order that the flags are arranged in: (little endian)
    # N V U B D I Z C
    def get_flags(self) -> int:
        flags = 0
        flags |= self.c << 0
        flags |= self.z << 1
        flags |= self.i << 2
        flags |= self.d << 3
        flags |= 1 << 4  # the b flag will always be set to 1 when the flags are being pushed to the stack
        # flags |= self.b << 4
        flags |= self.u << 5
        flags |= self.v << 6
        flags |= self.n << 7
        return flags

    def set_flags(self, flags: int) -> None:
        self.c = flags >> 0 & 1
        self.z = flags >> 1 & 1
        self.i = flags >> 2 & 1
        self.d = flags >> 3 & 1
        # bits 4 and 5 do not get set when flags are being pulled from the stack
        # self.b = flags >> 4 & 1
        # self.u = flags >> 5 & 1
        self.v = flags >> 6 & 1
        self.n = flags >> 7 & 1

    def push(self, byte: int) -> None:
        """
        Pushes one byte onto the stack

        Args:
            byte(int): one byte of data
        """
        self.memory[0x100 | self.sp] = byte
        self.sp = self.sp - 1 & 0xFF

    def pop(self) -> int:
        """
        Returns:
            int: one byte from the top of the stack
        """
        self.sp = self.sp + 1 & 0xFF
        value = self.fetch_uint16(1, address=0x100 | self.sp)
        return value

    def push16(self, data: int) -> None:
        """
        Pushes two bytes onto the stack

        Args:
            data(int): two bytes of data
        """
        lsb = data & 0xFF
        msb = data >> 8
        self.push(msb)
        self.push(lsb)

    def pop16(self) -> int:
        """
        Returns:
            int: two bytes from the top of the stack
        """
        lsb = self.pop()
        msb = self.pop()
        return msb << 8 | lsb

    def push_pc(self) -> None:
        self.push16(self.pc)

    def fetch_uint16(self, length: int = 2, address: int = -1) -> int:
        data = self.fetch_memory(length, address)
        if length > 1:
            return to_uint16(data)
        else:
            return data[0]

    def fetch_memory(self, length: int = 2, address: int = -1) -> list[int]:
        """
        Args:
            length(int): number of bytes to retrieve. default=2
            address(int): address to start reading from. uses self.pc if address=-1. default=-1

        Returns:
            list or int: if return_int, returns an integer. Otherwise, a list of bytes
        """
        if address == -1:
            address = self.pc
        # handle mirrored memory accesses
        if 0x2008 <= address <= 0x3FFF:
            address = (address % 0x8) + 0x2000
        # if this is a zero-page lookup, we have to handle potential overflows
        if address <= 0xFF < address + length:
            overflow_amount = address + length & 0xFF
            data = self.memory[address:address+length-overflow_amount]
            data += self.memory[0:overflow_amount]
        else:
            # TODO: handle 16-bit overflow?
            data = self.memory[address:address+length]

        return data

    def write_memory(self, address: int, value: int) -> None:
        self.memory[address] = value

    def emulate_cycle(self) -> None:
        self.opcode = self.fetch_uint16(length=1)

        # build disassembly output
        if self.disassemble:
            disassembly_values = {
                'x': to_hex(self.x),
                'y': to_hex(self.y),
                'a': to_hex(self.a),
            }
            location = to_hex(self.pc)
            instruction = InstructionMnemonicMap[self.opcode]
            addressing_mode = InstructionAddressingModeMap[self.opcode]
            instruction_length = InstructionLengthMap[self.opcode]
            instruction_bytes = self.fetch_memory(length=instruction_length)  # fetch whole instruction, with opcode
            raw_bytes = ' '.join([to_hex(x) for x in instruction_bytes])
            if instruction_length > 1:
                disassembly_values['operand'] = ''.join([to_hex(x) for x in instruction_bytes[1:][::-1]])
            # also show the value of any indirect memory accesses
            if addressing_mode in (AddressingMode.Indirect, AddressingMode.IndirectX, AddressingMode.IndirectY):
                pass  # TODO - show memory indirection during indirect memory accesses
            elif addressing_mode == AddressingMode.Relative:  # show the actual memory address for relative operations
                disassembly_values['value2'] = to_hex(self.pc + instruction_length + to_signed_int(instruction_bytes[1]))
            elif instruction in ("BIT",):  # BIT uses indirect memory access in Zero Page and Absolute modes
                disassembly_values['value2'] = to_hex(self.fetch_uint16(instruction_length-1,
                                                                        address=to_uint16(instruction_bytes[1:])))
            disassembly = AddressingModeDisasmFormat[addressing_mode]
            disassembly_extra = InstructionDisasmExtras.get(self.opcode, "")
            disassembly = (disassembly + disassembly_extra).format(**disassembly_values)
            registers = f"A={to_hex(self.a)} X={to_hex(self.x)} Y={to_hex(self.y)} flags={bin(self.get_flags())}"
            print(f"0x{location:<5}{raw_bytes:<9}{instruction:<4}{disassembly:<32}{registers}")

        self.pc += 1

        try:
            self.opcodes[self.opcode]()
        except KeyError:
            logging.warning(f"Invalid opcode: {to_hex(self.opcode)} at 0x{to_hex(self.pc)}")

    # handles IRQ and NMI
    def handle_interrupt(self) -> None:
        # cycle 1
        # cycle 2
        self.push_pc()
        flags = self.get_flags()
        # IRQ and NMI set bit 5 and clear bit 4 of the flags
        flags |= 1 << 5
        if self.irq_low:
            address = 0xFFFE
        elif self.nmi_low:
            address = 0xFFFA
        else:
            # TODO: can this even happen? interrupt cleared by something else?
            return
        self.pc = self.fetch_uint16(2, address=address)
        self.i = 1

    # ADC - Add with Carry
    # Flags: carry, zero, overflow, negative
    def adc(self) -> None:
        # immediate
        if self.opcode == 0x69:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0x65:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x75:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0x6D:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, x
        elif self.opcode == 0x7D:
            value_location = self.fetch_uint16(2) + self.x & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, y
        elif self.opcode == 0x79:
            value_location = self.fetch_uint16(2) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # indirect, x
        elif self.opcode == 0x61:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            value_location = self.fetch_uint16(2, address=indirect_address)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # indirect, y (opcode 71)
        else:
            indirect_address = self.fetch_uint16(1)
            value_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        self.z = 0
        self.n = 0
        self.v = 0
        old_accumulator = self.a
        self.a = self.a + value + self.c & 0xFF
        if self.a < old_accumulator:
            # accumulator overflowed and wrapped
            self.c = 1
        else:
            self.c = 0
        if self.a == 0:
            self.z = 1
        # if the old accumulator and value had the same sign (+ or -), AND the accumulator and sum have different signs
        # then set overflow
        # ^0xFF is used because python doesn't have a built-in unsigned bitwise NOT
        if ((old_accumulator ^ value) ^ 0xFF) & (old_accumulator ^ self.a) & 0x80:
            self.v = 1
        if self.a > 127:
            self.n = 1

    # AND - Logical AND
    # Flags: zero, negative
    def _and(self) -> None:
        # immediate
        if self.opcode == 0x29:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0x25:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x35:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0x2D:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, x
        elif self.opcode == 0x3D:
            value_location = self.fetch_uint16(2) + self.x & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, y
        elif self.opcode == 0x39:
            value_location = self.fetch_uint16(2) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # indirect, x
        elif self.opcode == 0x21:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            value_location = self.fetch_uint16(2, address=indirect_address)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # indirect, y (opcode 31)
        else:
            indirect_address = self.fetch_uint16(1)
            value_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
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
    def asl(self) -> None:
        # implicit (accumulator)
        if self.opcode == 0x0A:
            old_value = self.a
            value = old_value << 1 & 0xFF
            self.a = value
        # zero page
        elif self.opcode == 0x06:
            memory_location = self.fetch_uint16(1)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF
            self.memory[memory_location] = value
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x16:
            memory_location = self.fetch_uint16(1) + self.x & 0xFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF
            self.memory[memory_location] = value
            self.pc += 1
        # absolute
        elif self.opcode == 0x0E:
            memory_location = self.fetch_uint16(2)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF
            self.memory[memory_location] = value
            self.pc += 2
        # absolute, x (opcode 1E)
        else:
            memory_location = self.fetch_uint16(2) + self.x & 0xFFFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF
            self.memory[memory_location] = value
            self.pc += 2
        self.c = old_value >> 7 & 1
        self.z = 0
        self.n = value >> 7 & 1
        if value == 0:
            self.z = 1

    # BCC - Branch if Carry Clear (90)
    # Branch to relative offset if carry flag is not set
    def bcc(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.c == 0:
            self.pc += offset

    # BCS - Branch if Carry Set (B0)
    # Branch to relative offset if carry flag is not set
    def bcs(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.c == 1:
            self.pc += offset

    # BEQ - Branch if Equal (F0)
    # Branch to relative offset if zero flag is set
    def beq(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.z == 1:
            self.pc += offset

    # BIT - Bit Test
    # The value in memory is AND'd with the Accumulator to set the Zero flag, and then the result is discarded.
    # Bit 6 of that same value in memory is used to set the Overflow flag, and bit 7 is used for the Negative flag
    # Flags: zero, overflow, negative
    def bit(self) -> None:
        # zero page
        if self.opcode == 0x24:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, value_location)
            self.pc += 1
        # absolute (opcode 2C)
        else:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, value_location)
            self.pc += 2
        self.z = 0
        self.v = value >> 6 & 1
        self.n = value >> 7 & 1
        if self.a & value == 0:
            self.z = 1

    # BMI - Branch if Minus (30)
    # Branch to relative offset if negative flag is set
    def bmi(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.n == 1:
            self.pc += offset

    # BNE - Branch if Not Equal (D0)
    # Branch to relative offset if zero flag is not set
    def bne(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.z == 0:
            self.pc += offset

    # BPL - Branch if Positive (10)
    # Branch to relative offset if negative flag is not set
    def bpl(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.n == 0:
            self.pc += offset

    # BRK - Force Interrupt (00)
    # Push PC onto stack. Set Break flag. Push processor flags onto stack. Set Interrupt flag.
    # Jump to IRQ Interrupt (0xFFFE-0xFFFF)
    def brk(self) -> None:
        self.pc += 1  # when we return from the interrupt, we want to go to the next instruction, not repeat the BRK
        self.push_pc()
        self.b = 1
        flags = self.get_flags()
        # BRK sets bits 5 and 4 of flags
        flags |= 0b11 << 4
        self.push(flags)
        self.i = 1
        irq_interrupt_location = self.fetch_uint16(2, address=0xFFFE)
        self.pc = irq_interrupt_location

    # BVC - Branch if Overflow Clear (50)
    # Branch to relative offset if overflow flag is not set
    def bvc(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.v == 0:
            self.pc += offset

    # BVS - Branch if Overflow Set (70)
    # Branch to relative offset if overflow flag is set
    def bvs(self) -> None:
        offset = to_signed_int(self.fetch_uint16(1))
        self.pc += 1
        if self.v == 1:
            self.pc += offset

    # CLC - Clear Carry Flag (18)
    def clc(self) -> None:
        self.c = 0

    # CLD - Clear Decimal Mode Flag (D8)
    def cld(self) -> None:
        self.d = 0

    # CLI - Clear Interrupt Disable Flag (58)
    def cli(self) -> None:
        self.i = 0

    # CLV - Clear Overflow Flag (B8)
    def clv(self) -> None:
        self.v = 0

    # CMP - Compare
    # Compares A with a value in memory. Set Carry if A>=M, set Zero if A==M, set Negative if A-M<0
    # Flags: carry, zero, negative
    def cmp(self) -> None:
        # immediate
        if self.opcode == 0xC9:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0xC5:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0xD5:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0xCD:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, x
        elif self.opcode == 0xDD:
            value_location = self.fetch_uint16(2) + self.x & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, y
        elif self.opcode == 0xD9:
            value_location = self.fetch_uint16(2) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # indirect, x
        elif self.opcode == 0xC1:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            value_location = self.fetch_uint16(2, address=indirect_address)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # indirect y (opcode D1)
        else:
            indirect_address = self.fetch_uint16(1)
            value_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
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
    def cpx(self) -> None:
        # immediate
        if self.opcode == 0xE0:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0xE4:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute (opcode EC)
        else:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
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
    def cpy(self) -> None:
        # immediate
        if self.opcode == 0xC0:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0xC4:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute (opcode CC)
        else:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
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
    def dec(self) -> None:
        # zero page
        if self.opcode == 0xC6:
            value_location = self.fetch_uint16(1)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0xD6:
            value_location = self.fetch_uint16(1) + self.x & 0xff
            self.pc += 1
        # absolute
        elif self.opcode == 0xCE:
            value_location = self.fetch_uint16(2)
            self.pc += 2
        # absolute, x (opcode DE)
        else:
            value_location = self.fetch_uint16(2) + self.x & 0xffff
            self.pc += 2
        self.z = 0
        self.n = 0
        value = self.fetch_uint16(1, address=value_location) - 1 & 0xFF
        self.memory[value_location] = value
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1

    # DEX - Decrement X Register (CA)
    # Flags: negative, zero
    def dex(self) -> None:
        self.n = 0
        self.z = 0
        self.x = self.x - 1 & 0xFF
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1

    # DEY - Decrement Y Register (88)
    # Flags: negative, zero
    def dey(self) -> None:
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
    def eor(self) -> None:
        # immediate
        if self.opcode == 0x49:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0x45:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x55:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0x4D:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, x
        elif self.opcode == 0x5D:
            value_location = self.fetch_uint16(2) + self.x & 0xffff
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, y
        elif self.opcode == 0x59:
            value_location = self.fetch_uint16(2) + self.y & 0xffff
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # indirect, x
        elif self.opcode == 0x41:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            value_location = self.fetch_uint16(2, address=indirect_address)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # indirect, y (opcode 51)
        else:
            indirect_address = self.fetch_uint16(1)
            value_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        self.z = 0
        self.n = 0
        self.a = self.a ^ value
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # INC - Increment Memory
    # Flags: zero, negative
    def inc(self) -> None:
        # zero page
        if self.opcode == 0xE6:
            value_location = self.fetch_uint16(1)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0xF6:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            self.pc += 1
        # absolute
        elif self.opcode == 0xEE:
            value_location = self.fetch_uint16(2)
            self.pc += 2
        # absolute, x (opcode FE)
        else:
            value_location = self.fetch_uint16(2) + self.x & 0xffff
            self.pc += 2
        self.z = 0
        self.n = 0
        value = self.fetch_uint16(1, address=value_location) + 1 & 0xFF
        self.memory[value_location] = value
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1

    # INX - Increment X Register (E8)
    # Flags: negative, zero
    def inx(self) -> None:
        self.n = 0
        self.z = 0
        self.x = self.x + 1 & 0xFF
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1

    # INY - Increment Y Register (C8)
    # Flags: negative, zero
    def iny(self) -> None:
        self.n = 0
        self.z = 0
        self.y = self.y + 1 & 0xFF
        if self.y == 0:
            self.z = 1
        elif self.y > 127:
            self.n = 1

    # JMP - Jump
    # Set PC to specified address
    def jmp(self) -> None:
        location = self.fetch_uint16(2)
        # absolute (opcode 4C) -- no special logic
        # indirect (opcode 6C)
        if self.opcode == 0x6C:
            # indirect JMP on the 6502 has a bug where it wraps around to grab the MSB from $xx00 if the LSB is on $xxFF
            if location & 0xFF == 0xFF:
                msb_location = location & 0xFF00
                jump_to = self.fetch_memory(length=1, address=location)
                jump_to += self.fetch_memory(length=1, address=msb_location)
                location = to_uint16(jump_to)
            else:
                location = self.fetch_uint16(length=2, address=location)
        self.pc = location

    # JSR - Jump to Subroutine (20)
    # Store PC-1 in stack (RTS adds 1 when it returns), then jump to absolute address of subroutine
    def jsr(self) -> None:
        subroutine_loc = self.fetch_uint16(2)
        self.pc += 1  # set PC to last byte of current instruction
        self.push_pc()
        self.pc = subroutine_loc

    # LDA - Load Accumulator (A9, A5, B5, AD, BD, B9, A1, B1)
    # Load a byte into the accumulator.
    # Flags: negative, zero
    def lda(self) -> None:
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 0xA9:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0xA5:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # zero page,x
        elif self.opcode == 0xB5:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0xAD:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute,x
        elif self.opcode == 0xBD:
            value_location = self.fetch_uint16(2) + self.x & 0xffff
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute,y
        elif self.opcode == 0xB9:
            value_location = self.fetch_uint16(2) + self.y & 0xffff
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # indirect,x
        elif self.opcode == 0xA1:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            value_location = self.fetch_uint16(2, address=indirect_address)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # indirect,y (opcode B1)
        else:
            indirect_address = self.fetch_uint16(1)
            value_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        self.a = value
        if value > 127:
            self.n = 1
        elif value == 0:
            self.z = 1

    # LDX - Load X Register
    # Load a byte into the X register.
    # Flags: negative, zero
    def ldx(self) -> None:
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 0xA2:
            data_to_load = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0xA6:
            memory_location = self.fetch_uint16(1)
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 1
        # zero page,y
        elif self.opcode == 0xB6:
            memory_location = self.fetch_uint16(1) + self.y & 0xFF
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0xAE:
            memory_location = self.fetch_uint16(2)
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 2
        # absolute,y (opcode BE)
        else:
            memory_location = self.fetch_uint16(2) + self.y & 0xFFFF
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 2
        self.x = data_to_load
        if data_to_load == 0:
            self.z = 1
        elif data_to_load > 127:
            self.n = 1

    # LDY - Load Y Register
    # Load a byte into the Y register.
    # Flags: negative, zero
    def ldy(self) -> None:
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 0xA0:
            data_to_load = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0xA4:
            memory_location = self.fetch_uint16(1)
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0xB4:
            memory_location = self.fetch_uint16(1) + self.x & 0xFF
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0xAC:
            memory_location = self.fetch_uint16(2)
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 2
        # absolute, x (opcode BC)
        else:
            memory_location = self.fetch_uint16(2) + self.x & 0xFFFF
            data_to_load = self.fetch_uint16(1, address=memory_location)
            self.pc += 2
        self.y = data_to_load
        if data_to_load == 0:
            self.z = 1
        elif data_to_load > 127:
            self.n = 1

    # LSR - Logical Shift Right
    # Bitwise shift right by one bit. Bit 0 is shifted into the Carry flag. Bit 7 is set to zero.
    # Flags: carry, zero, negative
    def lsr(self) -> None:
        # implicit (accumulator)
        if self.opcode == 0x4A:
            old_value = self.a
            value = old_value >> 1
            self.a = value
        # zero page
        elif self.opcode == 0x46:
            memory_location = self.fetch_uint16(1)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x56:
            memory_location = self.fetch_uint16(1) + self.x & 0xFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 1
        # absolute
        elif self.opcode == 0x4E:
            memory_location = self.fetch_uint16(2)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 2
        # absolute, x (opcode 5E)
        else:
            memory_location = self.fetch_uint16(2) + self.x & 0xFFFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1
            self.memory[memory_location] = value
            self.pc += 2
        self.c = old_value & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1

    # NOP - No Operation (1 byte)
    def nop(self) -> None:
        pass

    def nop_immediate(self) -> None:
        """
        Unofficial opcode for NOP. Reads an immediate byte and ignores the value.
        """
        self.pc += 1

    # ORA - Logical Inclusive OR
    # Performs a bitwise OR on the Accumulator using a byte from memory
    # Flags: zero, negative
    def ora(self) -> None:
        # immediate
        if self.opcode == 0x09:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0x05:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x15:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0x0D:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, x
        elif self.opcode == 0x1D:
            value_location = self.fetch_uint16(2) + self.x & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, y
        elif self.opcode == 0x19:
            value_location = self.fetch_uint16(2) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # indirect, x
        elif self.opcode == 0x01:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            value_location = self.fetch_uint16(2, address=indirect_address)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # indirect, y (opcode 11)
        else:
            indirect_address = self.fetch_uint16(1)
            value_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        self.z = 0
        self.n = 0
        self.a = self.a | value
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # PHA - Push Accumulator (48)
    def pha(self) -> None:
        self.push(self.a)

    # PHP - Push Processor Status (08)
    def php(self) -> None:
        flags = self.get_flags()
        # PHP sets bits 5 and 4 when pushing the flags, but does not actually change the state of the flags
        flags |= 0b11 << 4
        self.push(flags)

    # PLA - Pull Accumulator (68)
    # Flags: negative, zero
    def pla(self) -> None:
        self.n = 0
        self.z = 0
        self.a = self.pop()
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # PLP - Pull Processor Status (28)
    # Flags: all
    def plp(self) -> None:
        self.set_flags(self.pop())

    # ROL - Rotate Left
    # Flags: carry, zero, negative
    def rol(self) -> None:
        # implicit (accumulator)
        if self.opcode == 0x2A:
            old_value = self.a
            value = old_value << 1 & 0xFF | self.c
            self.a = value
        # zero page
        elif self.opcode == 0x26:
            memory_location = self.fetch_uint16(1)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF | self.c
            self.memory[memory_location] = value
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x36:
            memory_location = self.fetch_uint16(1) + self.x & 0xFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF | self.c
            self.memory[memory_location] = value
            self.pc += 1
        # absolute
        elif self.opcode == 0x2E:
            memory_location = self.fetch_uint16(2)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF | self.c
            self.memory[memory_location] = value
            self.pc += 2
        # absolute, x (opcode 3E)
        else:
            memory_location = self.fetch_uint16(2) + self.x & 0xFFFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value << 1 & 0xFF | self.c
            self.memory[memory_location] = value
            self.pc += 2
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
    def ror(self) -> None:
        # implicit (accumulator)
        if self.opcode == 0x6A:
            old_value = self.a
            value = old_value >> 1 | self.c << 7
            self.a = value
        # zero page
        elif self.opcode == 0x66:
            memory_location = self.fetch_uint16(1)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x76:
            memory_location = self.fetch_uint16(1) + self.x & 0xFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 1
        # absolute
        elif self.opcode == 0x6E:
            memory_location = self.fetch_uint16(2)
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 2
        # absolute, x (opcode 7E)
        else:
            memory_location = self.fetch_uint16(2) + self.x & 0xFFFF
            old_value = self.fetch_uint16(1, address=memory_location)
            value = old_value >> 1 | self.c << 7
            self.memory[memory_location] = value
            self.pc += 2
        self.c = old_value & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1

    # RTI - Return from Interrupt (40)
    # Pop processor flags from stack, followed by the program counter
    def rti(self) -> None:
        self.set_flags(self.pop())
        self.pc = self.pop16()

    # RTS - Return from Subroutine (60)
    # Pop return address from stack and jump to it
    def rts(self) -> None:
        self.pc = self.pop16()
        self.pc += 1

    # SBC - Subtract with Carry
    # Flags: carry, zero, overflow, negative
    def sbc(self) -> None:
        # immediate
        if self.opcode == 0xE9:
            value = self.fetch_uint16(1)
            self.pc += 1
        # zero page
        elif self.opcode == 0xE5:
            value_location = self.fetch_uint16(1)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0xF5:
            value_location = self.fetch_uint16(1) + self.x & 0xFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # absolute
        elif self.opcode == 0xED:
            value_location = self.fetch_uint16(2)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, x
        elif self.opcode == 0xFD:
            value_location = self.fetch_uint16(2) + self.x & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # absolute, y
        elif self.opcode == 0xF9:
            value_location = self.fetch_uint16(2) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 2
        # indirect, x
        elif self.opcode == 0xE1:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            value_location = self.fetch_uint16(2, address=indirect_address)
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        # indirect, y (opcode F1)
        else:
            indirect_address = self.fetch_uint16(1)
            value_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            value = self.fetch_uint16(1, address=value_location)
            self.pc += 1
        self.z = 0
        self.n = 0
        self.v = 0
        old_accumulator = self.a
        self.a = self.a - value - (1 - self.c) & 0xFF
        self.c = 1
        if self.a > old_accumulator:
            self.c = 0
        if self.a == 0:
            self.z = 1
        # if the sign (+ or -) of both inputs is different from the sign of the result, overflow is set
        # in the hardware, SBC is more like adding a negative number than subtracting a positive number.
        # with that in mind, overflow works a little differently. invert the bits on value before doing the below check.
        value = value ^ 0xFF
        if ((old_accumulator ^ value) ^ 0xFF) & (old_accumulator ^ self.a) & 0x80:
            self.v = 1
        if self.a > 127:
            self.n = 1

    # SEC - Set Carry (38)
    def sec(self) -> None:
        self.c = 1

    # SED - Set Decimal (F8)
    def sed(self) -> None:
        self.d = 1

    # SEI - Set Interrupt Disable (78)
    def sei(self) -> None:
        self.i = 1

    # STA - Store Accumulator
    # Store the accumulator at the specified location in memory
    def sta(self) -> None:
        # zero page
        if self.opcode == 0x85:
            memory_location = self.fetch_uint16(1)
            self.pc += 1
        # zero page,x
        elif self.opcode == 0x95:
            memory_location = self.fetch_uint16(1) + self.x & 0xFF
            self.pc += 1
        # absolute
        elif self.opcode == 0x8D:
            memory_location = self.fetch_uint16(2)
            self.pc += 2
        # absolute,x
        elif self.opcode == 0x9D:
            memory_location = self.fetch_uint16(2) + self.x & 0xFFFF
            self.pc += 2
        # absolute,y
        elif self.opcode == 0x99:
            memory_location = self.fetch_uint16(2) + self.y & 0xFFFF
            self.pc += 2
        # indirect,x
        elif self.opcode == 0x81:
            indirect_address = self.fetch_uint16(1) + self.x & 0xFF
            memory_location = self.fetch_uint16(2, address=indirect_address)
            self.pc += 1
        # indirect,y (opcode 91)
        else:
            indirect_address = self.fetch_uint16(1)
            memory_location = self.fetch_uint16(2, address=indirect_address) + self.y & 0xFFFF
            self.pc += 1
        self.memory[memory_location] = self.a

    # STX - Store X Register
    # Store the X register at the specified location in memory
    def stx(self) -> None:
        # zero page
        if self.opcode == 0x86:
            memory_location = self.fetch_uint16(1)
            self.pc += 1
        # zero page, y
        elif self.opcode == 0x96:
            memory_location = self.fetch_uint16(1) + self.y & 0xFF
            self.pc += 1
        # absolute (opcode 8E)
        else:
            memory_location = self.fetch_uint16(2)
            self.pc += 2
        self.memory[memory_location] = self.x

    # STY - Store Y Register
    # Store the Y register at the specified location in memory
    def sty(self) -> None:
        # zero page
        if self.opcode == 0x84:
            memory_location = self.fetch_uint16(1)
            self.pc += 1
        # zero page, x
        elif self.opcode == 0x94:
            memory_location = self.fetch_uint16(1) + self.x & 0xFF
            self.pc += 1
        # absolute (opcode 8C)
        else:
            memory_location = self.fetch_uint16(2)
            self.pc += 2
        self.memory[memory_location] = self.y

    # TAX - Transfer Accumulator to X (AA)
    # Flags: zero, negative
    def tax(self) -> None:
        self.z = 0
        self.n = 0
        self.x = self.a
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1

    # TAY - Transfer Accumulator to Y (A8)
    # Flags: zero, negative
    def tay(self) -> None:
        self.z = 0
        self.n = 0
        self.y = self.a
        if self.y == 0:
            self.z = 1
        elif self.y > 127:
            self.n = 1

    # TSX - Transfer Stack Pointer to X (BA)
    # Flags: zero, negative
    def tsx(self) -> None:
        self.z = 0
        self.n = 0
        self.x = self.sp
        if self.x == 0:
            self.z = 1
        elif self.x > 127:
            self.n = 1

    # TXA - Transfer X to Accumulator (8A)
    # Flags: zero, negative
    def txa(self) -> None:
        self.z = 0
        self.n = 0
        self.a = self.x
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1

    # TXS - Transfer X to Stack Pointer (9A)
    def txs(self) -> None:
        self.sp = self.x

    # TYA - Transfer Y to Accumulator(98)
    # Flags: zero, negative
    def tya(self) -> None:
        self.z = 0
        self.n = 0
        self.a = self.y
        if self.a == 0:
            self.z = 1
        elif self.a > 127:
            self.n = 1
