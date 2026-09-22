import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = ROOT / "database" / "init.sql"
MYSQL = r"C:\Program Files\MariaDB 12.3\bin\mysql.exe"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def main() -> None:
    sql = SQL_FILE.read_text(encoding="utf-8")

    # Prefer local root (common Windows MariaDB install), then app user from env.
    attempts = [
        [MYSQL, "-u", "root"],
        [MYSQL, "-u", "root", f"-p{os.environ.get('MARIADB_ROOT_PASSWORD', '')}"],
    ]

    db_user = os.environ.get("DB_USER", "mdo_user")
    db_password = os.environ.get("DB_PASSWORD", "mdo_password")
    attempts.append([MYSQL, "-u", db_user, f"-p{db_password}"])

    last_error = ""
    for cmd in attempts:
        # Skip empty -p for root when password env not set in second attempt duplicate
        if cmd[-1] == "-p":
            continue
        result = run(cmd + ["-e", sql])
        if result.returncode == 0:
            # Ensure app user exists when connected as root
            if "-u" in cmd and cmd[cmd.index("-u") + 1] == "root":
                grant_sql = f"""
CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_password}';
CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_password}';
GRANT ALL PRIVILEGES ON mdo.* TO '{db_user}'@'localhost';
GRANT ALL PRIVILEGES ON mdo.* TO '{db_user}'@'%';
FLUSH PRIVILEGES;
"""
                run(cmd + ["-e", grant_sql])
            print("Database initialized successfully.")
            return
        last_error = result.stderr.strip() or result.stdout.strip()

    raise SystemExit(f"Failed to initialize database.\n{last_error}")


if __name__ == "__main__":
    main()
