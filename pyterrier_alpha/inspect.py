"""Module for inspecting the input/output specifications of a transformer."""
from inspect import Parameter, signature
from typing import TYPE_CHECKING, List, NamedTuple, Protocol, Tuple, Type, Union, runtime_checkable

import pandas as pd

import pyterrier_alpha as pta

if TYPE_CHECKING: # avoid cyclic import for type checking
    import pyterrier as pt


class IOSpec(NamedTuple):
    """Specification of an input/output configuration for a transformer."""
    inputs: List[str]
    outputs: List[str]
    desc: str


@runtime_checkable
class ProvidesIOSpec(Protocol):
    """Protocol for objects that provide input/output specifications."""
    def io_spec(self) -> List[IOSpec]:
        """Returns the input/output specifications of the transformer."""


def transformer_io_spec(transformer: Union[Type, 'pt.Transformer']) -> List[IOSpec]:
    """Infers the input/output specifications of a transformer.

    Args:
        transformer: The transformer to inspect, either as type that inherits from transformer or
        as an instnace of a transformer.
    """
    orig_transformer = transformer

    transformer = _coerce_transformer(transformer)

    if isinstance(transformer, ProvidesIOSpec):
        return transformer.io_spec()

    modes = None
    try:
        transformer.transform(pd.DataFrame()) # pass an empty dataframe to (hopefully) obtain a InputValidationError
    except pta.validate.InputValidationError as ex:
        modes = ex.modes
    except Exception as ex:
        raise TypeError(f'Could not infer transformer spec from {orig_transformer}') from ex

    if modes is None:
        raise TypeError(f'Could not infer transformer spec from {orig_transformer} (did not validate inputs)')

    specs = []
    for mode in modes:
        input_columns = list(mode.missing_columns)
        try:
            output = transformer.transform(pd.DataFrame(columns=input_columns))
        except Exception as ex:
            raise TypeError(f'Could not infer transformer spec from {orig_transformer} (error on empty input)') from ex
        output_columns = list(output.columns)
        specs.append(IOSpec(input_columns, output_columns, mode.mode_name))

    return specs


def artifact_sample(artifact_cls: Type) -> 'pta.Artifact':
    """Returns a sample artifact from an artifact class.

    A sample of an artifact is a small version of the artifact useful for demonstrations or simple testing.

    Samples are loaded from `macavaney/sample` on huggingface, with branch names of the the artifact's type and format.

    Args:
        artifact_cls: The artifact class to obtain a sample of.

    Raises:
        TypeError: If the artifact's type or format could not be determined, which is needed for making a sample.
    """
    artifact_type, artifact_format = artifact_type_format(artifact_cls)
    return artifact_cls.from_hf(f'macavaney/sample@{artifact_type}.{artifact_format}')


def artifact_type_format(artifact: Union[Type, 'pta.Artifact']) -> Tuple[str, str]:
    """Returns the type and format of the specified artifact.

    These values are sourced by either the ARTIFACT_TYPE and ARTIFACT_FORMAT constants of the artifact, or (if these
    are not available) by matching on the entry points.

    Returns:
        A tuple containing the artifact's type and format.

    Raises:
        TypeError: If the artifact's type or format could not be determined.
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
        raise TypeError(f'{artifact} does not provide type and format (either as constants or via entry point)')

    return artifact_type, artifact_format


def _coerce_transformer(transformer: Union[Type, 'pt.Transformer']) -> 'pt.Transformer':
    import pyterrier as pt
    if isinstance(transformer, pt.Transformer):
        return transformer
    init_signature = signature(transformer.__init__)
    args = []
    kwargs = {}
    for param in init_signature.parameters.values():
        if param.default == Parameter.empty or param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            continue # no need to deal with this parameter since it has a default value
        if param.annotation == Parameter.empty:
            raise TypeError(f'Could not infer paramter for {param!r} due to missing type annotation')
        print(param.annotation)
        if issubclass(param.annotation, pta.Artifact):
            value = artifact_sample(param.annotation)
        else:
            raise TypeError(f'Could not infer paramter for {param!r} of type {param.annotation!r}')
        if param.kind == Parameter.POSITIONAL_ONLY:
            args.append(value)
        else:
            kwargs[param.name] = value
    return transformer(*args, **kwargs)
