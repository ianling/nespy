def to_unsigned_int(value):
    """
    Args:
        value(str): one or more hex bytes (example: "fff0")

    Returns:
        int: unsigned decimal
    """
    return int(value, 16)


def to_signed_int(value):
    """
    6502 uses 2's complement for some instructions, (e.g. relative branches),
    so some values will have to be converted to signed.

    Args:
        value(str): one hex byte (example: "ff")

    Returns:
        int: signed integer
    """
    unsigned = to_unsigned_int(value)
    if unsigned >= 128:
        return -128 + (unsigned-128)
    return unsigned


def to_hex(value):
    """
    Args:
        value(int): any integer

    Returns:
        str: hex without leading '0x'. Example: to_hex(255) -> "ff"
    """
    return format(int(value), '02x')
