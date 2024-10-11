#!/usr/bin/python

from dataclasses import dataclass
import re
from typing import Dict, List, Tuple


iota_counter = 0  # pylint: disable=invalid-name


def iota(reset=False):
    global iota_counter  # pylint: disable=global-statement
    if reset:
        iota_counter = 0
    result = iota_counter
    iota_counter += 1
    return result


TOKEN_COMMENT = iota(True)
TOKEN_ASSIGN = iota()
TOKEN_QUEST = iota()
TOKEN_VAR = iota()
TOKEN_OP = iota()
TOKEN_RANGE = iota()
TOKEN_SIZE = iota()
# Other ops ...
TOKEN_MAX = iota()

token_names = [
    'COMMENT',
    'ASSIGN',
    'QUEST',
    'VAR',
    'OP',
    'RANGE',
    'SIZE'
]

code = [
    "x          0..10",
    "y          0..15",
    "arr  (10)  2..",
    "arr!        ..10",
    "z = x + y",
    ";; Print vars",
    "x?",
    "y?",
    "arr?",
    "z?",
    "?",
    ";; Finalyze z variable",
    "z.",
    "?",
    # Future
    # "z > 10:",
    # "| ; do something",
    # "else:",
    # "| ; do something else",
    # "end",
]

MODS = '!?.'
MODS_RE = MODS.replace('.', r'\.')

OPS = '+-*/'
OPS_RE = OPS.replace('-', r'\-').replace('/', r'\/')

# CONDS = '><'
# CONDS_RE =
# COND_RE = r'^([])$'

SIZE_RE = r'^\((?P<size>[0-9,]*)\)$'

VAR_RE = rf'^([_A-z0-9]+)([{MODS_RE}]?)$'
OP_RE = rf'^([{OPS_RE}])$'
RANGE_RE = r'^(?P<min>[0-9]*)\.\.(?P<max>[0-9]*)$'

COMMENT_RE = r'^[;]+(?P<comment>[.]*)$'


IntOrFloat = int | float
BoundsType = Tuple[IntOrFloat | None, IntOrFloat | None]


@dataclass
class VarData:
    """Holds data for a variable"""
    name: str
    bounds: BoundsType = (None, None)
    size: int = 1
    expr: List[str] | None = None

    def __init__(self,
                 name: str,
                 arg2: BoundsType | List[str],
                 size: str | None):
        self.name = name
        if size is not None:
            self.size = int(size)

        if isinstance(arg2, list):
            assert all(isinstance(arg2i, str) for arg2i in arg2), \
                f'Expression {arg2} must be a list of strings'
            self.expr = arg2
        else:
            self.bounds = arg2

    def __str__(self):

        if self.expr is None:
            b_min = self.bounds[0] if self.bounds[0] is not None else ' '
            b_max = self.bounds[1] if self.bounds[1] is not None else ' '
            return f'{self.name} ({self.size}) [{b_min}..{b_max}]'

        return f'{self.name} ({self.size}) "{' '.join(self.expr)}"'


vardict: Dict[str, VarData] = {}


def get_token_type(tok: str):

    comm_match = re.match(COMMENT_RE, tok)
    if comm_match:
        comm_text = comm_match.groupdict()['comment']
        return (TOKEN_COMMENT, comm_text)

    if tok == '=':
        return (TOKEN_ASSIGN, tok)

    if tok == '?':
        return (TOKEN_QUEST, tok)

    var_match = re.match(VAR_RE, tok)
    if var_match:
        # print(var_match.groups())
        return (TOKEN_VAR, var_match.groups()[0], var_match.groups()[1])

    op_match = re.match(OP_RE, tok)

    if op_match:
        return (TOKEN_OP, )

    range_match = re.match(RANGE_RE, tok)

    if range_match:
        groups = range_match.groupdict()
        r_min = groups['min']
        r_max = groups['max']
        return (TOKEN_RANGE, r_min, r_max)

    size_match = re.match(SIZE_RE, tok)
    if size_match:
        groups = size_match.groupdict()
        size = groups['size']
        # print(groups)
        return (TOKEN_SIZE, size)

    assert False, f'Token "{tok}" not matched'


def numOrNone(s: str) -> IntOrFloat | None:

    if s == '':
        return None

    if '.' in s:
        return float(s)

    return int(s)


def collapse_expr(
    opvars: list[Tuple[IntOrFloat | None, IntOrFloat | None]],
    opops: list[str]
) -> Tuple[IntOrFloat | None, IntOrFloat | None]:
    ops = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: x * y,
    }
    while (len(opops) > 0):
        op = opops.pop(0)
        assert op in OPS, f'Operator {op} not implemented'

        r1 = opvars.pop(0)
        r2 = opvars.pop(0)

        if op == '/':
            if r1[0] is None or r2[1] is None:
                r_min = None
            else:
                r_min = r1[0] / r2[1]
            if r1[1] is None or r2[0] is None:
                r_max = None
            else:
                r_max = r1[1] / r2[0]

            return (r_min, r_max)

        op = ops[op]
        if r1[0] is None or r2[0] is None:
            r_min = None
        else:
            r_min = op(r1[0], r2[0])
        if r1[1] is None or r2[1] is None:
            r_max = None
        else:
            r_max = op(r1[1], r2[1])
        opvars.append((r_min, r_max))

    return opvars[0]


def calc_bounds(v: str) -> Tuple[IntOrFloat | None, IntOrFloat | None]:
    assert v in vardict, f'Variable {v} not defined'
    vardata = vardict[v]
    if vardata.bounds != (None, None):
        return vardata.bounds
    expr = vardata.expr
    assert expr is not None, f'Variable {v} has no expression'
    if len(expr) == 2:
        return (numOrNone(expr[0]), numOrNone(expr[1]))

    opvars = []
    opops = []

    for e in expr:
        match_var = re.match(VAR_RE, e)
        if match_var:
            opvars.append(match_var.groups()[0])
            for g in match_var.groups()[1:]:
                assert g == '', \
                    f'Variable {e} cannot have modifiers in expression'
            continue

        match_op = re.match(OP_RE, e)
        if match_op:
            opops.append(e)  # match_op.groups()[0]
            continue

        assert False, \
            f'Token {e} in expression {vardata} not implemented'

    assert (len(opvars) == len(opops) + 1), \
        f'Expression {vardata} malformed'
    # print('opvars:', opvars)
    # print('opvars:', list(map(calc_bounds, opvars)))
    # print('opops:', opops)
    result = collapse_expr(list(map(calc_bounds, opvars)), opops)
    return result


def print_vars(vardict: Dict[str, VarData]):
    print('vars:')
    for v in vardict:
        print(f"\t{vardict[v]}")
        # print(vardict)


VERBOSE = False
VERBOSE = True

if __name__ == "__main__":
    for line in code:
        tokens = line.split()
        # print('tokens:',tokens)
        varname = None
        bounds = None
        size = None
        rest_line = None
        for ti, token in enumerate(tokens):
            (token_type, *rest) = get_token_type(token)

            if VERBOSE:
                print('token:', (token, token_names[token_type], rest))

            if token_type == TOKEN_COMMENT:
                comm_text = ' '.join([*rest, *tokens[ti+1:]])
                if VERBOSE:
                    print('comment:', comm_text)
                break

            if token_type == TOKEN_VAR:
                varname = rest[0]
                mods = rest[1:]
                if '?' in mods:
                    assert varname in vardict, f'Variable {
                        varname} not defined'
                    bounds = calc_bounds(varname)
                    print(f'BOUNDS({varname}): {bounds}')

            elif token_type == TOKEN_RANGE:
                assert len(rest) == 2, f'Range {rest} malformed'
                rest_line = (numOrNone(rest[0]), numOrNone(rest[1]))
            elif token_type == TOKEN_ASSIGN:
                rest_line = tokens[ti+1:]
                # if VERBOSE:
                #     print('assign:', r)
                break
            elif token_type == TOKEN_QUEST:
                print_vars(vardict)
                break
            elif token_type == TOKEN_SIZE:
                size = rest[0]
            else:
                assert False, f'Token "{
                    token}" ({token_names[token_type]}) not implemented'

        if varname is None:
            continue

        if '?' in mods:
            continue

        if '!' in mods:
            assert varname in vardict, f'Variable {
                varname} not defined, cannot overwerite'
        else:
            if '.' in mods:
                assert varname in vardict, \
                    f'Variable {varname} not defined, canno finalyze value'
            else:
                assert varname not in vardict, \
                    f'Variable {varname} already defined. Cannot redeclare'

        if '.' in mods:
            bounds = calc_bounds(varname)
            print(f'BOUNDS({varname}): {bounds}')
            # rest_line = list(map(str, bounds))
            rest_line = bounds

        if rest_line is None:
            assert False, f'r for variable {varname} not initialized'

        # if bounds is not None:
        #     bounds = (None, None)
        vardict[varname] = VarData(varname, rest_line, size)
        # vardict[v] = VarData(v, r,

    if VERBOSE:
        print_vars(vardict)

    exit(0)
