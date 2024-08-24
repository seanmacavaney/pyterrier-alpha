Input Validation
===================================

DataFrame Validation
------------------------------------

It's a good idea to check the input to a transformer to make sure its compatible before you start using it.
`pta.validate` provides functions for this.

.. code-block:: python
    :caption: DataFrame input validation in a Transformer

    def MyTransformer(pt.Transformer):
        def transform(self, inp: pd.DataFrame):
            # e.g., expects a query frame with query_vec
            pta.validate.query_frame(inp, extra_columns=['query_vec'])
            # raises an error if the specification doesn't match

=========================================================  ===============================  =======================
Function                                                   Must have column(s)              Must NOT have column(s)
=========================================================  ===============================  =======================
``pta.validate.query_frame(inp, extra_columns=...)``       qid + ``extra_columns``          docno
``pta.validate.document_frame(inp, extra_columns=...)``    docno + ``extra_columns``        qid
``pta.validate.result_frame(inp, extra_columns=...)``      qid + docno + ``extra_columns``  
``pta.validate.columns(inp, includes=..., excludes=...)``  ``includes``                     ``excludes``
=========================================================  ===============================  =======================


Iterable validation
------------------------------------

For indexing pipelines that accept iterators, it checks the fields of the first element. You need
to first wrap `inp` in `pta.utils.peekable()` for this to work.

.. code-block:: python
    :caption: Iterable input validation in a Transformer

    import pyterrier_alpha as pta
    my_iterator = [{'docno': 'doc1'}, {'docno': 'doc2'}, {'docno': 'doc3'}]
    my_iterator = pta.utils.peekable(my_iterator)
    pta.validate.columns_iter(my_iterator, includes=['docno']) # passes
    pta.validate.columns_iter(my_iterator, includes=['docno', 'toks']) # raises errors

Advanced Usage
------------------------------------------

Sometimes a transformer has multiple acceptable input specifications, e.g., if
it can act as either a retriever (with a query input) or re-ranker (with a result input).
In this case, you can specify multiple possible configurations in a `with pta.validate.any(inpt) as v:` block:

.. code-block:: python
    :caption: Validation with multiple acceptable input specifications

    def MyTransformer(pt.Transformer):
        def transform(self, inp: pd.DataFrame):
            # e.g., expects a query frame with query_vec
            with pta.validate.any(inp) as v:
                v.query_frame(extra_columns=['query'], mode='retrieve')
                v.result_frame(extra_columns=['query', 'text'], mode='rerank')
            # raises an error if ALL specifications do not match
            # v.mode is set to the FIRST specification that matches
            if v.mode == 'retrieve':
                ...
            if v.mode == 'rerank':
                ...

API Documentation
---------------------------------------------------------

.. autofunction:: pyterrier_alpha.validate.columns

.. autofunction:: pyterrier_alpha.validate.query_frame

.. autofunction:: pyterrier_alpha.validate.result_frame

.. autofunction:: pyterrier_alpha.validate.document_frame

.. autofunction:: pyterrier_alpha.validate.columns_iter

.. autofunction:: pyterrier_alpha.validate.any

.. autofunction:: pyterrier_alpha.validate.any_iter
