from nespy import NES
import cProfile
from sys import argv


if __name__ == '__main__':
    nes = NES(resolution=None, disassemble=True)
    nes.insert_cartridge(argv[1])
    # nes._cpu.pc = 0xc000  # for nestest.nes
    #cProfile.run("nes.run()")
    nes.run()
