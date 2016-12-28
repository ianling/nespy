import binascii
from random import randint
import pygame
from sys import exit


def toDecimal(value):
    return int(value, 16)
def toHex(value):  # returns string like 'ff', '0a', etc.
    return format(int(value), '02x')

class NESPy:
    def __init__(self, display, rom):
        # initialize registers and stuff
        self.rom = open(rom, "rb")
        # see http://nemulator.com/files/nes_emu.txt for memory info
        self.memory = ['00']*0x10000  # 16KiB of RAM
        self.sp = 0x100  # stack pointer
        self.p = [  0,  # carry
                    0,  # zero
                    0,  # interrupt disable
                    0,  # decimal mode
                    0,  # break command
                    0,  # unused
                    0,  # overflow
                    0]  # negative
        self.a = 0  # accumulator
        self.x = 0  # x and y are general purpose registers
        self.y = 0
        self.pc = 0x8000  # program counter
        self.display = display
        # point all opcodes to invalidOpcode(), then fill in the jump table one-by-one with valid function pointers
        self.opcodes = dict.fromkeys([format(opcode_decimal, '02X') for opcode_decimal in range(0, 256)], self.invalidOpcode)

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
        prgBanks = toDecimal(romHeader[4])
        chrBanks = toDecimal(romHeader[5])
        flags6 = toDecimal(romHeader[6])
        flags7 = toDecimal(romHeader[7])
        prgRAMSize = toDecimal(romHeader[8])
        flags9 = toDecimal(romHeader[9])
        flags10 = toDecimal(romHeader[10])
        # bits 11-15 of the header are unused

        if flags6 & 0b00000100:  # bit 2 of flags6 indicates whether a trainer is present
            romHasTrainer = 1
        else:
            romHasTrainer = 0

        romPrgStart = 0x10 + (0x200 * romHasTrainer)  # trainer is 0x200 bytes long
        romPrgEnd = romPrgStart + (0x4000 * prgBanks) # each prgBank is 0x4000 bytes long
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

    def emulateCycle(self):
        opcode = str(self.memory[self.pc])
        print 'running: ' + opcode
        self.opcodes[opcode]()
        pass

    def invalidOpcode(self):
        print 'INVALID OPCODE'