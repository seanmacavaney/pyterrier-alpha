Rank Biased Overlap (RBO)
==================================================

Rank Biased Overlap (RBO) is a measurement between two rankings that prioritizes overlap
at the top of the ranking. This module provides a way to calculate RBO between two rankings,
both as a standalone function and as an evaluation measure.

API Documentation
---------------------------------------------------------

.. autofunction:: pyterrier_alpha.rbo

.. autoclass:: pyterrier_alpha.RBO
    :members:

Acknowledgements
---------------------------------------------------------

If you use this measure, be sure to cite:

.. code-block:: bibtex
    :caption: Citation for RBO

    @article{DBLP:journals/tois/WebberMZ10,
      author       = {William Webber and
                      Alistair Moffat and
                      Justin Zobel},
      title        = {A similarity measure for indefinite rankings},
      journal      = {{ACM} Trans. Inf. Syst.},
      volume       = {28},
      number       = {4},
      pages        = {20:1--20:38},
      year         = {2010},
      url          = {https://doi.org/10.1145/1852102.1852106},
      doi          = {10.1145/1852102.1852106}
    }

This implemtation was based on the one provided by `Charlie Clarke 
<https://uwaterloo.ca/computer-science/contacts/charles-clarke>`__ to `ir-measures <https://github.com/terrierteam/ir_measures/commit/62503917285b7f4e3d60fcdd23df09ef5780c27e>`__.
