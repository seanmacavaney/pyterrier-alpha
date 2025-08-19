"""Module for inspecting pyterrier objects.

Part of pyterrier core since: TODO
"""
from pyterrier.inspect import HasTransformOutputs, InspectError, artifact_type_format, transformer_outputs

__all__ = [
    'artifact_type_format',
    'InspectError',
    'ProvidesTransformerOutputs',
    'transformer_outputs',
]

ProvidesTransformerOutputs = HasTransformOutputs # new name in core, map here for now
