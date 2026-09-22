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
)
cur = conn.cursor()

cur.execute(
    "CREATE DATABASE IF NOT EXISTS mdo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)
cur.execute("USE mdo")

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS currencies (
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

# Migrate old VARCHAR currency_id to AUTO_INCREMENT INT if needed.
cur.execute(
    """
    SELECT DATA_TYPE
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'currencies'
      AND COLUMN_NAME = 'currency_id'
    """
)
row = cur.fetchone()
if row and row[0].lower() != "int":
    cur.execute(
        """
        CREATE TABLE currencies_new (
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
    cur.execute(
        """
        INSERT IGNORE INTO currencies_new (currency_name, status)
        SELECT currency_name, status FROM currencies
        WHERE currency_name IS NOT NULL AND currency_name <> ''
        """
    )
    cur.execute("DROP TABLE currencies")
    cur.execute("RENAME TABLE currencies_new TO currencies")
    print("migrated currency_id to AUTO_INCREMENT INT")

conn.commit()
cur.execute("DESCRIBE currencies")
print("tables schema:")
for item in cur.fetchall():
    print(item)
cur.close()
conn.close()
print("schema_ok")
