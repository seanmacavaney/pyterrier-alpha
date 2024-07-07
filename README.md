# pyterrier-alpha

Alpha channel of features for [PyTerrier](https://github.com/terrier-org/pyterrier).

Features in ths package are under development and intend to be merged with the main package or split into a separate package when stable.

<details>

<summary>Table of Contents</summary>

 - [Getting Started](#gettingstarted)
 - [`pta.validate`](#ptavalidate)
 - [`pta.DataFrameBuilder`](#ptadataframebuilder)
 - [`pta.Artifact`](#ptaartifact)
 - [`pta.io`](#ptaio)

</details>

## Getting Started

```bash
pip install pyterrier-alpha
```

Import `pyterrier_alpha` alongside `pyterrier`:

```python
import pyterrier as pt
import pyterrier_alpha as pta
```

## pta.validate

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

## pta.DataFrameBuilder

A common pattern in `Transformer` implementation builds up an intermediate representation of the output DataFrame,
but this can be a bit clunky, as shown below:

```python
def MyTransformer(pt.Transformer):
    def transform(self, inp: pd.DataFrame):
        result = {
            'qid': [],
            'query': [],
            'docno': [],
            'score': [],
        }
        for qid, query in zip(inp['qid'], inp['query']):
            docnos, scores = self.some_function(qid, query)
            result['qid'].append([qid] * len(docnos))
            result['query'].append([query] * len(docnos))
            result['docno'].append(docnos)
            result['score'].append(scores)
        result = pd.DataFrame({
            'qid': np.concatenate(result['qid']),
            'query': np.concatenate(result['query']),
            'docno': np.concatenate(result['docno']),
            'score': np.concatenate(result['score']),
        })
        return result
```

`pta.DataFrameBuilder` simplifies the process of building a DataFrame by removing lots of the boilerplate.
It also automatically handles various types and ensures that all columns end up with the same length.
The above example can be rewritten with `pta.DataFrameBuilder` as follows:

```python
def MyTransformer(pt.Transformer):
    def transform(self, inp: pd.DataFrame):
        result = pta.DataFrameBuilder(['qid', 'query', 'docno', 'score'])
        for qid, query in zip(inp['qid'], inp['query']):
            docnos, scores = self.some_function(qid, query)
            result.extend({
                'qid': qid, # automatically repeats to the length of this batch
                'query': query, # ditto
                'docno': docnos,
                'score': scores,
            })
        return result.to_df()
```


## pta.Artifact

Available in: `pyterrier-alpha >= 0.2.0`

An artifact is a component stored on disk, such as an index.

Artifacts usually act as factories for transformers that use them. For example, an index artifact
may provide a `.retriever()` method that returns a transformer that searches the index.

You can use `pta.Artifact.load('path/to/artifact')` to load an artifact. The function automatically
identfies the artifact's type and initializes it:

```python
index = pta.Artifact.load('path/to/msmarco-passage.pisa')
# PisaIndex('path/to/msmarco-passage.pisa')
index.bm25() # returns a BM25 PisaRetriever for the index
```

You can also save and load artifacts from HuggingFace Hub:

```python
# uploads the artifact to HuggingFace Hub
index.to_hf('username/repo')

# loads an artifact from HuggingFace Hub
pta.Artifact.from_hf('username/repo')
```

## pta.io

Available in: `pyterrier-alpha >= 0.2.0`

`pta.io` includes extra input/output utilities:

**Files/downloads/streaming:**

 - `pta.io.open_or_download_stream(path_or_url: str)`  Returns a stream of `path_or_url`, depending on whether it is a URL
   or local file path.
 - `pta.io.download_stream(url: str)` Returns a stream of `url`.
 - `pta.io.download(url: str, path: str)` Downloads `url` to `path`.
 - `pta.io.finalized_directory(path: str)` A context manager that returns a temporary directory. The directory is moved to `path`
   on successful completion of the context manager, or deleted if an exception is raised during executation.
 - `pta.io.finalized_open(path: str)` A context manager that returns a temporary file. The file is moved to `path` on successful
   completion of the context manager, or deleted if an exception is raised during executation.

**Hashing/security:**

 - `pta.io.path_is_under_base(path: str, base: str) -> bool`  tests whether `path` refers to a path under `base`. This
   is helpful to avoid tarbombing.
 - `pta.io.HashWriter(writer: io.IOBase)` is a wrapper around a `io.IOBase` that keeps track of the hash (default SHA256)
   as it is being written to (accessible as the `.hash` property).
 - `pta.io.HashReader(reader: io.IOBase, expected: Optional[str])` is a wrapper around a `io.IOBase` that keeps track of
   the hash (default SHA256) as it is being read from (accessible as the `.hash` property or the `.hexdigest()` method).
   If `expected` is provided, an error is thrown when the reader is closed if the `.hexdigest()` does not match this value.
 - `pta.io.TqdmReader(reader: io.IOBase, total: int, desc: str)` is a wrapper around a `io.IOBase` that shows a tqdm
   progress bar as the reader is being read.

**Misc:**

 - `pta.io.pyterrier_home() -> str` returns the PyTerrier home directory
 - `pta.io.byte_count_to_human_readable(byte_count: float) -> str` returns a human-readable version of a
   byte count, e.g., 4547 bytes -> "4.4 KB". Supports units from B to TB
 - `pta.io.entry_points(group: str) -> Tuple[EntryPoint, ...]` is an implementation of
   [`importlib.metadata.entry_points(group)`](https://docs.python.org/3/library/importlib.metadata.html#entry-points)
   that supports python<=3.12.
