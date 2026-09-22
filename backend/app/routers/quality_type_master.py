from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import QualityTypeCreate, QualityTypeOut, QualityTypeUpdate

router = APIRouter(prefix="/quality-types", tags=["quality-types"])

SELECT_COLUMNS = "quality_type_id, quality_name, status, created_at, updated_at"


def _row_to_quality_type(row: dict) -> QualityTypeOut:
    return QualityTypeOut(
        quality_type_id=row["quality_type_id"],
        quality_name=row["quality_name"],
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.get("", response_model=list[QualityTypeOut])
def list_quality_types(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    f"""
                    SELECT {SELECT_COLUMNS}
                    FROM quality_types
                    WHERE quality_name LIKE %s
                    ORDER BY quality_type_id
                    """,
                    (term,),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT {SELECT_COLUMNS}
                    FROM quality_types
                    ORDER BY quality_type_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_quality_type(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{quality_type_id}", response_model=QualityTypeOut)
def get_quality_type(quality_type_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {SELECT_COLUMNS}
                FROM quality_types
                WHERE quality_type_id = %s
                """,
                (quality_type_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Quality type not found")
            return _row_to_quality_type(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=QualityTypeOut, status_code=201)
def create_quality_type(payload: QualityTypeCreate):
    quality_name = payload.quality_name.strip()
    if not quality_name:
        raise HTTPException(status_code=400, detail="Quality is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO quality_types (quality_name, status)
                VALUES (%s, %s)
                """,
                (quality_name, payload.status.value),
            )
            new_id = cursor.lastrowid
            cursor.execute(
                f"""
                SELECT {SELECT_COLUMNS}
                FROM quality_types
                WHERE quality_type_id = %s
                """,
                (new_id,),
            )
            row = cursor.fetchone()
            return _row_to_quality_type(row)
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Quality type already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{quality_type_id}", response_model=QualityTypeOut)
def update_quality_type(quality_type_id: int, payload: QualityTypeUpdate):
    quality_name = payload.quality_name.strip()
    if not quality_name:
        raise HTTPException(status_code=400, detail="Quality is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT quality_type_id FROM quality_types WHERE quality_type_id = %s",
                (quality_type_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Quality type not found")

            cursor.execute(
                """
                UPDATE quality_types
                SET quality_name = %s, status = %s
                WHERE quality_type_id = %s
                """,
                (quality_name, payload.status.value, quality_type_id),
            )
            cursor.execute(
                f"""
                SELECT {SELECT_COLUMNS}
                FROM quality_types
                WHERE quality_type_id = %s
                """,
                (quality_type_id,),
            )
            row = cursor.fetchone()
            return _row_to_quality_type(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Quality type already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{quality_type_id}", status_code=204)
def delete_quality_type(quality_type_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM quality_types WHERE quality_type_id = %s",
                (quality_type_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Quality type not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
