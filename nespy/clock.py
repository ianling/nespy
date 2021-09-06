from time import time
from multiprocessing import Process
from typing import Callable


EMULATE_CYCLE_FUNCTION = Callable[[], None]


class Clock:
    """
    A Clock that ticks at a given frequency.
    ChildClocks whose frequencies are derived from this parent Clock's frequency can be added using `.add_child(...)`
    """
    def __init__(self, frequency: int) -> None:
        self.frequency = frequency
        self.cycle = 0
        self.ticking = False
        self.nanoseconds_per_tick = 1 * 1000 * 1000 * 1000 / self.frequency
        self.last_cycle_time = 0.0
        self.last_print_time = 0.0
        self.children: list[ChildClock] = []
        self.num_children = 0
        self.speed = 0
        self.start_time = 0.0

    def start(self) -> None:
        self.start_time = time()
        self.ticking = True
        # Process(target=self.tick).start()
        Process(target=self._tick_cwrapper).start()

    def stop(self) -> None:
        self.ticking = False

    def add_child(self, divisor: int, func: EMULATE_CYCLE_FUNCTION) -> None:
        """
        Creates a clock whose clock rate is derived from this clock.
        This child clock runs the given callable every time it ticks.
        """
        self.children.append(ChildClock(divisor, func))
        self.num_children += 1

    def _tick_cwrapper(self) -> None:
        self.tick()

    def tick(self) -> None:
        """
        Requests that the clock tick once.
        If enough time has passed, ticks any child clocks derived from this clock as well.
        Blocks until all child clocks have finished executing their cycle.
        """
        while self.ticking:
            self.cycle += 1
            ii = 0
            # while loop instead of for loop over the list for greater Cython speedup
            while ii < self.num_children:
                child: ChildClock = self.children[ii]
                if self.cycle % child.divisor == 0:
                    child.tick()
                ii += 1
            #while time_ns() - self._last_cycle_time_ns < self._nanoseconds_per_tick:
            #    # wait until enough time has passed to move onto the next tick
            #    pass
            # DEBUG
            if self.cycle % 10000000 == 0:  # print every 10 million cycles
                self.last_print_time = time()
                delta = self.last_print_time - self.start_time
                print(f"{'{:,}'.format(self.cycle // delta)} c/s avg over {delta}s")


class ChildClock:
    """
    A Clock whose frequency is calculated by dividing its parent's frequency by `divisor`.
    When this ChildClock ticks, it runs the callback function given when this clock is instantiated.
    """
    def __init__(self, divisor: int, func: EMULATE_CYCLE_FUNCTION) -> None:
        self.divisor = divisor
        self.func = func

    def tick(self) -> None:
        self.func()
