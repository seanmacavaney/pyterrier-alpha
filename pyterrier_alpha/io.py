"""Extension I/O utilities for PyTerrier."""
import io

from pyterrier.io import (
    CallbackReader,
    HashReader,
    HashWriter,
    MultiReader,
    TqdmReader,
    download,
    download_stream,
    finalized_directory,
    finalized_open,
    open_or_download_stream,
    path_is_under_base,
    pyterrier_home,
)
from pyterrier.utils import byte_count_to_human_readable

DEFAULT_CHUNK_SIZE = io.DEFAULT_BUFFER_SIZE

__all__ = [
    'finalized_open',
    'finalized_directory',
    'download',
    'download_stream',
    'open_or_download_stream',
    'HashReader',
    'HashWriter',
    'TqdmReader',
    'CallbackReader',
    'MultiReader',
    'path_is_under_base',
    'pyterrier_home',
    'byte_count_to_human_readable',
]
