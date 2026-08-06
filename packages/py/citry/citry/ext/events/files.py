"""
The neutral uploaded-file type of the ``events`` extension.

Custom payload codecs and transports can represent file uploads with
``UploadedFile`` values. The class is Citry's framework-neutral shape, so
handler code does not change when the app moves between hosts; the host's
original object stays reachable through ``native``. Citry's built-in codecs do
not parse multipart request bodies.
"""

from __future__ import annotations

import shutil
from io import SEEK_END
from pathlib import Path
from typing import IO, Any


class UploadedFile:
    """
    One file received by an event handler, independent of the web framework.

    Payload codecs and custom transports can construct this neutral wrapper so
    handler code does not depend on a host framework's file type. Reading is
    synchronous: plain handlers run in a worker thread under ASGI, so a plain
    ``read()`` cannot stall the event loop.

    Citry's built-in payload codecs do not parse multipart request bodies. Use
    this type with a custom codec or transport that supplies the file values.

    Attributes:
        filename: The file name the client sent (never a trusted path).
        size: The file size in bytes.
        content_type: The content type the client sent, or ``None`` when the
            request did not carry one.
        native: The host framework's own file object (e.g. Django's
            ``UploadedFile`` or Starlette's ``UploadFile``), for the rare
            case a handler needs a host-specific capability; ``None`` when
            there is no host object.

    Example:
        ```python
        class AvatarIn:
            avatar: UploadedFile

        class Profile(Component):
            class Events:
                def upload_avatar(self, data: AvatarIn):
                    data.avatar.save(MEDIA_DIR / f"{uuid4()}.png")
        ```

    """

    def __init__(
        self,
        file: IO[bytes],
        *,
        filename: str,
        size: int | None = None,
        content_type: str | None = None,
        native: Any = None,
    ) -> None:
        """
        Wrap a binary file object as an uploaded file.

        Args:
            file: The binary file object holding the content, positioned
                anywhere (a seekable file is rewound before full reads).
            size: The size in bytes; measured from ``file`` when omitted and
                the file is seekable.
            filename: The client-sent file name.
            content_type: The client-sent content type, if any.
            native: The host framework's own file object, if any.

        """
        self.file = file
        self.filename = filename
        self.content_type = content_type
        self.native = native
        if size is None and file.seekable():
            file.seek(0, SEEK_END)  # to the end, to measure
            size = file.tell()
            file.seek(0)
        self.size = size

    def read(self, size: int = -1) -> bytes:
        """
        Read the file's content, synchronously.

        A full read (no ``size``) always returns the whole content: a
        seekable file is rewound first, so calling ``read()`` twice returns
        the content twice. A partial ``read(n)`` reads the next ``n`` bytes
        from the current position, like any Python file.

        Args:
            size: How many bytes to read; the whole content when negative.

        Returns:
            The bytes read.

        """
        if size < 0 and self.file.seekable():
            self.file.seek(0)
        return self.file.read(size)

    def save(self, path: str | Path) -> Path:
        """
        Write the file's whole content to ``path``.

        A seekable file is rewound first, so ``save()`` writes the full
        content regardless of earlier reads. The parent directory must
        already exist.

        Args:
            path: Where to write the file.

        Returns:
            The destination as a ``Path``.

        """
        destination = Path(path)
        if self.file.seekable():
            self.file.seek(0)
        with destination.open("wb") as target:
            shutil.copyfileobj(self.file, target)
        return destination

    def __repr__(self) -> str:
        return f"UploadedFile(filename={self.filename!r}, size={self.size!r}, content_type={self.content_type!r})"
