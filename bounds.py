from configuration import UNICODE_OUT
from typing import Callable, Literal, Tuple, Self

# TODO: move this into types
type IntOrFloat = int | float


class IntervalPoint:

    def __init__(self, value: IntOrFloat, is_included: bool = True) -> None:
        self.value = value
        self.is_included = is_included

    def __eq__(self, other: Self | IntOrFloat | object) -> bool:
        if other is None:
            return self is None
        if isinstance(other, IntervalPoint):
            return (self.value == other.value) and (
                (self.is_included) == (other.is_included)
            )
        if isinstance(other, type(self)):
            return self.value == other
        return self.value == other

    def __gt__(self, other: Self | IntOrFloat) -> bool:
        if isinstance(other, IntervalPoint):
            return self.value > other.value
        if self.is_included:
            return self.value > other
        return self.value > other

    def __lt__(self, other: Self | IntOrFloat) -> bool:
        if isinstance(other, IntervalPoint):
            return self.value < other.value
        if self.is_included:
            return self.value < other
        return self.value < other

    def __ge__(self, other: Self | IntOrFloat) -> bool:
        gt = self.__gt__(other)
        return gt or self == other

    def __le__(self, other: Self | IntOrFloat) -> bool:
        lt = self.__lt__(other)
        return lt or self == other

    def __repr__(self) -> str:
        return f'{self.value}'


class Interval(tuple[IntervalPoint | None, IntervalPoint | None]):
    def __new__(cls, first: IntervalPoint | None, second: IntervalPoint | None) -> Self:
        return super().__new__(cls, (first, second))

    def get_braces(
        self,
    ) -> Tuple[Literal['('] | Literal['['], Literal[')'] | Literal[']']]:
        s0, s1 = self
        return (
            '(' if (s0 is None or (not s0.is_included)) else '[',
            ')' if (s1 is None or (not s1.is_included)) else ']',
        )

    def __repr__(self) -> str:
        b1, b2 = self.get_braces()
        return f'{b1}{self[0]!r}, {self[1]!r}{b2}'

    def __str__(self) -> str:
        b1, b2 = self.get_braces()
        return f'{b1}{self[0]!r}, {self[1]!r}{b2}'
        # return f'({self[0]}, {self[1]})'


def tup2interval(
    tup: tuple[IntOrFloat | None, IntOrFloat | None],
    included: tuple[bool, bool] = (True, True),
) -> Interval:
    v1 = None if tup[0] is None else IntervalPoint(tup[0], included[0])
    v2 = None if tup[1] is None else IntervalPoint(tup[1], included[1])
    return Interval(v1, v2)


def f_intersect(
    f: Callable[[IntervalPoint, IntervalPoint], IntervalPoint],
    x: IntervalPoint | None,
    y: IntervalPoint | None,
) -> IntervalPoint | None:
    """Returns None only if both x and y are None"""
    if x is None or y is None:
        if x is None:
            return y
        return x
    return f(x, y)


def f_apply(f: Callable[[IntervalPoint], IntervalPoint], i: Interval, invert: bool):
    i0, i1 = i

    if i0:
        i0 = f(i0)
    if i1:
        i1 = f(i1)
    if not invert:
        return Interval(i0, i1)

    return Interval(i1, i0)


def interval_intersect(b1: Interval, b2: Interval) -> Interval:
    b_min = f_intersect(min, b1[0], b2[0])
    b_max = f_intersect(max, b1[1], b2[1])
    return Interval(b_min, b_max)


def invert_interval(b: Interval) -> list[Interval]:
    if b[0] is None:
        return [Interval(b[1], None)]

    if b[1] is None:
        return [Interval(None, b[0])]

    return [Interval(None, b[0]), Interval(b[1], None)]


def split_interval(
    i: Interval, x: IntervalPoint
) -> tuple[Interval | None, Interval | None]:
    """Splits an interval at point x in two intervals"""
    i0, i1 = i

    # NOTE: is it correct to restrict x to be in bounds?
    if i0 is not None:
        # assert x > i0.value
        if x < i0.value:
            return None, i
    if i1 is not None:
        # assert x < i1.value
        if x > i1.value:
            return i, None

    # TODO: Check what to do with includedness ?
    return Interval(i0, x), Interval(x, i1)


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

    def __init__(
        self,
        bounds: Tuple[
            Interval | tuple[IntervalPoint | None, IntervalPoint | None], ...
        ],
    ) -> None:

        # Maybe this could be translated to (None, None) ?
        assert len(bounds) > 0, 'Empty bounds'
        # Redundant?
        assert all(len(interval) == 2 for interval in bounds), 'Invalid bounds'

        _bounds = [b if isinstance(b, Interval) else Interval(*b) for b in bounds]
        self.__set_list(_bounds)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bounds):
            return NotImplemented

        if len(self.__list) != len(other.__list):
            return False

        for self_point, other_point in zip(self.__list, other.__list):
            if self_point != other_point:
                return False

        return True

    @classmethod
    def from_list(cls, interval: list[Interval]):
        return cls(tuple(interval))

    @classmethod
    def from_num_tuples(
        cls,
        interval: tuple[tuple[IntOrFloat | None, IntOrFloat | None], ...],
        included: bool = True,
    ):
        return cls(
            tuple(
                Interval(
                    None if l_b is None else IntervalPoint(l_b, included),
                    None if u_b is None else IntervalPoint(u_b, included),
                )
                for l_b, u_b in interval
            )
        )

    @classmethod
    def from_interval(
        cls, interval: Interval | tuple[IntervalPoint | None, IntervalPoint | None]
    ):
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
            # print(
            #     'bds_1: ',
            #     '--' if tracing_1 else ' ',
            #     b_1,
            #     ')' if not b_1.is_included else ']',
            # )
            # print(
            #     'bds_2: ',
            #     '--' if tracing_2 else ' ',
            #     b_2,
            #     ')' if not b_2.is_included else ']',
            # )

            if b_1 is None or b_2 is None:
                new_bds.append(None)
                break
            assert b_1 is not None and b_2 is not None, 'Unreachable'

            # print('test: ', b_1, b_1.is_included, b_2, b_2.is_included, '->', b_1 <= b_2)
            if b_1 <= b_2:
                i_1 += 1

                if not tracing_2:
                    # Add point if not between two intervals
                    b_1.is_included = (
                        b_1.is_included or b_1.is_included != b_2.is_included
                    )
                    new_bds.append(b_1)
                tracing_1 = not tracing_1
            else:
                i_2 += 1
                if not tracing_1:
                    # Add point if not between two intervals
                    b_2.is_included = (
                        b_2.is_included or b_1.is_included != b_2.is_included
                    )

                    new_bds.append(b_2)
                tracing_2 = not tracing_2

            # print('new_bds:', new_bds)

            # print(
            #     'new_bds:',
            #     [f'{b} {')' if not b.is_included else ']'}' for b in new_bds],
            # )
        if len(new_bds) == 1 or new_bds[-1] is not None:
            if i_1 < len(bds_1):
                new_bds.extend(bds_1[i_1:])
            elif i_2 < len(bds_2):
                new_bds.extend(bds_2[i_2:])

        # print(
        #     'new_bds pre_sanit:',
        #     [f'{b} {')' if not b.is_included else ']'}' for b in new_bds],
        # )
        # Sanitize - remove overlapping bounds
        i = len(new_bds) - 2
        while i > 0:

            b1, b2 = new_bds[i], new_bds[i + 1]

            # if isinstance(b1, IntervalPoint):
            #     b1d = ')' if not b1.is_included else ']'
            # else:
            #     b1d = ';'
            # if isinstance(b2, IntervalPoint):
            #     b2d = ')' if not b2.is_included else ']'
            # else:
            #     b2d = ';'

            # print(
            #     'test_eq: ',
            #     b1,
            #     b1d,
            #     # ')' if not b1.is_included else ']',
            #     b2,
            #     b2d,
            #     # ')' if not b2.is_included else ']',
            #     b1 == b2,
            # )

            def pop(i, b_prev: IntervalPoint | None = None):
                if (
                    b_prev
                    # i > 1
                    # and b1 is not None
                    # and new_bds[i - 1] is not None
                    and isinstance(b1, IntervalPoint)
                    and b_prev.value == b1.value
                    and (b1.is_included != b_prev.is_included)
                ):
                    new_bds[i - 1].is_included = True
                new_bds.pop(i + 1)
                new_bds.pop(i)

            if b1 == b2:
                if b1 is None and b2 is None:
                    pop(i)
                    i -= 1
                else:
                    assert b1 is not None and b2 is not None
                    assert isinstance(b1, IntervalPoint)
                    if b1.is_included and b2.is_included:
                        if i > 1:
                            b_prev = new_bds[i - 1]
                            assert isinstance(b_prev, IntervalPoint)
                            if (
                                b_prev is not None
                                and b_prev.value == b1.value
                                and (b1.is_included == b_prev.is_included)
                            ):
                                pop(i, b_prev)
                                i -= 1
                        elif i < len(new_bds) - 2:
                            # print('i:', i, len(new_bds))
                            pop(i)
                            i -= 1

            # print(
            #     'new_bds after_check:',
            #     [f'{b}{')' if not b.is_included else ']'}' for b in new_bds],
            # )
            i -= 1

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
            # print('bds_1: ', '-' if tracing_1 else ' ', b_1)
            # print('bds_2: ', '-' if tracing_2 else ' ', b_2)

            if b_1 is None and b_2 is None:
                new_bds.append(None)
                break
            # assert b_1 is not None and b_2 is not None, 'Unreachable'
            if b_1 is None or b_2 is None:
                break
            if b_1 <= b_2:
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

    def intersect_interval(
        self, interval: Interval | tuple[IntervalPoint | None, IntervalPoint | None]
    ):
        """Intersection of bounds with an interval"""

        return self.intersect_bounds(Bounds.from_interval(interval))

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        lst = map(str, self.get_bounds())
        if not UNICODE_OUT:
            return '' + ' U '.join(lst) + ''

        return '' + ' ∪ '.join(lst) + ''


def main():

    b = Bounds(
        (
            Interval(None, IntervalPoint(1)),
            Interval(IntervalPoint(2), IntervalPoint(3)),
            Interval(IntervalPoint(4), None),
        )
    )
    print('bound', b)
    # b = Bounds(((0, 2), (4, 6), (8, 10)))
    # i_union = (1, 3)
    # i_union = (3, 7)
    # i_union = Bounds.from_interval((IntervalPoint(0), IntervalPoint(1.5)))
    # i_union = Bounds.from_interval((IntervalPoint(2.5), None))
    i_union = Bounds(
        (
            Interval(IntervalPoint(0), IntervalPoint(0.5)),
            Interval(IntervalPoint(2.5), None),
        )
    )
    # i_union = (IntervalPoint(0), IntervalPoint(1.5))
    # print('origin:', b, 'U', i_union)

    print('interval', i_union)
    # b = b.union_interval(i_union)
    # print('union :', b)

    # print('->', b.union_bounds(i_union))
    print('->', b.intersect_bounds(i_union))


if __name__ == '__main__':
    main()
