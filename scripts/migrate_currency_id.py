from pathlib import Path

from dotenv import load_dotenv
import mariadb
import os

load_dotenv(Path(__file__).resolve().parents[1] / "backend" / ".env", override=True)

conn = mariadb.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "mdo"),
)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS currencies_new (
      currency_id INT NOT NULL AUTO_INCREMENT,
      currency_name VARCHAR(100) NOT NULL,
      status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (currency_id),
      UNIQUE KEY uq_currencies_name (currency_name)
    )
    """
)

# Preserve existing names if the old table still has rows.
cur.execute("SHOW TABLES LIKE 'currencies'")
if cur.fetchone():
    cur.execute(
        """
        INSERT IGNORE INTO currencies_new (currency_name, status)
        SELECT currency_name, status FROM currencies
        WHERE currency_name IS NOT NULL AND currency_name <> ''
        """
    )
    cur.execute("DROP TABLE currencies")

cur.execute("RENAME TABLE currencies_new TO currencies")
conn.commit()

cur.execute("DESCRIBE currencies")
print("SCHEMA:")
for row in cur.fetchall():
    print(row)

cur.execute("SELECT currency_id, currency_name, status FROM currencies")
print("ROWS:")
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
print("migration_ok")
