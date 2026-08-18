from __future__ import annotations

import os
import tempfile

from contextlib import contextmanager
from pathlib import Path

from doc_process.models import Document


@contextmanager
def materialize_original_document(
    document: Document,
):
    """
    Local:
        return the original FileField path.

    Production:
        write BinaryField bytes to the platform temporary directory.
    """

    # Production / DB-backed file
    if document.original_file_data:
        suffix = Path(
            document.original_filename or "document.docx"
        ).suffix or ".docx"

        fd, temp_path = tempfile.mkstemp(
            suffix=suffix,
        )

        try:
            with os.fdopen(fd, "wb") as temp_file:
                temp_file.write(
                    bytes(document.original_file_data)
                )

            yield Path(temp_path)

        finally:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass

        return

    # Local filesystem
    if document.original_file:
        yield Path(document.original_file.path)
        return

    raise ValueError(
        "DOCX document has neither original_file "
        "nor original_file_data."
    )