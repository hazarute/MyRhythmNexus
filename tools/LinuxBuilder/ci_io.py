from pathlib import Path
from typing import Iterable


def is_binary(p: Path, blocksize: int = 1024) -> bool:
    try:
        with p.open('rb') as fh:
            chunk = fh.read(blocksize)
        return b'\x00' in chunk
    except Exception:
        return True


def normalize_crlf_file(p: Path) -> None:
    try:
        data = p.read_bytes()
        if b'\r\n' in data:
            data = data.replace(b'\r\n', b'\n')
            p.write_bytes(data)
    except Exception:
        # best-effort; failures will be shown by callers
        pass


def normalize_crlf_in_dir(d: Path) -> None:
    if not d.exists():
        return
    for f in d.rglob('*'):
        if not f.is_file():
            continue
        if is_binary(f):
            continue
        normalize_crlf_file(f)


def write_bytes_lf(path: Path, data: bytes, mode: int | None = None) -> None:
    # ensure LF-only sequences and write as bytes
    b = data.replace(b'\r\n', b'\n')
    path.write_bytes(b)
    if mode is not None:
        try:
            path.chmod(mode)
        except Exception:
            pass


def write_text_lf(path: Path, text: str, encoding: str = 'utf-8', mode: int | None = None) -> None:
    b = text.replace('\r\n', '\n').encode(encoding)
    write_bytes_lf(path, b, mode=mode)
