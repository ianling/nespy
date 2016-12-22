"""
main


"""
from nespy import NESPy
import pygame
from sys import argv, exit
from os.path import isfile

def updateScreen():
    pass

def main():
    # get rom path
    rom = argv[1]
    print rom
    if not isfile(rom):
        exit()

    # initialize graphics
    # NES native resolution = 256x240
    pygame.init()
    pygame.display.set_caption('NESPy')
    clock = pygame.time.Clock()
    nespy = NESPy(pygame.display.set_mode((512, 480)), rom)

    # main loop
    while True:
        # if we're updating the screen, make sure the screen only updates at 60FPS max
        if nespy.getDrawFlag():
            clock.tick(60)
            pygame.display.update()
            # check if the player has tried to close the window
            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                exit()
            pygame.event.clear() # we don't use pygame events
            nespy.setDrawFlag(False)
            nespy.emulateCycle()
        else:
            # still run other opcodes, even if we aren't drawing anything
            nespy.emulateCycle()

main()
