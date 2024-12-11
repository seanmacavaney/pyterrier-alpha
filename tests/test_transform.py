import unittest
import pandas as pd
import pyterrier as pt
import pyterrier_alpha as pta


class MyTransformer(pt.Transformer):
    def __init__(self):
        self.invocations = []

    @pta.transform.by_query()
    def transform(self, inp):
        self.invocations.append(inp)
        return inp


class MyIterTransformer(pt.Transformer):
    def __init__(self):
        self.invocations = []

    @pta.transform.by_query(add_ranks=False)
    def transform_iter(self, inp):
        inp = list(inp)
        self.invocations.append(inp)
        yield from inp


class TestTransform(unittest.TestCase):
    def test_transform_by_query(self):
        t = MyTransformer()
        t.transform(pd.DataFrame([
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]))
        self.assertEqual(len(t.invocations), 2)

        t = MyTransformer()
        t.transform(pd.DataFrame([], columns=['qid', 'query']))
        self.assertEqual(len(t.invocations), 1)
        self.assertEqual(len(t.invocations[0]), 0)

    # This test fails now because add_ranks=False doesn't work with ApplyIterForEachQuery
    def test_transform_iter_by_query(self):
        t = MyIterTransformer()
        list(t.transform_iter([
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]))
        self.assertEqual(len(t.invocations), 2)

        t = MyIterTransformer()
        list(t.transform_iter([]))
        self.assertEqual(len(t.invocations), 0)
