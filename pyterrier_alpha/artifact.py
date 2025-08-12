"""PyTerrier artifact module."""
import json
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import pyterrier as pt
from pyterrier._artifact import Artifact, _hf_url_resolver

__all__ = [
    'ArtifactBuilder',
    'ArtifactBuilderMode',
    'from_url',
    'from_dataset',
    '_hf_url_resolver',
]

from_url = Artifact.from_url
from_dataset = Artifact.from_dataset


class ArtifactBuilderMode(Enum):
    """Enumeration of artifact builder modes."""
    create = 'create'
    overwrite = 'overwrite'
    append = 'append'


class ArtifactBuilder:
    """Context manager for building artifacts."""
    def __init__(
        self,
        artifact: Optional[Artifact] = None,
        *,
        mode: Union[ArtifactBuilderMode, str] = 'create',
        path: Optional[Union[str, Path]] = None,
        type: Optional[str] = None,
        format: Optional[str] = None,
        package_hint: Optional[str] = None,
    ) -> None:
        """Context manager for building artifacts."""
        if artifact is None:
            assert path is not None, "path must be provided if artifact isn't"
            assert type is not None, "type must be provided if artifact isn't"
            assert format is not None, "format must be provided if artifact isn't"
            assert package_hint is not None, "package_hint must be provided if artifact isn't"

        self.mode = ArtifactBuilderMode(mode)
        self.path = Path(path or artifact.path)

        if type is None or format is None:
            type, format = pt.inspect.artifact_type_format(artifact)

        if package_hint is None:
            if hasattr(artifact, 'ARTIFACT_PACKAGE_HINT'):
                package_hint = artifact.ARTIFACT_PACKAGE_HINT
            else:
                package_hint = artifact.__class__.__module__.split('.')[0]

        self.metadata = {
            'type': type,
            'format': format,
            'package_hint': package_hint,
        }

    def __enter__(self) -> 'ArtifactBuilder':
        # TODO: check if the path exists and either:
        if self.mode == ArtifactBuilderMode.create:
            if self.path.exists():
                raise FileExistsError(f'{str(self.path)} already exists.')
            self.path.mkdir(parents=True)
        elif self.mode == ArtifactBuilderMode.overwrite:
            if self.path.exists():
                raise NotImplementedError()
                # This might be a bit tricky... Do we recursively delete the entire
                # directory if it exists? What if the user accidently enters a path
                # such as '/'? Do we need some sort of check or warning if the path
                # is very large? Hmmm...
            else:
                self.path.mkdir(parents=True)
        elif self.mode == ArtifactBuilderMode.append:
            raise NotImplementedError()

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if exc_type is not None:
            # TODO clean up
            pass
        else:
            # Log the artifact metadata
            meta_path = self.path / 'pt_meta.json'
            try:
                with open(meta_path, 'wt') as fout:
                    json.dump(self.metadata, fout)
            except:
                if meta_path.exists():
                    meta_path.unlink()
                raise
