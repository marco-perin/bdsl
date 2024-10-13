#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
from bdsl_types import (
    VarData,
    Context,
    # Conditions,
    numOrNone,
    iota
)

VERBOSE = False
VERBOSE = True


TOKEN_COMMENT = iota(True)
TOKEN_ASSIGN = iota()
TOKEN_QUEST = iota()
TOKEN_VAR = iota()
TOKEN_OP = iota()
TOKEN_COND = iota()
TOKEN_RANGE = iota()
TOKEN_SIZE = iota()
TOKEN_IF = iota()
TOKEN_ELSE = iota()
TOKEN_END = iota()
# Other ops ...
TOKEN_MAX = iota()

token_names = [
    'COMMENT',
    'ASSIGN',
    'QUEST',
    'VAR',
    'OP',
    'COND',
    'RANGE',
    'SIZE',
    'IF',
    'ELSE',
    'END',
]

assert len(token_names) == TOKEN_MAX, \
    f'Token names {token_names} do not match token count {TOKEN_MAX}'


MODS = '!?.'
MODS_RE = MODS.replace('.', r'\.')

OPS = '+-*/'
OPS_RE = OPS.replace('-', r'\-').replace('/', r'\/')


CONDS_RE = '>|<|==|!=|>=|<='


COMMENT_RE = r'^[;]+(?P<comment>[.]*)$'

VAR_RE = rf'^([_A-z0-9]+)([{MODS_RE}]?)$'
OP_RE = rf'^([{OPS_RE}])$'
RANGE_RE = r'^(?P<min>-?[0-9]*)\.\.(?P<max>-?[0-9]*)$'
COND_RE = rf'[ ]?({CONDS_RE})[ ]?$'
CMD_RE = r'^(\?\?|>>|--)[ ]?$'
SIZE_RE = r'^\((?P<size>[0-9,]*)\)$'


vardict: Context = {}
context_stack: list[Context] = []


def get_token_type(tok: str):
    if VERBOSE:
        print(f'get_token_type: "{tok}"')

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
        return (TOKEN_SIZE, size)

    cond_match = re.match(COND_RE, tok)
    if cond_match:
        return (TOKEN_COND, tok)

    cmd_match = re.match(CMD_RE, tok)
    if cmd_match:
        tok_match = cmd_match.groups()[0]
        if tok_match == '??':
            return (TOKEN_IF, tok)
        if tok_match == '>>':
            return (TOKEN_ELSE, tok)
        if tok_match == '--':
            return (TOKEN_END, tok)

    assert False, f'Token "{tok}" not matched'


def collapse_expr(
    opvars: list,
    opops: list[str]
):
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


def calc_bounds(v: str):
    assert v in vardict, f'Variable {v} not defined'
    vardata = vardict[v]
    if vardata.bounds.get_bounds()[0] != (None, None):
        # TODO: bounds needs to be a set.
        return vardata.bounds.get_bounds()[0]
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


def print_vars(context: Context):
    print('vars:')
    for v in context:
        print(f"\t{context[v]}")
        # print(vardict)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python test.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    code = []
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.readlines()
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
            # elif token_type == TOKEN_COND:
                # if VERBOSE:
                #     print('COND: ', tokens[ti+1:])
                # break
            elif token_type == TOKEN_IF:
                if VERBOSE:
                    print('IF: ', tokens[ti+1:])
                # Filter context
                break
            elif token_type == TOKEN_ELSE:
                if VERBOSE:
                    print('ELSE: ', tokens[ti+1:])
                # Select complementary context
                break
            elif token_type == TOKEN_END:
                if VERBOSE:
                    print('END.')
                # Merge contexts
                # vardict = merge_contexts(vardict, context_stack.pop())
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
