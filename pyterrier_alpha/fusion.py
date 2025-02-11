"""Fusion methods for combining ranking results."""
from typing import Optional

import pandas as pd
import pyterrier as pt


class RRFusion(pt.Transformer):
  """Reciprocal Rank Fusion between the results from two transformers.

  This transformer merges two ranking results by computing the reciprocal rank of each document in each ranking, and
  summing them up. The reciprocal rank is computed as 1/(rank + k), where k is a constant. The resulting score is used
  to rank the documents.

  Consider using the :func:`rr_fusion` function if you want to apply fusion outside of a pipeline.

  .. cite.dblp:: conf/sigir/CormackCB09
  """
  def __init__(self,
    a: pt.Transformer,
    b: pt.Transformer,
    *,
    k: int = 60,
    num_results: Optional[int] = 1000
  ):
    """Initializes the transformer.

    Args:
      a: The first transformer.
      b: The second transformer.
      k: The constant used in the reciprocal rank computation.
      num_results: The number of results to keep for each query. If None, all results are kept.
    """
    self.a = a
    self.b = b
    self.k = k
    self.num_results = num_results

  def transform(self, inp: pd.DataFrame) -> pd.DataFrame:
    """Performs the reciprocal rank fusion on the input data."""
    return rr_fusion(self.a(inp), self.b(inp), k=self.k, num_results=self.num_results)

def rr_fusion(
  results_a: pd.DataFrame,
  results_b: pd.DataFrame,
  *,
  k: int = 60,
  num_results: Optional[int] = 1000
) -> pd.DataFrame:
  """Reciprocal Rank Fusion between two ranking result lists.

  Consider using :class:`RRFusion` if you want to use this direclty in a pipeline.
  """
  inp_a = {k: v for k, v in results_a.groupby('qid')}
  inp_b = {k: v for k, v in results_b.groupby('qid')}
  res = []
  for qid in inp_a.keys() | inp_b.keys():
    if qid not in inp_a:
      res.append(inp_b[qid][['qid', 'query', 'docno', 'rank']])
    if qid not in inp_b:
      res.append(inp_a[qid][['qid', 'query', 'docno', 'rank']])
    else:
      merged = pd.merge(
        inp_a[qid][['qid', 'query', 'docno', 'rank']],
        inp_b[qid][['qid', 'query', 'docno', 'rank']],
        how='outer', on=['qid', 'query', 'docno'])
      merged['score'] = (
        (1/(merged['rank_x'] + k)).fillna(0.) +
        (1/(merged['rank_y'] + k)).fillna(0.)
      )
      merged.drop(columns=['rank_x', 'rank_y'], inplace=True)
      pt.model.add_ranks(merged)
      merged.sort_values('rank', ascending=True, inplace=True)
      if num_results is not None: # apply cutoff if present
        res.append(merged[merged['rank'] < num_results])
  return pd.concat(res, ignore_index=True)
