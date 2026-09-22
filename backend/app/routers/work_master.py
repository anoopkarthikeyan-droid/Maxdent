from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import WorkCreate, WorkOut, WorkUpdate

router = APIRouter(prefix="/works", tags=["works"])

SELECT_COLUMNS = """
    w.work_id, w.work_name, w.work_type, w.stage, w.production_time,
    w.section_id, s.section_name,
    w.status, w.existing_id, w.created_at, w.updated_at
"""


def _row_to_work(row: dict) -> WorkOut:
    return WorkOut(
        work_id=row["work_id"],
        work_name=row["work_name"],
        work_type=row["work_type"],
        stage=row["stage"],
        production_time=int(row["production_time"]),
        section_id=row.get("section_id"),
        section_name=row.get("section_name"),
        status=row["status"],
        existing_id=row.get("existing_id"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _fetch_work(cursor, work_id: int) -> dict | None:
    cursor.execute(
        f"""
        SELECT {SELECT_COLUMNS}
        FROM works w
        LEFT JOIN sections s ON s.section_id = w.section_id
        WHERE w.work_id = %s
        """,
        (work_id,),
    )
    return cursor.fetchone()


def _ensure_section(cursor, section_id: int) -> None:
    cursor.execute("SELECT section_id FROM sections WHERE section_id = %s", (section_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected section does not exist")


@router.get("", response_model=list[WorkOut])
def list_works(
    search: str | None = Query(default=None),
    section_id: int | None = Query(default=None),
):
    try:
        with db_cursor() as cursor:
            where = []
            params: list = []
            if search and search.strip():
                where.append("w.work_name LIKE %s")
                params.append(f"%{search.strip()}%")
            if section_id is not None:
                where.append("w.section_id = %s")
                params.append(section_id)
            sql = f"""
                SELECT {SELECT_COLUMNS}
                FROM works w
                LEFT JOIN sections s ON s.section_id = w.section_id
            """
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY w.work_id"
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [_row_to_work(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{work_id}", response_model=WorkOut)
def get_work(work_id: int):
    try:
        with db_cursor() as cursor:
            row = _fetch_work(cursor, work_id)
            if not row:
                raise HTTPException(status_code=404, detail="Work not found")
            return _row_to_work(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=WorkOut, status_code=201)
def create_work(payload: WorkCreate):
    work_name = payload.work_name.strip()
    if not work_name:
        raise HTTPException(status_code=400, detail="Work Name is required")

    try:
        with db_cursor() as cursor:
            _ensure_section(cursor, payload.section_id)
            cursor.execute(
                """
                INSERT INTO works (
                    work_name, work_type, stage, production_time,
                    section_id, status, existing_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    work_name,
                    payload.work_type.value,
                    payload.stage.value,
                    payload.production_time,
                    payload.section_id,
                    payload.status.value,
                    payload.existing_id,
                ),
            )
            new_id = cursor.lastrowid
            row = _fetch_work(cursor, new_id)
            return _row_to_work(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Work already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{work_id}", response_model=WorkOut)
def update_work(work_id: int, payload: WorkUpdate):
    work_name = payload.work_name.strip()
    if not work_name:
        raise HTTPException(status_code=400, detail="Work Name is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT work_id FROM works WHERE work_id = %s",
                (work_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Work not found")

            _ensure_section(cursor, payload.section_id)
            cursor.execute(
                """
                UPDATE works
                SET work_name = %s,
                    work_type = %s,
                    stage = %s,
                    production_time = %s,
                    section_id = %s,
                    status = %s,
                    existing_id = %s
                WHERE work_id = %s
                """,
                (
                    work_name,
                    payload.work_type.value,
                    payload.stage.value,
                    payload.production_time,
                    payload.section_id,
                    payload.status.value,
                    payload.existing_id,
                    work_id,
                ),
            )
            row = _fetch_work(cursor, work_id)
            return _row_to_work(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Work already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{work_id}", status_code=204)
def delete_work(work_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM works WHERE work_id = %s", (work_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Work not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
