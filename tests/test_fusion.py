import unittest
import pandas as pd
import pyterrier as pt
import pyterrier_alpha as pta


class TestFusion(unittest.TestCase):

    def test_rrf_transformer(self):
        index = pt.terrier.TerrierIndex.from_hf('pyterrier/vaswani.terrier')
        topics = pt.get_dataset('irds:vaswani').get_topics()
        res_a = index.bm25(k1=1.0, b=1.0)(topics)
        res_b = index.bm25(k1=5.0, b=0.0)(topics)
        results = pta.fusion.rr_fusion(res_a, res_b)

    def test_rrf_transformer(self):
        index = pt.terrier.TerrierIndex.from_hf('pyterrier/vaswani.terrier')
        pipeline_a = index.bm25(k1=1.0, b=1.0)
        pipeline_b = index.bm25(k1=5.0, b=0.0)
        rrf = pta.RRFusion(pipeline_a, pipeline_b)
        topics = pt.get_dataset('irds:vaswani').get_topics()
        results = rrf(topics)
