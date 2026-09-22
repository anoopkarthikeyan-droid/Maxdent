from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import SectionCreate, SectionOut, SectionUpdate

router = APIRouter(prefix="/sections", tags=["sections"])


def _row_to_section(row: dict) -> SectionOut:
    return SectionOut(
        section_id=row["section_id"],
        section_name=row["section_name"],
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.get("", response_model=list[SectionOut])
def list_sections(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT section_id, section_name, status, created_at, updated_at
                    FROM sections
                    WHERE section_name LIKE %s
                    ORDER BY section_id
                    """,
                    (term,),
                )
            else:
                cursor.execute(
                    """
                    SELECT section_id, section_name, status, created_at, updated_at
                    FROM sections
                    ORDER BY section_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_section(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{section_id}", response_model=SectionOut)
def get_section(section_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT section_id, section_name, status, created_at, updated_at
                FROM sections
                WHERE section_id = %s
                """,
                (section_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Section not found")
            return _row_to_section(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=SectionOut, status_code=201)
def create_section(payload: SectionCreate):
    section_name = payload.section_name.strip()
    if not section_name:
        raise HTTPException(status_code=400, detail="Section is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sections (section_name, status)
                VALUES (%s, %s)
                """,
                (section_name, payload.status.value),
            )
            new_section_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT section_id, section_name, status, created_at, updated_at
                FROM sections
                WHERE section_id = %s
                """,
                (new_section_id,),
            )
            row = cursor.fetchone()
            return _row_to_section(row)
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Section already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{section_id}", response_model=SectionOut)
def update_section(section_id: int, payload: SectionUpdate):
    section_name = payload.section_name.strip()
    if not section_name:
        raise HTTPException(status_code=400, detail="Section is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT section_id FROM sections WHERE section_id = %s",
                (section_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Section not found")

            cursor.execute(
                """
                UPDATE sections
                SET section_name = %s, status = %s
                WHERE section_id = %s
                """,
                (section_name, payload.status.value, section_id),
            )
            cursor.execute(
                """
                SELECT section_id, section_name, status, created_at, updated_at
                FROM sections
                WHERE section_id = %s
                """,
                (section_id,),
            )
            row = cursor.fetchone()
            return _row_to_section(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Section already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{section_id}", status_code=204)
def delete_section(section_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM sections WHERE section_id = %s", (section_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Section not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
