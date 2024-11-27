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
    """Protocol for transformers that provide a ``transform_outputs`` method."""
    def transform_outputs(self, input_columns: List[str]) -> List[str]:
        """Returns a list of the output columns present given the ``input_columns``."""


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

    .. versionadded:: 0.11.0
    """
    if isinstance(transformer, ProvidesTransformerOutputs):
        try:
            return transformer.transform_outputs(input_columns)
        except Exception as ex:
            if strict:
                raise InspectError(f"Cannot determine outputs for {transformer} with inputs: {input_columns}") from ex
            else:
                return None

    try:
        res = transformer.transform(pd.DataFrame(columns=input_columns))
        return list(res.columns)
    except Exception as ex:
        if strict:
            raise InspectError(f"Cannot determine outputs for {transformer} with inputs: {input_columns}") from ex
        else:
            return None
