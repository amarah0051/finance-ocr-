from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_dir: Path = Path(__file__).resolve().parents[3]
    template_path: Path = Path(__file__).resolve().parents[3] / "templates" / "template.xlsx"
    db_path: Path = Path(__file__).resolve().parents[2] / "data" / "app.db"
    uploads_dir: Path = Path(__file__).resolve().parents[2] / "data" / "uploads"
    outputs_dir: Path = Path(__file__).resolve().parents[2] / "data" / "outputs"
    temp_dir: Path = Path(__file__).resolve().parents[2] / "data" / "tmp"
    retention_days: int = 30


settings = Settings()
