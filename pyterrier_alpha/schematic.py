"""Tools for drawing schematic diagrams of PyTerrier transformers."""
import html
import uuid
from typing import List, Optional

import numpy as np
import pyterrier as pt

import pyterrier_alpha as pta

# Tools for building a structured version of a transformer schematic.


def transformer_title(transformer: pt.Transformer) -> str: # TODO: should take input_columns?
    """Returns a title for the transformer for use in schematic diagrams."""
    if hasattr(transformer, '_schematic_title'):
        if callable(transformer._schematic_title):
            return transformer._schematic_title()
        return transformer._schematic_title
    elif hasattr(transformer, '__class__') and hasattr(transformer.__class__, '__name__'):
        return transformer.__class__.__name__
    else:
        return str(transformer)


def transformer_attributes(transformer: pt.Transformer) -> str: # TODO: should take input_columns?
    """Returns a dictionary containing the transformer's attributes for use in schematic diagrams."""
    if hasattr(transformer, '_schematic_attributes'):
        return transformer._schematic_attributes()
    return {}


_INFER = object()
def transformer_schematic(
    transformer: pt.Transformer,
    input_columns: Optional[List[str]] = _INFER,
    *,
    default: bool = False,
) -> dict:
    """Builds a structured schematic of the trnasformer."""
    if not default and hasattr(transformer, '_schematic'):
        return transformer._schematic(input_columns)
    else:
        if input_columns is _INFER:
            input_columns = pta.inspect.transformer_inputs(transformer, single=True, strict=False)
        if input_columns is not None:
            output_columns = pta.inspect.transformer_outputs(transformer, input_columns, strict=False)
        else:
            output_columns = None
        result = {
            'type': 'transformer',
            'transformer': transformer,
            'title': transformer_title(transformer), # TODO: should take input_columns?
            'attributes': transformer_attributes(transformer), # TODO: should take input_columns?
            'input_columns': input_columns,
            'output_columns': output_columns,
        }
        subtransformers = pta.inspect.subtransformers(transformer)
        if subtransformers:
            labeled_pipelines = []
            for key, value in subtransformers.items():
                if isinstance(value, list):
                    for i, v in enumerate(value):
                        labeled_pipelines.append({
                            'type': 'labeled_pipeline',
                            'label': f'{key}[{i}]',
                            'pipeline': transformer_schematic(v),
                        })
                else:
                    labeled_pipelines.append({
                        'type': 'labeled_pipeline',
                        'label': key,
                        'pipeline': transformer_schematic(value),
                    })
            result['inner_schematic'] = {
                'type': 'labeled_pipelines',
                'pipelines': labeled_pipelines,
            }
        return result

# A few temporary shims:
#   (these will need to be moved to the approprate place and/or implemented correctly)

pt.terrier.Retriever._schematic_title = 'BM25'
pt.rewrite.SequentialDependence._schematic_title = 'SDM'
def _compose_schematic(self: pt.Transformer, input_columns: Optional[List[str]] = None) -> dict:
    """Builds a schematic of the Compose transformer."""
    if len(self) == 1:
        return transformer_schematic(self[0], input_columns)
    pipeline = []
    columns = input_columns
    for transformer in self:
        schematic = transformer_schematic(transformer, columns)
        pipeline.append(schematic)
        columns = schematic['output_columns']
    return {
        'type': 'pipeline',
        'transformer': self,
        'input_columns': pipeline[0]['input_columns'] if pipeline else None,
        'output_columns': pipeline[-1]['output_columns'] if pipeline else None,
        'title': None,
        'pipeline': pipeline,
    }
pt.Compose._schematic = _compose_schematic

# def _feature_union_schematic(self, input_columns: Optional[list[str]] = None) -> dict:
#     schematic = pta.schematic.transformer_schematic(self, input_columns=input_columns, default=True)
#     schematic['inner_schematic'] = {
#       'type': 'parallel',
#       'pipelines': [pta.schematic.transformer_schematic(t) for t in self._transformers],
#     }
#     return schematic
# pt._ops.FeatureUnion._schematic = _feature_union_schematic



# Tools for converting the schematic diagrams to html

_css = '''
#ID {
    padding: 16px;
    position: relative;
    min-height: 96px;
    --jp-ui-font-size1: 11px;
}

#ID .infobox {
    position: absolute;
    top: 0;
    left: 0;
    width: 256px;
    max-height: 100%;
    border: 1px solid black;
    overflow-y: auto;
    display: none;
    background: white;
    box-shadow: 0 0 4px black;
    opacity: 0.9;
    margin: 4px;
    font-size: 0.8em;
}
#ID .infobox-item {
    display: none;
}
#ID .infobox-title {
    background: black;
    color: white;
    padding: 2px 6px;
    position: sticky;
    top: 0;
}
#ID .infobox-body {
    overflow-x: auto;
}
#ID [data-infobox] {
    cursor: pointer;
}
#ID .infobox-source.transformer {
    background: rgba(100, 100, 100, 0.4);
}
#ID .infobox-source.df {
    background-color: #ddd;
}

#ID .hline {
    width: 64px;
    border-bottom: 2px solid black;
    position: relative;
}
#ID .arr-inner {
    margin-right: -6px;
}
#ID .arr-input {
    margin-right: -6px;
    width: 16px;
    margin-left: 28px;
}
#ID .arr-output {
    width: 16px;
    margin-right: 32px;
}
#ID .arr::after {
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
#ID .io-label {
    margin: 0 5px 4px 5px;
}

#ID .vline {
    border-right: 2px solid black;
    position: relative;
    margin-right: -2px;
    margin-left: -2px;
}

#ID .df {
    display: inline-block;
    width: 28px;
    height: 28px;
    font-size: 14px;
    border: 3px double black;
    background-color: white;
    box-sizing: border-box;
    border-radius: 3px;
    text-align: center;
    line-height: 1;
    padding-top: 3px;
    font-weight: bold;
}
#ID .df.df-alert {
    border-color: #a35;
    color: #a35;
}
#ID .arr > .df {
    position: absolute;
    top: -14px;
    left: 18px;
}
#ID .arr-input > .df {
    left: -28px;
}
#ID .arr-output > .df {
    left: 22px;
}
#ID .df-columns {
    margin-bottom: 0;
    min-width: 100%;
}
#ID .df-columns td, #ID .df-columns th {
    border-top: 1px solid black;
    background: white;
    text-align: left;
    padding: 2px 2px 2px 4px;
    white-space: nowrap;
}
#ID .df-columns .add th, #ID .df-columns .add td {
    background: #ecf7ed;
}
#ID .df-columns td {
    width: 100%;
}

#ID .pipeline {
    display: flex;
    align-items: center;
    align-content: stretch;
    overflow-x: auto;
}
#ID .pipeline > * {
    flex-shrink: 0;
}

#ID .transformer {
    font-size: 14px;
    display: inline-block;
    position: relative;
    color: #333;
    background: rgba(100, 100, 100, 0.3);
    box-sizing: border-box;
    padding: 4px 18px;
    clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 50%, calc(100% - 16px) 100%, 0 100%, 16px 50%);
}
#ID .transformer-title {
    text-align: center;
    font-weight: bold;
}

/* re-size things within a transformer block */
#ID .transformer .df {
    width: 21px;
    height: 21px;
    font-size: 12px;
    padding-top: 1px;
}
#ID .transformer .hline {
    width: 34px;
}
#ID .transformer .transformer {
    font-size: 12px;
    padding: 2px 18px;
}
#ID .transformer .hline > .df {
    position: absolute;
    top: -10px;
    left: 6px;
}
#ID .transformer .arr-input {
    margin-left: 8px;
}

.inner-schematic {
    display: flex;
    flex-direction: column;
}

#ID .parallel-scaffold {
    display: grid;
    grid-template-areas:
      "larr title rarr"
      "larr body  rarr";
}
#ID .parallel-scaffold > .hline {
    grid-area: larr;
    align-self: center;
    width: 16px;
}
#ID .parallel-scaffold > .hline.arr {
    grid-area: rarr;
    margin-right: -8px;
}
#ID .parallel-scaffold > .transformer-title {
    grid-area: title;
}
#ID .parallel-scaffold > .inner-schematic {
    grid-area: body;
}

#ID .parallel-item {
    display: flex;
    align-content: stretch;
    justify-content: stretch;
}
#ID .parallel-item:first-child > .vline {
    height: 50%;
    align-self: end;
}
#ID .parallel-item:last-child > .vline {
    height: 50%;
    align-self: start;
}
#ID .parallel-item > .pipeline {
    flex-grow: 1;
    margin: 4px 0;
}
'''

_js = '''
(function () {
    var infobox_stick = null;
    var infobox_source_el = null;
    const infobox_items = {};
    const infobox = document.querySelectorAll('#ID .infobox')[0];
    const infobox_title = document.querySelectorAll('#ID .infobox-title')[0];
    const infobox_body = document.querySelectorAll('#ID .infobox-body')[0];
    const container = document.querySelectorAll('#ID')[0];
    function replace_infobox(el) {
        if (infobox_source_el !== null) {
            infobox_source_el.classList.remove('infobox-source');
            infobox_source_el = null;
        }
        infobox_body.innerHTML = '';
        infobox_title.textContent = infobox_items[el.dataset.infobox].dataset.title || '';
        infobox.style.display = 'block';
        infobox_body.appendChild(infobox_items[el.dataset.infobox]);
        infobox.scrollTop = 0;
        infobox_body.scrollLeft = 0;
        const infRect = infobox.getBoundingClientRect();
        const contRect = container.getBoundingClientRect();
        const elRect = el.getBoundingClientRect();
        if (elRect.left - contRect.left > infRect.width + 14) {
        // move the infobox to the immediate left/right of this element, depending on where there is space
            infobox.style.left = (elRect.left - contRect.left - infRect.width - 10) + 'px';
        } else {
            infobox.style.left = (elRect.right - contRect.left + 2) + 'px';
        }
        // Move to top of this element (if there is vertical space, otherwise as cloase as possible)
        var top = elRect.top - contRect.top;
        if (top + infRect.height > contRect.height) {
            top = contRect.height - infRect.height;
        }
        infobox.style.top = top + 'px';
        infobox_source_el = el;
        el.classList.add('infobox-source');
    }
    function hide_infobox() {
        if (infobox_source_el !== null) {
            infobox_source_el.classList.remove('infobox-source');
            infobox_source_el = null;
        }
        infobox_stick = null;
        infobox.style.display = 'none';
        infobox.style.opacity = '';
    }
    container.addEventListener('click', () => {
        if (infobox_stick) {
            hide_infobox();
        }
    });
    document.querySelectorAll('#ID .infobox-item').forEach(el => {
        el.remove();
        el.style.display = 'block';
        infobox_items[el.id] = el;
    });
    document.querySelectorAll('#ID [data-infobox]').forEach(el => {
        el.addEventListener('mouseenter', () => {
            if (!infobox_stick) {
                replace_infobox(el);
            }
        });
        el.addEventListener('mouseleave', () => {
            if (!infobox_stick) {
                hide_infobox();
            }
        });
        el.addEventListener('click', (e) => {
            if (!infobox_stick) {
                infobox_stick = el.dataset.infobox;
                infobox.style.opacity = 1;
                infobox_stick = el.dataset.infobox;
                replace_infobox(el);
                e.stopPropagation();
            } else if (infobox_stick === el.dataset.infobox) {
                hide_infobox();
                e.stopPropagation();
            } else {
                infobox_stick = el.dataset.infobox;
                replace_infobox(el);
                e.stopPropagation();
            }
        });
    });
})();
'''

def draw_html_transformer(transformer: pt.Transformer) -> str:
    """Draws a transformer as an HTML schematic."""
    return draw_html_schematic(transformer_schematic(transformer))

draw = draw_html_transformer

def draw_html_schematic(schematic: dict) -> str:
    """Draws a structured schematic as an HTML representation."""
    uid = str(uuid.uuid4())
    css = _css.replace('#ID', f'#id-{uid}')
    js = _js.replace('#ID', f'#id-{uid}')
    return f'''
    <div id="id-{uid}">
        <style>{css}</style>
        {_draw_html_schematic(schematic)}
        <div class="infobox">
            <div class="infobox-title"></div>
            <div class="infobox-body"></div>
        </div>
        <script>{js}</script>
    </div>
    '''


def _draw_html_schematic(schematic: dict, *, mode: str = 'outer') -> None:
    if schematic['type'] == 'transformer':
        return _draw_html_schematic({
            'type': 'pipeline',
            'transformer': schematic['transformer'],
            'input_columns': schematic.get('input_columns'),
            'output_columns': schematic.get('output_columns'),
            'title': None,
            'pipeline': [schematic],
        }, mode=mode)
    if schematic['type'] == 'pipeline':
        result = '<div class="pipeline">'
        if mode == 'outer':
            result += '<div class="io-label">Input</div>'
            result += f'<div class="hline arr arr-input">{_draw_df_html(schematic["input_columns"])}</div>'
        elif mode == 'inner_linked':
            result += '<div class="hline arr arr-inner" style="width: 16px;"></div>'
        elif mode == 'inner_labeled':
            result += f'<div class="hline arr arr-input">{_draw_df_html(schematic["input_columns"])}</div>'
        columns = schematic["input_columns"]
        for i, record in enumerate(schematic['pipeline']):
            assert record['input_columns'] == columns
            assert record['type'] == 'transformer'
            uid = str(uuid.uuid4())
            infobox = ''
            infobox_attr = ''
            if 'transformer' in record:
                doc_url = pta.documentation.url_for_class(record["transformer"])
                cls_name = f'{record["transformer"].__class__.__module__}.{record["transformer"].__class__.__name__}'
                if cls_name.startswith('pyterrier.'):
                    cls_name = 'pt.' + cls_name[len('pyterrier.'):]
                attrs = ''
                if record['attributes']:
                    attr_rows = []
                    for key, value in record['attributes'].items():
                        attr_rows.append(f'<tr><th>{html.escape(key)}</th><td>{html.escape(str(value))}</td></tr>')
                    attrs = f'<table class="df-columns">{"".join(attr_rows)}</table>'
                infobox = f'''
                <div class="infobox-item" id="id-{uid}" data-title="Transformer">
                    <div style="font-family: monospace; padding: 3px 6px;">
                        {'<a href="' + doc_url + '" target="_blank">' if doc_url else ''}
                        {cls_name}
                        {'</a>' if doc_url else ''}
                    </div>
                    {attrs}
                </div>
                '''
                infobox_attr = f'data-infobox="id-{uid}"'
            if 'inner_schematic' in record:
                if record['inner_schematic']['type'] == 'linked_pipelines':
                    result += f'''
                    <div class="transformer parallel-scaffold" {infobox_attr}>
                        {infobox}
                        <div class="hline"></div>
                        <div class="transformer-title">{html.escape(record["title"])}</div>
                        <div class="inner-schematic inner-linked">
                            {_draw_html_schematic(record["inner_schematic"], mode='inner_linked')}
                        </div>
                        <div class="hline arr"></div>
                    </div>
                    '''
                elif record['inner_schematic']['type'] == 'labeled_pipelines':
                    result += f'''
                    <div class="transformer" {infobox_attr}>
                        {infobox}
                        <div class="transformer-title">{html.escape(record["title"])}</div>
                        <div class="inner-schematic inner-labeled">
                            {_draw_html_schematic(record["inner_schematic"], mode='inner_labeled')}
                        </div>
                    </div>
                    '''
            else:
                result += f'''
                <div class="transformer" {infobox_attr}>
                    {infobox}
                    <div class="transformer-title">{html.escape(record["title"])}</div>
                </div>
                '''
            if i != len(schematic['pipeline']) - 1:
                result += f'<div class="hline arr arr-inner">{_draw_df_html(record["output_columns"], record["input_columns"])}</div>'
            columns = record['output_columns']
        if mode == 'outer':
            result += f'<div class="hline arr arr-output">{_draw_df_html(schematic["output_columns"], schematic["pipeline"][-1]["input_columns"])}</div>'
            result += '<div class="io-label">Output</div>'
        elif mode == 'inner_linked':
            result += f'<div class="hline" style="flex-grow: 1;">{_draw_df_html(schematic["output_columns"], schematic["pipeline"][-1]["input_columns"])}</div>'
        elif mode == 'inner_labeled':
            result += f'<div class="hline arr arr-output">{_draw_df_html(schematic["output_columns"], schematic["pipeline"][-1]["input_columns"])}</div>'
        result += '</div>'
        return result
    if schematic['type'] == 'linked_pipelines':
        result = ''
        for i, record in enumerate(schematic['pipelines']):
            result += '<div class="parallel-item"><div class="vline"></div>' + _draw_html_schematic(record, mode=mode) + '<div class="vline"></div></div>'
        return result
    if schematic['type'] == 'labeled_pipelines':
        result = ''
        for pipeline in schematic['pipelines']:
            result += _draw_html_schematic(pipeline, mode=mode)
        return result
    if schematic['type'] == 'labeled_pipeline':
        return f'<div><b>{schematic["label"]}:</b></div>' + _draw_html_schematic(schematic['pipeline'], mode=mode)
    return result + '</div>'


def _draw_df_html(columns: Optional[List[str]], prev_columns: Optional[List[str]] = None) -> str:
    """Draws a DataFrame as an HTML table."""
    df_label = '?'
    df_label_long = 'Unknown Frame'
    df_class = ''
    if columns is None:
        columns = []
        df_class = ' df-alert'
    elif 'qid' in columns and 'docno' in columns:
        df_label = 'R'
        df_label_long = 'Result Frame'
    elif 'qid' in columns:
        df_label = 'Q'
        df_label_long = 'Query Frame'
    elif 'docno' in columns:
        df_label = 'D'
        df_label_long = 'Document Frame'
    uid = str(uuid.uuid4())
    if columns:
        column_rows = []
        for col in columns:
            col_info = pta.documentation.column_info(col) or {}
            col_desc = ''
            type_name = ''
            if 'type' in col_info:
                type_name = str(col_info['type'])
                if col_info['type'] == np.array:
                    type_name = 'np.array'
                elif hasattr(col_info['type'], '__name__'):
                    type_name = col_info['type'].__name__
                type_name = f'<span style="font-family: monospace;">{html.escape(type_name)}</span>'
            if 'phrase' in col_info:
                col_desc += f'<i>({html.escape(col_info["phrase"])})</i> '
            if 'short_desc' in col_info:
                col_desc += f'{html.escape(col_info["short_desc"])} '
            is_added = prev_columns and col not in prev_columns
            column_rows.append(f'''
                <tr class="{"add" if is_added else ""}">
                    <th>{html.escape(col)}</th>
                    <td>{type_name}</td>
                    <td>{col_desc}</td>
                </tr>
            ''')
        col_table = f'''
        <div id="id-{uid}" class="infobox-item" data-title="{df_label_long}">
            <table class="df-columns">
                {''.join(column_rows)}
            </table>
        </div>'''
    else:
        col_table = f'''
        <div id="id-{uid}" class="infobox-item" data-title="{df_label_long}">
            <div style="margin: 4px; color: #a35; font-weight: bold;">Unknown/incompatible columns</div>
        </div>'''
    return f'<div class="df {df_class}" data-infobox="id-{uid}">{df_label}{col_table}</div>'


pt.Transformer._repr_html_ = draw
pt.terrier.rewrite.RM3._schematic_attributes = lambda x: {'fb_docs': x.fb_docs, 'fb_terms': x.fb_terms}
