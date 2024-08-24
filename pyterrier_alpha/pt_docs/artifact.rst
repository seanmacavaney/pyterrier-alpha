Artifacts
=============================================

An artifact is a component stored on disk, such as an index.

Artifacts usually act as factories for transformers that use them. For example, an index artifact
may provide a ``.retriever()`` method that returns a transformer that searches the index.

You can use ``pta.Artifact.load('path/to/artifact')`` to load an artifact. The function automatically
identfies the artifact's type and initializes it:

.. code-block:: python
    :caption: Loading an Artifact

    index = pta.Artifact.load('path/to/msmarco-passage.pisa')
    # PisaIndex('path/to/msmarco-passage.pisa')
    index.bm25() # returns a BM25 PisaRetriever for the index

You can also save and load artifacts from HuggingFace Hub:

.. code-block:: python
    :caption: Save and Load an artifact from HuggingFace Hub

    # uploads the artifact to HuggingFace Hub
    index.to_hf('username/repo')

    # loads an artifact from HuggingFace Hub
    pta.Artifact.from_hf('username/repo')

API Documentation
---------------------------------------------------------

.. autoclass:: pyterrier_alpha.Artifact
    :members:
