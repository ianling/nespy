import binascii
from random import randint
import pygame
from sys import exit
from functions import *




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
        # point all opcodes to invalidOpcode(), then fill in the jump table one-by-one with valid function pointers
        self.opcodes = dict.fromkeys([format(opcode_decimal, '02X') for opcode_decimal in range(0, 256)], self.invalidOpcode)
        self.opcodes.update({'69': self.adc, '65': self.adc, '75': self.adc, '6D': self.adc,
                             '7D': self.adc, '79': self.adc, '61': self.adc, '71': self.adc})
        self.opcodes.update({'29': self._and, '25': self._and, '35': self._and, '2D': self._and,
                             '3D': self._and, '39': self._and, '21': self._and, '31': self._and})
        self.opcodes.update({'0A': self.asl, '06': self.asl, '16': self.asl, '0E': self.asl,
                             '1E': self.asl})
        self.opcodes.update({'90': self.bcc})
        self.opcodes.update({'B0': self.bcs})
        self.opcodes.update({'F0': self.beq})
        self.opcodes.update({'24': self.bit, '2C': self.bit})
        self.opcodes.update({'30': self.bmi})
        self.opcodes.update({'D0': self.bne})
        self.opcodes.update({'10': self.bpl})
        self.opcodes.update({'00': self.brk})
        self.opcodes.update({'50': self.bvc})
        self.opcodes.update({'70': self.bvs})
        self.opcodes.update({'18': self.clc})
        self.opcodes.update({'D8': self.cld})
        self.opcodes.update({'58': self.cli})
        self.opcodes.update({'B8': self.clv})
        self.opcodes.update({'C9': self.cmp, 'C5': self.cmp, 'D5': self.cmp, 'CD': self.cmp,
                             'DD': self.cmp, 'D9': self.cmp, 'C1': self.cmp, 'D1': self.cmp})
        self.opcodes.update({'E0': self.cpx, 'E4': self.cpx, 'EC': self.cpx})
        self.opcodes.update({'C0': self.cpy, 'C4': self.cpy, 'CC': self.cpy})
        self.opcodes.update({'C6': self.dec, 'D6': self.dec, 'CE': self.dec, 'DE': self.dec})
        self.opcodes.update({'C8': self.dex})
        self.opcodes.update({'88': self.dey})
        self.opcodes.update({'49': self.eor, '45': self.eor, '55': self.eor, '4D': self.eor,
                             '5D': self.eor, '59': self.eor, '41': self.eor, '51': self.eor})
        self.opcodes.update({'E6': self.inc, 'F6': self.inc, 'EE': self.inc, 'FE': self.inc})
        self.opcodes.update({'E8': self.inx})
        self.opcodes.update({'C8': self.iny})
        self.opcodes.update({'4C': self.jmp, '6C': self.jmp})
        self.opcodes.update({'20': self.jsr})
        self.opcodes.update({'A9': self.lda, 'A5': self.lda, 'B5': self.lda, 'AD': self.lda,
                             'BD': self.lda, 'B9': self.lda, 'A1': self.lda, 'B1': self.lda})
        self.opcodes.update({'A2': self.ldx, 'A6': self.ldx, 'B6': self.ldx, 'AE': self.ldx,
                             'BE': self.ldx})
        self.opcodes.update({'A0': self.ldy, 'A4': self.ldy, 'B4': self.ldy, 'AC': self.ldy,
                             'BC': self.ldy})
        self.opcodes.update({'4A': self.lsr, '46': self.lsr, '56': self.lsr, '4E': self.lsr,
                             '5E': self.lsr})
        self.opcodes.update({'EA': self.nop})
        self.opcodes.update({'09': self.ora, '05': self.ora, '15': self.ora, '0D': self.ora,
                             '1D': self.ora, '19': self.ora, '01': self.ora, '11': self.ora})
        self.opcodes.update({'48': self.pha})
        self.opcodes.update({'08': self.php})
        self.opcodes.update({'68': self.pla})
        self.opcodes.update({'28': self.plp})
        self.opcodes.update({'2A': self.rol, '26': self.rol, '36': self.rol, '2E': self.rol,
                             '3E': self.rol})
        self.opcodes.update({'6A': self.ror, '66': self.ror, '76': self.ror, '6E': self.ror,
                             '7E': self.ror})
        self.opcodes.update({'40': self.rti})
        self.opcodes.update({'60': self.rts})
        self.opcodes.update({'E9': self.sbc, 'E5': self.sbc, 'F5': self.sbc, 'ED': self.sbc,
                             'FD': self.sbc, 'F9': self.sbc, 'E1': self.sbc, 'F1': self.sbc})
        self.opcodes.update({'38': self.sec})
        self.opcodes.update({'F8': self.sed})
        self.opcodes.update({'78': self.sei})
        self.opcodes.update({'85': self.sta, '95': self.sta, '8D': self.sta, '9D': self.sta,
                             '99': self.sta, '81': self.sta, '91': self.sta})
        self.opcodes.update({'86': self.stx, '96': self.stx, '8E': self.stx})
        self.opcodes.update({'84': self.sty, '94': self.sty, '8C': self.sty})
        self.opcodes.update({'AA': self.tax})
        self.opcodes.update({'A8': self.tay})
        self.opcodes.update({'BA': self.tsx})
        self.opcodes.update({'8A': self.txa})
        self.opcodes.update({'9A': self.txs})
        self.opcodes.update({'98': self.tya})

        # set pc to RESET vector (0xFFFC-0xFFFD)
        reset_interrupt = self.memory[0xFFFC:0xFFFE]
        reset_interrupt = reset_interrupt[1] + reset_interrupt[0]  # reverse them since NES is little-endian
        self.pc = int(reset_interrupt, 16)

    # the 6502 has a very particular order that the flags are arranged in: (little endian)
    # N V U B D I Z C
    def getFlags(self):
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

    def setFlags(self, flags):
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
        return toUnsignedDecimal(value)

    # pushes two bytes onto the stack
    def push16(self):
        pass

    # pops two bytes off of the stack
    def pull16(self):
        pass

    def pushPC(self):
        pcHex = toHex(self.pc).zfill(4)  # ex: "0C28"
        pcMSB = pcHex[0:2]
        pcLSB = pcHex[2:]
        self.push(pcMSB)
        self.push(pcLSB)

    def emulateCycle(self):
        self.opcode = str(self.memory[self.pc])
        print 'running: ' + self.opcode + ' at 0x' + toHex(self.pc)
        self.opcodes[self.opcode]()

    def invalidOpcode(self):
        print 'INVALID OPCODE'
        self.pc += 1

    # ADC - Add with Carry
    # Flags: carry, zero, overflow, negative
    def adc(self):
        # immediate
        if self.opcode == '69':
            value = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page
        elif self.opcode == '65':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # zero page, x
        elif self.opcode == '75':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == '6D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, x
        elif self.opcode == '7D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, y
        elif self.opcode == '79':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # indirect, x
        elif self.opcode == '61':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # indirect, y
        elif self.opcode == '71':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        self.z = 0
        self.n = 0
        self.v = 0
        oldAccumulator = self.a
        self.a += value + self.c
        if self.a > 255:
            self.c = 1
        else:
            self.c = 0
        if self.a == 0:
            self.z = 1
        elif oldAccumulator >> 7 & 1 != self.a >> 7 & 1:
            self.v = 1
        if self.a >> 7 & 1 == 1:
            self.n = 1
        self.a = self.a & 0xFF

    # AND - Logical AND
    # Flags: zero, negative
    def _and(self):
        # immediate
        if self.opcode == '29':
            value = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page
        elif self.opcode == '25':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # zero page, x
        elif self.opcode == '35':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == '2D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, x
        elif self.opcode == '3D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, y
        elif self.opcode == '39':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # indirect, x
        elif self.opcode == '21':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # indirect, y
        elif self.opcode == '31':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
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
            oldValue = self.a
            value = oldValue << 1
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '06':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1
            self.memory[memoryLoc] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '16':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1
            self.memory[memoryLoc] = value
            self.pc += 2
        # absolute
        elif self.opcode == '0E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1
            self.memory[memoryLoc] = value
            self.pc += 3
        # absolute, x
        elif self.opcode == '1E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1]) + self.x
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1
            self.memory[memoryLoc] = value
            self.pc += 3
        self.c = oldValue >> 7 & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1
        if value > 127:
            self.n = 1

    # BCC - Branch if Carry Clear (90)
    # Branch to relative offset if carry flag is not set
    def bcc(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
        self.pc += 2
        if self.c == 0:
            self.pc += offset

    # BCS - Branch if Carry Set (B0)
    # Branch to relative offset if carry flag is not set
    def bcs(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
        self.pc += 2
        if self.c == 1:
            self.pc += offset

    # BEQ - Branch if Equal (F0)
    # Branch to relative offset if zero flag is set
    def beq(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
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
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == '2C':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        self.z = 0
        self.v = value >> 6 & 1
        self.n = value >> 7 & 1
        if self.a & value == 0:
            self.z = 1

    # BMI - Branch if Minus (30)
    # Branch to relative offset if negative flag is set
    def bmi(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
        self.pc += 2
        if self.n == 1:
            self.pc += offset

    # BNE - Branch if Not Equal (D0)
    # Branch to relative offset if zero flag is not set
    def bne(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
        self.pc += 2
        if self.z == 0:
            self.pc += offset

    # BPL - Branch if Positive (10)
    # Branch to relative offset if negative flag is not set
    def bpl(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
        self.pc += 2
        if self.n == 0:
            self.pc += offset

    # BRK - Force Interrupt (00)
    # Push PC onto stack. Set Break flag. Push processor flags onto stack. Set Interrupt flag. Jump to IRQ Interrupt
    def brk(self):
        self.pc += 1
        self.pc += 1
        self.pushPC()
        self.b = 1
        self.push(self.getFlags())
        self.i = 1
        irqInterruptLoc = toUnsignedDecimal(self.memory[0xFFFF] + self.memory[0xFFFE])
        self.pc = irqInterruptLoc

    # BVC - Branch if Overflow Clear (50)
    # Branch to relative offset if overflow flag is not set
    def bvc(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
        self.pc += 2
        if self.v == 0:
            self.pc += offset

    # BVS - Branch if Overflow Set (70)
    # Branch to relative offset if overflow flag is set
    def bvs(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
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
            value = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page
        elif self.opcode == 'C5':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'D5':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == 'CD':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, x
        elif self.opcode == 'DD':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, y
        elif self.opcode == 'D9':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # indirect, x
        elif self.opcode == 'C1':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # indirect y
        elif self.opcode == 'D1':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
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
            value = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page
        elif self.opcode == 'E4':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == 'EC':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
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
            value = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page
        elif self.opcode == 'C4':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == 'CC':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
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
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'D6':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 'CE':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x
        elif self.opcode == 'DE':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        self.z = 0
        self.n = 0
        value = toUnsignedDecimal(self.memory[valueLoc]) - 1 & 0xFF
        self.memory[valueLoc] = value
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
            valueLoc = toUnsignedDecimal(self.pc+1)
            self.pc += 2
        # zero page
        elif self.opcode == '45':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page, x
        elif self.opcode == '55':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '4D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x
        elif self.opcode == '5D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        # absolute, y
        elif self.opcode == '59':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            self.pc += 3
        # indirect, x
        elif self.opcode == '41':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            self.pc += 2
        # indirect, y
        elif self.opcode == '51':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            self.pc += 2
        self.z = 0
        self.n = 0
        value = toUnsignedDecimal(self.memory[valueLoc])
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
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'F6':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == 'EE':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x
        elif self.opcode == 'FE':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        self.z = 0
        self.n = 0
        value = toUnsignedDecimal(self.memory[valueLoc]) + 1 & 0xFF
        self.memory[valueLoc] = value
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
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # indirect
        elif self.opcode == '6C':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            location = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            self.pc += 3
        self.pc = location

    # JSR - Jump to Subroutine (20)
    # Store PC-1 in stack (RTS adds 1 when it returns), then jump to absolute address of subroutine
    def jsr(self):
        subroutineLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
        self.pc += 2
        self.pushPC()
        self.pc = subroutineLoc

    # LDA - Load Accumulator (A9, A5, B5, AD, BD, B9, A1, B1)
    # Load a byte into the accumulator.
    # Flags: negative, zero
    def lda(self):
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 'A9':
            value = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page
        elif self.opcode == 'A5':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # zero page,x
        elif self.opcode == 'B5':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == 'AD':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute,x
        elif self.opcode == 'BD':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute,y
        elif self.opcode == 'B9':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # indirect,x
        elif self.opcode == 'A1':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # indirect,y
        elif self.opcode == 'B1':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
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
            dataToLoad = toUnsignedDecimal(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'A6':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 1])
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 2
        # zero page,y
        elif self.opcode == 'B6':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 1]) + self.y & 0xFF
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 2
        # absolute
        elif self.opcode == 'AE':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 3
        # absolute,y
        elif self.opcode == 'BE':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 3
        self.x = dataToLoad
        if dataToLoad == 0:
            self.z = 1
        elif dataToLoad < 0:
            self.n = 1

    # LDY - Load Y Register
    # Load a byte into the Y register.
    # Flags: negative, zero
    def ldy(self):
        self.n = 0
        self.z = 0
        # immediate
        if self.opcode == 'A0':
            dataToLoad = toUnsignedDecimal(self.memory[self.pc + 1])
            self.pc += 2
        # zero page
        elif self.opcode == 'A4':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 1])
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'B4':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 1]) + self.x & 0xFF
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 2
        # absolute
        elif self.opcode == 'AC':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 3
        # absolute, x
        elif self.opcode == 'BC':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            dataToLoad = toUnsignedDecimal(self.memory[memoryLoc])
            self.pc += 3
        self.y = dataToLoad
        if dataToLoad == 0:
            self.z = 1
        elif dataToLoad < 0:
            self.n = 1

    # LSR - Logical Shift Right
    # Bitwise shift right by one bit. Bit 0 is shifted into the Carry flag. Bit 7 is set to zero.
    # Flags: carry, zero, negative
    def lsr(self):
        # accumulator
        if self.opcode == '4A':
            oldValue = self.a
            value = oldValue >> 1
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '46':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1
            self.memory[memoryLoc] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '56':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1
            self.memory[memoryLoc] = value
            self.pc += 2
        # absolute
        elif self.opcode == '4E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1
            self.memory[memoryLoc] = value
            self.pc += 3
        # absolute, x
        elif self.opcode == '5E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1]) + self.x
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1
            self.memory[memoryLoc] = value
            self.pc += 3
        self.c = oldValue & 1
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
            valueLoc = toUnsignedDecimal(self.pc+1)
            self.pc += 2
        # zero page
        elif self.opcode == '05':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page, x
        elif self.opcode == '15':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '0D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            self.pc += 3
        # absolute, x
        elif self.opcode == '1D':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            self.pc += 3
        # absolute, y
        elif self.opcode == '19':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            self.pc += 3
        # indirect, x
        elif self.opcode == '01':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            self.pc += 2
        # indirect, y
        elif self.opcode == '11':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            self.pc += 2
        self.z = 0
        self.n = 0
        value = toUnsignedDecimal(self.memory[valueLoc])
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
        self.push(self.getFlags())
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
        self.setFlags(self.pop())
        self.pc += 1

    # ROL - Rotate Left
    # Flags: carry, zero, negative
    def rol(self):
        # accumulator
        if self.opcode == '2A':
            oldValue = self.a
            value = oldValue << 1 | self.c
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '26':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1 | self.c
            self.memory[memoryLoc] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '36':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1 | self.c
            self.memory[memoryLoc] = value
            self.pc += 2
        # absolute
        elif self.opcode == '2E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1 | self.c
            self.memory[memoryLoc] = value
            self.pc += 3
        # absolute, x
        elif self.opcode == '3E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1]) + self.x
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue << 1 | self.c
            self.memory[memoryLoc] = value
            self.pc += 3
        self.c = 0
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1
        if oldValue > 127:
            self.c = 1

    # ROR - Rotate Right
    # Flags: carry, zero, negative
    def ror(self):
        # accumulator
        if self.opcode == '6A':
            oldValue = self.a
            value = oldValue >> 1 | self.c << 7
            self.a = value
            self.pc += 1
        # zero page
        elif self.opcode == '66':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1 | self.c << 7
            self.memory[memoryLoc] = value
            self.pc += 2
        # zero page, x
        elif self.opcode == '76':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1 | self.c << 7
            self.memory[memoryLoc] = value
            self.pc += 2
        # absolute
        elif self.opcode == '6E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1 | self.c << 7
            self.memory[memoryLoc] = value
            self.pc += 3
        # absolute, x
        elif self.opcode == '7E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1]) + self.x
            oldValue = toUnsignedDecimal(self.memory[memoryLoc])
            value = oldValue >> 1 | self.c << 7
            self.memory[memoryLoc] = value
            self.pc += 3
        self.c = oldValue & 1
        self.z = 0
        self.n = 0
        if value == 0:
            self.z = 1
        elif value > 127:
            self.n = 1

    # RTI - Return from Interrupt (40)
    # Pop processor flags from stack, followed by the program counter
    def rti(self):
        self.setFlags(self.pop())
        returnLocLSB = self.pop()
        returnLocMSB = self.pop() << 8
        returnLoc = toUnsignedDecimal(returnLocMSB | returnLocLSB)
        self.pc = returnLoc

    # RTS - Return from Subroutine (60)
    # Pop return address (minus 1) from stack and jump to it
    def rts(self):
        returnLocLSB = self.pop()
        returnLocMSB = self.pop() << 8
        returnLoc = toUnsignedDecimal(returnLocMSB | returnLocLSB)
        self.pc = returnLoc
        self.pc += 1

    # SBC - Subtract with Carry
    # Flags: carry, zero, overflow, negative
    def sbc(self):
        # immediate
        if self.opcode == 'E9':
            value = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page
        elif self.opcode == 'E5':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # zero page, x
        elif self.opcode == 'F5':
            valueLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # absolute
        elif self.opcode == 'ED':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, x
        elif self.opcode == 'FD':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.x
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # absolute, y
        elif self.opcode == 'F9':
            valueLoc = toUnsignedDecimal(self.memory[self.pc + 2] + self.memory[self.pc + 1]) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 3
        # indirect, x
        elif self.opcode == 'E1':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # indirect, y
        elif self.opcode == 'F1':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        self.z = 0
        self.n = 0
        self.v = 0
        oldAccumulator = self.a
        self.a -= value - (1 - self.c)
        if self.a < 0:
            self.c = 1
        else:
            self.c = 0
        if self.a == 0:
            self.z = 1
        elif oldAccumulator >> 7 & 1 != self.a >> 7 & 1:
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
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page,x
        elif self.opcode == '95':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '8D':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
            self.pc += 3
        # absolute,x
        elif self.opcode == '9D':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1]) + self.x
            self.pc += 3
        # absolute,y
        elif self.opcode == '99':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1]) + self.y
            self.pc += 3
        # indirect,x
        elif self.opcode == '81':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            memoryLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress)
            self.pc += 2
        # indirect,y
        elif self.opcode == '91':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            memoryLoc = toUnsignedDecimal(indirectAddress+1 << 8 | indirectAddress) + self.y
            self.pc += 2
        self.memory[memoryLoc] = self.a

    # STX - Store X Register
    # Store the X register at the specified location in memory
    def stx(self):
        # zero page
        if self.opcode == '86':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page, y
        elif self.opcode == '96':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.y & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '8E':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
            self.pc += 3
        self.memory[memoryLoc] = self.x

    # STY - Store Y Register
    # Store the Y register at the specified location in memory
    def sty(self):
        # zero page
        if self.opcode == '84':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1])
            self.pc += 2
        # zero page, x
        elif self.opcode == '94':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+1]) + self.x & 0xFF
            self.pc += 2
        # absolute
        elif self.opcode == '8C':
            memoryLoc = toUnsignedDecimal(self.memory[self.pc+2]+self.memory[self.pc+1])
            self.pc += 3
        self.memory[memoryLoc] = self.y

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
