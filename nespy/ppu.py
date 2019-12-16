class PPU:
    def __init__(self, cpu_memory):
        self._cpu_memory = cpu_memory
        self._memory = [0] * 0x4000  # 16KiB of RAM
