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
        # see http://blog.alexanderdickson.com/javascript-nes-emulator-part-1 for memory info
        # 0x0000 - 0x00FF -- zero page
        # 0x0100 - 0x01FF -- stack
        # 0x0200 - 0x0800 -- general purpose RAM
        # 0x0801 - 0x2000 -- mirror of previous addresses (0x0000 - 0x07FF)
        # 0x2000 - 0x2007 -- PPU's registers
        # 0x2008 - 0x4000 -- mirrors of previous addresses
        # 0x4000 - 0x4020 -- DMA
        # 0x4020 - 0x6000 -- expansion ROM
        # 0x6000 - 0x8000 -- SRAM
        # 0x8000 - 0xC000 -- program (lower bank)
        # 0xC000 - 0xFFFF -- program (upper bank)
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
            exit()  # invalid ROM header
        print 'Valid ROM loaded!'
        prgBanks = toDecimal(romHeader[4])
        chrBanks = toDecimal(romHeader[5])
        flags6 = toDecimal(romHeader[6])
        flags7 = toDecimal(romHeader[7])
        prgRAMSize = toDecimal(romHeader[8])
        flags9 = toDecimal(romHeader[9])  # rarely used
        flags10 = toDecimal(romHeader[10])  # unofficial, optional
        # bits 11-15 are unused

        # check if ROM includes a trainer
        if flags6 & 0b00000100:  # bit 2 of flags6 indicates whether a trainer is present
            romHasTrainer = 1
        else:
            romHasTrainer = 0

        romPrgStart = 0x10 + (0x200 * romHasTrainer) # start reading from ROM after the trainer, if trainer is present
        romPrgEnd = romPrgStart + (0x4000 * prgBanks) + 1  # +1 because python uses exclusive ranges
        print 'we start reading prg at ' + str(romPrgStart) + ' and end at ' + str(romPrgEnd)
        print 'first byte is ' + str(romBytes[romPrgStart])
        memoryPointer = 0x8000  # start writing ROM to RAM at 0x8000
        romPrgBytes = romBytes[romPrgStart:romPrgEnd]
        print len(romPrgBytes)
        if prgBanks == 2:  # write lower bank and upper bank to memory
            for byte in romPrgBytes:
                self.memory[memoryPointer] = byte
                memoryPointer += 1
                print toHex(memoryPointer)
        elif prgBanks == 1:  # if there's only one bank on the ROM, copy it to the second area in memory too
            for byte in romBytes[romPrgStart:romPrgEnd]:
                self.memory[memoryPointer] = byte
                self.memory[memoryPointer+0x4000] = byte
                memoryPointer += 1
        print 'value at memory address 0x8000: ' + self.memory[0x8000]
        print 'value at memory address 0xC000: ' + self.memory[0xC000]

    def emulateCycle(self):
        # CHIP-8 opcodes are two bytes long, big-endian
        #opcodeFirstByte = str(self.memory[self.pc])
        #opcodeLastByte = str(self.memory[self.pc+1])
        #opcode = opcodeFirstByte + opcodeLastByte
        #print opcode
        #pcIncrementBy = 2  # amount to increase pc by after cycle. 2 bytes by default
        pass