from time import time
from multiprocessing import Process
from typing import Callable


EMULATE_CYCLE_FUNCTION = Callable[[], None]


class Clock:
    def __init__(self, frequency: int) -> None:
        self.frequency = frequency
        self.cycle = 0
        self.ticking = False
        self.nanoseconds_per_tick = 1 * 1000 * 1000 * 1000 / self.frequency
        self.last_cycle_time = 0.0
        self.last_print_time = 0.0
        self.children: list[ChildClock] = []
        self.speed = 0
        self.start_time = time()

    def start(self) -> None:
        self.ticking = True
        Process(target=self.tick).start()

    def stop(self) -> None:
        self.ticking = False

    def add_child(self, divisor: int, func: EMULATE_CYCLE_FUNCTION) -> None:
        """
        Creates a clock whose clock rate is derived from this clock.
        This child clock runs the given callable every time it ticks.
        """
        self.children.append(ChildClock(divisor, func))

    def tick(self) -> None:
        """
        Requests that the clock tick once. Ticks any child clocks derived from this clock as well.
        Blocks until all child clocks have finished executing their cycle.
        """
        while self.ticking:
            self.cycle += 1
            for child in self.children:
                if self.cycle % child.get_divisor() == 0:
                    child.tick()
            #while time_ns() - self._last_cycle_time_ns < self._nanoseconds_per_tick:
            #    # wait until enough time has passed to move onto the next tick
            #    pass
            self.last_cycle_time = time()
            # DEBUG
            if self.last_cycle_time - self.last_print_time > 1:
                self.last_print_time = self.last_cycle_time
                delta = self.last_cycle_time - self.start_time
                print(f"{self.cycle / delta} {delta}")


class ChildClock:
    def __init__(self, divisor: int, func: EMULATE_CYCLE_FUNCTION) -> None:
        self.divisor = divisor
        self.func = func

    def tick(self) -> None:
        self.func()

    def get_divisor(self) -> int:
        return self.divisor
