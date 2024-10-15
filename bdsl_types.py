
from typing import Dict

from bounds import Bounds, IntOrFloat
from vardata import VarData


def numOrNone(s: str) -> IntOrFloat | None:

    if s == '':
        return None

    if '.' in s:
        return float(s)

    return int(s)


type Context = Dict[str, VarData]
# TODO: Use Bounds instead of Interval for conditions?.
type Conditions = Dict[str, Bounds]


def split_context(
        context: Context, conds: Conditions
) -> tuple[Context, Context]:

    filter_context = {}
    complement_context = {}

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
        curr_context: Context,
        comp_context: Context,
        split_cond: Conditions
) -> Context:
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


def iota(reset=False):
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
