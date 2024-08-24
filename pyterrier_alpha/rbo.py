"""Module providing the Rank Biased Overlap (RBO) measure."""

from typing import Callable, Iterable, Optional, Tuple

import ir_measures
import pandas as pd


def RBO(other: pd.DataFrame, p: float = 0.99, *, name: Optional[str] = None) -> ir_measures.Measure: # noqa: N802
    """Create an RBO measure from a dataframe of rankings.

    .. versionadded:: 0.3.0

    .. versionchanged:: 0.3.1
        Fixed bug where ``p`` wasn't honored.
    """
    return ir_measures.define(_rbo_wrapper(other, p=p), name=name or f'RBO(p={p})')


def _rbo_wrapper(a: pd.DataFrame, p: float = 0.99) -> Callable:
    # adapted from https://github.com/terrierteam/ir_measures/blob/main/ir_measures/providers/compat_provider.py
    a_q_col = 'query_id' if 'query_id' in a.columns else 'qid'
    a_d_col = 'doc_id' if 'doc_id' in a.columns else 'docno'
    a = a.sort_values(by=[a_q_col, 'score'], ascending=False)
    a = dict(iter(a.groupby(a_q_col)))
    def inner(qrels: pd.DataFrame, b: pd.DataFrame) -> Iterable[Tuple[str, float]]:
        # qrels ignored
        b_q_col = 'query_id' if 'query_id' in b.columns else 'qid'
        b_d_col = 'doc_id' if 'doc_id' in b.columns else 'docno'
        res = {}
        b = b.sort_values(by=[b_q_col, 'score'], ascending=False)
        b = dict(iter(b.groupby(b_q_col)))
        for qid in set(a.keys()) | set(b.keys()):
            ranking = list(a[qid][a_d_col]) if qid in a else []
            ideal = list(b[qid][b_d_col]) if qid in b else []
            ranking_set = set()
            ideal_set = set()
            score = 0.0
            normalizer = 0.0
            weight = 1.0
            for i in range(1000):
                if i < len(ranking):
                    ranking_set.add(ranking[i])
                if i < len(ideal):
                    ideal_set.add(ideal[i])
                score += weight*len(ideal_set.intersection(ranking_set))/(i + 1)
                normalizer += weight
                weight *= p
            res[qid] = score/normalizer
        return res.items()
    return inner


def rbo(a: pd.DataFrame, b: pd.DataFrame, p: float = 0.99) -> Iterable[Tuple[str, float]]:
    """Calculate the Rank Biased Overlap between two rankings.

    .. versionadded:: 0.3.0
    """
    return _rbo_wrapper(a, p)(b)
