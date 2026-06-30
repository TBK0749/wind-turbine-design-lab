"""Local SQLite design storage for each installed copy of the app."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from windlab.design_state import design_input_from_dict, design_input_to_dict
from windlab.models import SimulationInput

DEFAULT_USER_DATA_DIR = Path("user_data")
DEFAULT_DATABASE_PATH = DEFAULT_USER_DATA_DIR / "windlab.sqlite"


class DesignStore:
    """Small SQLite store for autosaved and named designs."""

    def __init__(self, database_path: Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS designs (
                    name TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    is_current INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _save(self, name: str, inputs: SimulationInput, *, is_current: bool) -> None:
        payload_json = json.dumps(design_input_to_dict(inputs), sort_keys=True)
        now = self._now()
        with self._connect() as connection:
            if is_current:
                connection.execute("UPDATE designs SET is_current = 0 WHERE is_current = 1")
            connection.execute(
                """
                INSERT INTO designs (name, payload_json, is_current, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    is_current = excluded.is_current,
                    updated_at = excluded.updated_at
                """,
                (name, payload_json, 1 if is_current else 0, now, now),
            )
            connection.commit()

    def autosave_current(self, inputs: SimulationInput) -> None:
        """Save the current working design."""

        self._save("__current__", inputs, is_current=True)

    def load_current_design(self) -> SimulationInput | None:
        """Load the current autosaved design if available."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM designs WHERE is_current = 1 LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return design_input_from_dict(json.loads(row[0]))

    def save_named_design(self, name: str, inputs: SimulationInput) -> None:
        """Save a named design."""

        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Design name cannot be blank.")
        self._save(clean_name, inputs, is_current=False)

    def load_named_design(self, name: str) -> SimulationInput | None:
        """Load a named design."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM designs WHERE name = ? AND is_current = 0",
                (name,),
            ).fetchone()
        if row is None:
            return None
        return design_input_from_dict(json.loads(row[0]))

    def list_design_names(self) -> list[str]:
        """Return saved design names in display order."""

        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name FROM designs WHERE is_current = 0 ORDER BY updated_at DESC, name"
            ).fetchall()
        return [row[0] for row in rows]
