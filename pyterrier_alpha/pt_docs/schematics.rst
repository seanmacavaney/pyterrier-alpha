.. _pyterrier.schematic:

Schematics
==================================================

Schematics let you visualize :class:`~pyterrier.Transformer` objects. They are especially useful for
understanding the structure of complex pipelines and checking the whether the input/output specifications of
individual transformers are compatible with one another.

.. schematic::
    import pyterrier_alpha as pta
    index = pt.Artifact.from_hf('pyterrier/vaswani.terrier')
    dataset = pt.get_dataset('irds:vaswani')
    pta.fusion.RRFusion(
        index.bm25(),
        pt.rewrite.SDM() >> index.bm25(),
        index.bm25() >> pt.rewrite.RM3(index.index_ref()) >> index.bm25(),
    ) >> dataset.text_loader()

In notebooks (Jupyter, Colab, etc.) schematics are rendered automatically when the output of a cell is a
:class:`~pyterrier.Transformer`. You can also pass a transformer to :func:`pyterrier_alpha.schematic.draw`
to get the HTML version of the schematic directly.

The remainder of this page focuses on customizing the appearance of transformers in schematics and the underling
mechanics of schematics. These topics are not necessary if you are just want to use schematics to visualize
transformers.

Customizing a Transformer's Schematic
--------------------------------------------------------

If you have implemented your own transformer, there are several easy ways you can customize how it appears
in a schematic.

1. ``_schematic_title``: This is the short label that appears on the transformer in schematics. By default,
   it is the class name of the transformer. ``_schematic_title`` can either be a string atribute of the instance/class
   or a callable that takes input columns and returns a string. For example, you might have:

.. code-block:: python
    :caption: Example of a transformer with a schematic title

    class MyTransformer(pt.Transformer):
        _schematic_title = "Custom"
        ...

    # or

    class MyOtherTransformer(pt.Transformer):
        def _schematic_title(self, *, input_columns: Optional[List[str]]) -> str:
            # Input_columns is a list of the input columns to the transformer. This is useful if
            # your transformer behaves differently based on the input columns.
            if input_columns is not None and 'query' in input_columns:
                return "Other w/ Query"
            return "Other"
        ...

.. schematic::
    class MyTransformer(pt.Transformer):
        _schematic_title = "Custom"
        def transform(inp):
            return inp
    MyTransformer()

.. schematic::
    class MyOtherTransformer(pt.Transformer):
        def _schematic_title(self, *, input_columns):
            # Input_columns is a list of the input columns to the transformer. This is useful if
            # your transformer behaves differently based on the input columns.
            if input_columns is not None and 'query' in input_columns:
                return "Other w/ Query"
            return "Other"
        def transform(inp):
            return inp
    MyOtherTransformer()

2. ``_schematic_settings``: This is a dictionary that can contain the transformer's additional settings for display on the
   tooltip for the transfomrer in a schematic. By default, no settings are shown. ``_schematic_settings`` can either be a dictionary
   attribute of the instance/class or a callable that takes input columns and returns a dictionary. For example, you might have:

.. code-block:: python
    :caption: Example of a transformer with schematic settings

    class YetAnotherTransformer(pt.Transformer):
        def __init__(self, beta=0.2):
            self.beta = beta
        def _schematic_settings(self, *, input_columns: Optional[List[str]]) -> Dict[str, str]:
            return {"beta": self.beta}
        ...

.. schematic::
    class YetAnotherTransformer(pt.Transformer):
        def __init__(self, beta=0.2):
            self.beta = beta
        def _schematic_settings(self, *, input_columns):
            return {"beta": self.beta}
        def transform(inp):
            return inp
    YetAnotherTransformer()

3. ``subtransformers``: Some transformers call other transformers (i.e., sub-transformers). These are detected automatically
   based on any of the instance's attributes that are of type :class:`~pyterrier.Transformer`. If you want to customize
   which sub-transformers appears in a schematic, you can add a ``subtransformers`` method to the class, which should return
   a dictionary mapping to the sub-transformers. The keys of the dictionary are used as labels in the schematic.


4. ``_schematic``: This is an advanced option that returns an intermediate schematic representation of the transformer. More
   details about this can be found in the Advanced section below.

.. hint::
    Schematics use :ref:`pyterrier.inspect` to handle a transformer's input/output specification. Use :ref:`pyterrier.validate`
    to help ensure good handling of your transformer's input specifications in schematics. Meanwhile, be sure to handle cases
    where ``transform`` is called with empty frames to ensure that your transformer's output specification is also shown properly.



Advanced
--------------------------------------------------

Internally, schematics



API Documentation
--------------------------------------------------

.. autofunction:: pyterrier_alpha.schematic.draw

.. autofunction:: pyterrier_alpha.schematic.transformer_title

.. autofunction:: pyterrier_alpha.schematic.transformer_settings

.. autoclass:: pyterrier_alpha.schematic.ProvidesSchematicTitle
    :members: _schematic_title

.. autoclass:: pyterrier_alpha.schematic.ProvidesSchematicSettings
    :members: _schematic_settings
