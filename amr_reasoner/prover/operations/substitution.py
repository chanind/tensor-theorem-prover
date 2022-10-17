from __future__ import annotations
from typing import Tuple, Union
from immutables import Map

from amr_reasoner.types.Constant import Constant
from amr_reasoner.types.Variable import Variable


# using from __future__ import annotations with | doesn't work here
# I think because this is declaring a type as a variable
SubstitutionsMap = Map[int, Map[Variable, Union[Constant, Tuple[int, Variable]]]]


class VariableBindingError(Exception):
    pass


_count = 0


def generate_variable_scope() -> int:
    """simple helper to output different int each time its called to use as a scope for variable binding"""
    global _count
    _count += 1
    return _count


def resolve_term(
    term: Variable | Constant, scope: int, substitutions: SubstitutionsMap
) -> Variable | Constant:
    """
    if this term is a variable that's already been bound to a constant in the substitutions map, swap it for its bound value
    else, just return the term
    """
    if isinstance(term, Constant):
        return term
    var_binding = get_var_binding(term, scope, substitutions)
    return var_binding if var_binding else term


def is_var_bound(
    variable: Variable, scope: int, substitutions: SubstitutionsMap
) -> bool:
    return bool(get_var_binding(variable, scope, substitutions))


def get_var_binding(
    variable: Variable, scope: int, substitutions: SubstitutionsMap
) -> Constant | None:
    """Return the currently bound constant for this variable if already bound, or None if not bound yet"""
    scope_bindings = substitutions.get(scope)
    if not scope_bindings:
        return None
    var_binding = scope_bindings.get(variable)
    # if this is bound to another variable, recursively look up that variable
    if isinstance(var_binding, tuple):
        return get_var_binding(var_binding[1], var_binding[0], substitutions)
    return var_binding


def set_var_binding(
    variable: Variable,
    scope: int,
    # tuple[rule, var] represents the path to look up that variable recursively in the substitutions mapping
    value: Constant | tuple[int, Variable],
    substitutions: SubstitutionsMap,
) -> SubstitutionsMap:
    scope_bindings = substitutions.get(scope)
    if not scope_bindings:
        return substitutions.set(scope, Map({variable: value}))
    var_binding = scope_bindings.get(variable)
    # if this is bound to another variable, recursively set that var instead
    if isinstance(var_binding, tuple):
        return set_var_binding(var_binding[1], var_binding[0], value, substitutions)
    if var_binding is not None:
        raise VariableBindingError(
            f"Tried to bind an already-bound variable {variable} in scope {scope}"
        )
    return substitutions.set(scope, scope_bindings.set(variable, value))
