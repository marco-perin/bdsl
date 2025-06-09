
from configuration import UNICODE_OUT
from typing import Callable, Tuple, Self

# TODO: move this into types
type IntOrFloat = int | float


class IntervalPoint:

    def __init__(self, value: IntOrFloat, is_included: bool = True) -> None:
        self.value = value
        self.is_included = is_included

    def __eq__(self, other: Self | IntOrFloat) -> bool:
        if isinstance(other, IntervalPoint):
            return (
                self.value == other.value
            ) and (
                self.is_included
            ) and (
                other.is_included
            )
        return self.value == other

    def __gt__(self, other: Self | IntOrFloat) -> bool:
        if isinstance(other, IntervalPoint):
            if self.is_included and other.is_included:
                return self.value >= other.value
            return self.value > other.value
        if self.is_included:
            return self.value >= other
        return self.value > other

    def __lt__(self, other: Self | IntOrFloat) -> bool:
        if isinstance(other, IntervalPoint):
            if self.is_included and other.is_included:
                return self.value <= other.value
            return self.value < other.value
        if self.is_included:
            return self.value <= other
        return self.value < other

    def __ge__(self, other: Self | IntOrFloat) -> bool:
        assert False, 'Use > instead of >=, it takes into account the inclusion'

    def __le__(self, other: Self | IntOrFloat) -> bool:
        assert False, 'Use < instead of <=, it takes into account the inclusion'

    def __repr__(self) -> str:
        return f'{self.value}'


class Interval(tuple[IntervalPoint | None, IntervalPoint | None]):
    def __new__(cls, first: IntervalPoint | None, second: IntervalPoint | None) -> Self:
        return super().__new__(cls, (first, second))

    def get_braces(self):
        s0, s1 = self
        return (
            '(' if s0 is None or not s0.is_included else '[',
            ')' if s1 is None or not s1.is_included else ']'
        )

    def __repr__(self) -> str:
        b1, b2 = self.get_braces()
        return f"{b1}{self[0]!r}, {self[1]!r}{b2}"

    def __str__(self) -> str:
        b1, b2 = self.get_braces()
        return f"{b1}{self[0]!r}, {self[1]!r}{b2}"
        # return f"({self[0]}, {self[1]})"


def tup2interval(tup: tuple[IntOrFloat | None, IntOrFloat | None], included: tuple[bool, bool] = (True, True)) -> Interval:
    v1 = None if tup[0] is None else IntervalPoint(tup[0], included[0])
    v2 = None if tup[1] is None else IntervalPoint(tup[1], included[1])
    return Interval(v1, v2)


def f_intersect(
        f: Callable[[IntervalPoint, IntervalPoint], IntervalPoint],
        x: IntervalPoint | None,
        y: IntervalPoint | None
) -> IntervalPoint | None:
    """Returns None only if both x and y are None"""
    if x is None or y is None:
        if x is None:
            return y
        return x
    return f(x, y)


def interval_intersect(b1: Interval, b2: Interval) -> Interval:
    b_min = f_intersect(min,  b1[0], b2[0])
    b_max = f_intersect(max,  b1[1], b2[1])
    return Interval(b_min, b_max)


def invert_interval(b: Interval) -> list[Interval]:
    if b[0] is None:
        return [Interval(b[1], None)]

    if b[1] is None:
        return [Interval(None, b[0])]

    return [Interval(None, b[0]), Interval(b[1], None)]


def nInInterval(n: IntervalPoint, interval: Interval) -> bool:
    ret = True
    i0 = interval[0]
    i1 = interval[1]

    if i0 is None:
        ret = ret and True
    else:
        if i0.is_included:
            ret = ret and n > i0.value
        else:
            ret = ret and n > i0.value

    if i1 is None:
        return ret and True

    if i1.is_included:
        return ret and n < i1.value

    return ret and n < i1.value


class Bounds:
    __list: list[IntervalPoint | None]

    def __init__(self, bounds: Tuple[Interval | tuple[IntervalPoint | None, IntervalPoint | None], ...]) -> None:

        # Maybe this could be translated to (None, None) ?
        assert len(bounds) > 0, 'Empty bounds'
        # Redundant?
        assert all(len(interval) == 2 for interval in bounds), 'Invalid bounds'

        _bounds = [
            b if isinstance(b, Interval) else Interval(*b)
            for b in bounds
        ]
        self.__set_list(_bounds)

    @classmethod
    def from_list(cls, interval: list[Interval]):
        return cls(tuple(interval))

    @classmethod
    def from_num_tuples(
            cls,
            interval: tuple[tuple[IntOrFloat | None, IntOrFloat | None], ...],
            included: bool = True
    ):
        return cls(tuple(
            Interval(
                None if l_b is None else IntervalPoint(l_b, included),
                None if u_b is None else IntervalPoint(u_b, included),
            )
            for l_b, u_b in interval
        ))

    @classmethod
    def from_interval(cls, interval: Interval | tuple[IntervalPoint | None, IntervalPoint | None]):
        if not isinstance(interval, Interval):
            interval = Interval(*interval)
        return cls((interval,))

    def copy(self):
        return Bounds(self.get_bounds())

    def __set_list(self, bounds: tuple[Interval, ...] | list[Interval]):
        self.__list = []
        for interval in bounds:
            self.__list.extend(interval)

        return self

    def get_bounds(self) -> Tuple[Interval, ...]:
        """Returns a tuple of intervals"""
        try:
            return tuple(
                Interval(self.__list[i], self.__list[i + 1])
                for i in range(0, len(self.__list), 2)
            )
        except IndexError:
            assert False, f'Invalid bounds: {self.__list}'

    def invert(self):
        """Inverts the bounds"""
        assert len(self.__list) > 0, 'Empty bounds'
        assert len(self.__list) % 2 == 0, 'Odd number of bounds'

        if self.__list[0] is None:
            self.__list.pop(0)
        else:
            self.__list.insert(0, None)
        if self.__list[-1] is None:
            self.__list.pop(-1)
        else:
            self.__list.append(None)
        return self

    def union_interval(self, interval: Interval):
        """
        Perform a union ofthe bounds with an interval
        """

        return self.union_bounds(Bounds.from_interval(interval))

    def union_bounds(self, bounds: 'Bounds'):

        bds_1 = self.__list.copy()
        bds_2 = bounds.__list.copy()
        new_bds: list[IntervalPoint | None] = []

        tracing_1, tracing_2 = (bds_1[0] is None, bds_2[0] is None)

        # remove Initial Nones
        if tracing_1 or tracing_2:
            new_bds.append(None)
            if tracing_1:
                bds_1.pop(0)
            if tracing_2:
                bds_2.pop(0)

        # tracing = f_1 or f_2

        i_1, i_2 = 0, 0

        # done_1, done_2 = False, False

        while i_1 < len(bds_1) and i_2 < len(bds_2):

            b_1 = bds_1[i_1]
            b_2 = bds_2[i_2]
            # print(f'new_bds {i_1}-{i_2}:', new_bds)
            # print(f'-- {i_1} {i_2}')
            # print("bds_1: ", '-' if tracing_1 else ' ', bds_1[i_1])
            # print("bds_1: ", '-' if tracing_2 else ' ', bds_2[i_2])

            if b_1 is None or b_2 is None:
                new_bds.append(None)
                break
            assert b_1 is not None and b_2 is not None, 'Unreachable'

            if b_1 < b_2:
                i_1 += 1

                if (not tracing_2):
                    # Add point if not between two intervals
                    new_bds.append(b_1)
                tracing_1 = not tracing_1
            else:
                i_2 += 1
                if (not tracing_1):
                    # Add point if not between two intervals
                    new_bds.append(b_2)
                tracing_2 = not tracing_2

            # print('new_bds:', new_bds)

        if len(new_bds) == 1 or new_bds[-1] is not None:
            if i_1 < len(bds_1):
                new_bds.extend(bds_1[i_1:])
            elif i_2 < len(bds_2):
                new_bds.extend(bds_2[i_2:])

        # Sanitize - remove overlapping bounds
        for i in range(len(new_bds)-2, 0, -1):
            if new_bds[i] == new_bds[i+1]:
                new_bds.pop(i+1)
                new_bds.pop(i)

        # print('new_bds fin:', new_bds)
        self.__list = new_bds
        return self

    def intersect_bounds(self, bounds: 'Bounds'):

        bds_1 = self.__list.copy()
        bds_2 = bounds.__list.copy()
        new_bds: list[IntervalPoint | None] = []

        tracing_1, tracing_2 = (bds_1[0] is None, bds_2[0] is None)

        # remove Initial Nones
        if tracing_1 and tracing_2:
            new_bds.append(None)
        if tracing_1:
            bds_1.pop(0)
        if tracing_2:
            bds_2.pop(0)

        # tracing = f_1 or f_2

        i_1, i_2 = 0, 0

        # done_1, done_2 = False, False
        b_1, b_2 = None, None
        while i_1 < len(bds_1) and i_2 < len(bds_2):

            b_1 = bds_1[i_1]
            b_2 = bds_2[i_2]
            # print(f'new_bds {i_1}-{i_2}:', new_bds)
            # print(f'-- {i_1} {i_2}')
            # print("bds_1: ", '-' if tracing_1 else ' ', b_1)
            # print("bds_2: ", '-' if tracing_2 else ' ', b_2)

            if b_1 is None and b_2 is None:
                new_bds.append(None)
                break
            # assert b_1 is not None and b_2 is not None, 'Unreachable'
            if b_1 is None or b_2 is None:
                break
            if b_1 < b_2:
                # print('b_1 < b_2')
                i_1 += 1

                if tracing_2:
                    # Add point if not between two intervals
                    new_bds.append(b_1)

                tracing_1 = not tracing_1
            else:
                # print('b_2 >= b_2')
                i_2 += 1
                if tracing_1:
                    # Add point if not between two intervals
                    new_bds.append(b_2)
                tracing_2 = not tracing_2

            # print('new_bds:', new_bds)

        if i_1 < len(bds_1) or i_2 < len(bds_2):
            if b_1 is None or b_2 is None:
                if i_1 < len(bds_1) and b_2 is None:
                    new_bds.extend(bds_1[i_1:])
                elif i_2 < len(bds_2) and b_1 is None:
                    new_bds.extend(bds_2[i_2:])

        # print('new_bds:', new_bds)
        self.__list = new_bds
        return self

    def intersect_interval(self, interval: Interval | tuple[IntervalPoint | None, IntervalPoint | None]):
        """Intersection of bounds with an interval"""

        return self.intersect_bounds(Bounds.from_interval(interval))

    def __repr__(self) -> str:
        lst = [b1 if b1 == b2 else (b1, b2) for (b1, b2) in self.get_bounds()]

        if not UNICODE_OUT:
            return str(lst)
        return '[' + ' ∪ '.join(map(str, lst)) + ']'

    def __str__(self):
        lst = [b1 if b1 == b2 else (b1, b2) for (b1, b2) in self.get_bounds()]

        if not UNICODE_OUT:
            return str(lst)
        return '[' + ' ∪ '.join(map(str, lst)) + ']'


def main():

    b = Bounds((
        Interval(None,             IntervalPoint(1)),
        Interval(IntervalPoint(2), IntervalPoint(3)),
        Interval(IntervalPoint(4), None),
    ))
    print('bound', b)
    # b = Bounds(((0, 2), (4, 6), (8, 10)))
    # i_union = (1, 3)
    # i_union = (3, 7)
    # i_union = Bounds.from_interval((IntervalPoint(0), IntervalPoint(1.5)))
    # i_union = Bounds.from_interval((IntervalPoint(2.5), None))
    i_union = Bounds((Interval(IntervalPoint(0), IntervalPoint(0.5)),
                     Interval(IntervalPoint(2.5), None)))
    # i_union = (IntervalPoint(0), IntervalPoint(1.5))
    # print('origin:', b, 'U', i_union)

    print('interval', i_union)
    # b = b.union_interval(i_union)
    # print('union :', b)

    # print('->', b.union_bounds(i_union))
    print('->', b.intersect_bounds(i_union))


if __name__ == '__main__':
    main()
