import os
import io
import tempfile
import shutil
import urllib
from abc import ABC, abstractmethod
from hashlib import sha256
from contextlib import contextmanager, ExitStack
from importlib.metadata import EntryPoint
from importlib.metadata import entry_points as eps
import pyterrier as pt
from typing import Optional, Tuple

DEFAULT_CHUNK_SIZE = 16_384 # 16kb


@contextmanager
def _finalized_open_base(path: str, mode: str, open_fn) -> io.IOBase:
    assert mode in ('b', 't') # must supply either binary or text mode
    prefix = f'.{os.path.basename(path)}.tmp.'
    dirname = os.path.dirname(path)
    try:
        fd, path_tmp = tempfile.mkstemp(prefix=prefix, dir=dirname)
        os.close(fd) # mkstemp returns a low-level file descriptor... Close it and re-open the file the normal way
        with open_fn(path_tmp, f'w{mode}') as fout:
            yield fout
        os.chmod(path_tmp, 0o666) # default file umask
    except:
        os.remove(path_tmp)
        raise

    os.replace(path_tmp, path)


def finalized_open(path: str, mode: str):
    """
    Opens a file for writing, but reverts it if there was an error in the process.

    Args:
        path(str): Path of file to open
        mode(str): Either t or b, for text or binary mode

    Example:
        Returns a contextmanager that provides a file object, so should be used in a "with" statement. E.g.::

            with pt.io.finalized_open("file.txt", "t") as f:
                f.write("some text")
            # file.txt exists with contents "some text"

        If there is an error when writing, the file is reverted::

            with pt.io.finalized_open("file.txt", "t") as f:
                f.write("some other text")
                raise Exception("an error")
            # file.txt remains unchanged (if existed, contents unchanged; if didn't exist, still doesn't)
    """
    return _finalized_open_base(path, mode, open)


@contextmanager
def finalized_directory(path: str) -> str:
    prefix = f'.{os.path.basename(path)}.tmp.'
    dirname = os.path.dirname(path)
    try:
        path_tmp = tempfile.mkdtemp(prefix=prefix, dir=dirname)
        yield path_tmp
        os.chmod(path_tmp, 0o777) # default directory umask
    except:
        try:
            shutil.rmtree(path_tmp)
        except:
            raise
        raise

    os.replace(path_tmp, path)


def download(url: str, path: str, *, expected_sha256: str = None, verbose: bool = True) -> None:
    with finalized_open(path) as fout, \
         download_stream(url, expected_sha256=expected_sha256, verbose=verbose) as fin:
        while chunk := fin.read1():
            fout.write(chunk)


@contextmanager
def download_stream(url: str, *, expected_sha256: Optional[str] = None, verbose: bool = True) -> io.IOBase:
    with ExitStack() as stack:
        fin = stack.enter_context(urllib.request.urlopen(url))
        if fin.status != 200:
            raise OSError(f'Unhandled status code: {fin.status}')

        if verbose:
            total = int(fin.headers.get('Content-Length', 0)) or None
            fin = stack.enter_context(TqdmReader(fin, total=total, desc=url))

        if expected_sha256 is not None:
            fin = stack.enter_context(HashReader(fin, expected=expected_sha256))

        yield fin


@contextmanager
def open_or_download_stream(
    path_or_url: str,
    *,
    expected_sha256: Optional[str] = None,
    verbose: bool = True
) -> io.IOBase:
    if path_or_url.startswith('http://') or path_or_url.startswith('https://'):
        with download_stream(path_or_url, expected_sha256=expected_sha256, verbose=verbose) as fin:
            yield fin
    elif os.path.isfile(path_or_url):
        with ExitStack() as stack:
            fin = stack.enter_context(open(path_or_url, 'rb'))

            if verbose:
                total = os.path.getsize(path_or_url)
                fin = stack.enter_context(TqdmReader(fin, total=total, desc=path_or_url))

            if expected_sha256 is not None:
                fin = stack.enter_context(HashReader(fin, expected=expected_sha256))

            yield fin
    else:
        raise OSError(f'path or url {path_or_url!r} not found')


class _NosyReader(io.BufferedIOBase, ABC):
    def __init__(self, reader: io.IOBase):
        self.reader = reader
        self.seek = self.reader.seek
        self.tell = self.reader.tell
        self.seekable = self.reader.seekable
        self.readable = self.reader.readable
        self.writable = self.reader.writable
        self.flush = self.reader.flush
        self.isatty = self.reader.isatty

    @abstractmethod
    def on_data(self, data: bytes) -> None:
        pass

    def read1(self, size: int = -1) -> bytes:
        if size == -1:
            size = DEFAULT_CHUNK_SIZE
        chunk = self.reader.read1(min(size, DEFAULT_CHUNK_SIZE))
        self.on_data(chunk)
        return chunk

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            size = DEFAULT_CHUNK_SIZE
        chunk = self.reader.read(min(size, DEFAULT_CHUNK_SIZE))
        self.on_data(chunk)
        return chunk

    def close(self) -> None:
        self.reader.close()


class _NosyWriter(io.BufferedIOBase, ABC):
    def __init__(self, writer: io.IOBase):
        self.writer = writer
        self.seek = self.writer.seek
        self.tell = self.writer.tell
        self.seekable = self.writer.seekable
        self.readable = self.writer.readable
        self.writable = self.writer.writable
        self.flush = self.writer.flush
        self.isatty = self.writer.isatty
        self.close = self.writer.close
        self.sha256 = sha256()

    @abstractmethod
    def on_data(self, data: bytes) -> None:
        pass

    def write(self, data: bytes) -> None:
        self.writer.write(data)
        self.on_data(data)

    def replace_writer(self, writer: io.IOBase) -> None:
        self.writer = writer
        self.seek = self.writer.seek
        self.tell = self.writer.tell
        self.seekable = self.writer.seekable
        self.readable = self.writer.readable
        self.writable = self.writer.writable
        self.flush = self.writer.flush
        self.isatty = self.writer.isatty
        self.close = self.writer.close


class HashReader(_NosyReader):
    def __init__(self, reader: io.IOBase, *, hashfn=sha256, expected: Optional[str] = None):
        super().__init__(reader)
        self.hash = hashfn()
        self.expected = expected

    def on_data(self, data: bytes) -> None:
        self.hash.update(data)

    def hexdigest(self) -> str:
        return self.hash.hexdigest()

    def close(self) -> None:
        self.reader.close()
        if self.expected is not None:
            if self.expected.lower() != self.hexdigest():
                raise ValueError(f'Expected sha256 {self.expected!r} but found {self.hexdigest()!r}')


class HashWriter(_NosyWriter):
    def __init__(self, writer: io.IOBase, *, hashfn=sha256):
        super().__init__(writer)
        self.hash = hashfn()

    def on_data(self, data: bytes) -> None:
        self.hash.update(data)

    def hexdigest(self) -> str:
        return self.hash.hexdigest()


class TqdmReader(_NosyReader):
    def __init__(self, reader: io.IOBase, *, total: int = None, desc: str = None, disable: bool = False):
        super().__init__(reader)
        self.pbar = pt.tqdm(total=total, desc=desc, unit="B", unit_scale=True, unit_divisor=1024, disable=disable)

    def on_data(self, data: bytes) -> None:
        self.pbar.update(len(data))

    def close(self) -> None:
        super().close()
        self.reader.close()


class CallbackReader(_NosyReader):
    def __init__(self, reader: io.IOBase, callback):
        super().__init__(reader)
        self.callback = callback

    def on_data(self, data: bytes) -> None:
        self.callback(data)


class MultiReader(io.BufferedIOBase):
    def __init__(self, readers):
        self.readers = readers
        self._reader = next(self.readers)
        self.reader = self._reader.__enter__()
        self.seek = self.reader.seek
        self.tell = self.reader.tell
        self.seekable = self.reader.seekable
        self.readable = self.reader.readable
        self.writable = self.reader.writable
        self.flush = self.reader.flush
        self.isatty = self.reader.isatty
        self.close = self.reader.close

    def read1(self, size: int = -1) -> bytes:
        if size == -1:
            size = DEFAULT_CHUNK_SIZE
        chunk = self.reader.read1(min(size, DEFAULT_CHUNK_SIZE))
        if len(chunk) == 0:
            self.reader.close()
            try:
                self._reader = next(self.readers)
            except StopIteration:
                self._reader = None
                self.reader = None
                return chunk
            self.reader = self._reader.__enter__()
            self.pbar = self.reader.pbar
            self.seek = self.reader.seek
            self.tell = self.reader.tell
            self.seekable = self.reader.seekable
            self.readable = self.reader.readable
            self.writable = self.reader.writable
            self.flush = self.reader.flush
            self.isatty = self.reader.isatty
            self.close = self.reader.close
            chunk = self.reader.read1(min(size, DEFAULT_CHUNK_SIZE))
        return chunk

    def read(self, size: int = -1) -> bytes:
        chunk = b''
        if size == -1:
            size = DEFAULT_CHUNK_SIZE
        while len(chunk) < size and self.reader is not None:
            chunk += self.reader.read(size - len(chunk))
            if len(chunk) < size:
                self.reader.close()
                try:
                    self._reader = next(self.readers)
                except StopIteration:
                    self._reader = None
                    self.reader = None
                    return chunk
                self.reader = self._reader.__enter__()
                self.pbar = self.reader.pbar
                self.seek = self.reader.seek
                self.tell = self.reader.tell
                self.seekable = self.reader.seekable
                self.readable = self.reader.readable
                self.writable = self.reader.writable
                self.flush = self.reader.flush
                self.isatty = self.reader.isatty
                self.close = self.reader.close
        return chunk


def path_is_under_base(path: str, base: str) -> bool:
    return os.path.realpath(os.path.abspath(os.path.join(base, path))).startswith(os.path.realpath(base))


def byte_count_to_human_readable(byte_count: float) -> str:
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    while byte_count > 1024 and len(units) > 1:
        byte_count /= 1024
        units = units[1:]
    if units[0] == 'B':
        return f'{byte_count:.0f} {units[0]}'
    return f'{byte_count:.1f} {units[0]}'


def entry_points(group: str) -> Tuple[EntryPoint, ...]:
    try:
        return tuple(eps(group=group))
    except TypeError:
        return tuple(eps().get(group, tuple()))


def pyterrier_home() -> str:
    if "PYTERRIER_HOME" in os.environ:
        home = os.environ["PYTERRIER_HOME"]
    else:
        home = os.path.expanduser('~/.pyterrier')
    if not os.path.exists(home):
        os.makedirs(home)
    return home
