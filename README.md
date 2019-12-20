NES emulator written in python

Usage
=====

```
from nespy.nes import NES


nes = NES()
nes.load_rom("roms/Donkey Kong.nes")
nes.run()
```

Resources:

* http://nesdev.com/6502_cpu.txt -- Extremely detailed information about the CPU
* http://blog.alexanderdickson.com/javascript-nes-emulator-part-1 -- tons of useful information about the NES
* http://www.obelisk.me.uk/6502/reference.html -- opcode reference
* http://wiki.nesdev.com/w/index.php/CPU_unofficial_opcodes -- opcode grid
* http://wiki.nesdev.com/w/index.php/INES -- parsing a NES rom
* http://nemulator.com/files/nes_emu.txt -- more info about parsing ROMs
* https://www.reddit.com/r/pygame/comments/5ifplr/ive_updated_the_pyglet_procedural_audio_module/ -- playing raw waveforms with pyglet