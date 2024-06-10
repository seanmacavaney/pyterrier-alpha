# pyterrier-alpha

Alpha channel of features for [PyTerrier](https://github.com/terrier-org/pyterrier).

Features in ths package are under development and intend to be merged with the main package or split into a separate package when stable.

## Getting Started

```bash
pip install pyterrier-alpha
```

Import `pyterrier_alpha` alongside `pyterrier`:

```python
import pyterrier as pt
import pyterrier_alpha as pta
```

## `pta.validate`

It's a good idea to check the input to a transformer to make sure its compatible before you start using it.
`pta.validate` provides functions for this.

```python
def MyTransformer(pt.Transformer):
    def transform(self, inp: pd.DataFrame):
        # e.g., expects a query frame with query_vec
        pta.validate.query_frame(inp, extra_columns=['query_vec'])
        # raises an error if the specification doesn't match
```

| Function | Must have column(s) | Must NOT have column(s) |
|----------|---------------------|-------------------------|
| `pta.validate.query_frame(inp, extra_columns=...)` | qid + `extra_columns` | docno |
| `pta.validate.document_frame(inp, extra_columns=...)` | docno + `extra_columns` | qid |
| `pta.validate.result_frame(inp, extra_columns=...)` | qid + docno + `extra_columns` | |
| `pta.validate.columns(inp, includes=..., excludes=...)` | `includes` | `excludes` |

<details>

<summary>Advanced Usage (click to expand)</summary>

Sometimes a transformer has multiple acceptable input specifications, e.g., if
it can act as either a retriever (with a query input) or re-ranker (with a result input).
In this case, you can specify multiple possible configurations in a `with pta.validate.any(inpt) as v:` block:

```python
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
```

</details>
