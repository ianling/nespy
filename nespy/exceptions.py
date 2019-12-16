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


class UnsupportedMapper(Exception):
    """
    Raised when the emulator attempts to load a ROM that uses an unsupported mapper
    """
    pass
