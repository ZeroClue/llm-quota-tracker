import sqlite3
from pathlib import Path
from datetime import date

CONFIG_DIR = Path.home() / ".config" / "llm-tracker"


class History:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = CONFIG_DIR / "history.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_snapshots (
                    date TEXT,
                    provider TEXT,
                    remaining_quota REAL,
                    PRIMARY KEY (date, provider)
                )
            """)

    def save_snapshot(self, provider: str, remaining_quota: float):
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO daily_snapshots (date, provider, remaining_quota) VALUES (?, ?, ?)",
                (today, provider, remaining_quota),
            )

    def get_trailing_avg(self, provider: str, days: int = 7) -> list[float]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT remaining_quota FROM daily_snapshots WHERE provider = ? ORDER BY date DESC LIMIT ?",
                (provider, days),
            ).fetchall()
        return [r[0] for r in reversed(rows)]
