class Mapper:
    def cpu_get(self, address: int, size: int) -> list[int]:
        """
        Returns the value at the given memory location, mapped assuming the CPU is the caller.
        """
        raise NotImplementedError

    def cpu_set(self, address: int, value: int) -> None:
        """
        Sets the value at the given memory location, mapped assuming the CPU is the caller.
        """
        raise NotImplementedError

    def ppu_get(self, address: int, size: int) -> int:
        """
        Returns the value at the given memory location, mapped assuming the PPU is the caller.
        """
        raise NotImplementedError

    def ppu_set(self, address: int, value: int) -> None:
        """
        Sets the value at the given memory location, mapped assuming the PPU is the caller.
        """
        raise NotImplementedError
