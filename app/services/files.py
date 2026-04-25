import os
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "doc",
    "docx",
    "ppt",
    "pptx",
}


def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(upload: FileStorage, upload_folder):
    filename = secure_filename(upload.filename or "")
    if not filename:
        raise ValueError("Nenhum arquivo selecionado")

    if not is_allowed_file(filename):
        raise ValueError("Tipo de arquivo não permitido")

    upload_dir = Path(upload_folder)
    upload_dir.mkdir(parents=True, exist_ok=True)

    unique_filename = build_unique_filename(filename)
    file_path = upload_dir / unique_filename
    upload.save(file_path)

    return unique_filename, os.fspath(file_path)


def build_unique_filename(filename):
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower()
    return f"{stem}-{uuid.uuid4().hex[:8]}{suffix}"
