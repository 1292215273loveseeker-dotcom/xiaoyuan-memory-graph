from pathlib import Path

import relate


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_db_path() -> Path:
    return project_root() / "data" / "xiaoyuan_memory.rl"


def connect(db_path: str | Path | None = None, read_only: bool = False):
    path = Path(db_path) if db_path else default_db_path()
    if not read_only:
        path.parent.mkdir(parents=True, exist_ok=True)
    return relate.connect(str(path), read_only=read_only)
