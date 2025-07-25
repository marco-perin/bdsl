from abc import abstractmethod
from dataclasses import dataclass
from math import sqrt
from typing import Dict

from bounds import Bounds, IntOrFloat, Interval, IntervalPoint, f_apply, split_interval
from vardata import VarData


def numOrNone(s: str) -> IntOrFloat | None:

    if s == '':
        return None

    if '.' in s:
        return float(s)

    return int(s)


type VarContext = Dict[str, VarData]
# TODO: Use Bounds instead of Interval for conditions?.
type Conditions = Dict[str, Bounds]

builtinFunctions: list['BuiltinFunction'] = []


def populate_builtin_fcns(functions: dict[str, 'FunctionData | BuiltinFunction']):
    for f in builtinFunctions:
        functions[f.name] = f


@dataclass
class ProgramData:
    """
    Data class to hold program execution context information
    """

    filename: str
    # args: List[str] = None

    # def __post_init__(self):
    # if self.args is None:1

    def get_startline(self, lineno: int, default_digits: int = 3):
        return f'{self.filename}:{lineno:0{default_digits}}'


@dataclass
class InterpreterContext:
    """
    Data class to hold the current interpreter context
    """

    @dataclass
    class LineData:
        line_txt: str
        line_num: int

    program_data: ProgramData
    curr_line: LineData | None

    def set_linedata(self, line: str, lineno: int):
        self.curr_line = InterpreterContext.LineData(line, lineno)


class FunctionData:
    """
    Data class to store a function
    """

    name: str
    args: list[str]
    body: list[str] | None = None
    _builtin: bool = False

    def __init__(self, name: str, args: list[str]) -> None:
        self.name = name
        self.args = args

    def set_body(self, body: list[str]):
        """Sets the body of a function"""
        self.body = body

    @property
    def is_builtin(self):
        return self._builtin


class BuiltinFunction(FunctionData):
    """Builtin functions. evaluates directly"""

    _builtin = True

    @abstractmethod
    def eval(self, interval: Interval) -> None | Interval:
        raise NotImplementedError


class SqrtFunction(BuiltinFunction):

    def __init__(self) -> None:
        super().__init__(name='sqrt', args=['x'])

    def eval(self, interval: Interval) -> None | Interval:
        _, sol = split_interval(interval, IntervalPoint(0, True))

        if sol is None:
            return None

        def i_sqrt(x: IntervalPoint) -> IntervalPoint:
            assert x.value >= 0
            x.value = sqrt(x.value)
            return x

        return f_apply(i_sqrt, sol, False)


builtinFunctions.append(SqrtFunction())


def split_context(
    context: VarContext, conds: Conditions
) -> tuple[VarContext, VarContext]:

    filter_context: VarContext = {}
    complement_context: VarContext = {}

    for c_var_name, c_interval in conds.items():
        if c_var_name in context:
            curr_var = context[c_var_name].copy()
            curr_var_compl = context[c_var_name].copy()
            # both 0..10
            assert curr_var.bounds is not None, 'Variable bounds are None'

            curr_var.bounds.intersect_bounds(c_interval)
            # curr_var \in c_interval ( 5..10 )
            assert curr_var_compl.bounds is not None, 'Variable bounds are None'

            # print('c_interval:', c_interval)
            # print('invert_interval(c_interval):', invert_interval(c_interval))
            # print('curr_var_compl bounds', curr_var_compl.bounds)
            curr_var_compl.bounds.intersect_bounds(c_interval.copy().invert())
            # print('curr_var_compl bounds', curr_var_compl.bounds)

            filter_context[c_var_name] = curr_var
            complement_context[c_var_name] = curr_var_compl
    for c_var_name in context:
        if c_var_name not in filter_context:
            filter_context[c_var_name] = context[c_var_name]
            complement_context[c_var_name] = context[c_var_name]

    return filter_context, complement_context


def merge_contexts(
    curr_context: VarContext, comp_context: VarContext, split_cond: Conditions
) -> VarContext:
    res = curr_context.copy()

    for c_var_name, _ in split_cond.items():
        if c_var_name in curr_context:
            curr_var = res[c_var_name]

            # print('curr_context:', curr_context)
            assert curr_var.bounds is not None, f'Variable {c_var_name} bounds are None'

            comp_bounds = comp_context[c_var_name].bounds
            assert (
                comp_bounds is not None
            ), f'Variable {c_var_name} bounds are None in compl. bounds'

            # print('curr_var:', curr_var)
            # print('curr_bounds:', curr_var.bounds)
            # print('comp_bounds:', comp_bounds)

            curr_var.bounds.union_bounds(comp_bounds)

    return res


iota_counter = 0  # pylint: disable=invalid-name


def iota(reset: bool = False):
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
