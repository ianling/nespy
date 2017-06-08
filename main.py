"""
main


"""
from cpu import CPU
import pygame
from sys import argv, exit
from os.path import isfile
import binascii
from functions import *

def main():
    # get rom path
    romPath = argv[1]
    if not isfile(romPath):
        exit()

    # initialize graphics
    # NES native resolution = 256x240
    nesX = 256
    nesY = 240
    scale = 2
    pygame.init()
    pygame.display.set_caption('NESPy')
    display = pygame.display.set_mode((nesX * scale, nesY * scale))
    clock = pygame.time.Clock()

    # initialize memory
    # see http://nemulator.com/files/nes_emu.txt for memory and ROM info
    memory = ['00'] * 0x10000  # 16KiB of RAM
    # read rom into memory
    rom = open(romPath, "rb")
    romBytes = []
    while True:
        byte = rom.read(1)
        if not byte:
            break
        romBytes.append(binascii.b2a_hex(byte).upper())
    romHeader = romBytes[0:16]
    # parse ROM header
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

    if flags6 & 0b00000100 != 0:  # bit 2 of flags6 indicates whether a trainer is present
        romHasTrainer = 1
    else:
        romHasTrainer = 0

    romPrgStart = 0x10 + (0x200 * romHasTrainer)  # trainer is 0x200 bytes long
    romPrgEnd = romPrgStart + (0x4000 * prgBanks)  # each prgBank is 0x4000 bytes long
    memoryPointer = 0x8000  # prgBanks get written to memory starting at 0x8000
    romPrgBytes = romBytes[romPrgStart:romPrgEnd]
    if prgBanks == 2:
        for byte in romPrgBytes:
            memory[memoryPointer] = byte
            memoryPointer += 1
    elif prgBanks == 1:  # if there's only one PRG bank on the ROM, it gets duplicated to the 2nd area in memory
        for byte in romBytes[romPrgStart:romPrgEnd]:
            memory[memoryPointer] = byte
            memory[memoryPointer + 0x4000] = byte
            memoryPointer += 1

    cpu = CPU(memory)

    #debug
    loopIterations = 0
    # main loop
    while True:
        # make sure the screen only updates at 60FPS max
        clock.tick(60)
        pygame.display.update()
        # check if the player has tried to close the window
        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            exit()
        pygame.event.clear() # we don't use pygame events
        cpu.emulateCycle()

        #debug
        loopIterations += 1
        if loopIterations > 60:
            break

main()
