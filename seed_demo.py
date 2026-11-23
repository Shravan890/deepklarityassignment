"""Add the sample MUG catalog item to an empty local SQLite database."""
import sys

from tillpoint import db
from tillpoint.catalog import Catalog


def main(path):
    conn = db.connect(path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            Catalog(conn).add_product("MUG", "Mug", 1200, 10)
            print("Added demo product MUG (Mug, $12.00, 10 in stock).")
        else:
            print(f"Catalog already has {count} product(s); nothing changed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tillpoint.db")
