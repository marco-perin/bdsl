from dataclasses import dataclass

from bounds import Bounds, Interval
from configuration import UNICODE_OUT
from colors import c


@dataclass
class VarData:
    """Holds data for a variable"""

    name: str
    bounds: Bounds | None
    size: int = 1
    expr: list[str] | None = None

    @classmethod
    def auto(
        cls, name: str, arg2: Bounds | Interval | list[str] | None, size: str | None
    ):

        size_i: int | None = 1 if size is None else int(size)
        if arg2 is None:
            bounds = None
            expr = None
        elif isinstance(arg2, list):
            assert all(
                isinstance(arg2i, str) for arg2i in arg2
            ), f'Expression {arg2} must be a list of strings'
            expr = arg2
            bounds = None
        else:
            expr = None
            if isinstance(arg2, Bounds):
                bounds = arg2
            else:
                a20, a21 = arg2[0], arg2[1]
                if a20 is not None and a21 is not None:
                    assert (
                        a20 <= a21
                    ), f'Bounds {arg2} in line are invalid: min > max ({a20}<{a21})!'
                bounds = Bounds(((arg2,)))

        return cls(name, bounds, size_i, expr)

    def copy(self):
        if self.bounds is not None:
            return VarData(self.name, self.bounds.copy(), self.size, self.expr)
        return VarData(self.name, None, self.size, self.expr)

    def __repr__(self) -> str:
        # varname = self.name
        return f'{self.name} : {self.bounds}'

    def __str__(self):

        varname = c.GREEN(self.name)
        if self.expr is None:
            assert self.bounds is not None
            bs = self.bounds  # .get_bounds()
            # bs_string = '|'.join(
            #     # pylint: disable=consider-using-f-string
            #     '{}..{}'.format(
            #         b[0] if b[0] is not None else ' ',
            #         b[1] if b[1] is not None else ' '
            #     )
            #     for b in bs
            # )
            bs_string = str(bs)
            # return f'{self.name} ({self.size}) [{b_min}..{b_max}]'

            if UNICODE_OUT:
                return f'{varname} ∈ {bs_string}'

            return f'{varname} : {bs_string}'

        # return f'{self.name} ({self.size}) "{' '.join(self.expr)}"'
        return f'{varname} "{' '.join(self.expr)}"'
