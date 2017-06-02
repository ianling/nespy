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
    if not isfile(rom):
        exit()

    # initialize graphics
    # NES native resolution = 256x240
    nesX = 256
    nesY = 240
    scale = 2
    pygame.init()
    pygame.display.set_caption('NESPy')
    clock = pygame.time.Clock()
    nespy = NESPy(pygame.display.set_mode((nesX * scale, nesY * scale)), rom)

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
        nespy.emulateCycle()
        #debug
        loopIterations += 1
        if loopIterations > 120:
            break

main()
