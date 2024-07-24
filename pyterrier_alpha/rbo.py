from typing import Optional
import ir_measures


def RBO(other, p=0.99, *, name: Optional[str] = None):
    return ir_measures.define(_rbo_wrapper(other, p=p), name=name or f'RBO(p={p})')


def _rbo_wrapper(a, p=0.99):
    # adapted from https://github.com/terrierteam/ir_measures/blob/main/ir_measures/providers/compat_provider.py
    a_q_col = 'query_id' if 'query_id' in a.columns else 'qid'
    a_d_col = 'doc_id' if 'doc_id' in a.columns else 'docno'
    a = a.sort_values(by=[a_q_col, 'score'], ascending=False)
    a = dict(iter(a.groupby(a_q_col)))
    def inner(qrels, b):
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


def rbo(a, b, p=0.99):
    return _rbo_wrapper(a, p)(b)
