
from typing import Tuple

type IntOrFloat = int | float
type Interval = Tuple[IntOrFloat | None, IntOrFloat | None]


def nInInterval(n: IntOrFloat, interval: Interval) -> bool:
    return (
        (interval[0] is None or n >= interval[0])
        and
        (interval[1] is None or n <= interval[1])
    )


class Bounds:
    __list: list[IntOrFloat | None]

    def __init__(self, bounds: Tuple[Interval, ...]) -> None:

        # Maybe this could be translated to (None, None) ?
        assert len(bounds) > 0, 'Empty bounds'
        # Redundant?
        assert all(len(interval) == 2 for interval in bounds), 'Invalid bounds'
        self.__list = []
        for interval in bounds:
            self.__list.extend(interval)

    def get_bounds(self) -> Tuple[Interval, ...]:
        return tuple(
            (self.__list[i], self.__list[i + 1])
            for i in range(0, len(self.__list), 2)
        )

    def invert(self):
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
        (None, 1), (3, 5), (7, None) U (2, 4) = (None, 1), (3, None)
        |
        [None, 1, 3, 5, 7, None] U [2, 4] = [None, 1, 3, None]

        (1, 3) U (2, 4) = (1, 4)
           ^  ^
        [1, 3] U [2, 4] = [1, 4]
           ^  ^

        (None, 1), (3, 5), (7, None) U (2, 4) = (None, 1), (2, 5), (7, None)
                  ^   ^
        [None, 1, 3, 5, 7, None] U [2, 4] = [None, 1, 2, 5, 3, None]
                 ^  ^
        [None, 1, 2  4  5, 7, None] U [2, 4] = [None, 1, 2, 5, 3, None]

        """
        # if len(self.__list) == 0:
        #     self.__list = list(interval)
        #     return

        interval_l = interval[0]
        interval_u = interval[1]
        oks = [interval_l is None, interval_u is None]

        # This seems tedious
        assert not all(oks), 'Both bounds are None. Not supported now.'
        # if interval_l is None and self.__list[0] is not None:
        #     # self.__list.insert(0, None)
        #     idxs[0] = 0

        # if interval_u is None and self.__list[-1] is not None:
        #     # self.__list.insert(-1, None)
        #     idxs[1] = len(self.__list)
        assert interval_l is not None and interval_u is not None, 'Both bounds are None. Not supported now.'

        bounds_cp = list(self.get_bounds())

        for i, bound in enumerate(bounds_cp):
            bound_l, bound_u = bound
            # assert bound_u is not None, "Not implemented"

            if bound_u is not None and interval_l > bound_u:
                # Need to be inserted after this bound.
                # Like bound = (1, 3), interval = (4, 5)
                continue

            if bound_l is not None and interval_u < bound_l:
                # We're done, technically?
                if i > 0:
                    bound_l_prev, bound_u_prev = bounds_cp[i-1]
                    if bounds_cp[i-1] != interval:
                        bounds_cp.insert(i, interval)
                break

            if bound_l is None:
                b_l = None
            else:
                b_l = min(bound_l, interval_l)
            if bound_u is None:
                b_u = None
            else:
                b_u = max(bound_u, interval_u)

            bounds_cp[i] = (b_l, b_u)

            if i == 0:
                continue
            #     assert False, "This should not happen?"

            bound_l_prev, bound_u_prev = bounds_cp[i-1]
            assert bound_u_prev is not None, "Prev bound cannot be None"

            # intersection / merging
            if bound_l is None or bound_l < bound_u_prev:
                if bound_l_prev is None:
                    # This is the first bound
                    new_b = (None, bound_u)
                else:
                    b_l = None if bound_l is None else min(
                        bound_l_prev, bound_l)
                    new_b = (b_l, bound_u)
                bounds_cp[i] = new_b
                bounds_cp.pop(i-1)

        # Add interval if outside of bounds
        bounds_cp_u = bounds_cp[-1][1]
        if bounds_cp_u is not None:
            if interval_l > bounds_cp_u:
                bounds_cp.append(interval)

        self.__list = []
        for bound in bounds_cp:
            self.__list.extend(bound)
        return self

    def __str__(self):
        return str(self.get_bounds())


if __name__ == '__main__':
    b = Bounds(((None, 1), (2, 3), (4, None)))
    # b = Bounds(((0, 2), (4, 6), (8, 10)))
    # i_union = (1, 3)
    # i_union = (3, 7)
    i_union = (0, 1.5)
    print('origin:', b, 'U', i_union)

    b = b.union_interval(i_union)
    print('union :', b)
