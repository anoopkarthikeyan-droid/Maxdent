from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import BranchTypeCreate, BranchTypeOut, BranchTypeUpdate

router = APIRouter(prefix="/branch-types", tags=["branch-types"])

SELECT_COLUMNS = """
    branch_type_id, branch_type_name,
    work_collection, case_study, production, qc,
    billing, transportation, payment_collection,
    status, created_at, updated_at
"""


def _flag(value) -> bool:
    return bool(value)


def _row_to_branch_type(row: dict) -> BranchTypeOut:
    return BranchTypeOut(
        branch_type_id=row["branch_type_id"],
        branch_type_name=row["branch_type_name"],
        work_collection=_flag(row.get("work_collection")),
        case_study=_flag(row.get("case_study")),
        production=_flag(row.get("production")),
        qc=_flag(row.get("qc")),
        billing=_flag(row.get("billing")),
        transportation=_flag(row.get("transportation")),
        payment_collection=_flag(row.get("payment_collection")),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _flag_values(payload: BranchTypeCreate | BranchTypeUpdate) -> tuple:
    return (
        int(payload.work_collection),
        int(payload.case_study),
        int(payload.production),
        int(payload.qc),
        int(payload.billing),
        int(payload.transportation),
        int(payload.payment_collection),
    )


@router.get("", response_model=list[BranchTypeOut])
def list_branch_types(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    f"""
                    SELECT {SELECT_COLUMNS}
                    FROM branch_types
                    WHERE branch_type_name LIKE %s
                    ORDER BY branch_type_id
                    """,
                    (term,),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT {SELECT_COLUMNS}
                    FROM branch_types
                    ORDER BY branch_type_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_branch_type(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{branch_type_id}", response_model=BranchTypeOut)
def get_branch_type(branch_type_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {SELECT_COLUMNS}
                FROM branch_types
                WHERE branch_type_id = %s
                """,
                (branch_type_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Branch type not found")
            return _row_to_branch_type(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=BranchTypeOut, status_code=201)
def create_branch_type(payload: BranchTypeCreate):
    branch_type_name = payload.branch_type_name.strip()
    if not branch_type_name:
        raise HTTPException(status_code=400, detail="Branch Type is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO branch_types (
                    branch_type_name, work_collection, case_study, production, qc,
                    billing, transportation, payment_collection, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (branch_type_name, *_flag_values(payload), payload.status.value),
            )
            new_id = cursor.lastrowid
            cursor.execute(
                f"""
                SELECT {SELECT_COLUMNS}
                FROM branch_types
                WHERE branch_type_id = %s
                """,
                (new_id,),
            )
            row = cursor.fetchone()
            return _row_to_branch_type(row)
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Branch type already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{branch_type_id}", response_model=BranchTypeOut)
def update_branch_type(branch_type_id: int, payload: BranchTypeUpdate):
    branch_type_name = payload.branch_type_name.strip()
    if not branch_type_name:
        raise HTTPException(status_code=400, detail="Branch Type is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT branch_type_id FROM branch_types WHERE branch_type_id = %s",
                (branch_type_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Branch type not found")

            cursor.execute(
                """
                UPDATE branch_types
                SET branch_type_name = %s,
                    work_collection = %s,
                    case_study = %s,
                    production = %s,
                    qc = %s,
                    billing = %s,
                    transportation = %s,
                    payment_collection = %s,
                    status = %s
                WHERE branch_type_id = %s
                """,
                (branch_type_name, *_flag_values(payload), payload.status.value, branch_type_id),
            )
            cursor.execute(
                f"""
                SELECT {SELECT_COLUMNS}
                FROM branch_types
                WHERE branch_type_id = %s
                """,
                (branch_type_id,),
            )
            row = cursor.fetchone()
            return _row_to_branch_type(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Branch type already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{branch_type_id}", status_code=204)
def delete_branch_type(branch_type_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM branch_types WHERE branch_type_id = %s",
                (branch_type_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Branch type not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
