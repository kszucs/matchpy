import operator
from typing import List, Optional, Any, Union
import dataclasses
from matchpy.functions import substitute

import pytest
from pydantic import ValidationError
import ibis.expr.operations as ops
from matchpy import Operation, Arity, Wildcard, match, Pattern, ReplacementRule, replace_all, is_match, match_anywhere, preorder_iter_with_position
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    def __init_subclass__(
        cls,
        /,
        associative=False,
        commutative=False,
        one_identity=False,
        infix=False,
        **kwargs,
    ):
        cls.pattern = Operation.new(
            head=cls,
            name=f"{cls.__name__}Pattern",
            arity=Arity(len(cls.__annotations__), True),
            associative=associative,
            commutative=commutative,
            one_identity=one_identity,
            infix=infix,
        )

    def __len__(self):
        return len(self.__annotations__)

    def __iter__(self):
        for name in self.__annotations__.keys():
            yield getattr(self, name)


Operation.register(Node)


@dataclass(frozen=True)
class Literal(Node):
    value: int


@dataclass(frozen=True)
class Add(Node, commutative=True):
    left: Node
    right: Node


@dataclass(frozen=True)
class Multiply(Node, commutative=True):
    left: Node
    right: Node


zero = Literal(value=0)
one = Literal(value=1)
two = Literal(value=2)
three = Literal(value=3)
eleven = Literal(value=11)

expr = Multiply(
    left=Add(left=Multiply(left=three, right=one), right=two),
    right=Multiply(left=two, right=eleven),
)
expr1 = Add(
    Multiply(
        Add(
            Multiply(three, one),
            two
        ),
        Multiply(
            Add(zero, two),
            eleven
        ),
    ),
    zero
)

_ = Wildcard.dot()
x = Wildcard.dot("x")
y = Wildcard.dot("y")


def test_wildcard_not_allowed():
    with pytest.raises(ValidationError):
        Literal(value=Wildcard.dot())


def test_matching():
    pattern = Multiply.pattern(Add.pattern(x, _), y)

    sub = next(match(expr, Pattern(pattern)))
    assert sub["x"] == Multiply(left=three, right=one)
    assert sub["y"] == Multiply(left=two, right=eleven)


def test_is_match():
    assert is_match(one, Pattern(one))
    assert is_match(one, Pattern(Literal.pattern(1)))
    assert not is_match(one, Pattern(Literal.pattern(2)))


def test_replacement():
    rules = [
        (Pattern(ops.Multiply.pattern(x, one)), lambda x: x),
        (Pattern(ops.Add.pattern(x, zero)), lambda x: x)
    ]
    result = replace_all(expr, rules)

    expected = Multiply(
        left=Add(left=three, right=two),
        right=Multiply(left=two, right=eleven),
    )
    assert expected == result

    result1 = replace_all(expr1, rules)
    expected1 = Multiply(
        Add(three, two),
        Multiply(two, eleven),
    )
    assert result1 == expected1
