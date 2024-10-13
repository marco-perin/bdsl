
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from bounds import Bounds, Interval, IntOrFloat


def numOrNone(s: str) -> IntOrFloat | None:

    if s == '':
        return None

    if '.' in s:
        return float(s)

    return int(s)


@dataclass
class VarData:
    """Holds data for a variable"""
    name: str
    bounds: Bounds = Bounds(((None, None),))
    size: int = 1
    expr: List[str] | None = None

    def __init__(self,
                 name: str,
                 arg2: Interval | List[str],
                 size: str | None):
        self.name = name
        if size is not None:
            self.size = int(size)

        if isinstance(arg2, list):
            assert all(isinstance(arg2i, str) for arg2i in arg2), \
                f'Expression {arg2} must be a list of strings'
            self.expr = arg2
        else:
            if arg2[0] is not None and arg2[1] is not None:
                assert arg2[0] <= arg2[1], \
                    f'Bounds {arg2} in line are invalid: min > max!'
            self.bounds = Bounds(((arg2,)))

    def __str__(self):

        if self.expr is None:
            bs = self.bounds.get_bounds()[0]
            b_min = bs[0] if bs[0] is not None else ' '
            b_max = bs[1] if bs[1] is not None else ' '
            return f'{self.name} ({self.size}) [{b_min}..{b_max}]'

        return f'{self.name} ({self.size}) "{' '.join(self.expr)}"'


type Context = Dict[str, VarData]


def f_intersect(
        f: Callable[[IntOrFloat, IntOrFloat], IntOrFloat],
        x: IntOrFloat | None,
        y: IntOrFloat | None
) -> IntOrFloat | None:
    """Returns None only if both x and y are None"""
    if x is None or y is None:
        if x is None:
            return y
        return x
    return f(x, y)


def interval_intersect(b1: Interval, b2: Interval) -> Interval:
    b_min = f_intersect(min,  b1[0], b2[0])
    b_max = f_intersect(max,  b1[1], b2[1])
    return (b_min, b_max)

iota_counter = 0  # pylint: disable=invalid-name


def iota(reset=False):
    """
    Returns a unique integer each time it is called.
    If reset is True, the counter is reset to 0.
    """
    global iota_counter  # pylint: disable=global-statement
    if reset:
        iota_counter = 0
    result = iota_counter
    iota_counter += 1
    return result
