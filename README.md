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


**Iterable validation**

Available in: `pyterrier-alpha >= 0.6.0`

For indexing pipelines that accept iterators, it checks the fields of the first element. You need
to first wrap `inp` in `pta.utils.peekable()` for this to work.

```python
import pyterrier_alpha as pta
my_iterator = [{'docno': 'doc1'}, {'docno': 'doc2'}, {'docno': 'doc3'}]
my_iterator = pta.utils.peekable(my_iterator)
pta.validate.columns_iter(my_iterator, includes=['docno']) # passes
pta.validate.columns_iter(my_iterator, includes=['docno', 'toks']) # raises error
```

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

 - `pta.io.byte_count_to_human_readable(byte_count: float) -> str` returns a human-readable version of a
   byte count, e.g., 4547 bytes -> "4.4 KB". Supports units from B to TB
 - `pta.io.entry_points(group: str) -> Tuple[EntryPoint, ...]` is an implementation of
   [`importlib.metadata.entry_points(group)`](https://docs.python.org/3/library/importlib.metadata.html#entry-points)
   that supports python<=3.12.
 - ~~`pta.io.pyterrier_home() -> str` returns the PyTerrier home directory.~~ **Moved to PyTerrier Core in 0.11.0**


## pta.RBO

Available in: `pyterrier-alpha >= 0.3.0`

`pta.RBO` provides a `ir_measures`-compatible implementation of [Rank Biased Overlap (RBO)](https://dl.acm.org/doi/10.1145/1852102.1852106).
RBO is a rank-baised correlation measure. In other words, it measures how similar two ranked lists are with one another, giving
higher priority to the top of the list. The priority is adjusted using the `p` parameter, as discussed below. Note that RBO
ignores the qrels; it only compares the current ranking with another one.

`pta.RBO` takes two parameters:
 - `other` (DataFrame): The ranked list that you want to compare against
 - `p` (float): the "persistence" parameter in the range of (0, 1), which adjusts how much priority is given to the top of
   the list. Common values include 0.9 (gives the most priority to top 10 ranks) and 0.99 (top 100).

You can use `pta.RBO` in `pt.Experiment` as follows:

```python
import pyterrier as pt
import pyterrier_alpha as pta
from ir_measures import *
pt.init()

# define your pipeline(s), dataset, etc.
... 

# get the "other" list to compare against e.g.,
other = baseline(dataset.get_topics())
# or
other = pt.io.read_results('some_result_file.res')

pt.Experiment(
    [pipeline],
    dataset.get_topics(),
    dataset.get_qrels(),
    [nDCG@10, pta.RBO(other, p=0.9), pta.RBO(other, p=0.99)]
)
```

## pta.transformer_repr

Available in: `pyterrier-alpha >= 0.4.0`

`pta.transformer_repr` provides a drop-in repr implementation for a Transformer's `__repr__`, assuming it adheres to
a few basic requirements. Namely, it should be able to be constructed using the fields it has of the same name and not
take `*args` or `**kwargs` in the constructor. For example:

```python
class MyTransformer(pt.Transformer):
    def __init__(self, a, b=5, *, other=None):
        self.a = a
        self.b = b
        self.other = other

    def transform(self, inp):
        ...

    __repr__ = pta.transformer_repr

repr(MyTransformer("hello"))
# MyTransformer("hello")
repr(MyTransformer("hello", "world"))
# MyTransformer("hello", "world")
repr(MyTransformer("hello", other=5))
# MyTransformer("hello", other=5)
```

## pta.utils.peekable

Available in: `pyterrier-alpha >= 0.6.0`

`pta.utils.peekable` returns an iterator that you can peek ahead into without advancing it.

It's most commonly used with `pta.validate.columns_iter()` to peek into the first element for validation.

```python
import pyterrier_alpha as pta
my_iterator = [{'docno': 'doc1'}, {'docno': 'doc2'}, {'docno': 'doc3'}]
my_iterator = pta.utils.peekable(my_iterator)
my_iterator.peek()
{'docno': 'doc1'}
my_iterator.peek()
{'docno': 'doc1'}
next(my_iterator)
{'docno': 'doc1'}
next(my_iterator)
{'docno': 'doc2'}
my_iterator.peek()
{'docno': 'doc3'}
```
