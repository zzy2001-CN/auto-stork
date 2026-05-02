from stork_agent.models import PaperItem
from stork_agent.storage.sqlite import SQLiteStore


def test_sqlite_store_saves_papers_and_runs(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "agent.sqlite3")
    try:
        store.save_papers([PaperItem(title="Paper", doi="10.1/test")])
        store.save_daily_run("2026-05-02", "default", 1)
        assert "10.1/test" in store.seen_keys()
    finally:
        store.close()
