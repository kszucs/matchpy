# -*- coding: utf-8 -*-
import unittest
from ddt import ddt, data, unpack

from patternmatcher.expressions import Operation, Symbol, Variable, Arity, Wildcard
from patternmatcher.functions import match, substitute
from patternmatcher.utils import match_repr_str


f = Operation.new('f', Arity.variadic)
f2 = Operation.new('f2', Arity.variadic)
fc = Operation.new('fc', Arity.variadic, commutative=True)
fc2 = Operation.new('fc2', Arity.variadic, commutative=True)
fa = Operation.new('fa', Arity.variadic, associative=True)
fa2 = Operation.new('fa2', Arity.variadic, associative=True)
fac1 = Operation.new('fac1', Arity.variadic, associative=True, commutative=True)
fac2 = Operation.new('fac2', Arity.variadic, associative=True, commutative=True)
a = Symbol('a')
b = Symbol('b')
c = Symbol('c')
_ = Wildcard.dot()
x_ = Variable.dot('x')
y_ = Variable.dot('y')
__ = Wildcard.plus()
x__ = Variable.plus('x')
y__ = Variable.plus('y')
___ = Wildcard.star()
x___ = Variable.star('x')
y___ = Variable.star('y')

@ddt
class MatchTest(unittest.TestCase):
    @unpack
    @data(
        (a,                 a,              True),
        (b,                 a,              False),
        (f(a),              f(a),           True),
        (f(b),              f(a),           False),
        (f2(a),             f(a),           False),
        (f(a, b),           f(a),           False),
        (f(a, b),           f(a, b),        True),
        (f(a),              f(a, b),        False),
        (f(b, a),           f(a, b),        False),
        (f(a, b, c),        f(a, b),        False),
        (f(a, f2(b)),       f(a, b),        False),
        (f(f2(a), f2(b)),   f(a, b),        False),
        (f(f2(a), b),       f(a, b),        False),
        (f(f(a, b)),        f(a, b),        False),
        (f2(a, b),          f(a, b),        False),
        (f(a, f2(b)),       f(a, f2(b)),    True),
        (f(f2(a), b),       f(f2(a), b),    True),
        (f(f(a, b)),        f(f(a, b)),     True)
    )
    def test_constant_match(self, expr, pattern, is_match):
        result = list(match(expr, pattern))
        if is_match:
            self.assertEqual(result, [dict()], 'Expression %s and %s did not match but were supposed to' % (expr, pattern))
        else:
            self.assertEqual(result, [], 'Expression %s and %s did match but were not supposed to' % (expr, pattern))

    @unpack
    @data(
        (fc(a, b),          fc(a, b),           True),
        (fc(b, a),          fc(a, b),           True),
        (fc(b, a, c),       fc(a, b, c),        True),
        (fc(c, a, b),       fc(a, b, c),        True),
        (fc(b, a, c),       fc(c, b, a),        True),
        (fc(b, a, a),       fc(a, a, b),        True),
        (fc(a, b, a),       fc(a, a, b),        True),
        (fc(b, b, a),       fc(a, a, b),        False),
        (fc(c, a, f2(b)),   fc(a, f2(b), c),    True),
        (fc(c, a, f2(b)),   fc(f2(a), b, c),    False),
        (f2(c, fc(a, b)),   f2(c, fc(b, a)),    True),
        (f2(c, fc(a, b)),   f2(fc(a, b), c),    False),
    )
    def test_commutative_match(self, expr, pattern, is_match):
        result = list(match(expr, pattern))
        if is_match:
            self.assertEqual(result, [dict()], 'Expression %s and %s did not match but were supposed to' % (expr, pattern))
        else:
            self.assertEqual(result, [], 'Expression %s and %s did match but were not supposed to' % (expr, pattern))

    @unpack
    @data(
        (a,                 x_,                 {'x': a}),
        (b,                 x_,                 {'x': b}),
        (f(a),              f(x_),              {'x': a}),
        (f(b),              f(x_),              {'x': b}),
        (f(a),              x_,                 {'x': f(a)}),
        (f2(a),             f(x_),              None),
        (f(a, b),           f(x_),              None),
        (f(a, b),           f(x_, b),           {'x': a}),
        (f(a, b),           f(x_, a),           None),
        (f(a, b),           f(a, x_),           {'x': b}),
        (f(a, b),           f(x_, x_),          None),
        (f(a, a),           f(x_, x_),          {'x': a}),
        (f(a, b),           f(x_, y_),          {'x': a,       'y': b}),
        (f(a),              f(x_, y_),          None),
        (f(a, b, c),        f(x_, y_),          None),
        (f(a, f2(b)),       f(x_, y_),          {'x': a,       'y': f2(b)}),
        (f(a, f2(b)),       f(x_, f2(y_)),      {'x': a,       'y': b}),
        (f(a, f2(b)),       f(x_, f2(x_)),      None),
        (f(a, f2(a)),       f(x_, f2(x_)),      {'x': a}),
        (f(f2(a), f2(b)),   f(x_, x_),          None),
        (f(f2(a), f2(b)),   f(x_, y_),          {'x': f2(a),   'y': f2(b)}),
        (f(f2(a), a),       f(x_, x_),          None),
        (f(f2(a), a),       f(f2(x_), x_),      {'x': a}),
        (f(f(a, b)),        f(x_, y_),          None),
        (f(f(a, b)),        f(x_),              {'x': f(a, b)}),
        (f2(a, b),          f(x_, y_),          None),
        (f(f(a, b)),        f(f(x_, y_)),       {'x': a,       'y': b})
    )
    def test_wildcard_dot_match(self, expr, pattern, expected_match):
        result = list(match(expr, pattern))
        if expected_match is not None:
            self.assertEqual(result, [expected_match], 'Expression %s and %s did not match as %s but were supposed to' \
                % (expr, pattern, match_repr_str(expected_match)))
        else:
            self.assertEqual(result, [], 'Expression %s and %s did match but were not supposed to' % (expr, pattern))

    @unpack
    @data(
        (fa(a),                 fa(x_),         [{'x': a}]),
        (fa(a, b),              fa(x_),         [{'x': fa(a, b)}]),
        (fa(a, b),              fa(a, x_),      [{'x': b}]),
        (fa(a, b, c),           fa(a, x_),      [{'x': fa(b, c)}]),
        (fa(a, b, c),           fa(x_, c),      [{'x': fa(a, b)}]),
        (fa(a, b, c),           fa(x_),         [{'x': fa(a, b, c)}]),
        (fa(a, b, a, b),        fa(x_, x_),     [{'x': fa(a, b)}]),
        (fa(a, b, a),           fa(x_, b, x_),  [{'x': a}]),
        (fa(a, a, b, a, a),     fa(x_, b, x_),  [{'x': fa(a, a)}]),
        (fa(a, b, c),           fa(x_, y_),     [{'x': a,          'y': fa(b, c)}, \
                                                 {'x': fa(a, b),    'y': c}])
    )
    def test_associative_wildcard_dot_match(self, expr, pattern, expected_matches):
        result = list(match(expr, pattern))
        for expected_match in expected_matches:
            self.assertIn(expected_match, result, 'Expression %s and %s did not yield the match %s but were supposed to' % (expr, pattern, match_repr_str(expected_match)))
        for result_match in result:
            self.assertIn(result_match, expected_matches, 'Expression %s and %s yielded the unexpected match %s' % (expr, pattern, match_repr_str(result_match)))

    @unpack
    @data(
        (a,                         x___,               [{'x': [a]}]),
        (f(a),                      f(x___),            [{'x': [a]}]),
        (f(),                       f(x___),            [{'x': []}]),
        (f(a),                      x___,               [{'x': [f(a)]}]),
        (f2(a),                     f(x___),            []),
        (f(a, b),                   f(x___),            [{'x': [a, b]}]),
        (f(a, b),                   f(x___, b),         [{'x': [a]}]),
        (f(a, b),                   f(x___, a),         []),
        (f(a, b),                   f(a, x___),         [{'x': [b]}]),
        (f(a, b),                   f(x___, x___),      []),
        (f(a, a),                   f(x___, x___),      [{'x': [a]}]),
        (f(a, b),                   f(x___, y___),      [{'x': [],                'y': [a, b]},     \
                                                         {'x': [a],               'y': [b]},        \
                                                         {'x': [a, b],            'y': []}]),
        (f(a),                      f(x___, y___),      [{'x': [],                'y': [a]},        \
                                                         {'x': [a],               'y': []}]),
        (f(a, b, c),                f(x___, y___),      [{'x': [],                'y': [a, b, c]},  \
                                                         {'x': [a],               'y': [b, c]},     \
                                                         {'x': [a, b],            'y': [c]},        \
                                                         {'x': [a, b, c],         'y': []}]),
        (f(a, f2(b)),               f(x___, y___),      [{'x': [],                'y': [a, f2(b)]}, \
                                                         {'x': [a],               'y': [f2(b)]},    \
                                                         {'x': [a, f2(b)],        'y': []}]),
        (f(a, f2(b)),               f(x___, f2(y___)),  [{'x': [a],               'y': [b]}]),
        (f(a, f2(b)),               f(x___, f2(x___)),  []),
        (f(a, f2(a)),               f(x___, f2(x___)),  [{'x': [a]}]),
        (f(f2(a), f2(b)),           f(x___, x___),      []),
        (f(f2(a), f2(b)),           f(x___, y___),      [{'x': [f2(a), f2(b)],    'y': []},         \
                                                         {'x': [f2(a)],           'y': [f2(b)]},    \
                                                         {'x': [],                'y': [f2(a), f2(b)]}]),
        (f(f2(a), a),               f(x___, x___),      []),
        (f(f2(a), a),               f(f2(x___), x___),  [{'x': [a]}]),
        (f(f(a, b)),                f(x___, y___),      [{'x': [f(a, b)],         'y': []},         \
                                                         {'x': [],                'y': [f(a, b)]}]),
        (f(f(a, b)),                f(x___),            [{'x': [f(a, b)]}]),
        (f2(a, b),                  f(x___, y___),      []),
        (f(a, a, a),                f(x___, b, y___),   []),
        (f(a, a, a),                f(x___, a, y___),   [{'x': [],                'y': [a, a]},     \
                                                         {'x': [a],               'y': [a]},        \
                                                         {'x': [a, a],            'y': []}]),
        (f(a),                      f(x___, a, y___),   [{'x': [],                'y': []}]),
        (f(a, a),                   f(x___, a, y___),   [{'x': [a],               'y': []},         \
                                                         {'x': [],                'y': [a]}]),
        (f(a, b, a),                f(x___, a, y___),   [{'x': [],                'y': [b, a]},     \
                                                         {'x': [a, b],            'y': []}]),
        (f(a, b, a, b),             f(x___, x___),      [{'x': [a, b]}]),
        (f(a, b, a, a),             f(x___, x___),      []),
        (f(a, b, a),                f(x___, b, x___),   [{'x': [a]}]),
        (f(a, b, a, a),             f(x___, b, x___),   []),
        (f(a, a, b, a),             f(x___, b, x___),   []),
        (f(a, b, a, b, a, b, a),    f(x___, b, x___),   [{'x': [a, b, a]}]),
        (f(a, b, a, b),             f(x___, b, y___),   [{'x': [a, b, a],         'y': []},         \
                                                         {'x': [a],               'y': [a, b]}]),
    )
    def test_wildcard_star_match(self, expr, pattern, expected_matches):
        result = list(match(expr, pattern))
        for expected_match in expected_matches:
            self.assertIn(expected_match, result, 'Expression %s and %s did not yield the match %s but were supposed to' % (expr, pattern, match_repr_str(expected_match)))
        for result_match in result:
            self.assertIn(result_match, expected_matches, 'Expression %s and %s yielded the unexpected match %s' % (expr, pattern, match_repr_str(result_match)))
    
    @unpack
    @data(
        (a,                         x__,                 [{'x': [a]}]),
        (f(a),                      f(x__),              [{'x': [a]}]),
        (f(),                       f(x__),              []),
        (f(a),                      x__,                 [{'x': [f(a)]}]),
        (f2(a),                     f(x__),              []),
        (f(a, b),                   f(x__),              [{'x': [a, b]}]),
        (f(a, b),                   f(x__, b),           [{'x': [a]}]),
        (f(a, b),                   f(x__, a),           []),
        (f(a, b),                   f(a, x__),           [{'x': [b]}]),
        (f(a, b),                   f(x__, x__),         []),
        (f(a, a),                   f(x__, x__),         [{'x': [a]}]),
        (f(a, b),                   f(x__, y__),         [{'x': [a],          'y': [b]}]),
        (f(a),                      f(x__, y__),         []),
        (f(a, b, c),                f(x__, y__),         [{'x': [a],          'y': [b, c]},     \
                                                          {'x': [a, b],       'y': [c]}]),
        (f(a, f2(b)),               f(x__, y__),         [{'x': [a],          'y': [f2(b)]}]),
        (f(a, f2(b)),               f(x__, f2(y__)),     [{'x': [a],          'y': [b]}]),
        (f(a, f2(b)),               f(x__, f2(x__)),     []),
        (f(a, f2(a)),               f(x__, f2(x__)),     [{'x': [a]}]),
        (f(f2(a), f2(b)),           f(x__, x__),         []),
        (f(f2(a), f2(b)),           f(x__, y__),         [{'x': [f2(a)],      'y': [f2(b)]}]),
        (f(f2(a), a),               f(x__, x__),         []),
        (f(f2(a), a),               f(f2(x__), x__),     [{'x': [a]}]),
        (f(f(a, b)),                f(x__, y__),         []),
        (f(f(a, b)),                f(x__),              [{'x': [f(a, b)]}]),
        (f2(a, b),                  f(x__, y__),         []),
        (f(a, a, a),                f(x__, b, y__),      []),
        (f(a, a, a),                f(x__, a, y__),      [{'x': [a],          'y': [a]}]),
        (f(a),                      f(x__, a, y__),      []),
        (f(a, a),                   f(x__, a, y__),      []),
        (f(a, b, a),                f(x__, a, y__),      []),
        (f(a, b, a, b),             f(x__, x__),         [{'x': [a, b]}]),
        (f(a, b, a, a),             f(x__, x__),         []),
        (f(a, b, a),                f(x__, b, x__),      [{'x': [a]}]),
        (f(a, b, a, a),             f(x__, b, x__),      []),
        (f(a, a, b, a),             f(x__, b, x__),      []),
        (f(a, b, a, b, a, b, a),    f(x__, b, x__),      [{'x': [a, b, a]}]),
        (f(a, b, a, b),             f(x__, b, y__),      [{'x': [a],          'y': [a, b]}]),
    )
    def test_wildcard_plus_match(self, expr, pattern, expected_matches):
        result = list(match(expr, pattern))
        for expected_match in expected_matches:
            self.assertIn(expected_match, result, 'Expression %s and %s did not yield the match %s but were supposed to' % (expr, pattern, match_repr_str(expected_match)))
        for result_match in result:
            self.assertIn(result_match, expected_matches, 'Expression %s and %s yielded the unexpected match %s' % (expr, pattern, match_repr_str(result_match)))

from hypothesis import given, assume
import hypothesis.strategies as st

def func_wrap_strategy(args, func):
    return st.lists(args, min_size=1, max_size=4).map(lambda a: func(*a))

ExpressionStrategy = st.recursive(st.sampled_from([a, b, c, x_, y_, x__, y__, x___, y___]), lambda args: func_wrap_strategy(args, f) | func_wrap_strategy(args, f2), max_leaves=10)

class RandomizedMatchTest(unittest.TestCase):
    @given(ExpressionStrategy, ExpressionStrategy)
    def test_correctness(self, expr, pattern):
        # expr must be constant, pattern cannot be constant
        assume(expr.is_constant)
        assume(not pattern.is_constant)

        expr_symbols = expr.symbols
        pattern_symbols = pattern.symbols

        # pattern must not be just a single variable
        assume(sum(pattern_symbols.values()) > 0)

        diff1 = sum((expr_symbols - pattern_symbols).values())
        diff2 = sum((pattern_symbols - expr_symbols).values())

        # Pattern cannot contain symbols which are not contained in the expression
        assume(diff2 < 1)

        #var_count = sum(pattern.variables.values())
        #assume(abs(var_count - diff1) < 3)

        results = list(match(expr, pattern))

        # exclude non-matching pairs
        assume(len(results) > 0)
        #print(expr, pattern)
        for result in results:
            #print('->', match_repr_str(result))
            reverse, replaced = substitute(pattern, result)
            if isinstance(reverse, list) and len(reverse) == 1:
                reverse = reverse[0]
            self.assertEqual(expr, reverse)

@ddt
class SubstituteTest(unittest.TestCase):
    @unpack
    @data(
        (a,                                 {},                      a,                  False),
        (a,                                 {'x': b},                a,                  False),
        (x_,                                {'x': b},                b,                  True),
        (x_,                                {'x': [a, b]},           [a, b],             True),
        (y_,                                {'x': b},                y_,                 False),
        (Variable('x', Variable('y', a)),   {'y': b},                Variable('x', b),   True),
        (f(x_),                             {'x': b},                f(b),               True),
        (f(x_),                             {'y': b},                f(x_),              False),
        (f(x_),                             {},                      f(x_),              False),
        (f(a, x_),                          {'x': b},                f(a, b),            True),
        (f(x_),                             {'x': [a, b]},           f(a, b),            True),
        (f(x_, c),                          {'x': [a, b]},           f(a, b, c),         True),
        (f(x_, y_),                         {'x': a, 'y': b},        f(a, b),            True),
        (f(x_, y_),                         {'x': [a, c], 'y': b},   f(a, c, b),         True),
        (f(x_, y_),                         {'x': a, 'y': [b, c]},   f(a, b, c),         True),
    )
    def test_substitution_match(self, expr, subst, expected_result, replaced):
        result, did_replace = substitute(expr, subst)
        self.assertEqual(result, expected_result, 'Substitution did not yield expected result (%s x___ %s)' % (result, expected_result))
        self.assertEqual(did_replace, replaced, 'Substitution did not yield expected result')
        if not did_replace:
            self.assertIs(result, expr, 'When nothing is substituted, the original expression has to be returned')

if __name__ == '__main__':
    unittest.main()