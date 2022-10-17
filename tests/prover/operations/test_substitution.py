# -- get_var_binding helper --


from immutables import Map
import pytest  # type: ignore
from amr_reasoner.prover.operations.substitution import (
    SubstitutionsMap,
    VariableBindingError,
    get_var_binding,
    set_var_binding,
)
from amr_reasoner.types.Constant import Constant
from amr_reasoner.types.Variable import Variable


def test_get_var_binding_recursively_resolves_dependencies() -> None:
    const1 = Constant("jared")
    var1 = Variable("X")
    var2 = Variable("Y")
    subs: SubstitutionsMap = Map(
        {  # type: ignore
            3: Map({var1: const1, var2: (7, var1)}),
            7: Map({var2: (3, var1)}),
        }
    )
    assert get_var_binding(var1, 3, subs) == const1
    assert get_var_binding(var2, 3, subs) is None
    assert get_var_binding(var2, 7, subs) == const1


# -- set_var_binding helper --


def test_set_var_binding_can_set_var_to_another_var() -> None:
    var1 = Variable("X")
    var2 = Variable("Y")
    subs: SubstitutionsMap = Map()

    new_subs = set_var_binding(var1, 3, (3, var2), subs)

    # should recursively find the first referenced var and set its subtitution
    assert new_subs[3][var1] == (3, var2)


def test_set_var_binding_recursively_resolves_dependencies() -> None:
    const1 = Constant("jared")
    const2 = Constant("mark")
    var1 = Variable("X")
    var2 = Variable("Y")
    subs: SubstitutionsMap = Map(
        {  # type: ignore
            3: Map({var1: const1, var2: (7, var1)}),
            7: Map({var2: (3, var1)}),
        }
    )

    new_subs = set_var_binding(var1, 7, const2, subs)

    # should recursively find the first referenced var and set its subtitution
    assert new_subs[7][var1] == const2
    assert get_var_binding(var1, 7, new_subs) == const2


def test_set_var_binding_raises_exception_when_binding_already_bound_var() -> None:
    const1 = Constant("jared")
    var1 = Variable("X")
    var2 = Variable("Y")
    subs: SubstitutionsMap = Map({3: Map({var1: const1})})

    with pytest.raises(VariableBindingError):
        set_var_binding(var1, 3, (3, var2), subs)
