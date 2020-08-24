class Memory:
    def __init__(self):
        self.data = [0] * 0x10000  # 64KiB

    def __getitem__(self, key):
        # catch accesses to mirrored addresses
        if type(key) is not slice and 0x2008 <= key <= 0x3FFF:
            key = (key % 0x8) + 0x2000
        return self.data[key]

    def __setitem__(self, key, value):
        # catch accesses to mirrored addresses
        if type(key) is not slice and 0x2008 <= key <= 0x3FFF:
            key = (key % 0x8) + 0x2000
        self.data[key] = value
