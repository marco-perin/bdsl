#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
from typing import Callable
from bounds import Bounds, IntOrFloat, Interval, IntervalPoint
from examples.errors import VariableNotDefinedError
import lexer
from bdsl_types import (
    InterpreterContext,
    ProgramData,
    VarData,
    VarContext,
    Conditions,
    merge_contexts,
    numOrNone,
    split_context,
    Colors as c
)

VERBOSE = False
# VERBOSE = True


context_stack: list[VarContext] = []
other_context_stack: list[VarContext] = []
split_cond_stack: list[Conditions] = []


def collapse_expr(
    opvars: list[Interval],
    opops: list[str]
):
    ops = {
        '+': lambda x, y: x.value + y.value,
        '-': lambda x, y: x.value - y.value,
        '*': lambda x, y: x.value * y.value,
    }
    while len(opops) > 0:
        op = opops.pop(0)
        assert op in lexer.OPS, f'Operator {op} not implemented'

        r1 = opvars.pop(0)
        r2 = opvars.pop(0)

        if op == '/':
            if r1[0] is None or r2[1] is None:
                r_min = None
            else:
                r_min = r1[0].value / r2[1].value
            if r1[1] is None or r2[0] is None:
                r_max = None
            else:
                r_max = r1[1].value / r2[0].value
        else:
            op = ops[op]
            if r1[0] is None or r2[0] is None:
                r_min = None
            else:
                r_min = op(r1[0], r2[0])
            if r1[1] is None or r2[1] is None:
                r_max = None
            else:
                r_max = op(r1[1], r2[1])
            if r_min is not None and r_max is not None:
                if r_max < r_min:
                    r_min, r_max = r_max, r_min
                # r_min, r_max = min(r_min, r_max), max(r_min, r_max)

        if r_min is not None:
            r_min = IntervalPoint(r_min)
        if r_max is not None:
            r_max = IntervalPoint(r_max)
        opvars.append((r_min, r_max))
    return opvars[0]


def calc_bounds(v_name: str, context: VarContext) -> Bounds:
    """Calculate bounds for variable v_name from given context"""
    assert v_name in context, f'Variable {v_name} not defined'
    vardata = context[v_name]
    if vardata.bounds is not None:
        if vardata.bounds.get_bounds()[0] != (None, None):
            # print('TRUE BOUNDS: ', vardata.bounds.get_bounds())
            return Bounds(vardata.bounds.get_bounds())
    expr = vardata.expr
    assert expr is not None, f'Variable {v_name} has no expression'
    if len(expr) == 2:
        l_v = numOrNone(expr[0])
        u_v = numOrNone(expr[1])
        return Bounds.from_interval((
            IntervalPoint(l_v) if l_v is not None else None,
            IntervalPoint(u_v) if u_v is not None else None
        ))

    opvars = list[str | IntervalPoint]()
    opops = []

    for e in expr:
        # match_var = re.match(VAR_RE, e)
        match_var, match_groups = lexer.match_token(e, lexer.VAR_RE)
        if match_var:
            assert match_groups is not None
            opvars.append(match_groups[0])
            for g in match_groups[1:]:
                assert g == '', \
                    f'Variable {e} cannot have modifiers in expression'
            continue

        # match_op = re.match(OP_RE, e)
        match_op, _ = lexer.match_token(e, lexer.OP_RE)
        if match_op:
            opops.append(e)  # match_op.groups()[0]
            continue
        match_num, match_groups = lexer.match_token(e, lexer.NUM_RE)
        if match_num:
            assert match_groups is not None
            num_val = numOrNone(match_groups[0])
            assert num_val is not None, f'Value {match_groups[0]} not a number'
            opvars.append(IntervalPoint(num_val))
            # opvars.append(match_groups[0])
            # for g in match_groups[1:]:
            #     assert g == '', \
            #         f'Variable {e} cannot have modifiers in expression'
            continue

        assert False, \
            f'Token {e} in expression {vardata} not implemented'

    assert len(opvars) == len(opops) + 1, \
        f'Expression {vardata} malformed'

    varlist = []
    for op in opvars:
        if isinstance(op, IntervalPoint):
            varlist.append((op, op))
        else:
            varlist.extend(calc_bounds(op, context).get_bounds())

    result = collapse_expr(varlist, opops)
    return Bounds.from_interval(result)


def print_vars(context: VarContext):
    print('vars:')
    for v in context:
        print(f"\t{context[v]}")
        # print(vardict)


def gt(x: IntOrFloat | str, y: IntOrFloat | str, eq: bool) -> Bounds:
    curr_context = context_stack[-1]
    assert not (isinstance(x, str) and isinstance(y, str)), \
        f'Cannot compare vars rn {x} == {y}'

    if isinstance(x, str):
        assert not isinstance(y, str)

        bds = curr_context[x].bounds
        # print('bds:', curr_context[x].bounds)
        # print('expr:', curr_context[x].expr)
        if bds is None:
            bds = calc_bounds(x, curr_context)
        # assert bds is not None, f'Variable {x} has no bounds'
        return bds.copy().intersect_interval((IntervalPoint(y, eq), None))

    assert isinstance(y, str) and not isinstance(x, str)

    bds = curr_context[y].bounds
    assert bds is not None, f'Variable {y} has no bounds'
    return bds.copy().intersect_interval((None, IntervalPoint(x, eq)))


def eq(x: IntOrFloat | str, y: IntOrFloat | str) -> Bounds:
    curr_context = context_stack[-1]
    assert not (isinstance(x, str) and isinstance(y, str)), \
        f'Operator "==" not implemented for two vars ({x} == {y}) atm'

    if isinstance(x, str):
        var = curr_context[x]
        assert not isinstance(y, str)
        val = IntervalPoint(y, True)
    else:
        assert isinstance(y, str)
        assert not isinstance(x, str)
        var = curr_context[y]
        val = IntervalPoint(x, True)

    bds = var.bounds
    assert bds is not None, f'Variable {var.name} has no bounds'
    return bds.copy().intersect_interval((val, val))


def neq(x: IntOrFloat | str, y: IntOrFloat | str) -> Bounds:

    assert False, 'Operator "!=" not implemented'
    # assert not (isinstance(x, str) and isinstance(y, str)), \
    #     f'Operator "==" not implemented for two vars ({x} == {y}) atm'

    # if isinstance(x, str):
    #     var = vardict[x]
    #     assert not isinstance(y, str)
    #     val = y
    # else:
    #     assert isinstance(y, str)
    #     assert not isinstance(x, str)
    #     var = vardict[y]
    #     val = x

    # bds = var.bounds
    # assert bds is not None, f'Variable {var.name} has no bounds'
    # return bds.copy().intersect_interval((val+1, None)).union_interval().get_bounds()


def get_cond(vals: list[IntOrFloat | str], cond: str) -> Bounds:
    assert len(vals) == 2, f'Need 2 values for condition, got {vals}'

    if cond == '>':
        return gt(vals[0], vals[1], False)
    if cond == '<':
        return gt(vals[1], vals[0], False)
    if cond == '==':
        return eq(vals[0], vals[1])
    if cond == '!=':
        assert False, 'Operator "!=" not implemented'
        # return neq(vals[0], vals[1])
    if cond == '>=':
        return gt(vals[0], vals[1], True)
        # assert False, 'Operator >=" not implemented'
        # return gte(vals[0], vals[1])
    if cond == '<=':
        # assert False, 'Operator <=" not implemented'
        return gt(vals[1], vals[0], True)
    assert False, f'Condition {cond} not implemented'


def pase_condition(tokens: list[str], context: VarContext) -> Conditions:
    assert len(tokens) > 0, 'No tokens to parse'
    assert len(tokens) % 3 == 0, f'Condition {tokens} malformed'

    assert len(tokens) == 3, 'Only one condition with 3 tokens supported now.'

    conds = {}
    varname = None
    vals: list[IntOrFloat | str] = []
    cond = None
    if VERBOSE:
        print('pase_condition: ', tokens)
    for token in tokens:
        (t_type, *rest) = lexer.get_token_type(token)
        if VERBOSE:
            print('t_type:', lexer.token_names[t_type], rest)
        if t_type == lexer.TOKEN_VAR:
            varname = rest[0]
            assert varname in context, f'Variable {varname} not defined'
            vals.append(varname)
        elif t_type == lexer.TOKEN_COND:
            cond = rest[0]
            # print('cond:', cond)

        elif t_type == lexer.TOKEN_NUM:
            val_n = numOrNone(rest[0])
            assert val_n is not None, f'Value {rest[0]} not a number'
            vals.append(val_n)

    assert varname is not None, 'Variable not defined'
    assert cond is not None, 'Condition not defined'

    assert len(vals) == 2, 'need 2 values for condition'

    conds[varname] = get_cond(vals, cond)
    return conds


def exec_code(code: list[str], program_data: ProgramData, opts: 'Opts'):

    if len(context_stack) == 0:
        context_stack.append({})

    interpreter_context = InterpreterContext(
        program_data,
        curr_line=None
    )

    curr_context = context_stack[-1]
    mods = None
    for line_num, line in enumerate(code, start=1):
        interpreter_context.set_linedata(line, line_num)
        tokens = line.split()
        # print('tokens:',tokens)
        varname = None
        bounds = None
        size = None
        rest_line = None
        for ti, token in enumerate(tokens):
            (token_type, *rest) = lexer.get_token_type(token)

            if VERBOSE:
                print('token:', (token, lexer.token_names[token_type], rest))

            if token_type == lexer.TOKEN_COMMENT:
                comm_text = ' '.join([*rest, *tokens[ti+1:]])
                if VERBOSE:
                    print('comment:', comm_text)
                break

            if token_type == lexer.TOKEN_VAR:
                varname = rest[0]
                mods = rest[1:]
                if '?' in mods:
                    if varname not in curr_context:
                        raise VariableNotDefinedError(
                            varname,
                            line_num,
                            interpreter_context=interpreter_context,
                            colno=line.find(varname)+1
                        )

                    bounds = calc_bounds(varname, curr_context)

                    header = c.FAINT.get_text(f'{line_num:03}')
                    if opts.verbose > 0:
                        endl = c.FAINT.get_text(
                            f' [{line.strip().removesuffix('\n')}]')
                        if opts.verbose > 1:
                            header = f'{program_data.filename}:{line_num:03}'
                    else:
                        endl = ''
                    if UNICODE_OUT:
                        msg = f'{header} : {c.GREEN.get_text(varname)} ∈ {bounds}{endl}'
                    else:
                        msg = f'{header} : BOUNDS({c.GREEN.get_text(varname)}): {bounds}{endl}'

                    print(msg)

            elif token_type == lexer.TOKEN_RANGE:
                assert len(rest) == 2, f'Range {rest} malformed'
                b_l = numOrNone(rest[0])
                b_u = numOrNone(rest[1])
                if b_l is not None:
                    b_l = IntervalPoint(b_l)
                if b_u is not None:
                    b_u = IntervalPoint(b_u)
                rest_line = (b_l, b_u)
            elif token_type == lexer.TOKEN_ASSIGN:
                rest_line = tokens[ti+1:]
                assert isinstance(varname, str)
                if VERBOSE:
                    print('assign:', tokens[ti+1:])
                match_n, rest = lexer.match_token(tokens[ti+1], lexer.NUM_RE)
                if match_n:
                    # print('NUM:', tokens[ti+1:])
                    val = numOrNone(tokens[ti+1])
                    if val is not None:
                        val = IntervalPoint(val)
                    rest_line = (val, val)
                    # print(rest_line)
                    # curr_context[varname].bounds = Bounds(((val, val),))
                    # curr_context[varname].expr = None
                break

            elif token_type == lexer.TOKEN_QUEST:
                print_vars(curr_context)
                break
            # elif token_type == TOKEN_COND:
                # if VERBOSE:
                #     print('COND: ', tokens[ti+1:])
                # break
            elif token_type == lexer.TOKEN_IF:
                if VERBOSE:
                    print('IF: ', tokens[ti+1:])

                cond: Conditions = pase_condition(tokens[ti+1:], curr_context)
                # print('cond:', cond)
                # context_stack.append(curr_context.copy())
                for v_name in cond:
                    assert v_name in curr_context, f'Variable {
                        v_name} not defined'
                    curr_context[v_name].bounds = calc_bounds(
                        v_name, curr_context)
                    curr_context[v_name].expr = None
                ctx, compl = split_context(curr_context, cond)
                other_context_stack.append(compl)
                context_stack.append(ctx)
                curr_context = ctx
                split_cond_stack.append(cond)
                break
            elif token_type == lexer.TOKEN_ELSE:
                if VERBOSE:
                    print('ELSE: ', tokens[ti+1:])
                # Select complementary context

                curr_context = other_context_stack[-1]
                # for v_name in cond:
                #     assert v_name in curr_context, f'Variable {
                #         v_name} not defined'
                #     curr_context[v_name].bounds = calc_bounds(
                #         v_name, curr_context)
                #     curr_context[v_name].expr = None
                # break
            elif token_type == lexer.TOKEN_END:
                if VERBOSE:
                    print('END.')
                # Merge contexts
                curr_context = context_stack.pop()
                comp_context = other_context_stack.pop()
                split_cond = split_cond_stack.pop()

                for v_name in curr_context:
                    if curr_context[v_name].bounds is None:
                        curr_context[v_name].bounds = calc_bounds(
                            v_name, curr_context)
                        curr_context[v_name].expr = None
                for v_name in comp_context:
                    if comp_context[v_name].bounds is None:
                        comp_context[v_name].bounds = calc_bounds(
                            v_name, comp_context)
                        comp_context[v_name].expr = None
                curr_context = merge_contexts(
                    curr_context, comp_context, split_cond
                )
                break
            elif token_type == lexer.TOKEN_SIZE:
                size = rest[0]
            else:
                assert False, f'Token "{
                    token}" ({lexer.token_names[token_type]}) not implemented'

        if varname is None:
            continue

        if '?' in mods:
            continue

        if '!' in mods:
            assert varname in curr_context, f'Variable {
                varname} not defined, cannot overwerite'
        else:
            if '.' in mods:
                assert varname in curr_context, \
                    f'Variable {varname} not defined, canno finalyze value'
            else:
                assert varname not in curr_context, \
                    f'Variable {varname} already defined. Cannot redeclare'

        if '.' in mods:
            bounds = calc_bounds(varname, curr_context)
            rest_line = bounds

        if rest_line is None:
            assert False, f'r for variable {varname} not initialized'

        curr_context[varname] = VarData.auto(varname, rest_line, size)


def print_usage():
    print("Usage: python test.py [opts] <arg>")
    print()
    print("  [opts] can be: ")
    print()
    print("    -v | --verbose to enable verbose mode.")
    print("    -h | --help    to print this help message.")
    print()
    print("  <arg> can be: ")
    print()
    print("    filename       to be executed.")
    print("    file_number    in the examples to be executed.")
    print()


class Opts():
    verbose: int = 0

    def parse_option(self, opt: str):
        if opt in ['-v', '--verbose']:
            self.verbose = 1
            return True
        if opt in ['-vv', '--vverbose']:
            self.verbose = 2
            return True

        return False

    def is_help(self, opt: str):
        return opt in ['-h', '--help']

    def parse_all_args(self, args, help_fcn: Callable[[], None]):

        while args and args[-1].startswith('-'):
            opt = args.pop()

            if self.is_help(opt):
                help_fcn()
                sys.exit(0)

            if not self.parse_option(opt):
                # TODO: manage this with python errors
                print(c.RED.get_text(f'ERR: unknown option: {opt}'))
                help_fcn()
                sys.exit(1)


def main():
    import glob
    import re

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    args = list(reversed(sys.argv[1:]))
    # print('args: ', args)

    opts = Opts()

    opts.parse_all_args(args, print_usage)

    if len(args) < 1:
        print(c.RED.get_text('Not enough parameters'))
        print_usage()
        sys.exit(1)

    filename_arg = args.pop()
    filename = filename_arg
    code = []
    try:
        filenum = int(filename_arg)
        print('filenum:', filenum)
        files = glob.glob('examples/*')

        for f in files:
            if re.search(rf'0*{filenum}_.*\.bdsl', f):
                filename = f
                break
        assert filename_arg != filename, f'File {filenum} not found'
        print('executing:', filename)
    except ValueError:
        pass

    with open(filename, 'r', encoding='utf-8') as f:
        code = f.readlines()

    program_data = ProgramData(filename)

    exec_code(code, program_data, opts)

    sys.exit(0)


if __name__ == "__main__":
    main()
