import unittest
import pandas as pd
import pyterrier as pt
import pyterrier_alpha as pta


class MyTransformer(pt.Transformer):
    def __init__(self):
        self.invocations = []

    @pta.transform.by_query()
    def transform(self, inp):
        assert isinstance(inp, pd.DataFrame)
        self.invocations.append(inp)
        return inp


class MyIterTransformer(pt.Transformer):
    def __init__(self):
        self.invocations = []

    @pta.transform.by_query(add_ranks=False)
    def transform_iter(self, inp):
        assert not isinstance(inp, pd.DataFrame)
        inp = list(inp)
        self.invocations.append(inp)
        yield from inp


class TestTransform(unittest.TestCase):

    def test_transform_by_query_verbose(self):
        class VerboseMyTransformer(MyTransformer):
            def __init__(self, verbose):
                super().__init__()
                self.verbose = verbose
        v = VerboseMyTransformer(True)
        v.transform(pd.DataFrame([
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]))
        self.assertEqual(len(v.invocations), 2)

        not_v = VerboseMyTransformer(False)
        not_v.transform(pd.DataFrame([
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]))
        self.assertEqual(len(not_v.invocations), 2)

    def test_transform_by_query_verbose(self):
        class VerboseMyTransformerIter(MyIterTransformer):
            def __init__(self, verbose):
                super().__init__()
                self.verbose = verbose
        v = VerboseMyTransformerIter(True)
        v.transform(pd.DataFrame([
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]))
        self.assertEqual(len(v.invocations), 2)

        not_v = VerboseMyTransformerIter(False)
        not_v.transform(pd.DataFrame([
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]))
        self.assertEqual(len(not_v.invocations), 2)

    def test_transform_by_query(self):
        t = MyTransformer()
        data = [
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]
        t.transform(pd.DataFrame(data))
        self.assertEqual(len(t.invocations), 2)
        t(pd.DataFrame(data))
        self.assertEqual(len(t.invocations), 4)
        t(data)
        self.assertEqual(len(t.invocations), 6)

        t = MyTransformer()
        t.transform(pd.DataFrame([], columns=['qid', 'query']))
        self.assertEqual(len(t.invocations), 1)
        self.assertEqual(len(t.invocations[0]), 0)

    # This test fails now because add_ranks=False doesn't work with ApplyIterForEachQuery
    def test_transform_iter_by_query(self):
        t = MyIterTransformer()
        data = [
            {'qid': '1', 'query': 'hello world', 'docno': '1', 'score': 1.2},
            {'qid': '2', 'query': 'hello terrier', 'docno': '1', 'score': 1.5},
            {'qid': '2', 'query': 'hello terrier', 'docno': '2', 'score': 1.1},
        ]
        list(t.transform_iter(data))
        self.assertEqual(len(t.invocations), 2)
        list(t(data))
        self.assertEqual(len(t.invocations), 4)
        t.transform(pd.DataFrame(data))
        self.assertEqual(len(t.invocations), 6)
        t(pd.DataFrame(data))
        self.assertEqual(len(t.invocations), 8)
        

        t = MyIterTransformer()
        list(t.transform_iter([]))
        self.assertEqual(len(t.invocations), 0)
