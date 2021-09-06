from nespy import NES
import cProfile
from sys import argv


if __name__ == '__main__':
    nes = NES(resolution=None, disassemble=False)
    nes.load_rom(argv[1])
    #nes._cpu.pc = 0xc000
    #cProfile.run("nes.run()")
    nes.run()
