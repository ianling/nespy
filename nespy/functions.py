def to_signed_int(value):
    """
    Converts an unsigned integer to a signed integer

    6502 uses 2's complement for some instructions, (e.g. relative branches),
    so some values will have to be converted to signed.

    Args:
        value(int): one hex byte (example: "ff")

    Returns:
        int: signed integer
    """
    if value >= 128:
        return -128 + (value-128)
    return value


def to_hex(value):
    """
    Args:
        value(int): any integer

    Returns:
        str: hex without leading '0x'. Example: to_hex(255) -> "ff"
    """
    return format(int(value), '02x')


def to_uint16(values, reverse=True):
    """
    Args:
        values(iterable): two bytes in little-endian order (MSB, LSB)
        reverse(bool): if True, reverses the order of the bytes
    Returns:
        int: a 16-bit value
    """
    if reverse:
        values.reverse()
    try:
        return values[0] << 8 | values[1]
    except IndexError:
        return values[0]