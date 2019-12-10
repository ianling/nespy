class InvalidOpcode(Exception):
    """
    Raised when the emulator encounters an opcode it is unable to parse
    """
    pass


class InvalidROM(Exception):
    """
    Raised when the emulator is unable to parse a ROM file
    """
    pass
