"""Fusion methods for combining ranking results."""
from collections import defaultdict
from typing import Optional

import pandas as pd
import pyterrier as pt

import pyterrier_alpha as pta


class PerQueryMaxMinScore(pt.Transformer):
  """Applies per-query maxmin scaling on the input scores.

  The underlying implementation uses :func:`sklearn.preprocessing.minmax_scale`
  to scale the scores of each query independently in the range 0-1.

  Example::

      import pyterrier_alpha as pta
      fusion = (bm25 >> pta.fusion.PerQueryMaxMinScore()) +
        (dpr >> pta.fusion.PerQueryMaxMinScore())
  """

  def transform(self, topics_and_res: pd.DataFrame) -> pd.DataFrame:
      """Performs per-query maxmin scaling on the input data."""
      from sklearn.preprocessing import minmax_scale

      from .validate import validate
      validate.result_frame(topics_and_res, extra_columns=['score'])
      topics_and_res = topics_and_res.copy()
      topics_and_res["score"] = topics_and_res.groupby('qid')["score"].transform(lambda x: minmax_scale(x))
      return topics_and_res

class RRFusion(pt.Transformer):
  """Reciprocal Rank Fusion between the results from multiple transformers.

  This transformer merges multiple ranking results by computing the reciprocal rank of each document in each ranking,
  and summing them up. The reciprocal rank is computed as 1/(rank + k), where k is a constant. The resulting score is
  used to rank the documents.

  Consider using the :func:`rr_fusion` function if you want to apply fusion outside of a pipeline.

  .. cite.dblp:: conf/sigir/CormackCB09
  """
  schematic = {'inner_pipelines_mode': 'combine', 'label': 'RRF'}

  def __init__(self,
    *transformers: pt.Transformer,
    k: int = 60,
    num_results: Optional[int] = 1000
  ):
    """Initializes the transformer.

    Args:
      transformers: The transformers to merge.
      k: The constant used in the reciprocal rank computation.
      num_results: The number of results to keep for each query. If None, all results are kept.
    """
    assert len(transformers) > 0
    self.transformers = transformers
    self.k = k
    self.num_results = num_results

  def transform(self, inp: pd.DataFrame) -> pd.DataFrame:
    """Performs the reciprocal rank fusion on the input data."""
    return rr_fusion(*[t(inp) for t in self.transformers], k=self.k, num_results=self.num_results)


def rr_fusion(
  *results: pd.DataFrame,
  k: int = 60,
  num_results: Optional[int] = 1000
) -> pd.DataFrame:
  """Reciprocal Rank Fusion between two ranking result lists.

  Args:
    results: Multiple result frames to merge. At least one frame is required.
    k: The constant used in the reciprocal rank computation.
    num_results: The number of results to keep for each query. If None, all results are kept.

  Consider using :class:`RRFusion` if you want to use this directly in a pipeline.

  .. cite.dblp:: conf/sigir/CormackCB09
  """
  assert len(results) > 0
  all_qids = defaultdict(list)
  for r in results:
    pta.validate.result_frame(r, extra_columns=['score'])
    pt.model.add_ranks(r)
    r = r[['qid', 'query', 'docno']].assign(score=1/(r['rank'] + k))
    for qid, v in r.groupby('qid'):
      all_qids[qid].append(v)
  res = []
  if len(all_qids) == 0:
      all_qids[None] = results
  for qid, qid_frames in all_qids.items():
    merged_frame = qid_frames[0]
    for next_frame in qid_frames[1:]:
      merged_frame = merged_frame.merge(next_frame, how='outer', on=['qid', 'query', 'docno'])
      merged_frame = merged_frame.assign(score=merged_frame['score_x'].fillna(0.) + merged_frame['score_y'].fillna(0.))
      merged_frame.drop(columns=['score_x', 'score_y'], inplace=True)
    pt.model.add_ranks(merged_frame)
    merged_frame.sort_values('rank', ascending=True, inplace=True)
    if num_results is not None: # apply cutoff if present
      res.append(merged_frame[merged_frame['rank'] < num_results])
  return pd.concat(res, ignore_index=True)
