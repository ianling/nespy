NES emulator written in Python 3.

This emulator features a simple API to interact with the system's internals while software
is running. This is useful for things such as AI development, reverse engineering, 
game modifications, memory editing, tool-assisted speedruns (TAS), and more.

This is a work in progress. The CPU implementation is completed (except for unofficial opcodes)
and passes the nestest ROM. I have started working on the PPU.

Usage
=====

```
from nespy.nes import NES


nes = NES()
nes.load_rom("roms/Donkey Kong.nes")
nes.run()
```

Keys
====

* F11 - Open PPU debug window

Future Usage
============
In its final form, I want this emulator to have features that support the following use cases.
None of these things currently exist in the emulator, this is a wishlist.

Reverse Engineering
-------------------
This emulator includes a 6502 disassembler and debugger, as well as an interface for
altering a ROM.

```
nes = NES(debug=True)
nes.load_rom("roms/Donkey_Kong.nes")
nes.run()
```

Disassembler output:
```
0xc000 4c f5 c5 JMP $c5f5                           A=00 X=00 Y=00 flags=0b110100
0xc5f5 a2 00    LDX #$00                            A=00 X=00 Y=00 flags=0b110100
0xc5f7 86 00    STX $00; = 00                       A=00 X=00 Y=00 flags=0b110110
0xc5f9 86 10    STX $10; = 00                       A=00 X=00 Y=00 flags=0b110110
0xc5fb 86 11    STX $11; = 00                       A=00 X=00 Y=00 flags=0b110110
0xc5fd 20 2d c7 JSR $c72d                           A=00 X=00 Y=00 flags=0b110110
0xc72d ea       NOP                                 A=00 X=00 Y=00 flags=0b110110
0xc72e 38       SEC                                 A=00 X=00 Y=00 flags=0b110110
0xc72f b0 04    BCS $04; = $c735                    A=00 X=00 Y=00 flags=0b110111
...
```

Modifications
-------------
Create and load patches and modifications to ROMs that can affect the behavior of any part
of the NES and the emulator itself, including Game Genie-style cheats, ROM hacks, 
CPU instruction overrides, and even custom OpenGL shaders.

```
nes.load_rom("roms/Donkey Kong.nes")
nes.load_patch("patches/nude_dk.patch")
nes.load_patch("patches/rtx_shader_dk.patch")
```

```
def my_jmp_handler(nes):
    # always just set PC to 0x1000 whenever a JMP instruction is reached
    nes.cpu.set_pc(0x1000)

nes.cpu.jmp = my_jmp_handler
```

AI
--
Retrieve information directly from the system's RAM and use it to make decisions in real time.
```
SCORE_ADDRESS = 0x25
ENEMY_LOC_ADDRESS = 0x78
MY_LOC_ADDRESS = 0x7A

def get_score():
    return nes.cpu.fetch_memory(length=2, address=SCORE_ADDRESS)

def get_enemy_position():
    return nes.cpu.fetch_memory(length=2, address=ENEMY_LOC_ADDRESS)

def get_my_position():
    return nes.cpu.fetch_memory(length=2, address=MY_LOC_ADDRESS)


score = get_score()

if get_enemy_position() == get_my_position():
    player1_controller.hold_a(frames=1)

nes.wait_frames(60)  # block script for 60 frames

new_score = get_score()
if new_score > score:
    # the enemy was killed, continue moving right
    player1_controller.press_right()
```

TAS
---
Allow creation and playback of TAS input recordings.
```
with nes.start_recording_inputs("mario_tas.fm2"):
    nes.advance_frames(10)  # advance the system by 10 frames
    player1_controller.press_a()
    nes.advance_frames(1)
    player1_controller.release_a()
    # ...

nes.import_recorded_inputs("mario_tas.fm2")
nes.play_inputs()
```

Resources
=========

* http://nesdev.com/6502_cpu.txt -- Extremely detailed information about the CPU
* http://blog.alexanderdickson.com/javascript-nes-emulator-part-1 -- tons of useful information about the NES
* http://www.obelisk.me.uk/6502/reference.html -- opcode reference
* http://wiki.nesdev.com/w/index.php/CPU_unofficial_opcodes -- opcode grid
* http://wiki.nesdev.com/w/index.php/INES -- parsing a NES rom
* http://nemulator.com/files/nes_emu.txt -- more info about parsing ROMs
* https://www.reddit.com/r/pygame/comments/5ifplr/ive_updated_the_pyglet_procedural_audio_module/ -- playing raw waveforms with pyglet
* https://wiki.nesdev.com/w/index.php/Emulator_tests -- NES test roms