"""Module for inspecting pyterrier objects."""
import html
from typing import List, Optional, Protocol, Tuple, Type, Union, runtime_checkable

import pandas as pd
import pyterrier as pt
from graphviz import Digraph
from IPython.display import SVG, display

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

def short_name(transformer):
    if hasattr(transformer, 'short_name'):
        return transformer.short_name()
    elif hasattr(transformer, '__class__') and hasattr(transformer.__class__, '__name__'):
        return transformer.__class__.__name__
    else:
        return str(transformer)


def transformer_structure(
    transformer: pt.Transformer,
    input_columns: List[str] = None,
    include_data: bool = True,
) -> dict:
    """Builds a simple structure representation of the transformer."""
    result = _transformer_structure(transformer)
    if include_data:
        result_with_data = []
        # apply data elements in between each transformer
        columns = input_columns or ['qid', 'query']
        result_with_data.append({
            'type': 'data',
            'columns': columns,
        })
        for record in result:
            result_with_data.append(record)
            columns = transformer_outputs(record['transformer'], columns, strict=False)
            result_with_data.append({
                'type': 'data',
                'columns': columns,
            })
        result = result_with_data
    return result


def _transformer_structure(
    transformer: pt.Transformer,
) -> list:
    """Builds a simple structure representation of the transformer."""
    if hasattr(transformer, 'structure'):
        return transformer.structure()
    elif isinstance(transformer, pt.Compose):
        result = []
        for inner_transformer in transformer:
            result.extend(_transformer_structure(inner_transformer))
        return result
    else:
        return [{
            'type': 'transformer',
            'transformer': transformer,
            'name': short_name(transformer),
        }]


css = '''
.outer {
    padding: 16px;
    overflow-x: auto;
    padding-bottom: 68px;
}
.arrow {
    width: 64px;
    border-bottom: 2px solid black;
    position: relative;
    margin-right: -6px;
}
.arrow.start {
    width: 32px;
}
.arrow.end {
    width: 16px;
    margin-right: 0;
}
.split-transformer-inner .arrow {
    width: 46px;
}
.split-transformer-inner .df {
    left: 8px;
}
.arrow::after {
    content: "";
    position: absolute;
    right: -4px;
    top: 1px;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-left: 6px solid black;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
}
/*.container {
    display: grid;
    grid-template-rows: auto auto;
    grid-auto-flow: column;
    grid-auto-columns: max-content;
    grid-auto-flow: column dense;
    align-items: center;
    justify-content: stretch;
}*/
.container {
    display: flex;
    align-items: center;
}
.container > * {
    flex-shrink: 0;
}

.transformer {
    display: inline-block;
    position: relative;
    padding: 0 0;
    margin: 0 18px;
    color: #333;
    background: rgba(100, 100, 100, 0.3);
    box-sizing: border-box;
    padding: 4px 2px;
}

.transformer::before,
.transformer::after {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    height: 100%;
    width: 16px;
    background: inherit;
    pointer-events: none;
    will-change: transform;
}
.transformer::before {
    left: 1px;
    transform: translateX(calc(-100% - 1px));
    clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%, 100% 50%);
}
.transformer::after {
    right: 1px;
    transform: translateX(calc(100% + 1px));
    clip-path: polygon(0 0, 100% 50%, 0 100%);
}
.df {
    position: absolute;
    display: inline-block;
    width: 28px;
    height: 28px;
    border: 3px double black;
    background-color: white;
    top: -14px;
    left: 18px;
    box-sizing: border-box;
    border-radius: 3px;
    text-align: center;
    line-height: 1;
    padding-top: 3px;
    font-weight: bold;
    cursor: help;
}
.arrow.start {
    margin-left: 12px;
}
.arrow.start .df {
    left: -12px;
}
.arrow.end {
    margin-right: 34px;
}
.arrow.end .df {
    left: 22px;
}
.df > .columns {
    visibility: hidden;
    position: absolute;
    top: 30px;
    left: 0;
    z-index: 1;
    cursor: default;
    font-weight: normal;
    margin-bottom: 0;
    box-shadow: 0 0 4px black;
}
.columns > table {
    margin-bottom: 0;
}
.df > .columns::before {
    content: "";
    position: absolute;
    left: 6px;
    bottom: 100%;
    border-width: 6px;
    border-style: solid;
    border-color: transparent transparent #333 transparent; /* triangle pointing up */
    transform: translateY(1px);
}
.df:hover > .columns {
    visibility: visible;
}
.columns th, .columns td {
    font-size: 0.8em;
    border: 1px solid #333;
    text-align: left !important;
    font-weight: normal;
}
.columns th.old {
    background-color: #333;
    color: white;
}
.columns th.new {
    background-color: #708a5a;
    color: white;
}
.columns td {
    background-color: white;
    color: black;
}
.columns .info {
    background-color: #333;
    color: white;
    white-space: nowrap;
    padding: 6px 6px;
    font-size: 0.8em;
}
.split-transformer {
    display: grid;
    grid-template-areas:
      "larr title rarr"
      "larr body  rarr";
}
.split-transformer-inner {
    display: grid;
    grid-template-columns: repeat(3, auto);
}
.inner-larr, .inner-rarr {
    width: 12px;
    border-bottom: 2px solid black;
    position: relative;
}
.inner-larr {
    flex-grow: 1;
}
.inner-rarr {
    margin-right: -6px;
}
.inner-rarr::after {
    content: "";
    position: absolute;
    right: -4px;
    top: 1px;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-left: 6px solid black;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
}
'''

def draw(transformer: pt.Transformer) -> None:
    struct = pta.inspect.transformer_structure(transformer)
    return f'<style>{css}</style><div class="outer">{_draw(struct)}</div>'


def _draw(struct: list, inp_out=True) -> None:
    result = '<div class="container">'
    prev_cols = set()
    if inp_out:
        result += '<div style="margin-right: 4px; margin-bottom: 5px;">Input</div><div></div>'
    for i, record in enumerate(struct):
        if record['type'] == 'data':
            columns = record["columns"]
            df_label = '?'
            if columns is None:
                columns = []
            elif 'qid' in columns and 'docno' in columns:
                df_label = 'R'
            elif 'qid' in columns:
                df_label = 'Q'
            elif 'docno' in columns:
                df_label = 'D'
            if columns:
                if len(prev_cols) == 0:
                    prev_cols = set(columns)
                col_table = '<div class="columns"><table><tr> ' + ''.join(f'<th class="{"old" if c in prev_cols else "new"}">{html.escape(c)}</th>' for c in columns) + '</tr><tr>' + ''.join('<td>&hellip;</td>' for c in columns) + '</tr></table></div>'
            else:
                col_table = '<div class="columns"><div class="info">Unknown/incompatible columns</div></div>'
            prev_cols = set(columns)
            clz = 'arrow'
            if i == 0:
                if inp_out:
                    clz += ' start'
                else:
                    result += '<div class="inner-rarr"></div><div></div>'
                    continue
            elif i == len(struct) - 1:
                if inp_out:
                    clz += ' end'
                else:
                    result += f'<div class="inner-larr" style="min-width: 46px;"><div class="df">{df_label}{col_table}</div></div><div></div>'
                    continue
            result += f'<div class="{clz}"><div class="df">{df_label}{col_table}</div></div>'
            result += '<div></div>'
        elif record['type'] == 'transformer':
            result += f'<div class="transformer"><div style="text-align: center;"><b>{html.escape(record["name"])}</b></div></div>'
            result += '<div></div>'
        elif record['type'] == 'split_transformer':
            result += f'''
                <div class="transformer">
                    <div class="split-transformer">
                        <div style="grid-area: larr;align-self: center;"><div class="inner-larr"></div></div>
                        <div style="grid-area: title; text-align: center;"><b>{html.escape(record["name"])}</b></div>
                        <div style="grid-area: rarr;align-self: center;"><div class="inner-rarr"></div></div>
                        <div class="split-transformer-inner" style="grid-area: body;">'''
            for i, inner_transformer in enumerate(record['inner_transformers']):
                style = ''
                if i == 0:
                    style += 'height: 50%; align-self: end;'
                elif i == len(record['inner_transformers']) - 1:
                    style += 'height: 50%; align-self: start;'
                result += f'<div style="border-left: 2px solid black; margin-right: -2px; {style}"></div>'
                result += '<div style="margin: 4px 0;">' + _draw(pta.inspect.transformer_structure(inner_transformer), inp_out=False) + '</div>'
                result += f'<div style="border-left: 2px solid black; margin-left: -2px; {style}"></div>'
            result += '</div></div></div>'
            result += '<div></div>'
    if inp_out:
        result += '<div style="margin-left: 4px; margin-bottom: 5px;">Output</div><div></div>'

    return result + '</div>'


pt.Transformer._repr_html_ = draw

pt.terrier.Retriever.short_name = lambda self: 'BM25 Retriever'
