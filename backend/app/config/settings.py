import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    @property
    def is_vercel(self) -> bool:
        return os.environ.get("VERCEL") == "1"

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def data_dir(self) -> Path:
        if self.is_vercel:
            return Path("/tmp")
        return self.base_dir / "backend" / "data"

    @property
    def template_path(self) -> Path:
        return self.base_dir / "templates" / "template.xlsx"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def temp_dir(self) -> Path:
        return self.data_dir / "tmp"

    retention_days: int = 30


settings = Settings()
