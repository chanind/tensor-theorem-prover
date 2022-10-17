from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from immutables import Map

from amr_reasoner.prover.operations.substitution import SubstitutionsMap, resolve_term
from amr_reasoner.types.Constant import Constant
from amr_reasoner.types.Rule import Rule
from amr_reasoner.types.Atom import Atom
from amr_reasoner.types.Variable import Variable


@dataclass(frozen=True, eq=False)
class ProofNode:
    goal: Atom
    rule: Rule
    goal_scope: int
    rule_scope: int
    unification_similarity: float
    overall_similarity: float
    children: Optional[list[ProofNode]] = None
    substitutions: SubstitutionsMap = Map()


@dataclass(frozen=True, eq=False)
class Proof:
    head: ProofNode

    @property
    def goal(self) -> Atom:
        return self.head.goal

    @property
    def similarity_score(self) -> float:
        return self.head.overall_similarity

    @property
    def variable_bindings(self) -> Map[Variable, Constant | Variable]:
        bindings: dict[Variable, Constant | Variable] = {}
        for term in self.goal.terms:
            if isinstance(term, Variable):
                bindings[term] = resolve_term(
                    term, self.head.goal_scope, self.head.substitutions
                )
        return Map(bindings)

    def __str__(self) -> str:
        return self.pretty_print()

    def pretty_print(self) -> str:
        return pretty_print_node(self.head)


# -- pretty print helpers --


def resolve_substitutions_str(
    atom: Atom, scope: int, substitutions: SubstitutionsMap
) -> str | None:
    resolved_vars: set[tuple[Variable, Constant]] = set()
    for term in atom.terms:
        if isinstance(term, Variable):
            resolved_term = resolve_term(term, scope, substitutions)
            if isinstance(resolved_term, Constant):
                resolved_vars.add((term, resolved_term))
    if len(resolved_vars) == 0:
        return None
    sorted_resolved_vars = sorted(
        [res for res in resolved_vars], key=lambda res: res[0].name
    )
    return ", ".join(
        [f"{sub[0].name}->{sub[1].symbol}" for sub in sorted_resolved_vars]
    )


def pretty_print_node(node: ProofNode) -> str:
    goal_subs_str = resolve_substitutions_str(
        node.goal, node.goal_scope, node.substitutions
    )
    head_subs_str = resolve_substitutions_str(
        node.rule.head, node.rule_scope, node.substitutions
    )

    output_lines = [
        f"| goal: {node.goal}",
        f"| rule: {node.rule}",
        f"| unification similarity: {node.unification_similarity}",
        f"| overall similarity: {node.overall_similarity}",
    ]
    if goal_subs_str:
        output_lines.append(f"| goal subs: {goal_subs_str}")
    if head_subs_str:
        output_lines.append(f"| rule subs: {head_subs_str}")
    if node.children:
        output_lines.append(
            f"| subgoals: {', '.join([str(child.goal) for child in node.children])}"
        )

    output = "\n".join(output_lines)

    if node.children:
        for child in node.children:
            child_output = pretty_print_node(child)
            output += "\n" + prepend_indentation(child_output)
    return output


def prepend_indentation(child_node_output: str) -> str:
    child_node_output_lines = child_node_output.split("\n")
    first_prefix = "  ╠═ "
    subsequent_prefix = "  ║  "
    first_prepended_line = first_prefix + child_node_output_lines[0]
    subsequent_lines = [
        subsequent_prefix + line for line in child_node_output_lines[1:]
    ]
    prepended_lines = [
        subsequent_prefix.rstrip(),
        first_prepended_line,
        *subsequent_lines,
    ]
    return "\n".join(prepended_lines)
