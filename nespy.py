import binascii
from random import randint
import pygame
from sys import exit


# 6502 uses 2's complement for some instructions, (e.g. relative branches)
# so some values will have to be converted to signed
def toUnsignedDecimal(value):
    return int(value, 16)


def toSignedDecimal(value):
    unsigned = toUnsignedDecimal(value)
    if unsigned >= 128:
        return -128 + (unsigned-128)
    return unsigned


def toHex(value):  # returns one byte of hex as a string
    return format(int(value), '02x')


class NESPy:
    def __init__(self, display, rom):
        # initialize registers and stuff
        self.rom = open(rom, "rb")
        # see http://nemulator.com/files/nes_emu.txt for memory info
        self.memory = ['00']*0x10000  # 16KiB of RAM
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
        self.display = display
        self.opcode = None  # the current opcode being executed
        # point all opcodes to invalidOpcode(), then fill in the jump table one-by-one with valid function pointers
        self.opcodes = dict.fromkeys([format(opcode_decimal, '02X') for opcode_decimal in range(0, 256)], self.invalidOpcode)
        self.opcodes.update({'10': self.bpl})
        self.opcodes.update({'00': self.brk})
        self.opcodes.update({'18': self.clc})
        self.opcodes.update({'D8': self.cld})
        self.opcodes.update({'58': self.cli})
        self.opcodes.update({'B8': self.clv})
        self.opcodes.update({'E8': self.inx})
        self.opcodes.update({'C8': self.iny})
        self.opcodes.update({'20': self.jsr})
        self.opcodes.update({'A9': self.lda, 'A5': self.lda, 'B5': self.lda, 'AD': self.lda,
                             'BD': self.lda, 'B9': self.lda, 'A1': self.lda, 'B1': self.lda})
        self.opcodes.update({'A2': self.ldx, 'A6': self.ldx, 'B6': self.ldx, 'AE': self.ldx,
                             'BE': self.ldx})
        self.opcodes.update({'A0': self.ldy, 'A4': self.ldy, 'B4': self.ldy, 'AC': self.ldy,
                             'BC': self.ldy})
        self.opcodes.update({'EA': self.nop})
        self.opcodes.update({'48': self.pha})
        self.opcodes.update({'08': self.php})
        self.opcodes.update({'68': self.pla})
        self.opcodes.update({'28': self.plp})
        self.opcodes.update({'60': self.rts})
        self.opcodes.update({'78': self.sei})
        self.opcodes.update({'85': self.sta, '95': self.sta, '8D': self.sta, '9D': self.sta,
                             '99': self.sta, '81': self.sta, '91': self.sta})
        self.opcodes.update({'86': self.stx, '96': self.stx, '8E': self.stx})
        self.opcodes.update({'84': self.sty, '94': self.sty, '8C': self.sty})
        self.opcodes.update({'9A': self.txs})

        # read rom into memory
        romBytes = []
        while True:
            byte = self.rom.read(1)
            if not byte:
                break
            romBytes.append(binascii.b2a_hex(byte).upper())
        romHeader = romBytes[0:16]

        # parse ROM header
        # http://nemulator.com/files/nes_emu.txt
        if romHeader[0:4] != ['4E', '45', '53', '1A']:  # first 3 bytes should be 'NES\x1A'
            print 'Invalid ROM header!'
            exit()
        prgBanks = toUnsignedDecimal(romHeader[4])
        chrBanks = toUnsignedDecimal(romHeader[5])
        flags6 = toUnsignedDecimal(romHeader[6])
        flags7 = toUnsignedDecimal(romHeader[7])
        prgRAMSize = toUnsignedDecimal(romHeader[8])
        flags9 = toUnsignedDecimal(romHeader[9])
        flags10 = toUnsignedDecimal(romHeader[10])
        # bits 11-15 of the header are unused

        if flags6 & 0b00000100:  # bit 2 of flags6 indicates whether a trainer is present
            romHasTrainer = 1
        else:
            romHasTrainer = 0

        romPrgStart = 0x10 + (0x200 * romHasTrainer)  # trainer is 0x200 bytes long
        romPrgEnd = romPrgStart + (0x4000 * prgBanks)  # each prgBank is 0x4000 bytes long
        memoryPointer = 0x8000  # prgBanks get written to memory starting at 0x8000
        romPrgBytes = romBytes[romPrgStart:romPrgEnd]
        if prgBanks == 2:
            for byte in romPrgBytes:
                self.memory[memoryPointer] = byte
                memoryPointer += 1
        elif prgBanks == 1:  # if there's only one PRG bank on the ROM, it gets duplicated to the 2nd area in memory
            for byte in romBytes[romPrgStart:romPrgEnd]:
                self.memory[memoryPointer] = byte
                self.memory[memoryPointer+0x4000] = byte
                memoryPointer += 1

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
        try:
            return int(value, 16)
        except:
            return value

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

    # BPL - Branch if Positive (10)
    # Branch to relative offset if negative flag is not set
    def bpl(self):
        offset = toSignedDecimal(self.memory[self.pc+1])
        self.pc += 2
        if self.n == 0:
            self.pc += offset  # offset is relative

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

    # INX - Increment X Register (E8)
    # Flags: negative, zero
    def inx(self):
        self.n = 0
        self.z = 0
        self.x += 1
        if self.x == 0:
            self.z = 1
        elif self.x < 0:
            self.n = 1

    # INY - Increment Y Register (C8)
    # Flags: negative, zero
    def iny(self):
        self.n = 0
        self.z = 0
        self.y += 1
        if self.y == 0:
            self.z = 1
        elif self.y < 0:
            self.n = 1

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
            valueLoc = toUnsignedDecimal(self.memory[indirectAddress+1] + self.memory[indirectAddress])
            value = toUnsignedDecimal(self.memory[valueLoc])
            self.pc += 2
        # indirect,y
        elif self.opcode == 'B1':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            valueLoc = toUnsignedDecimal(self.memory[indirectAddress+1] + self.memory[indirectAddress]) + self.y
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

    # NOP - No Operation (EA)
    def nop(self):
        self.pc += 1

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

    # RTS - Return from Subroutine (60)
    # Pop return address (minus 1) from stack and jump to it
    def rts(self):
        returnLocLSB = self.pop()
        returnLocMSB = self.pop() << 8
        returnLoc = toUnsignedDecimal(returnLocMSB | returnLocLSB)
        self.pc = returnLoc
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
            memoryLoc = toUnsignedDecimal(self.memory[indirectAddress+1] + self.memory[indirectAddress])
            self.pc += 2
        # indirect,y
        elif self.opcode == '91':
            indirectAddress = toUnsignedDecimal(self.memory[self.pc+1])
            memoryLoc = toUnsignedDecimal(self.memory[indirectAddress+1] + self.memory[indirectAddress]) + self.y
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

    # TXS - Transfer X to Stack Pointer (9A)
    def txs(self):
        self.sp = self.x
        self.pc += 1
