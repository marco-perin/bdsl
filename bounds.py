
from typing import Callable, Tuple, Self

# TODO: move this into types
type IntOrFloat = int | float


class IntervalPoint:

    def __init__(self, value: IntOrFloat, is_included: bool = True) -> None:
        self.value = value
        self.is_included = is_included

    def __eq__(self, other: Self | IntOrFloat) -> bool:
        if isinstance(other, IntervalPoint):
            return self.value == other.value and self.is_included and other.is_included
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


type Interval = tuple[IntervalPoint | None, IntervalPoint | None]


def tup2interval(tup: tuple[IntOrFloat | None, IntOrFloat | None], included: tuple[bool, bool] = (True, True)) -> Interval:
    v1 = None if tup[0] is None else IntervalPoint(tup[0], included[0])
    v2 = None if tup[1] is None else IntervalPoint(tup[1], included[1])
    return (v1, v2)


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
    return (b_min, b_max)


def invert_interval(b: Interval) -> list[Interval]:
    if b[0] is None:
        return [(b[1], None)]

    if b[1] is None:
        return [(None, b[0])]

    return [(None, b[0]), (b[1], None)]


def nInInterval(n: IntervalPoint, interval: Interval) -> bool:
    ret = True
    if interval[0] is None:
        ret = ret and True
    else:
        if interval[0].is_included:
            ret = ret and n > interval[0].value
        else:
            ret = ret and n > interval[0].value

    if interval[1] is None:
        return ret and True

    if interval[1].is_included:
        return ret and n < interval[1].value

    return ret and n < interval[1].value


class Bounds:
    __list: list[IntervalPoint | None]

    def __init__(self, bounds: Tuple[Interval, ...]) -> None:

        # Maybe this could be translated to (None, None) ?
        assert len(bounds) > 0, 'Empty bounds'
        # Redundant?
        assert all(len(interval) == 2 for interval in bounds), 'Invalid bounds'

        self.__set_list(bounds)

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
            (
                None if l_b is None else IntervalPoint(l_b, included),
                None if u_b is None else IntervalPoint(u_b, included),
            )
            for l_b, u_b in interval
        ))

    @classmethod
    def from_interval(cls, interval: Interval):
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
                (self.__list[i], self.__list[i + 1])
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
        # if len(self.__list) == 0:
        #     self.__list = list(interval)
        #     return

        # interval_l, interval_u = interval

        # if interval_l is None or interval_u is None:
        #     # print('Warning: Union with open interval')

        #     # if interval_l is None:
        #     #     assert interval_u is not None, 'Unreachable'

        #     #     if self.__list[0] is not None:
        #     #         i_cut = 0
        #     #         for i, val in enumerate(self.__list):
        #     #             if val is None and i == 0:
        #     #                 i_cut = i+1
        #     #                 continue
        #     #             if val is not None and val < interval_u:
        #     #                 i_cut = i+1
        #     #                 continue
        #     #             break
        #     #         self.__list = [None, *self.__list[i_cut:]]
        #     #     else:

        #     #         self.__list.pop(0)  # remove None

        #     #         is_in = True
        #     #         idx_cmp = 0

        #     #         while len(self.__list) > idx_cmp and \
        #     #                 self.__list[idx_cmp] is not None:

        #     #             if self.__list[idx_cmp] < interval_u:

        #     #                 if is_in:
        #     #                     self.__list.pop(idx_cmp)
        #     #                 else:
        #     #                     self.__list.append(interval_u)
        #     #                     idx_cmp += 1
        #     #                 is_in = not is_in

        #     #         # self.__list = [*interval, *self.__list]
        #     #         if len(self.__list) == 0:
        #     #             self.__list = [*interval, *self.__list]
        #     #         else:
        #     #             self.__list = [None, *self.__list]
        #     #         # else:
        #     #         #     # pass
        #     #         #     for i, val in enumerate(self.__list):
        #     #         #         if i == 0:
        #     #         #             i_cut = i+1
        #     #         #             continue
        #     #         #         if val is None and i == len(self.__list)-1:
        #     #         #             # i_cut = i+1
        #     #         #             # continue
        #     #         #             assert False, 'Unreachable??'
        #     #         #         # Middle of list
        #     #         #         assert val is not None, 'Unreachable'
        #     #         #         if val < interval_u:
        #     #         #             i_cut = i+1
        #     #         #             continue
        #     #         #         break
        #     #         #     self.__list = [None, *self.__list[i_cut:]]

        #     #     print(self.__list)
        #     #     return self

        #     # elif interval_u is None:
        #     #     if self.__list[-1] is not None:

        #     #         assert interval_l is not None, 'Unreachable'

        #     #         for i, val in reversed(list(enumerate(self.__list))):
        #     #             if val is None and i == len(self.__list)-1:
        #     #                 i_cut = i
        #     #                 continue
        #     #             if val is not None and val > interval_l:
        #     #                 i_cut = i
        #     #                 continue

        #     #         self.__list = [*self.__list[:i_cut], None]

        #     #         print(self.__list)
        #     #         return self

        #     intval_i = (interval_u, interval_l)
        #     # i_cp_inv = self.copy().invert()
        #     # print('--')
        #     # print('inte:    ', self.copy())
        #     # print('ionv:    ', i_cp_inv)
        #     # print('interval:', interval)
        #     # print('intval_i:', intval_i)
        #     # i_cp_inters = i_cp_inv.intersect_interval(intval_i)
        #     # print('ionv_int:', i_cp_inters)

        #     self.invert() \
        #         .intersect_interval(intval_i) \
        #         .invert()
        #     return self

        # This seems tedious
        # assert interval_l is not None and interval_u is not None, 'Both bounds are None. Not supported now.'
        # # assert interval_l is not None or interval_u is not None, 'Both bounds are None. Not supported now.'

        # bounds_cp = list(self.get_bounds())

        # # Add interval if outside of bounds
        # bounds_cp_u = bounds_cp[-1][1]
        # if bounds_cp_u is not None and interval_l > bounds_cp_u:
        #     bounds_cp.append(interval)
        # else:
        #     for i, bound in enumerate(bounds_cp):
        #         bound_l, bound_u = bound

        #         if bound_u is not None and interval_l > bound_u:
        #             # Need to be inserted after this bound.
        #             continue

        #         if bound_l is not None and interval_u < bound_l:
        #             # We're done, technically?
        #             if i > 0:
        #                 bound_l_prev, bound_u_prev = bounds_cp[i-1]
        #                 if bounds_cp[i-1] != interval:
        #                     bounds_cp.insert(i, interval)
        #             break

        #         b_l = None if bound_l is None else min(bound_l, interval_l)
        #         b_u = None if bound_u is None else max(bound_u, interval_u)

        #         bounds_cp[i] = (b_l, b_u)

        #         if i == 0:
        #             continue
        #         #     assert False, "This should not happen?"

        #         bound_l_prev, bound_u_prev = bounds_cp[i-1]
        #         assert bound_u_prev is not None, "Prev bound cannot be None"

        #         # intersection / merging
        #         if bound_l is None or bound_l < bound_u_prev:
        #             if bound_l_prev is None:
        #                 # This is the first bound
        #                 new_b = (None, bound_u)
        #             else:
        #                 b_l = None if bound_l is None else min(
        #                     bound_l_prev, bound_l)
        #                 new_b = (b_l, bound_u)
        #             bounds_cp[i] = new_b
        #             bounds_cp.pop(i-1)

        # self.__list = []
        # for bound in bounds_cp:
        #     self.__list.extend(bound)
        # return self

    def union_bounds(self, bounds: 'Bounds'):

        # print('union.self: ', self)
        # print('union.other:', bounds)
        # for interval in bounds.get_bounds():
        #     # print('U  self    :', self)
        #     # print('U  interval:', interval)
        #     self.union_interval(interval)
        # # print('U  self    :', self)
        # return self
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
        # new_bds: list[Interval] = []

        # for interval in bounds.get_bounds():
        #     new_bds.extend(self.copy().intersect_interval(
        #         interval).get_bounds())
        # # print('new_bds:', new_bds)
        # self.__list = Bounds.from_interval(new_bds[0]).union_bounds(
        #     Bounds.from_list(new_bds[1:])).__list
        # return self
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

    def intersect_interval(self, interval: Interval):
        """Intersection of bounds with an interval"""

        return self.intersect_bounds(Bounds.from_interval(interval))

        # interval_l = interval[0]
        # interval_u = interval[1]

        # if interval_l is None and interval_u is None:
        #     # Intersection with open interval. Returning self
        #     return self

        # bounds_cp = list(self.get_bounds())

        # if interval_l is None:
        #     assert interval_u is not None, 'Unreachable'
        #     # Conditions like (None, 3) ->(x < 3)"""
        #     for i, bound in enumerate(bounds_cp):
        #         is_in = nInInterval(interval_u, bound)
        #         if is_in:
        #             bounds_cp[i] = (bound[0], interval_u)
        #             self.__set_list(bounds_cp[:i+1])
        #         elif bound[0] is not None and interval_u < bound[0]:
        #             self.__set_list(bounds_cp[:i])
        #     return self

        # if interval_u is None:
        #     assert interval_l is not None, 'Unreachable'

        #     # Conditions like (None, 3) ->(x < 3)"""
        #     for i, bound in enumerate(bounds_cp):
        #         is_in = nInInterval(interval_l, bound)
        #         if (bound[0] is not None and interval_l < bound[0]):
        #             bounds_cp[i] = (bound[0], bound[1])
        #             self.__set_list(bounds_cp[i:])
        #             break
        #         if is_in:
        #             bounds_cp[i] = (interval_l, bound[1])
        #             self.__set_list(bounds_cp[i:])
        #             break

        #     return self

        # ok_l = False
        # i_cut_l, i_cut_u = 0, len(bounds_cp)
        # for i, bound in enumerate(bounds_cp):
        #     is_in_l = nInInterval(interval_l, bound)
        #     is_in_u = nInInterval(interval_u, bound)
        #     if is_in_l and is_in_u:
        #         self.__set_list([interval])
        #         return self
        #     if is_in_l:
        #         i_cut_l = i
        #         bounds_cp[i] = (interval_l, bounds_cp[i][1])
        #         ok_l = True
        #     elif not ok_l and bound[0] is not None and interval_u < bound[0]:
        #         i_cut_l = i-1
        #         ok_l = True

        #     if is_in_u:
        #         i_cut_u = i+1
        #         bounds_cp[i] = (bounds_cp[i][0], interval_u)
        #     elif bound[0] is not None and interval_u < bound[0]:
        #         i_cut_u = i
        #         break
        # self.__set_list(bounds_cp[i_cut_l:i_cut_u])
        # return self

    def __repr__(self) -> str:
        return str([b1 if b1 == b2 else (b1, b2) for (b1, b2) in self.get_bounds()])

    def __str__(self):
        return str([b1 if b1 == b2 else (b1, b2) for (b1, b2) in self.get_bounds()])


if __name__ == '__main__':

    b = Bounds((
        (None,             IntervalPoint(1)),
        (IntervalPoint(2), IntervalPoint(3)),
        (IntervalPoint(4), None),
    ))
    print('bound', b)
    # b = Bounds(((0, 2), (4, 6), (8, 10)))
    # i_union = (1, 3)
    # i_union = (3, 7)
    # i_union = Bounds.from_interval((IntervalPoint(0), IntervalPoint(1.5)))
    # i_union = Bounds.from_interval((IntervalPoint(2.5), None))
    i_union = Bounds(((IntervalPoint(0), IntervalPoint(0.5)),
                     (IntervalPoint(2.5), None)))
    # i_union = (IntervalPoint(0), IntervalPoint(1.5))
    # print('origin:', b, 'U', i_union)

    print('interval', i_union)
    # b = b.union_interval(i_union)
    # print('union :', b)

    # print('->', b.union_bounds(i_union))
    print('->', b.intersect_bounds(i_union))
