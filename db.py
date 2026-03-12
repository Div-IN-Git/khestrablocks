import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "landchain.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            documents_uploaded INTEGER DEFAULT 0,
            identity_verified INTEGER DEFAULT 0,
            aadhaar_doc TEXT,
            gov_id_doc TEXT,
            property_doc TEXT,
            public_key TEXT,
            private_key TEXT,
            wallet_address TEXT,
            is_government INTEGER DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            city TEXT NOT NULL,
            zone TEXT NOT NULL,
            area_sqft INTEGER NOT NULL,
            price INTEGER NOT NULL,
            owner_wallet TEXT NOT NULL,
            sale_deed TEXT DEFAULT 'Available',
            tax_certificate TEXT DEFAULT 'Available',
            registration_status TEXT DEFAULT 'approved'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT NOT NULL,
            from_wallet TEXT NOT NULL,
            to_wallet TEXT NOT NULL,
            sale_agreement TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER NOT NULL,
            property_id TEXT NOT NULL,
            from_wallet TEXT NOT NULL,
            to_wallet TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            hash TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            sale_agreement TEXT
        )
        """
    )

    conn.commit()

    cur.execute("SELECT COUNT(*) AS count FROM blocks")
    if cur.fetchone()["count"] == 0:
        cur.execute(
            """
            INSERT INTO blocks (block_index, property_id, from_wallet, to_wallet, timestamp, hash, previous_hash, sale_agreement)
            VALUES (0, 'GENESIS', 'SYSTEM', 'SYSTEM', CURRENT_TIMESTAMP, 'genesis_hash', '0', 'N/A')
            """
        )

    cur.execute("SELECT COUNT(*) AS count FROM properties")
    if cur.fetchone()["count"] == 0:
        seed_properties = [
            ("DLX10293", "Delhi Sector 62 Plot", "Delhi", "Residential", 1200, 4500000, "0xA38DEMO001"),
            ("MUM55321", "Navi Mumbai Tower Apartment", "Mumbai", "Commercial", 950, 6700000, "0xA38DEMO002"),
            ("BLR88410", "Whitefield Villa", "Bengaluru", "Residential", 2400, 9800000, "0xA38DEMO003"),
            ("HYD77812", "Gachibowli Office Space", "Hyderabad", "Commercial", 1800, 7600000, "0xA38DEMO004"),
        ]
        cur.executemany(
            """
            INSERT INTO properties (property_id, title, city, zone, area_sqft, price, owner_wallet)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            seed_properties,
        )

    conn.commit()
    conn.close()
