"""Module for inspecting pyterrier objects."""
from typing import List, Optional, Protocol, runtime_checkable

import pandas as pd
import pyterrier as pt
from pyterrier.inspect import artifact_type_format

import pyterrier_alpha as pta

__all__ = [
    'artifact_type_format',
    'InspectError',
    'ProvidesTransformerOutputs',
    'transformer_outputs',
]


try:
    from pyterrier.inspect import InspectError
except ImportError:
    class InspectError(TypeError):
        """Base exception for inspection errors."""
        pass


@runtime_checkable
class ProvidesTransformerOutputs(Protocol):
    """Protocol for transformers that provide a ``transform_outputs`` method.

    ``transform_outputs`` allows for inspection of the outputs of transformers without needing to run it.

    When this method is present in a :class:`~pyterrier.Transformer` object, it must return a
    list of the output columns present given the provided input columns or raise an ``InputValidationError``
    if the inputs are not accepted by the transformer.

    This method need not be present in Transformer - it is an optional extension;
    an alternative is that the output columns are determined by calling the transformer
    with an empty ``DataFrame``.

    Due to risks and maintanence burden in ensuring that ``transform`` and ``transform_outputs`` behave identically,
    it is recommended to only implement ``transform_outputs`` when calling the transformer with an empty DataFrame to
    inspect the behavior is undesireable, e.g., if calling the transformer is expensive.

    .. code-block:: python
        :caption: Example ``transform_output`` function,
            implementing :class:`~pyterrier_alpha.inspect.ProvidesTransformerOutputs`.

        class MyRetriever(pt.Transformer):

            def transform(self, inp: pd.DataFrame) -> pd.DataFrame:
                pta.validate.query_frame(inp, ['query'])
                # ... perform retrieval ...
                # return the same columns as inp plus docno, score, and rank. E.g., using DataFrameBuilder.

            def transform_outputs(self, input_columns: List[str]) -> List[str]:
                pta.validate.query_frame(input_columns, ['query'])
                return input_columns + ['docno', 'score', 'rank']

    """
    def transform_outputs(self, input_columns: List[str]) -> List[str]:
        """Returns a list of the output columns present given the ``input_columns``.

        The method must return exactly the same output columns as ``transform`` would given the provided input
        columns. If the input columns are not accepted by the transformer, the method should raise an
        ``InputValidationError`` (e.g., through ``pta.validate``).

        Args:
            input_columns: A list of the columns present in the input frame.

        Returns:
            A list of the columns present in the output for this transformer given ``input_columns``.

        Raises:
            pta.validate.InputValidationError: If the input columns are not accepted by the transformer.
        """


def transformer_outputs(
    transformer: pt.Transformer,
    input_columns: List[str],
    *,
    strict: bool = True,
) -> Optional[List[str]]:
    """Infers the output columns for a transformer based on the inputs.

    The method first checks if the transformer provides a ``transform_outputs`` method. If it does, this method is
    called and the result is returned. If the transformer does not provide this method, the method tries to infer the
    outputs by calling the transformer with an empty DataFrame.

    Args:
        transformer: An instance of the transformer to inspect.
        input_columns: A list of the columns present in the input frame.
        strict: If True, raises an error if the transformer cannot be inferred or are not accepted. If False, returns
            None in these cases.

    Returns:
        A list of the columns present in the output for ``transformer`` given ``input_columns``.

    Raises:
        InspectError: If the artifact's type or format could not be determined and ``strict==True``.
        pta.validate.InputValidationError: If input validation fails in the trnsformer and ``strict==True``.

    .. versionadded:: 0.11.0

    .. versionchanged:: 0.15.0
        Direct passthrough of ``pta.validate.InputValidationError``
    """
    if isinstance(transformer, ProvidesTransformerOutputs):
        try:
            return transformer.transform_outputs(input_columns)
        except pta.validate.InputValidationError:
            if strict:
                raise
            else:
                return None
        except Exception as ex:
            if strict:
                raise InspectError(f"Cannot determine outputs for {transformer} with inputs: {input_columns}") from ex
            else:
                return None

    try:
        res = transformer.transform(pd.DataFrame(columns=input_columns))
        return list(res.columns)
    except pta.validate.InputValidationError:
        if strict:
            raise
        else:
            return None
    except Exception as ex:
        if strict:
            raise InspectError(f"Cannot determine outputs for {transformer} with inputs: {input_columns}") from ex
        else:
            return None
