from typing import Iterable, Union

from .Atom import Atom
from .Rule import Rule

"Typing helper for the knowledge param of solvers"
Knowledge = Iterable[Union[Atom, Rule]]
