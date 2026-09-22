from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import CurrencyCreate, CurrencyOut, CurrencyUpdate

router = APIRouter(prefix="/currencies", tags=["currencies"])


def _row_to_currency(row: dict) -> CurrencyOut:
    return CurrencyOut(
        currency_id=row["currency_id"],
        currency_name=row["currency_name"],
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.get("", response_model=list[CurrencyOut])
def list_currencies(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT currency_id, currency_name, status, created_at, updated_at
                    FROM currencies
                    WHERE currency_name LIKE %s
                    ORDER BY currency_id
                    """,
                    (term,),
                )
            else:
                cursor.execute(
                    """
                    SELECT currency_id, currency_name, status, created_at, updated_at
                    FROM currencies
                    ORDER BY currency_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_currency(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{currency_id}", response_model=CurrencyOut)
def get_currency(currency_id: str):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT currency_id, currency_name, status, created_at, updated_at
                FROM currencies
                WHERE currency_id = %s
                """,
                (currency_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Currency not found")
            return _row_to_currency(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=CurrencyOut, status_code=201)
def create_currency(payload: CurrencyCreate):
    currency_name = payload.currency_name.strip()

    if not currency_name:
        raise HTTPException(status_code=400, detail="Currency Name is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO currencies (currency_name, status)
                VALUES (%s, %s)
                """,
                (currency_name, payload.status.value),
            )
            new_currency_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT currency_id, currency_name, status, created_at, updated_at
                FROM currencies
                WHERE currency_id = %s
                """,
                (new_currency_id,),
            )
            row = cursor.fetchone()
            return _row_to_currency(row)
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Currency Name already exists",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{currency_id}", response_model=CurrencyOut)
def update_currency(currency_id: str, payload: CurrencyUpdate):
    currency_name = payload.currency_name.strip()
    if not currency_name:
        raise HTTPException(status_code=400, detail="Currency Name is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT currency_id FROM currencies WHERE currency_id = %s",
                (currency_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Currency not found")

            cursor.execute(
                """
                UPDATE currencies
                SET currency_name = %s, status = %s
                WHERE currency_id = %s
                """,
                (currency_name, payload.status.value, currency_id),
            )
            cursor.execute(
                """
                SELECT currency_id, currency_name, status, created_at, updated_at
                FROM currencies
                WHERE currency_id = %s
                """,
                (currency_id,),
            )
            row = cursor.fetchone()
            return _row_to_currency(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Currency Name already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{currency_id}", status_code=204)
def delete_currency(currency_id: str):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM currencies WHERE currency_id = %s",
                (currency_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Currency not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
