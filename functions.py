# 6502 uses 2's complement for some instructions, (e.g. relative branches)
# so some values will have to be converted to signed
def toUnsignedDecimal(value):
    try:
        return int(value, 16)
    except:
        return value


def toSignedDecimal(value):
    unsigned = toUnsignedDecimal(value)
    if unsigned >= 128:
        return -128 + (unsigned-128)
    return unsigned


def toHex(value):  # returns one byte of hex as a string
    return format(int(value), '02x')
