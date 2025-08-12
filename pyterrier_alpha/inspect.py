"""Module for inspecting pyterrier objects."""
from typing import List, Optional, Protocol, Tuple, Type, Union, runtime_checkable

import pandas as pd
import pyterrier as pt

import pyterrier_alpha as pta


class InspectError(TypeError):
    """Base exception for inspection errors."""
    pass


def artifact_type_format(
    artifact: Union[Type, 'pta.Artifact'],
    *,
    strict: bool = True,
) -> Optional[Tuple[str, str]]:
    """Returns the type and format of the specified artifact.

    These values are sourced by either the ``ARTIFACT_TYPE`` and ``ARTIFACT_FORMAT`` constants of the artifact, or (if
    these are not available) by matching on the entry points.

    Args:
        artifact: The artifact to inspect.
        strict: If True, raises an error if the type or format could not be determined. If False, returns None
            in these cases.

    Returns:
        A tuple containing the artifact's type and format.

    Raises:
        InspectError: If the artifact's type or format could not be determined and ``strict==True``.
    """
    artifact_type, artifact_format = None, None

    # Source #1: ARTIFACT_TYPE and ARTIFACT_FORMAT constants
    if hasattr(artifact, 'ARTIFACT_TYPE') and hasattr(artifact, 'ARTIFACT_FORMAT'):
        artifact_type = artifact.ARTIFACT_TYPE
        artifact_format = artifact.ARTIFACT_FORMAT

    # Source #2: entry point name
    if artifact_type is None or artifact_format is None:
        for entry_point in pta.io.entry_points('pyterrier.artifact'):
            if artifact.__module__.split('.')[0] != entry_point.value.split(':')[0].split('.')[0]:
                continue # only try loading entry points that share the same top-level module
            entry_point_cls = entry_point.load()
            if isinstance(artifact, type) and artifact == entry_point_cls or isinstance(artifact, entry_point_cls):
                artifact_type, artifact_format = entry_point.name.split('.', 1)
                break

    if artifact_type is None or artifact_format is None:
        if strict:
            raise InspectError(f'{artifact} does not provide type and format (either as constants or via entry point)')
        else:
            return None

    return artifact_type, artifact_format


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
        :caption: Example ``transform_output`` function, implementing
        :class:`~pyterrier_alpha.inspect.ProvidesTransformerOutputs`.

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

def transformer_inputs(
    transformer: pt.Transformer,
    *,
    strict: bool = True,
    single: bool = True
) -> Optional[List[str]]:
    """TODO implement something like transformer_outputs."""
    assert single
    assert not strict
    try:
        transformer(pd.DataFrame())
    except pta.validate.InputValidationError as ex:
        return ex.modes[0].missing_columns
    except:
        for mode in [
            ['qid', 'query'],
            ['qid', 'query', 'docno', 'score', 'rank'],
        ]:
            try:
                transformer(pd.DataFrame(columns=mode))
                return mode
            except:
                continue
