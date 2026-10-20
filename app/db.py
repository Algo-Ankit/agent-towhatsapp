"""SQLite store for the demo. Swap for Postgres/Cosmos later; the function names stay the same."""
import sqlite3
import time
from contextlib import contextmanager

from .config import DB_PATH


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS vendors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,          -- WhatsApp number in E.164 without '+', e.g. 919812345678
                link_code TEXT UNIQUE       -- one-time code vendor sends to link their number
            );
            CREATE TABLE IF NOT EXISTS inventory (
                vendor_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                name TEXT NOT NULL,
                qty INTEGER NOT NULL,
                price REAL NOT NULL,
                PRIMARY KEY (vendor_id, sku)
            );
            CREATE TABLE IF NOT EXISTS processed_messages (
                wamid TEXT PRIMARY KEY,     -- Meta retries webhooks; this dedupes them
                at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pending_actions (
                phone TEXT PRIMARY KEY,     -- risky action waiting for YES
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                at REAL NOT NULL
            );
            """
        )
        # Demo seed: one vendor not yet linked, with a code to link
        c.execute(
            "INSERT OR IGNORE INTO vendors (id, name, phone, link_code) VALUES (?,?,?,?)",
            ("v_001", "Sharma Kirana Store", None, "SHARMA42"),
        )
        for sku, name, qty, price in [
            ("RICE5", "Basmati Rice 5kg", 40, 520.0),
            ("ATTA10", "Wheat Atta 10kg", 25, 410.0),
            ("OIL1", "Mustard Oil 1L", 8, 165.0),
        ]:
            c.execute(
                "INSERT OR IGNORE INTO inventory VALUES (?,?,?,?,?)",
                ("v_001", sku, name, qty, price),
            )


def already_processed(wamid: str) -> bool:
    with conn() as c:
        try:
            c.execute("INSERT INTO processed_messages VALUES (?,?)", (wamid, time.time()))
            return False
        except sqlite3.IntegrityError:
            return True


def vendor_by_phone(phone: str):
    with conn() as c:
        return c.execute("SELECT * FROM vendors WHERE phone=?", (phone,)).fetchone()


def link_vendor(phone: str, code: str):
    with conn() as c:
        v = c.execute("SELECT * FROM vendors WHERE link_code=?", (code.upper(),)).fetchone()
        if not v:
            return None
        c.execute("UPDATE vendors SET phone=?, link_code=NULL WHERE id=?", (phone, v["id"]))
        return v


def set_pending(phone, action, payload):
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO pending_actions VALUES (?,?,?,?)",
            (phone, action, payload, time.time()),
        )


def pop_pending(phone, max_age_s=600):
    with conn() as c:
        row = c.execute("SELECT * FROM pending_actions WHERE phone=?", (phone,)).fetchone()
        c.execute("DELETE FROM pending_actions WHERE phone=?", (phone,))
        if row and time.time() - row["at"] <= max_age_s:
            return row
        return None
