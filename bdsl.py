#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
from warnings import warn
from typing import Callable

from bounds import Bounds, IntOrFloat, Interval, IntervalPoint, split_interval
from examples.errors import VariableNotDefinedError
import lexer
from colors import c
from bdsl_types import (
    BuiltinFunction,
    InterpreterContext,
    ProgramData,
    VarData,
    VarContext,
    FunctionData,
    Conditions,
    merge_contexts,
    numOrNone,
    populate_builtin_fcns,
    split_context,
)

from configuration import UNICODE_OUT, VERBOSE, WARN_IF_NONE


context_stack: list[VarContext] = []
other_context_stack: list[VarContext] = []
split_cond_stack: list[Conditions] = []
functions: dict[str, FunctionData | BuiltinFunction] = {}


def collapse_expr(opvars: list[Bounds], opops: list[str]):
    # print(f'operating on {opvars} with {opops}')
    ops = {
        '+': lambda x, y: x.value + y.value,
        '-': lambda x, y: x.value - y.value,
        '*': lambda x, y: x.value * y.value,
    }

    def __collapse_expr_interval(r1: Interval, r2: Interval, op: str):

        r10, r11 = r1[0], r1[1]
        r20, r21 = r2[0], r2[1]
        min_in = False
        max_in = False
        zero_exclude = False
        if op == '/':
            if r10 is None or r21 is None:
                r_min = None
                # min_in = False
            else:
                r_min = r10.value / r21.value
                min_in = r10.is_included and r21.is_included

            if r11 is None or r20 is None:
                r_max = None
                # max_in = False
            else:
                r_max = r11.value / r20.value
                max_in = r11.is_included and r20.is_included

            zero_exclude = r_min is None or (r_min < 0 and (r_max is None or r_max > 0))

        else:
            opf = ops[op]
            if r10 is None or r20 is None:
                r_min = None
                # min_in = False
            else:
                r_min = opf(r10, r20)
                min_in = r10.is_included and r20.is_included

            if r11 is None or r21 is None:
                r_max = None
                # max_in = False
            else:
                r_max = opf(r11, r21)
                max_in = r11.is_included and r21.is_included

            if r_min is not None and r_max is not None:
                if r_max < r_min:
                    r_min, r_max = r_max, r_min
                    min_in, max_in = max_in, min_in
                # r_min, r_max = min(r_min, r_max), max(r_min, r_max)

        if r_min is not None:
            r_min = IntervalPoint(r_min, min_in)
        if r_max is not None:
            r_max = IntervalPoint(r_max, max_in)

        return Interval(r_min, r_max), zero_exclude

    while len(opops) > 0:
        op = opops.pop(0)
        assert op in lexer.OPS, f'Operator {op} not implemented'

        b1 = opvars.pop(0)
        b2 = opvars.pop(0)

        bbs: Bounds | None = None
        # print(f'b1: {b1}, b2: {b2}')
        for rs1_i in b1.get_bounds():
            for rs2_i in b2.get_bounds():

                result_ij, zero_exclude = __collapse_expr_interval(rs1_i, rs2_i, op)

                if zero_exclude:
                    i1, i2 = split_interval(result_ij, IntervalPoint(0, False))
                    if i1 and i2:
                        result_ij = Bounds.from_list([i1, i2])
                    elif i1:
                        result_ij = Bounds.from_interval(i1)
                    else:
                        assert i2
                        result_ij = Bounds.from_interval(i2)
                else:
                    result_ij = Bounds.from_interval(result_ij)
                if bbs is None:
                    bbs = result_ij
                else:
                    bbs.union_bounds(result_ij)
                # print(f'bbs: {bbs}')

        assert bbs
        opvars.append(bbs)
    return opvars[0]


def calc_bounds(
    v_name: str, context: VarContext, program_data: ProgramData, opts: 'Opts'
) -> Bounds | None:
    """Calculate bounds for variable v_name from given context"""
    assert v_name in context, f'Variable {v_name} not defined'
    vardata = context[v_name]
    if vardata.bounds is not None:
        if vardata.bounds.get_bounds()[0] != (None, None):
            # print('TRUE BOUNDS: ', vardata.bounds.get_bounds())
            return Bounds(vardata.bounds.get_bounds())
    expr = vardata.expr

    if expr is None:
        if WARN_IF_NONE:
            warn(f'variable {v_name} got None bounds and expression')
        return None

    assert len(expr) > 0
    is_fn_call, rest = lexer.match_token(''.join(expr), lexer.FN_CALL_RE)
    if is_fn_call:
        assert rest is not None
        fn_name = rest[0]
        func = functions[fn_name]
        args = rest[1].split(',')
        assert len(args) == len(func.args), 'Wrong number of arguments'

        return evaluate_func(func, args, context, program_data, opts)

        # Now the context stack will hold the function processed code.

    if len(expr) == 2:
        l_v = numOrNone(expr[0])
        u_v = numOrNone(expr[1])
        return Bounds.from_interval(
            Interval(
                IntervalPoint(l_v) if l_v is not None else None,
                IntervalPoint(u_v) if u_v is not None else None,
            )
        )

    opvars = list[str | IntervalPoint]()
    opops = []

    for e in expr:
        # match_var = re.match(VAR_RE, e)
        match_var, match_groups = lexer.match_token(e, lexer.VAR_RE)
        if match_var:
            assert match_groups is not None
            opvars.append(match_groups[0])
            for g in match_groups[1:]:
                assert g == '', f'Variable {e} cannot have modifiers in expression'
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

        assert False, f'Token {e} in expression {vardata} not implemented'

    assert len(opvars) == len(opops) + 1, f'Expression {vardata} malformed'

    varlist: list[Bounds] = []
    for op in opvars:
        if isinstance(op, IntervalPoint):
            varlist.append(Bounds(((op, op),)))
        else:
            bds = calc_bounds(op, context, program_data, opts)
            if bds is None:
                return None
            varlist.append(bds)

    return collapse_expr(varlist, opops)


def print_vars(context: VarContext):
    print(c.YELLOW('vars:'))
    for v in context:
        print(f'\t{context[v]}')
        # print(vardict)


def print_fcns(opts: 'Opts'):
    print(c.YELLOW('funcs:'))
    for f in functions.values():

        body = ['!builtin'] if f.is_builtin else f.body
        assert body

        if opts.verbose == 0:
            print(f'\t{c.GREEN(f.name)}, args: {f.args}, body_count: {len(body)}')
        else:
            print(f'   {c.GREEN(f.name)} ({', '.join(f.args)})')
            # print('  body:')
            for line in body:
                print('\t' + line)


def gt(
    x: IntOrFloat | str, y: IntOrFloat | str, eq: bool, program_data, opts
) -> Bounds:
    curr_context = context_stack[-1]
    assert not (
        isinstance(x, str) and isinstance(y, str)
    ), f'Cannot compare vars rn {x} == {y}'

    if isinstance(x, str):
        assert not isinstance(y, str)

        bds = curr_context[x].bounds
        # print('bds:', curr_context[x].bounds)
        # print('expr:', curr_context[x].expr)
        if bds is None:
            bds = calc_bounds(x, curr_context, program_data, opts)
        # assert bds is not None, f'Variable {x} has no bounds'
        return bds.copy().intersect_interval((IntervalPoint(y, eq), None))

    assert isinstance(y, str) and not isinstance(x, str)

    bds = curr_context[y].bounds
    assert bds is not None, f'Variable {y} has no bounds'
    return bds.copy().intersect_interval((None, IntervalPoint(x, eq)))


def eq(x: IntOrFloat | str, y: IntOrFloat | str) -> Bounds:
    curr_context = context_stack[-1]
    assert not (
        isinstance(x, str) and isinstance(y, str)
    ), f'Operator "==" not implemented for two vars ({x} == {y}) atm'

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


def get_cond(vals: list[IntOrFloat | str], cond: str, program_data, opts) -> Bounds:
    assert len(vals) == 2, f'Need 2 values for condition, got {vals}'

    if cond == '>':
        return gt(vals[0], vals[1], False, program_data, opts)
    if cond == '<':
        return gt(vals[1], vals[0], False, program_data, opts)
    if cond == '==':
        return eq(vals[0], vals[1])
    if cond == '!=':
        assert False, 'Operator "!=" not implemented'
        # return neq(vals[0], vals[1])
    if cond == '>=':
        return gt(vals[0], vals[1], True, program_data, opts)
        # assert False, 'Operator >=" not implemented'
        # return gte(vals[0], vals[1])
    if cond == '<=':
        # assert False, 'Operator <=" not implemented'
        return gt(vals[1], vals[0], True, program_data, opts)
    assert False, f'Condition {cond} not implemented'


def pase_condition(
    tokens: list[str], context: VarContext, program_data: ProgramData, opts: 'Opts'
) -> Conditions:
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
            # if varname not in context:
            #     raise VariableNotDefinedError(
            #         varname,
            #     )
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

    conds[varname] = get_cond(vals, cond, program_data, opts)
    return conds


def print_var_msg(
    varname: str,
    line: str,
    line_num: int,
    curr_context: VarContext,
    interpreter_context: InterpreterContext,
    program_data: ProgramData,
    opts: 'Opts',
):

    if varname not in curr_context:
        raise VariableNotDefinedError(
            varname,
            line_num,
            interpreter_context=interpreter_context,
            colno=line.find(varname) + 1,
        )
    header = c.FAINT(f'{line_num:03}')
    bounds = calc_bounds(varname, curr_context, program_data, opts)

    if opts.verbose > 0:
        endl = c.FAINT(f' [{line.strip().removesuffix('\n')}]')
        if opts.verbose > 1:
            header = c.FAINT(f'{program_data.filename}:{line_num:03}')
    else:
        endl = ''
    if UNICODE_OUT:
        msg = f'{header} : {c.GREEN(varname)} ∈ {bounds}{endl}'
    else:
        msg = f'{header} : BOUNDS({c.GREEN(varname)}): {bounds}{endl}'

    print(msg)


def evaluate_func(
    func: FunctionData,
    args: list[str],
    context: VarContext,
    program_data: ProgramData,
    opts: 'Opts',
) -> Bounds | None:

    if func.is_builtin:
        assert isinstance(func, BuiltinFunction)
        interval = context_stack[-1][args[0]].bounds
        assert interval

        res_mixed = [
            i for i in (func.eval(i) for i in interval.get_bounds()) if i is not None
        ]
        i = 0
        if len(res_mixed) == 0:
            return None
        res = Bounds.from_interval(res_mixed[0])
        # if len(res_mixed) > 1:
        for i in range(1, len(res_mixed)):
            res.union_interval(res_mixed[i])

        return res

    assert func.body, f'Function {func.name} has no body!'

    func_context: VarContext = {}
    for f_arg, arg in zip(func.args, args):
        func_context[f_arg] = context[arg]
        # NOTE: check if func name needs to be change or
        #   if retaining the original name could be a feature
        # func_context[f_arg].name = f_arg

    context_stack.append(func_context)
    exec_code(func.body, program_data, opts)
    func_stack = context_stack.pop()

    res_var_name = func_stack['!var_result'].name
    bds = calc_bounds(res_var_name, func_stack, program_data, opts)

    return bds


def get_tokens(line: str):

    # does not work when ops are not separated with spaces
    #   (like x+y instead of x + y)
    # TODO: implement custom tokenizer
    return line.split()


def exec_code(code: list[str], program_data: ProgramData, opts: 'Opts'):

    if len(context_stack) == 0:
        context_stack.append({})

    interpreter_context = InterpreterContext(program_data, curr_line=None)

    curr_context = context_stack[-1]
    mods = None
    fn_name = None
    fn_body = []
    for line_num, line in enumerate(code, start=1):
        interpreter_context.set_linedata(line, line_num)
        tokens = get_tokens(line)
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
                comm_text = ' '.join([*rest, *tokens[ti + 1 :]])
                if VERBOSE:
                    print('comment:', comm_text)
                break

            if fn_name is not None:
                # Parsing function, either save to function body or end it
                if token_type == lexer.TOKEN_END:
                    assert fn_name in functions
                    assert not functions[fn_name].is_builtin
                    functions[fn_name].set_body(fn_body)  # type: ignore
                    fn_name = None
                    fn_body = []

                fn_body.append(' '.join(tokens))
                break

            if token_type == lexer.TOKEN_FN_DEF:
                assert fn_name is None, 'Nested functions not supported atm'
                rest = ''.join(tokens[ti + 1 :])
                fn_name, rest = rest.split('(', 1)
                args = rest.removesuffix(')').split(',')
                functions[fn_name] = FunctionData(fn_name, args)
                break
            if token_type == lexer.TOKEN_FN_CALL:
                rest_line = [token]
                assert isinstance(varname, str)
                break
            if token_type == lexer.TOKEN_FN_RET:
                # Assign return variable with magic name to get it
                #   from context
                curr_context['!var_result'] = curr_context[tokens[ti + 1]]
                return

            if token_type == lexer.TOKEN_VAR:
                varname = rest[0]
                mods = rest[1:]
                if '?' in mods:
                    print_var_msg(
                        varname,
                        line,
                        line_num,
                        curr_context,
                        interpreter_context,
                        program_data,
                        opts,
                    )

            elif token_type == lexer.TOKEN_RANGE:
                assert len(rest) == 4, f'Range {rest} malformed'
                b_l = numOrNone(rest[0])
                b_u = numOrNone(rest[1])
                b_l_in = rest[2] == '.'
                b_u_in = rest[3] == '.'

                if b_l is not None:
                    b_l = IntervalPoint(b_l, b_l_in)
                if b_u is not None:
                    b_u = IntervalPoint(b_u, b_u_in)
                rest_line = Interval(b_l, b_u)
            elif token_type == lexer.TOKEN_ASSIGN:
                rest_line = tokens[ti + 1 :]
                assert isinstance(varname, str)
                if VERBOSE:
                    print('assign:', rest_line)
                match_n, rest = lexer.match_token(tokens[ti + 1], lexer.NUM_RE)
                if match_n:
                    # print('NUM:', tokens[ti+1:])
                    val = numOrNone(tokens[ti + 1])
                    if val is not None:
                        val = IntervalPoint(val)
                    rest_line = Interval(val, val)
                    # print(rest_line)
                    # curr_context[varname].bounds = Bounds(((val, val),))
                    # curr_context[varname].expr = None
                break

            elif token_type == lexer.TOKEN_QUEST:
                mod = rest[0]
                if mod is None:
                    mod = 'a'

                if mod in ('v', 'a'):
                    print_vars(curr_context)
                if mod in ('f', 'a'):
                    print_fcns(opts)

                break
            # elif token_type == TOKEN_COND:
            # if VERBOSE:
            #     print('COND: ', tokens[ti+1:])
            # break
            elif token_type == lexer.TOKEN_IF:
                if VERBOSE:
                    print('IF: ', tokens[ti + 1 :])

                cond: Conditions = pase_condition(
                    tokens[ti + 1 :], curr_context, program_data, opts
                )
                # print('cond:', cond)
                # context_stack.append(curr_context.copy())
                for v_name in cond:
                    assert (
                        v_name in curr_context
                    ), f'Variable {
                        v_name} not defined'
                    curr_context[v_name].bounds = calc_bounds(
                        v_name, curr_context, program_data, opts
                    )
                    curr_context[v_name].expr = None
                ctx, compl = split_context(curr_context, cond)
                other_context_stack.append(compl)
                context_stack.append(ctx)
                curr_context = ctx
                split_cond_stack.append(cond)
                break
            elif token_type == lexer.TOKEN_ELSE:
                if VERBOSE:
                    print('ELSE: ', tokens[ti + 1 :])
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
                            v_name, curr_context, program_data, opts
                        )
                        curr_context[v_name].expr = None
                for v_name in comp_context:
                    if comp_context[v_name].bounds is None:
                        comp_context[v_name].bounds = calc_bounds(
                            v_name, comp_context, program_data, opts
                        )
                        comp_context[v_name].expr = None
                curr_context = merge_contexts(curr_context, comp_context, split_cond)
                context_stack[-1] = curr_context
                break
            elif token_type == lexer.TOKEN_SIZE:
                size = rest[0]
            else:
                assert (
                    False
                ), f'Token "{
                    token}" ({lexer.token_names[token_type]}) not implemented'

        if varname is None:
            continue

        assert mods is not None, 'WTF??'

        if '?' in mods:
            continue

        if '!' in mods:
            assert (
                varname in curr_context
            ), f'Variable {
                varname} not defined, cannot overwerite'
        else:
            if '.' in mods:
                assert (
                    varname in curr_context
                ), f'Variable {varname} not defined, canno finalyze value'
            else:
                assert (
                    varname not in curr_context
                ), f'Variable {varname} already defined. Cannot redeclare'

        if '.' in mods:
            bounds = calc_bounds(varname, curr_context, program_data, opts)
            rest_line = bounds

        curr_context[varname] = VarData.auto(varname, rest_line, size)


def print_usage():
    print('Usage: python test.py [opts] <arg>')
    print()
    print('  [opts] can be: ')
    print()
    print('    -v | --verbose to enable verbose mode.')
    print('    -h | --help    to print this help message.')
    print()
    print('  <arg> can be: ')
    print()
    print('    filename       to be executed.')
    print('    file_number    in the examples to be executed.')
    print()


class Opts:
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
    populate_builtin_fcns(functions)
    exec_code(code, program_data, opts)

    sys.exit(0)


if __name__ == '__main__':
    main()
