
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from bounds import Bounds, IntOrFloat
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


class Colors(Enum):
    HEADER = '\033[95m'
    FAIL = '\033[91m'
    RED = '\033[31m'
    BRIGHTRED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WARNING = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[35m'
    BRIGHTMAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BRIGHTCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    FAINT = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK_SLOW = '\033[5m'
    BLINK_FAST = '\033[6m'
    REVERSE = '\033[7m'

    def get_text(self, text: str | int | float):
        return f'{self.value}{text}{Colors.ENDC.value}'


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
        curr_context: VarContext,
        comp_context: VarContext,
        split_cond: Conditions
) -> VarContext:
    res = curr_context.copy()

    for c_var_name, _ in split_cond.items():
        if c_var_name in curr_context:
            curr_var = res[c_var_name]

            # print('curr_context:', curr_context)
            assert curr_var.bounds is not None, \
                f'Variable {c_var_name} bounds are None'

            comp_bounds = comp_context[c_var_name].bounds
            assert comp_bounds is not None, \
                f'Variable {c_var_name} bounds are None in compl. bounds'

            # print('curr_var:', curr_var)
            # print('curr_bounds:', curr_var.bounds)
            # print('comp_bounds:', comp_bounds)

            for i in comp_bounds.get_bounds():
                # print('comp_bounds i:', i)
                curr_var.bounds.union_interval(i)

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
