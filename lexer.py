import re

from bdsl_types import iota


TOKEN_COMMENT = iota(True)
TOKEN_ASSIGN = iota()
TOKEN_QUEST = iota()
TOKEN_VAR = iota()
TOKEN_OP = iota()
TOKEN_COND = iota()
TOKEN_RANGE = iota()
TOKEN_SIZE = iota()
TOKEN_NUM = iota()
TOKEN_IF = iota()
TOKEN_ELSE = iota()
TOKEN_END = iota()
TOKEN_FN_DEF = iota()
TOKEN_FN_RET = iota()
TOKEN_FN_CALL = iota()
# Other ops ...

# Leave as last, used for assertions
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
    'NUM',
    'IF',
    'ELSE',
    'END',
    'FN_DEF',
    'FN_RET',
    'FN_CALL',
]

assert (
    len(token_names) == TOKEN_MAX
), f'Token names {token_names} do not match token count {TOKEN_MAX}'


MODS = '!?.'
MODS_RE = MODS.replace('.', r'\.')

OPS = '+-*/'
OPS_RE = OPS.replace('-', r'\-').replace('/', r'\/')


CONDS_RE = '>|<|==|!=|>=|<='

COMMENT_RE = r'^;; ?(?P<comment>.*)$'

VAR_RE = rf'^([_A-z]{{1}}[_A-z0-9]*)([{MODS_RE}]?)$'
OP_RE = rf'^([{OPS_RE}])$'
RANGE_RE = r'^(?P<min_in>\.?)(?P<min>-?[0-9]*)\.\.(?P<max>-?[0-9]*)(?P<max_in>\.?)$'
COND_RE = rf'[ ]?({CONDS_RE})[ ]?$'
CMD_RE = r'^(\?\?|>>|--)[ ]?$'
NUM_RE = r'^(-?[0-9]+(.[0-9]+)?)$'
SIZE_RE = r'^\((?P<size>[0-9,]*)\)$'
QUEST_RE = r'^\?(?P<mod>f|v|a)?$'

FN_RE = r'^fn$'
FN_FULL_RE = r'^fn? (?P<fn_name>[A-z]\w*)\((?P<fn_args>.*)\)$'

FN_RET_RE = r'^<<$'
FN_CALL_RE = r'^(?P<fn_name>[A-z]\w*)\((?P<fn_args>.*)\)$'


assert TOKEN_MAX == 15, f'Implementation not done for {TOKEN_MAX} tokens'


def get_token_type(tok: str):
    # if VERBOSE:
    #     print(f'get_token_type: "{tok}"')

    comm_match = re.match(COMMENT_RE, tok)
    if comm_match:
        comm_text = comm_match.groupdict()['comment']
        return (TOKEN_COMMENT, comm_text)

    if tok == '=':
        return (TOKEN_ASSIGN, tok)

    quest_match = re.match(QUEST_RE, tok)
    if quest_match:
        return (TOKEN_QUEST, quest_match.groups()[0])

    fn_match = re.match(FN_RE, tok)
    if fn_match:
        return (TOKEN_FN_DEF, tok)

    var_match = re.match(VAR_RE, tok)
    if var_match:
        return (TOKEN_VAR, var_match.groups()[0], var_match.groups()[1])

    op_match = re.match(OP_RE, tok)

    if op_match:
        return (TOKEN_OP,)

    range_match = re.match(RANGE_RE, tok)

    if range_match:
        groups = range_match.groupdict()
        r_min = groups['min']
        r_max = groups['max']
        r_min_in = groups['min_in']
        r_max_in = groups['max_in']
        return (TOKEN_RANGE, r_min, r_max, r_min_in, r_max_in)

    size_match = re.match(SIZE_RE, tok)
    if size_match:
        groups = size_match.groupdict()
        size = groups['size']
        return (TOKEN_SIZE, size)

    cond_match = re.match(COND_RE, tok)
    if cond_match:
        return (TOKEN_COND, tok)

    num_mark = re.match(NUM_RE, tok)
    if num_mark:
        return (TOKEN_NUM, num_mark.groups()[0])

    cmd_match = re.match(CMD_RE, tok)
    if cmd_match:
        tok_match = cmd_match.groups()[0]
        if tok_match == '??':
            return (TOKEN_IF, tok)
        if tok_match == '>>':
            return (TOKEN_ELSE, tok)
        if tok_match == '--':
            return (TOKEN_END, tok)

    fn_ret_match = re.match(FN_RET_RE, tok)
    if fn_ret_match:
        return (TOKEN_FN_RET, tok)

    fn_call_match = re.match(FN_CALL_RE, tok)
    if fn_call_match:
        groups = fn_call_match.groupdict()
        fn_name = groups['fn_name']
        fn_args = groups['fn_args']

        return (TOKEN_FN_CALL, fn_name, fn_args)

    assert False, f'Token "{tok}" not matched'


def match_token(tok: str, tok_re: str):

    re_match = re.match(tok_re, tok)

    if re_match is None:
        return False, None

    return True, re_match.groups()
