from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import (
    DistributionCreate,
    DistributionDetailIn,
    DistributionDetailOut,
    DistributionOut,
    DistributionUpdate,
)

router = APIRouter(prefix="/distributions", tags=["distributions"])

HEADER_SELECT = """
    d.distribution_id, d.distribution_name,
    d.section_id, s.section_name,
    d.currency_id, c.currency_name,
    d.company_id, co.company_name,
    d.effective_from, d.effective_to, d.status,
    d.created_at, d.updated_at
"""

DETAIL_SELECT = """
    dd.distribution_detail_id, dd.distribution_id, dd.work_id, w.work_name,
    dd.prime_rate, dd.supreme_rate, dd.supreme_plus_rate,
    dd.collection_charge, dd.collection_percentage
"""


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _as_float(value) -> float:
    return float(value or 0)


def _row_to_detail(row: dict) -> DistributionDetailOut:
    return DistributionDetailOut(
        distribution_detail_id=row["distribution_detail_id"],
        distribution_id=row["distribution_id"],
        work_id=row["work_id"],
        work_name=row.get("work_name"),
        prime_rate=_as_float(row.get("prime_rate")),
        supreme_rate=_as_float(row.get("supreme_rate")),
        supreme_plus_rate=_as_float(row.get("supreme_plus_rate")),
        collection_charge=_as_float(row.get("collection_charge")),
        collection_percentage=_as_float(row.get("collection_percentage")),
    )


def _row_to_distribution(row: dict, details: list[DistributionDetailOut]) -> DistributionOut:
    return DistributionOut(
        distribution_id=row["distribution_id"],
        distribution_name=row["distribution_name"],
        section_id=row["section_id"],
        section_name=row.get("section_name"),
        currency_id=row["currency_id"],
        currency_name=row.get("currency_name"),
        company_id=row["company_id"],
        company_name=row.get("company_name"),
        effective_from=_as_date(row["effective_from"]),
        effective_to=_as_date(row["effective_to"]),
        status=row["status"],
        details=details,
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _load_details(cursor, distribution_ids: list[int]) -> dict[int, list[DistributionDetailOut]]:
    grouped: dict[int, list[DistributionDetailOut]] = {item_id: [] for item_id in distribution_ids}
    if not distribution_ids:
        return grouped
    placeholders = ", ".join(["%s"] * len(distribution_ids))
    cursor.execute(
        f"""
        SELECT {DETAIL_SELECT}
        FROM distribution_details dd
        LEFT JOIN works w ON w.work_id = dd.work_id
        WHERE dd.distribution_id IN ({placeholders})
        ORDER BY dd.distribution_detail_id
        """,
        tuple(distribution_ids),
    )
    for row in cursor.fetchall():
        grouped[row["distribution_id"]].append(_row_to_detail(row))
    return grouped


def _fetch_header(cursor, distribution_id: int) -> dict | None:
    cursor.execute(
        f"""
        SELECT {HEADER_SELECT}
        FROM distributions d
        LEFT JOIN sections s ON s.section_id = d.section_id
        LEFT JOIN currencies c ON c.currency_id = d.currency_id
        LEFT JOIN companies co ON co.company_id = d.company_id
        WHERE d.distribution_id = %s
        """,
        (distribution_id,),
    )
    return cursor.fetchone()


def _validate_header(payload: DistributionCreate | DistributionUpdate) -> str:
    distribution_name = payload.distribution_name.strip()
    if not distribution_name:
        raise HTTPException(status_code=400, detail="Distribution Name is required")
    if payload.effective_to < payload.effective_from:
        raise HTTPException(
            status_code=400,
            detail="Effective To must be on or after Effective From",
        )
    return distribution_name


def _validate_details(details: list[DistributionDetailIn]) -> list[DistributionDetailIn]:
    cleaned: list[DistributionDetailIn] = []
    seen_works: set[int] = set()
    for item in details:
        if item.work_id in seen_works:
            raise HTTPException(status_code=400, detail="Each work can appear only once")
        seen_works.add(item.work_id)
        cleaned.append(item)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Add at least one work in the detail")
    return cleaned


def _ensure_refs(cursor, payload: DistributionCreate | DistributionUpdate) -> None:
    cursor.execute("SELECT section_id FROM sections WHERE section_id = %s", (payload.section_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected section does not exist")
    cursor.execute("SELECT currency_id FROM currencies WHERE currency_id = %s", (payload.currency_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected currency does not exist")
    cursor.execute("SELECT company_id FROM companies WHERE company_id = %s", (payload.company_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected company does not exist")


def _ensure_works(cursor, details: list[DistributionDetailIn], section_id: int) -> None:
    for item in details:
        cursor.execute(
            "SELECT work_id, section_id FROM works WHERE work_id = %s",
            (item.work_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Selected work does not exist")
        if row["section_id"] != section_id:
            raise HTTPException(
                status_code=400,
                detail="Works must belong to the selected section",
            )


def _insert_details(cursor, distribution_id: int, details: list[DistributionDetailIn]) -> None:
    for item in details:
        cursor.execute(
            """
            INSERT INTO distribution_details (
                distribution_id, work_id, prime_rate, supreme_rate, supreme_plus_rate,
                collection_charge, collection_percentage
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                distribution_id,
                item.work_id,
                item.prime_rate,
                item.supreme_rate,
                item.supreme_plus_rate,
                item.collection_charge,
                item.collection_percentage,
            ),
        )


def _build_out(cursor, distribution_id: int) -> DistributionOut:
    row = _fetch_header(cursor, distribution_id)
    details = _load_details(cursor, [distribution_id]).get(distribution_id, [])
    return _row_to_distribution(row, details)


@router.get("", response_model=list[DistributionOut])
def list_distributions(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    f"""
                    SELECT {HEADER_SELECT}
                    FROM distributions d
                    LEFT JOIN sections s ON s.section_id = d.section_id
                    LEFT JOIN currencies c ON c.currency_id = d.currency_id
                    LEFT JOIN companies co ON co.company_id = d.company_id
                    WHERE d.distribution_name LIKE %s
                    ORDER BY d.distribution_id
                    """,
                    (term,),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT {HEADER_SELECT}
                    FROM distributions d
                    LEFT JOIN sections s ON s.section_id = d.section_id
                    LEFT JOIN currencies c ON c.currency_id = d.currency_id
                    LEFT JOIN companies co ON co.company_id = d.company_id
                    ORDER BY d.distribution_id
                    """
                )
            rows = cursor.fetchall()
            grouped = _load_details(cursor, [row["distribution_id"] for row in rows])
            return [
                _row_to_distribution(row, grouped.get(row["distribution_id"], []))
                for row in rows
            ]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{distribution_id}", response_model=DistributionOut)
def get_distribution(distribution_id: int):
    try:
        with db_cursor() as cursor:
            row = _fetch_header(cursor, distribution_id)
            if not row:
                raise HTTPException(status_code=404, detail="Distribution not found")
            details = _load_details(cursor, [distribution_id]).get(distribution_id, [])
            return _row_to_distribution(row, details)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=DistributionOut, status_code=201)
def create_distribution(payload: DistributionCreate):
    distribution_name = _validate_header(payload)
    details = _validate_details(payload.details)

    try:
        with db_cursor() as cursor:
            _ensure_refs(cursor, payload)
            _ensure_works(cursor, details, payload.section_id)
            cursor.execute(
                """
                INSERT INTO distributions (
                    distribution_name, section_id, currency_id, company_id,
                    effective_from, effective_to, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    distribution_name,
                    payload.section_id,
                    payload.currency_id,
                    payload.company_id,
                    payload.effective_from,
                    payload.effective_to,
                    payload.status.value,
                ),
            )
            new_id = cursor.lastrowid
            _insert_details(cursor, new_id, details)
            return _build_out(cursor, new_id)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Distribution already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{distribution_id}", response_model=DistributionOut)
def update_distribution(distribution_id: int, payload: DistributionUpdate):
    distribution_name = _validate_header(payload)
    details = _validate_details(payload.details)

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT distribution_id FROM distributions WHERE distribution_id = %s",
                (distribution_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Distribution not found")

            _ensure_refs(cursor, payload)
            _ensure_works(cursor, details, payload.section_id)
            cursor.execute(
                """
                UPDATE distributions
                SET distribution_name = %s,
                    section_id = %s,
                    currency_id = %s,
                    company_id = %s,
                    effective_from = %s,
                    effective_to = %s,
                    status = %s
                WHERE distribution_id = %s
                """,
                (
                    distribution_name,
                    payload.section_id,
                    payload.currency_id,
                    payload.company_id,
                    payload.effective_from,
                    payload.effective_to,
                    payload.status.value,
                    distribution_id,
                ),
            )
            cursor.execute(
                "DELETE FROM distribution_details WHERE distribution_id = %s",
                (distribution_id,),
            )
            _insert_details(cursor, distribution_id, details)
            return _build_out(cursor, distribution_id)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Distribution already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{distribution_id}", status_code=204)
def delete_distribution(distribution_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM distributions WHERE distribution_id = %s",
                (distribution_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Distribution not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
