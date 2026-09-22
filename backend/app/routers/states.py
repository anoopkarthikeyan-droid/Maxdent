from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import StateCreate, StateOut, StateUpdate

router = APIRouter(prefix="/states", tags=["states"])


def _row_to_state(row: dict) -> StateOut:
    return StateOut(
        state_id=row["state_id"],
        state_name=row["state_name"],
        country_id=row["country_id"],
        country_name=row.get("country_name"),
        cgst_percent=float(row["cgst_percent"]),
        sgst_percent=float(row["sgst_percent"]),
        igst_percent=float(row["igst_percent"]),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _ensure_country_exists(cursor, country_id: int) -> None:
    cursor.execute(
        "SELECT country_id FROM countries WHERE country_id = %s",
        (country_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected country does not exist")


@router.get("", response_model=list[StateOut])
def list_states(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT s.state_id, s.state_name, s.country_id, c.country_name,
                           s.cgst_percent, s.sgst_percent, s.igst_percent,
                           s.status, s.created_at, s.updated_at
                    FROM states s
                    LEFT JOIN countries c ON c.country_id = s.country_id
                    WHERE s.state_name LIKE %s OR c.country_name LIKE %s
                    ORDER BY s.state_id
                    """,
                    (term, term),
                )
            else:
                cursor.execute(
                    """
                    SELECT s.state_id, s.state_name, s.country_id, c.country_name,
                           s.cgst_percent, s.sgst_percent, s.igst_percent,
                           s.status, s.created_at, s.updated_at
                    FROM states s
                    LEFT JOIN countries c ON c.country_id = s.country_id
                    ORDER BY s.state_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_state(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{state_id}", response_model=StateOut)
def get_state(state_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT s.state_id, s.state_name, s.country_id, c.country_name,
                       s.cgst_percent, s.sgst_percent, s.igst_percent,
                       s.status, s.created_at, s.updated_at
                FROM states s
                LEFT JOIN countries c ON c.country_id = s.country_id
                WHERE s.state_id = %s
                """,
                (state_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="State not found")
            return _row_to_state(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=StateOut, status_code=201)
def create_state(payload: StateCreate):
    state_name = payload.state_name.strip()
    if not state_name:
        raise HTTPException(status_code=400, detail="State is required")

    try:
        with db_cursor() as cursor:
            _ensure_country_exists(cursor, payload.country_id)
            cursor.execute(
                """
                INSERT INTO states (
                  state_name, country_id, cgst_percent, sgst_percent, igst_percent, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    state_name,
                    payload.country_id,
                    payload.cgst_percent,
                    payload.sgst_percent,
                    payload.igst_percent,
                    payload.status.value,
                ),
            )
            new_state_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT s.state_id, s.state_name, s.country_id, c.country_name,
                       s.cgst_percent, s.sgst_percent, s.igst_percent,
                       s.status, s.created_at, s.updated_at
                FROM states s
                LEFT JOIN countries c ON c.country_id = s.country_id
                WHERE s.state_id = %s
                """,
                (new_state_id,),
            )
            row = cursor.fetchone()
            return _row_to_state(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="State already exists for the selected country",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{state_id}", response_model=StateOut)
def update_state(state_id: int, payload: StateUpdate):
    state_name = payload.state_name.strip()
    if not state_name:
        raise HTTPException(status_code=400, detail="State is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT state_id FROM states WHERE state_id = %s",
                (state_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="State not found")

            _ensure_country_exists(cursor, payload.country_id)
            cursor.execute(
                """
                UPDATE states
                SET state_name = %s,
                    country_id = %s,
                    cgst_percent = %s,
                    sgst_percent = %s,
                    igst_percent = %s,
                    status = %s
                WHERE state_id = %s
                """,
                (
                    state_name,
                    payload.country_id,
                    payload.cgst_percent,
                    payload.sgst_percent,
                    payload.igst_percent,
                    payload.status.value,
                    state_id,
                ),
            )
            cursor.execute(
                """
                SELECT s.state_id, s.state_name, s.country_id, c.country_name,
                       s.cgst_percent, s.sgst_percent, s.igst_percent,
                       s.status, s.created_at, s.updated_at
                FROM states s
                LEFT JOIN countries c ON c.country_id = s.country_id
                WHERE s.state_id = %s
                """,
                (state_id,),
            )
            row = cursor.fetchone()
            return _row_to_state(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="State already exists for the selected country",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{state_id}", status_code=204)
def delete_state(state_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM states WHERE state_id = %s", (state_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="State not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
