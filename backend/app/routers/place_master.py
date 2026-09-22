from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import PlaceCreate, PlaceOut, PlaceUpdate

router = APIRouter(prefix="/places", tags=["places"])


def _row_to_place(row: dict) -> PlaceOut:
    return PlaceOut(
        place_id=row["place_id"],
        place_name=row["place_name"],
        region_id=row["region_id"],
        region_name=row.get("region_name"),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _ensure_region_exists(cursor, region_id: int) -> None:
    cursor.execute(
        "SELECT region_id FROM regions WHERE region_id = %s",
        (region_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected region does not exist")


@router.get("", response_model=list[PlaceOut])
def list_places(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT p.place_id, p.place_name, p.region_id, r.region_name,
                           p.status, p.created_at, p.updated_at
                    FROM places p
                    LEFT JOIN regions r ON r.region_id = p.region_id
                    WHERE p.place_name LIKE %s OR r.region_name LIKE %s
                    ORDER BY p.place_id
                    """,
                    (term, term),
                )
            else:
                cursor.execute(
                    """
                    SELECT p.place_id, p.place_name, p.region_id, r.region_name,
                           p.status, p.created_at, p.updated_at
                    FROM places p
                    LEFT JOIN regions r ON r.region_id = p.region_id
                    ORDER BY p.place_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_place(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{place_id}", response_model=PlaceOut)
def get_place(place_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT p.place_id, p.place_name, p.region_id, r.region_name,
                       p.status, p.created_at, p.updated_at
                FROM places p
                LEFT JOIN regions r ON r.region_id = p.region_id
                WHERE p.place_id = %s
                """,
                (place_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Place not found")
            return _row_to_place(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=PlaceOut, status_code=201)
def create_place(payload: PlaceCreate):
    place_name = payload.place_name.strip()
    if not place_name:
        raise HTTPException(status_code=400, detail="Place is required")

    try:
        with db_cursor() as cursor:
            _ensure_region_exists(cursor, payload.region_id)
            cursor.execute(
                """
                INSERT INTO places (place_name, region_id, status)
                VALUES (%s, %s, %s)
                """,
                (place_name, payload.region_id, payload.status.value),
            )
            new_place_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT p.place_id, p.place_name, p.region_id, r.region_name,
                       p.status, p.created_at, p.updated_at
                FROM places p
                LEFT JOIN regions r ON r.region_id = p.region_id
                WHERE p.place_id = %s
                """,
                (new_place_id,),
            )
            row = cursor.fetchone()
            return _row_to_place(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Place already exists for the selected region",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{place_id}", response_model=PlaceOut)
def update_place(place_id: int, payload: PlaceUpdate):
    place_name = payload.place_name.strip()
    if not place_name:
        raise HTTPException(status_code=400, detail="Place is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT place_id FROM places WHERE place_id = %s",
                (place_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Place not found")

            _ensure_region_exists(cursor, payload.region_id)
            cursor.execute(
                """
                UPDATE places
                SET place_name = %s, region_id = %s, status = %s
                WHERE place_id = %s
                """,
                (place_name, payload.region_id, payload.status.value, place_id),
            )
            cursor.execute(
                """
                SELECT p.place_id, p.place_name, p.region_id, r.region_name,
                       p.status, p.created_at, p.updated_at
                FROM places p
                LEFT JOIN regions r ON r.region_id = p.region_id
                WHERE p.place_id = %s
                """,
                (place_id,),
            )
            row = cursor.fetchone()
            return _row_to_place(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Place already exists for the selected region",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{place_id}", status_code=204)
def delete_place(place_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM places WHERE place_id = %s", (place_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Place not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
