from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import CountryCreate, CountryOut, CountryUpdate

router = APIRouter(prefix="/countries", tags=["countries"])


def _row_to_country(row: dict) -> CountryOut:
    return CountryOut(
        country_id=row["country_id"],
        country_name=row["country_name"],
        country_code=row["country_code"],
        currency_id=row["currency_id"],
        currency_name=row.get("currency_name"),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _ensure_currency_exists(cursor, currency_id: int) -> None:
    cursor.execute(
        "SELECT currency_id FROM currencies WHERE currency_id = %s",
        (currency_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected currency does not exist")


@router.get("", response_model=list[CountryOut])
def list_countries(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT c.country_id, c.country_name, c.country_code, c.currency_id,
                           cur.currency_name, c.status, c.created_at, c.updated_at
                    FROM countries c
                    LEFT JOIN currencies cur ON cur.currency_id = c.currency_id
                    WHERE c.country_name LIKE %s
                       OR c.country_code LIKE %s
                       OR cur.currency_name LIKE %s
                    ORDER BY c.country_id
                    """,
                    (term, term, term),
                )
            else:
                cursor.execute(
                    """
                    SELECT c.country_id, c.country_name, c.country_code, c.currency_id,
                           cur.currency_name, c.status, c.created_at, c.updated_at
                    FROM countries c
                    LEFT JOIN currencies cur ON cur.currency_id = c.currency_id
                    ORDER BY c.country_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_country(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{country_id}", response_model=CountryOut)
def get_country(country_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT c.country_id, c.country_name, c.country_code, c.currency_id,
                       cur.currency_name, c.status, c.created_at, c.updated_at
                FROM countries c
                LEFT JOIN currencies cur ON cur.currency_id = c.currency_id
                WHERE c.country_id = %s
                """,
                (country_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Country not found")
            return _row_to_country(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=CountryOut, status_code=201)
def create_country(payload: CountryCreate):
    country_name = payload.country_name.strip()
    country_code = payload.country_code.strip().upper()

    if not country_name or not country_code:
        raise HTTPException(
            status_code=400,
            detail="Country Name and Country Code are required",
        )

    try:
        with db_cursor() as cursor:
            _ensure_currency_exists(cursor, payload.currency_id)
            cursor.execute(
                """
                INSERT INTO countries (country_name, country_code, currency_id, status)
                VALUES (%s, %s, %s, %s)
                """,
                (country_name, country_code, payload.currency_id, payload.status.value),
            )
            new_country_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT c.country_id, c.country_name, c.country_code, c.currency_id,
                       cur.currency_name, c.status, c.created_at, c.updated_at
                FROM countries c
                LEFT JOIN currencies cur ON cur.currency_id = c.currency_id
                WHERE c.country_id = %s
                """,
                (new_country_id,),
            )
            row = cursor.fetchone()
            return _row_to_country(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Country Name or Country Code already exists",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{country_id}", response_model=CountryOut)
def update_country(country_id: int, payload: CountryUpdate):
    country_name = payload.country_name.strip()
    country_code = payload.country_code.strip().upper()

    if not country_name or not country_code:
        raise HTTPException(
            status_code=400,
            detail="Country Name and Country Code are required",
        )

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT country_id FROM countries WHERE country_id = %s",
                (country_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Country not found")

            _ensure_currency_exists(cursor, payload.currency_id)
            cursor.execute(
                """
                UPDATE countries
                SET country_name = %s, country_code = %s, currency_id = %s, status = %s
                WHERE country_id = %s
                """,
                (
                    country_name,
                    country_code,
                    payload.currency_id,
                    payload.status.value,
                    country_id,
                ),
            )
            cursor.execute(
                """
                SELECT c.country_id, c.country_name, c.country_code, c.currency_id,
                       cur.currency_name, c.status, c.created_at, c.updated_at
                FROM countries c
                LEFT JOIN currencies cur ON cur.currency_id = c.currency_id
                WHERE c.country_id = %s
                """,
                (country_id,),
            )
            row = cursor.fetchone()
            return _row_to_country(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Country Name or Country Code already exists",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{country_id}", status_code=204)
def delete_country(country_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM countries WHERE country_id = %s",
                (country_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Country not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
