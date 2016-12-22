import binascii
from random import randint
import pygame


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
        # 0xC000 - 0xFFFF -- program (upper bank) if applicable, or mirror of lower bank
        self.memory = [0]*0xFFFF  # 16KiB of RAM, 0x0000-0xFFFF
        self.stack = [None]*16
        self.sp = 0  # stack pointer
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
        self.v = [0]*16
        self.i = 0
        self.pc = 0x200  # program counter
        self.delayTimer = 0
        self.soundTimer = 0
        self.key = [0]*16
        self.drawFlag = False
        self.display = display
        self.pixelArray = [[False for y in range(33)] for x in range(65)]
        # via http://www.multigesture.net/articles/how-to-write-an-emulator-chip-8-interpreter
        self.fontSet = ['F0', '90', '90', '90', 'F0',  # 0
                        '20', '60', '20', '20', '70',  # 1
                        'F0', '10', 'F0', '80', 'F0',  # 2
                        'F0', '10', 'F0', '10', 'F0',  # 3
                        '90', '90', 'F0', '10', '10',  # 4
                        'F0', '80', 'F0', '10', 'F0',  # 5
                        'F0', '80', 'F0', '90', 'F0',  # 6
                        'F0', '10', '20', '40', '40',  # 7
                        'F0', '90', 'F0', '90', 'F0',  # 8
                        'F0', '90', 'F0', '10', 'F0',  # 9
                        'F0', '90', 'F0', '90', '90',  # A
                        'E0', '90', 'E0', '90', 'E0',  # B
                        'F0', '80', '80', '80', 'F0',  # C
                        'E0', '90', '90', '90', 'E0',  # D
                        'F0', '80', 'F0', '80', 'F0',  # E
                        'F0', '80', 'F0', '80', '80']  # F
        # see http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#keyboard
        self.keyboard = [pygame.K_x,  #0
                         pygame.K_1,  #1
                         pygame.K_2,  #2
                         pygame.K_3,  #3
                         pygame.K_q,  #4
                         pygame.K_w,  #5
                         pygame.K_e,  #6
                         pygame.K_a,  #7
                         pygame.K_s,  #8
                         pygame.K_d,  #9
                         pygame.K_z,  #A (10)
                         pygame.K_c,  #B (11)
                         pygame.K_4,  #C (12)
                         pygame.K_r,  #D (13)
                         pygame.K_f,  #E (14)
                         pygame.K_v   #F (15)
                         ]
        # store fontset in memory
        for index, byte in enumerate(self.fontSet):
            self.memory[index] = byte

        # store game in memory, starting at position 512
        memoryPointer = 512
        while True:
            byte = self.rom.read(1)
            if not byte:
                break
            self.memory[memoryPointer] = binascii.b2a_hex(byte).upper()
            memoryPointer += 1

    def emulateCycle(self):
        # CHIP-8 opcodes are two bytes long, big-endian
        opcodeFirstByte = str(self.memory[self.pc])
        opcodeLastByte = str(self.memory[self.pc+1])
        opcode = opcodeFirstByte + opcodeLastByte
        #print opcode
        pcIncrementBy = 2  # amount to increase pc by after cycle. 2 bytes by default

        if opcode == "00E0":  # clear screen
            self.display.fill((0, 0, 0))
            self.drawFlag = True

        elif opcode == "00EE":  # return from subroutine
            self.sp -= 1
            self.pc = self.stack[self.sp]

        # 1NNN - Jumps to address NNN
        elif opcode[0] == "1":
            self.pc = int(opcode[1:], 16)
            pcIncrementBy = 0

        # 2NNN - Calls subroutine at NNN
        elif opcode[0] == "2":
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = int(opcode[1:], 16)
            pcIncrementBy = 0

        # 3XNN - Skips the next instruction if V[X] == NN
        elif opcode[0] == "3":
            if int(self.v[int(opcode[1], 16)], 16) == int(opcodeLastByte, 16):
                pcIncrementBy = 4  # jump ahead 4 bytes instead of the usual 2

        # 4XNN - Skips the next instruction if V[X] != NN
        elif opcode[0] == "4":
            if int(self.v[int(opcode[1], 16)], 16) != int(opcodeLastByte, 16):
                pcIncrementBy = 4  # jump ahead 4 bytes instead of the usual 2

        # 5XY0 - Skips the next instruction if V[X] == V[Y]
        elif opcode[0] == "5":
            if int(self.v[int(opcode[1], 16)], 16) == int(self.v[int(opcode[2], 16)], 16):
                pcIncrementBy = 4  # jump ahead 4 bytes instead of the usual 2

        # 6XNN - Sets V[X] to NN
        elif opcode[0] == "6":
            self.v[int(opcode[1], 16)] = opcodeLastByte.lower()

        # 7XNN - Adds NN to V[X]. Wrap around if value is greater than 255.
        elif opcode[0] == "7":
            vx = int(self.v[int(opcode[1], 16)], 16)
            nn = int(opcodeLastByte, 16)
            self.v[int(opcode[1], 16)] = hex((vx + nn) % 256)[2:]

        # 8XY0 - Sets V[X] = V[Y]
        elif opcode[0] == "8" and opcode[3] == "0":
            self.v[int(opcode[1], 16)] = self.v[int(opcode[2], 16)]

        # 8XY1 - Sets V[X] = V[X] | V[Y]
        elif opcode[0] == "8" and opcode[3] == "1":
            self.v[int(opcode[1], 16)] = hex(int(self.v[int(opcode[1], 16)], 16) | int(self.v[int(opcode[2], 16)], 16))[2:]

        # 8XY2 - Sets V[X] = V[X] & V[Y]
        elif opcode[0] == "8" and opcode[3] == "2":
            self.v[int(opcode[1], 16)] = hex(int(self.v[int(opcode[1], 16)], 16) & int(self.v[int(opcode[2], 16)], 16))[2:]

        # 8XY3 - Sets V[X] = V[X] ^ V[Y]
        elif opcode[0] == "8" and opcode[3] == "3":
            self.v[int(opcode[1], 16)] = hex(int(self.v[int(opcode[1], 16)], 16) ^ int(self.v[int(opcode[2], 16)], 16))[2:]

        # 8XY4 - Sets V[X] += V[Y]. If V[X] + V[Y] > 255, then V[0xF] is set to 1, else set to 0
        elif opcode[0] == "8" and opcode[3] == "4":
            intVX = int(self.v[int(opcode[1], 16)], 16)
            intVY = int(self.v[int(opcode[2], 16)], 16)
            if intVX + intVY > 255:
                self.v[0xf] = '01'
            else:
                self.v[0xf] = '00'
            self.v[int(opcode[1], 16)] = hex((intVX + intVY) % 256)[2:]

        # 8XY5 - Sets V[X]-= V[Y]. If V[X] - V[Y] < 0, then VF is set to 0, else set to 1. Wrap around.
        elif opcode[0] == "8" and opcode[3] == "5":
            intVX = int(self.v[int(opcode[1], 16)], 16)
            intVY = int(self.v[int(opcode[2], 16)], 16)
            if intVX - intVY < 0:
                self.v[0xf] = '00'
            else:
                self.v[0xf] = '01'
            self.v[int(opcode[1], 16)] = hex((intVX - intVY) % 256)[2:]

        # 8XY6 - Shifts VX right by one. VF is set to the value of the least significant bit of VX before the shift.
        elif opcode[0] == "8" and opcode[3] == "6":
            intVX = int(self.v[int(opcode[1], 16)], 16)
            binVX = bin(intVX)
            self.v[int(opcode[1], 16)] = hex(intVX >> 1)[2:]
            self.v[0xf] = '0' + binVX[-1]

        # 8XY7 - Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't. Wrap around.
        elif opcode[0] == "8" and opcode[3] == "7":
            intVX = int(self.v[int(opcode[1], 16)], 16)
            intVY = int(self.v[int(opcode[2], 16)], 16)
            if intVY - intVX < 0:
                self.v[0xf] = '00'
            else:
                self.v[0xf] = '01'
            self.v[int(opcode[1], 16)] = hex((intVY - intVX) % 256)[2:]

        # 8XYE - Shifts VX left by one. VF is set to the value of the most significant bit of VX before the shift
        elif opcode[0] == "8" and opcode[3] == "E":
            intVX = int(self.v[int(opcode[1], 16)], 16)
            binVX = format(intVX, '010b')
            self.v[int(opcode[1], 16)] = hex(intVX << 1)[2:]
            self.v[0xf] = '0' + binVX[0]

        # 9XY0 - Skips the next instruction if VX doesn't equal VY.
        elif opcodeFirstByte[0] == "9":
            if int(self.v[int(opcode[1], 16)], 16) != int(self.v[int(opcode[2], 16)], 16):
                pcIncrementBy = 4  # jump ahead 4 bytes instead of the usual 2

        # ANNN - Sets I to the address NNN
        elif opcodeFirstByte[0] == "A":
            self.i = opcode[1:]

        # CXNN - Sets V[X] to the result of a bitwise and operation on a random number and NN.
        elif opcodeFirstByte[0] == "C":
            self.v[int(opcode[1], 16)] = hex(int(opcode[2:], 16) & randint(0, 255))[2:]

        # DXYN - Sprites stored in memory at location in index register (I), 8bits wide.
        #        Wraps around the screen. If when drawn, it clears a pixel,
        #        then register V[F] is set to 1. Otherwise it is zero.
        #        All drawing is XOR drawing (i.e. it toggles the screen pixels).
        #        Sprites are drawn starting at position V[X], V[Y].
        #        N is the number of 8bit rows that need to be drawn.
        #        If N is greater than 1, second line continues at position V[X], V[Y+1], and so on.
        elif opcodeFirstByte[0] == "D":
            intVX = int(self.v[int(opcode[1], 16)], 16) % 64
            intVY = int(self.v[int(opcode[2], 16)], 16) % 32
            height = int(opcode[3], 16)
            self.v[0xf] = '00'
            for heightIterator in range(0, height):
                spriteByteBinary = format(int(self.memory[int(self.i, 16) + heightIterator], 16), '08b')  # padded with zeroes
                for bitIterator in range(0, 8):  # rows are 8 bits long
                    if spriteByteBinary[bitIterator] == '1':  # need to toggle these pixels
                        if self.pixelArray[(intVX+bitIterator)%64][(intVY+heightIterator)%32]:
                            color = (0, 0, 0)  # black
                            self.v[0xf] = '01'  # we're clearing a pixel, set V[F] = 1
                        else:
                            color = (255, 255, 255)  # white
                        pygame.draw.rect(self.display, color, (intVX * 8 + (bitIterator * 8), intVY * 8 + (heightIterator*8), 8, 8))
                        self.pixelArray[(intVX+bitIterator)%64][(intVY+heightIterator)%32] = not self.pixelArray[(intVX+bitIterator)%64][(intVY+heightIterator)%32]  # toggle the pixel
                        self.drawFlag = True

        # EX9E - Skips the next instruction if the key stored in VX is pressed.
        elif opcodeFirstByte[0] == "E" and opcodeLastByte == "9E":
            keyStates = pygame.key.get_pressed()
            keyToCheck = int(self.v[int(opcode[1], 16)], 16)
            if keyStates[self.keyboard[keyToCheck]]:
                pcIncrementBy = 4

        # EXA1 - Skips the next instruction if the key stored in VX isn't pressed.
        elif opcodeFirstByte[0] == "E" and opcodeLastByte == "A1":
            keyStates = pygame.key.get_pressed()
            keyToCheck = int(self.v[int(opcode[1], 16)], 16)
            if not keyStates[self.keyboard[keyToCheck]]:
                pcIncrementBy = 4

        # FX07 - Sets VX to the value of the delay timer.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "07":
            self.v[int(opcode[1], 16)] = self.delayTimer

        # FX0A - A key press is awaited, and then stored in VX.
        #        All execution stops while waiting for a keypress.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "0A":
            keyStates = pygame.key.get_pressed()
            pcIncrementBy = 0  # keep pc on this opcode until a key is pressed
            for pygameKey in self.keyboard:
                if keyStates[pygameKey]:
                    pcIncrementBy = 2
                    self.v[int(opcode[1], 16)] = opcode[1]
                    break

        # FX15 - Sets the delay timer to VX.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "15":
            self.delayTimer = self.v[int(opcode[1], 16)]

        # FX18 - Sets the sound timer to VX.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "18":
            self.soundTimer = self.v[int(opcode[1], 16)]

        # FX1E- Adds VX to I.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "1E":
            intVX = int(self.v[int(opcode[1], 16)], 16)
            intI = int(self.i, 16)
            self.i = hex((intI + intVX))[2:]

        # FX29- Sets I to the location of the sprite for the character in VX.
        #       Characters 0-F (in hexadecimal) are represented by a 4x5 font.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "29":
            intVX = int(self.v[int(opcode[1], 16)], 16)
            self.i = hex(intVX * 5)

        # FX33- Stores the Binary-coded decimal representation of VX,
        #       with the most significant of three digits at the address in I,
        #       the middle digit at I plus 1, and the least significant digit at I plus 2.
        #       (In other words, take the decimal representation of VX,
        #       place the hundreds digit in memory at location in I,
        #       the tens digit at location I+1, and the ones digit at location I+2.)
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "33":
            intVX = format(int(self.v[int(opcode[1], 16)], 16), '03')  # padded with zeroes if <100 or <10
            self.memory[int(self.i, 16)] = hex(int(intVX[0]))[2:]
            self.memory[int(self.i, 16)+1] = hex(int(intVX[1]))[2:]
            self.memory[int(self.i, 16)+2] = hex(int(intVX[2]))[2:]

        # FX55- Stores V0 to VX (including VX) in memory starting at address I.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "55":
            x = int(opcode[1], 16)
            for vIterator in range(0, x+1):
                self.memory[int(self.i, 16)+vIterator] = self.v[vIterator]

        # FX65- Fills V0 to VX (including VX) with values from memory starting at address I.
        elif opcodeFirstByte[0] == "F" and opcodeLastByte == "65":
            x = int(opcode[1], 16)
            for vIterator in range(0, x+1):
                self.v[vIterator] = self.memory[int(self.i, 16)+vIterator]

        self.pc += pcIncrementBy
        # decrement the timers on every tick
        if int(self.delayTimer, 16) > 0:
            self.delayTimer = format(int(self.delayTimer, 16)-1, '02x')  # format(...) = 'ff'
        if int(self.soundTimer, 16) > 0:
            self.soundTimer = format(int(self.soundTimer, 16)-1, '02x')

    def getDrawFlag(self):
        return self.drawFlag

    def setDrawFlag(self, value):
        self.drawFlag = value

    def toDecimal(self, value):
        return int(value, 16)
    def toHex(self, value):  # returns string like 'ff', '0a', etc.
        return format(int(value, 16), '02x')