# -*- coding: utf-8 -*-
import inspect
try:
    from backport.typing import Callable, Set, Optional
except ImportError:
    from typing import Callable, Set, Optional
from abc import ABCMeta, abstractmethod

from patternmatcher.expressions import Substitution
from patternmatcher.utils import get_lambda_source

# pylint: disable=too-few-public-methods

class Constraint(object, metaclass=ABCMeta):
    """Base for pattern constraints.
    """
    @abstractmethod
    def __call__(self, match: Substitution) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self, other):
        raise NotImplementedError()

    @abstractmethod
    def __hash__(self):
        raise NotImplementedError()

class MultiConstraint(Constraint):
    def __init__(self, constraints: Set[Constraint]) -> None:
        self.constraints = constraints

    @classmethod
    def create(cls, *constraints: Optional[Constraint]) -> Optional[Constraint]:
        flat_constraints = set()
        for constraint in constraints:
            if isinstance(constraint, MultiConstraint):
                flat_constraints.update(constraint.constraints)
            elif constraint is not None:
                flat_constraints.add(constraint)

        if len(flat_constraints) == 1:
            return flat_constraints.pop()
        elif len(flat_constraints) == 0:
            return None

        return cls(flat_constraints)

    def __call__(self, match: Substitution) -> bool:
        return all(c(match) for c in self.constraints)

    def __str__(self):
        return '(%s)' % ' and '.join(map(str, self.constraints))

    def __repr__(self):
        return 'MultiConstraint(%s)' % ' and '.join(map(repr, self.constraints))

    def __eq__(self, other):
        return isinstance(other, MultiConstraint) and self.constraints == other.constraints

    def __hash__(self):
        return hash(self.constraints)

class EqualVariablesConstraint(Constraint):
    def __init__(self, *variables: str) -> None:
        self.variables = set(variables)

    @staticmethod
    def _wrap_expr(expr):
        if not isinstance(expr, list):
            return [expr]
        return expr

    def __call__(self, match: Substitution) -> bool:
        variables = self.variables.copy()
        v1 = self._wrap_expr(match[variables.pop()])
        while variables:
            v2 = self._wrap_expr(match[variables.pop()])
            if v2 != v1:
                return False
        return True

    def __str__(self):
        return '(%s)' % ' == '.join(self.variables)

    def __repr__(self):
        return 'EqualVariablesConstraint(%s)' % ' == '.join(self.variables)

    def __eq__(self, other):
        return isinstance(other, EqualVariablesConstraint) and self.variables == other.variables

    def __hash__(self):
        return hash(self.variables)

class CustomConstraint(Constraint):
    def __init__(self, constraint: Callable[..., bool]) -> None:
        self.constraint = constraint
        signature = inspect.signature(constraint)

        self.allow_any = False
        self.variables = set() # type: Set[str]

        for param in signature.parameters.values():
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or param.kind == inspect.Parameter.KEYWORD_ONLY:
                self.variables.add(param.name)
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                self.allow_any = True
            elif param.kind == inspect.Parameter.POSITIONAL_ONLY:
                raise ValueError('constraint cannot have positional-only arguments')

    def __call__(self, match: Substitution) -> bool:
        if self.allow_any:
            return self.constraint(**match)
        args = dict((name, match[name]) for name in self.variables)

        return self.constraint(**args)

    def __str__(self):
        return '(%s)' % get_lambda_source(self.constraint)

    def __repr__(self):
        return 'CustomConstraint(%s)' % get_lambda_source(self.constraint)

    def __eq__(self, other):
        return isinstance(other, CustomConstraint) and self.constraint == other.constraint

    def __hash__(self):
        return hash(self.constraint)


if __name__ == '__main__':
    from patternmatcher.expressions import Symbol
    a = Symbol('a')
    b = Symbol('b')
    c = Symbol('c')
    cc = CustomConstraint(lambda x, y: x == y)
    vc = EqualVariablesConstraint('x', 'y')
    print(cc.variables)
    print(cc({'x': a, 'y': a, 'z': b, 'k': c}))
    print(vc({'x': a, 'y': a, 'z': b, 'k': c}))
