import unittest
import pyterrier as pt
from pyterrier_alpha import transformer_repr


class MyTransformer(pt.Transformer):
    def __init__(self, a, b='x', c=None, *, d=1, e=None):
        self.a = a
        self.b = b
        self.c = c
        self._d = d
        self.e = e
        self.f = 1

    def d(self):
        pass

    __repr__ = transformer_repr


class TestTransformerRepr(unittest.TestCase):
    def test_basic(self):
        self.assertEqual('MyTransformer(1)', repr(MyTransformer(1)))
        self.assertEqual('MyTransformer(1)', repr(MyTransformer(1, "x")))
        self.assertEqual('MyTransformer(1, 2)', repr(MyTransformer(1, 2)))
        self.assertEqual('MyTransformer(1, 2)', repr(MyTransformer(1, b=2)))
        self.assertEqual('MyTransformer(1, c=2)', repr(MyTransformer(1, c=2)))
        self.assertEqual("MyTransformer(1, 'a', 2)", repr(MyTransformer(1, "a", c=2)))
        self.assertEqual("MyTransformer(1, 'a', 2)", repr(MyTransformer(1, "a", c=2)))
        self.assertEqual('MyTransformer(1, d=2)', repr(MyTransformer(1, d=2)))
