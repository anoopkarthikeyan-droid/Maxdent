from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import RegionCreate, RegionOut, RegionUpdate

router = APIRouter(prefix="/regions", tags=["regions"])


def _row_to_region(row: dict) -> RegionOut:
    return RegionOut(
        region_id=row["region_id"],
        region_name=row["region_name"],
        state_id=row["state_id"],
        state_name=row.get("state_name"),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _ensure_state_exists(cursor, state_id: int) -> None:
    cursor.execute(
        "SELECT state_id FROM states WHERE state_id = %s",
        (state_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected state does not exist")


@router.get("", response_model=list[RegionOut])
def list_regions(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT r.region_id, r.region_name, r.state_id, s.state_name,
                           r.status, r.created_at, r.updated_at
                    FROM regions r
                    LEFT JOIN states s ON s.state_id = r.state_id
                    WHERE r.region_name LIKE %s OR s.state_name LIKE %s
                    ORDER BY r.region_id
                    """,
                    (term, term),
                )
            else:
                cursor.execute(
                    """
                    SELECT r.region_id, r.region_name, r.state_id, s.state_name,
                           r.status, r.created_at, r.updated_at
                    FROM regions r
                    LEFT JOIN states s ON s.state_id = r.state_id
                    ORDER BY r.region_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_region(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{region_id}", response_model=RegionOut)
def get_region(region_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT r.region_id, r.region_name, r.state_id, s.state_name,
                       r.status, r.created_at, r.updated_at
                FROM regions r
                LEFT JOIN states s ON s.state_id = r.state_id
                WHERE r.region_id = %s
                """,
                (region_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Region not found")
            return _row_to_region(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=RegionOut, status_code=201)
def create_region(payload: RegionCreate):
    region_name = payload.region_name.strip()
    if not region_name:
        raise HTTPException(status_code=400, detail="Region is required")

    try:
        with db_cursor() as cursor:
            _ensure_state_exists(cursor, payload.state_id)
            cursor.execute(
                """
                INSERT INTO regions (region_name, state_id, status)
                VALUES (%s, %s, %s)
                """,
                (region_name, payload.state_id, payload.status.value),
            )
            new_region_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT r.region_id, r.region_name, r.state_id, s.state_name,
                       r.status, r.created_at, r.updated_at
                FROM regions r
                LEFT JOIN states s ON s.state_id = r.state_id
                WHERE r.region_id = %s
                """,
                (new_region_id,),
            )
            row = cursor.fetchone()
            return _row_to_region(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Region already exists for the selected state",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{region_id}", response_model=RegionOut)
def update_region(region_id: int, payload: RegionUpdate):
    region_name = payload.region_name.strip()
    if not region_name:
        raise HTTPException(status_code=400, detail="Region is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT region_id FROM regions WHERE region_id = %s",
                (region_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Region not found")

            _ensure_state_exists(cursor, payload.state_id)
            cursor.execute(
                """
                UPDATE regions
                SET region_name = %s, state_id = %s, status = %s
                WHERE region_id = %s
                """,
                (region_name, payload.state_id, payload.status.value, region_id),
            )
            cursor.execute(
                """
                SELECT r.region_id, r.region_name, r.state_id, s.state_name,
                       r.status, r.created_at, r.updated_at
                FROM regions r
                LEFT JOIN states s ON s.state_id = r.state_id
                WHERE r.region_id = %s
                """,
                (region_id,),
            )
            row = cursor.fetchone()
            return _row_to_region(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Region already exists for the selected state",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{region_id}", status_code=204)
def delete_region(region_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM regions WHERE region_id = %s", (region_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Region not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
