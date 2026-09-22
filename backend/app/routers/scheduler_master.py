from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.routers.scheduler_case import delete_files_for_details
from app.schemas import (
    SchedulerCreate,
    SchedulerDetailIn,
    SchedulerDetailOut,
    SchedulerNextCodeOut,
    SchedulerOut,
    SchedulerUpdate,
)

router = APIRouter(prefix="/schedulers", tags=["schedulers"])

HEADER_SELECT = """
    sch.scheduler_id, sch.customer_id, cu.branch_name AS customer_name,
    sch.route_id, rt.route_code, sch.fin_year, sch.order_no, sch.mdo_code,
    sch.billing_party_id, bp.branch_name AS billing_party_name,
    sch.sending_party_id, sp.branch_name AS sending_party_name,
    sch.work_type, sch.work_received_date, sch.completion_date,
    sch.created_at, sch.updated_at
"""

DETAIL_SELECT = """
    sd.scheduler_detail_id, sd.scheduler_id, sd.sl_no, sd.work_no,
    sd.work_id, w.work_name, sd.patient_name, sd.arch, sd.quality_type_id,
    q.quality_name, sd.additional_requirements, sd.rate, sd.qty,
    sd.extra_charge, sd.discount, sd.final_rate, sd.remarks,
    EXISTS (
      SELECT 1 FROM scheduler_case_studies cs
      WHERE cs.scheduler_detail_id = sd.scheduler_detail_id
    ) AS has_case,
    (
      SELECT cs.approval_status
      FROM scheduler_case_studies cs
      WHERE cs.scheduler_detail_id = sd.scheduler_detail_id
    ) AS case_approval_status
"""


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _as_float(value) -> float:
    return float(value or 0)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _fin_year(received: date) -> str:
    start = received.year if received.month >= 4 else received.year - 1
    return f"{start % 100:02d}{(start + 1) % 100:02d}"


def _mdo_code(route_code: str, fin_year: str, order_no: int) -> str:
    return f"{route_code}-{fin_year}-{order_no:04d}"


def _work_no(mdo_code: str, sl_no: int) -> str:
    return f"{mdo_code}#{sl_no:02d}"


def _final_rate(rate: float, qty: float, extra_charge: float, discount: float) -> float:
    return round((rate * qty) + extra_charge - discount, 2)


def _row_to_detail(row: dict) -> SchedulerDetailOut:
    return SchedulerDetailOut(
        scheduler_detail_id=row["scheduler_detail_id"],
        scheduler_id=row["scheduler_id"],
        sl_no=row["sl_no"],
        work_no=row["work_no"],
        work_id=row["work_id"],
        work_name=row.get("work_name"),
        patient_name=row["patient_name"],
        arch=row["arch"],
        quality_type_id=row["quality_type_id"],
        quality_name=row.get("quality_name"),
        additional_requirements=row.get("additional_requirements"),
        rate=_as_float(row.get("rate")),
        qty=_as_float(row.get("qty")),
        extra_charge=_as_float(row.get("extra_charge")),
        discount=_as_float(row.get("discount")),
        final_rate=_as_float(row.get("final_rate")),
        remarks=row.get("remarks"),
        has_case=bool(row.get("has_case")),
        case_approval_status=row.get("case_approval_status"),
    )


def _row_to_scheduler(row: dict, details: list[SchedulerDetailOut]) -> SchedulerOut:
    return SchedulerOut(
        scheduler_id=row["scheduler_id"],
        customer_id=row["customer_id"],
        customer_name=row.get("customer_name"),
        route_id=row["route_id"],
        route_code=row.get("route_code"),
        fin_year=row["fin_year"],
        order_no=row["order_no"],
        mdo_code=row["mdo_code"],
        billing_party_id=row["billing_party_id"],
        billing_party_name=row.get("billing_party_name"),
        sending_party_id=row["sending_party_id"],
        sending_party_name=row.get("sending_party_name"),
        work_type=row["work_type"],
        work_received_date=_as_date(row["work_received_date"]),
        completion_date=_as_date(row["completion_date"]),
        details=details,
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _load_details(cursor, scheduler_ids: list[int]) -> dict[int, list[SchedulerDetailOut]]:
    grouped: dict[int, list[SchedulerDetailOut]] = {item_id: [] for item_id in scheduler_ids}
    if not scheduler_ids:
        return grouped
    placeholders = ", ".join(["%s"] * len(scheduler_ids))
    cursor.execute(
        f"""
        SELECT {DETAIL_SELECT}
        FROM scheduler_details sd
        LEFT JOIN works w ON w.work_id = sd.work_id
        LEFT JOIN quality_types q ON q.quality_type_id = sd.quality_type_id
        WHERE sd.scheduler_id IN ({placeholders})
        ORDER BY sd.sl_no, sd.scheduler_detail_id
        """,
        tuple(scheduler_ids),
    )
    for row in cursor.fetchall():
        grouped[row["scheduler_id"]].append(_row_to_detail(row))
    return grouped


def _fetch_header(cursor, scheduler_id: int) -> dict | None:
    cursor.execute(
        f"""
        SELECT {HEADER_SELECT}
        FROM schedulers sch
        LEFT JOIN customers cu ON cu.customer_id = sch.customer_id
        LEFT JOIN customers bp ON bp.customer_id = sch.billing_party_id
        LEFT JOIN customers sp ON sp.customer_id = sch.sending_party_id
        LEFT JOIN routes rt ON rt.route_id = sch.route_id
        WHERE sch.scheduler_id = %s
        """,
        (scheduler_id,),
    )
    return cursor.fetchone()


def _validate_header(payload: SchedulerCreate | SchedulerUpdate) -> None:
    if payload.completion_date < payload.work_received_date:
        raise HTTPException(
            status_code=400,
            detail="Completion Date must be on or after Work Received Date",
        )


def _validate_details(details: list[SchedulerDetailIn]) -> list[tuple[SchedulerDetailIn, float]]:
    if not details:
        raise HTTPException(status_code=400, detail="Add at least one work in the detail")
    cleaned: list[tuple[SchedulerDetailIn, float]] = []
    for item in details:
        patient_name = item.patient_name.strip()
        if not patient_name:
            raise HTTPException(status_code=400, detail="Patient Name is required on each work")
        final_rate = _final_rate(item.rate, item.qty, item.extra_charge, item.discount)
        if final_rate < 0:
            raise HTTPException(status_code=400, detail="Final Rate cannot be negative")
        cleaned.append((item, final_rate))
    return cleaned


def _ensure_customer(cursor, customer_id: int, label: str) -> dict:
    cursor.execute(
        """
        SELECT cu.customer_id, cu.route_id, rt.route_code
        FROM customers cu
        LEFT JOIN routes rt ON rt.route_id = cu.route_id
        WHERE cu.customer_id = %s
        """,
        (customer_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail=f"Selected {label} does not exist")
    if not row.get("route_id") or not row.get("route_code"):
        raise HTTPException(status_code=400, detail="Selected customer does not have a route")
    return row


def _ensure_refs(cursor, payload: SchedulerCreate | SchedulerUpdate) -> dict:
    customer = _ensure_customer(cursor, payload.customer_id, "customer")
    _ensure_customer(cursor, payload.billing_party_id, "billing party")
    _ensure_customer(cursor, payload.sending_party_id, "sending party")
    return customer


def _ensure_detail_refs(cursor, details: list[SchedulerDetailIn]) -> None:
    for item in details:
        cursor.execute("SELECT work_id FROM works WHERE work_id = %s", (item.work_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Selected work does not exist")
        cursor.execute(
            "SELECT quality_type_id FROM quality_types WHERE quality_type_id = %s",
            (item.quality_type_id,),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Selected quality does not exist")


def _next_order(cursor, route_id: int, fin_year: str) -> int:
    cursor.execute(
        """
        SELECT COALESCE(MAX(order_no), 0) + 1 AS next_no
        FROM schedulers
        WHERE route_id = %s AND fin_year = %s
        """,
        (route_id, fin_year),
    )
    row = cursor.fetchone()
    return int(row["next_no"] if row else 1)


def _detail_values(item: SchedulerDetailIn, final_rate: float, sl_no: int, work_no: str) -> tuple:
    return (
        sl_no,
        work_no,
        item.work_id,
        item.patient_name.strip(),
        item.arch.value,
        item.quality_type_id,
        _clean(item.additional_requirements),
        item.rate,
        item.qty,
        item.extra_charge,
        item.discount,
        final_rate,
        _clean(item.remarks),
    )


def _insert_details(
    cursor,
    scheduler_id: int,
    mdo_code: str,
    details: list[tuple[SchedulerDetailIn, float]],
) -> None:
    for index, (item, final_rate) in enumerate(details, start=1):
        cursor.execute(
            """
            INSERT INTO scheduler_details (
                scheduler_id, sl_no, work_no, work_id, patient_name, arch,
                quality_type_id, additional_requirements, rate, qty,
                extra_charge, discount, final_rate, remarks
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (scheduler_id, *_detail_values(item, final_rate, index, _work_no(mdo_code, index))),
        )


def _sync_details(
    cursor,
    scheduler_id: int,
    mdo_code: str,
    details: list[tuple[SchedulerDetailIn, float]],
) -> None:
    cursor.execute(
        "SELECT scheduler_detail_id FROM scheduler_details WHERE scheduler_id = %s",
        (scheduler_id,),
    )
    existing_ids = {row["scheduler_detail_id"] for row in cursor.fetchall()}
    kept: set[int] = set()
    for index, (item, final_rate) in enumerate(details, start=1):
        values = _detail_values(item, final_rate, index, _work_no(mdo_code, index))
        if item.scheduler_detail_id and item.scheduler_detail_id in existing_ids:
            cursor.execute(
                """
                UPDATE scheduler_details
                SET sl_no = %s,
                    work_no = %s,
                    work_id = %s,
                    patient_name = %s,
                    arch = %s,
                    quality_type_id = %s,
                    additional_requirements = %s,
                    rate = %s,
                    qty = %s,
                    extra_charge = %s,
                    discount = %s,
                    final_rate = %s,
                    remarks = %s
                WHERE scheduler_detail_id = %s AND scheduler_id = %s
                """,
                (*values, item.scheduler_detail_id, scheduler_id),
            )
            kept.add(item.scheduler_detail_id)
        else:
            cursor.execute(
                """
                INSERT INTO scheduler_details (
                    scheduler_id, sl_no, work_no, work_id, patient_name, arch,
                    quality_type_id, additional_requirements, rate, qty,
                    extra_charge, discount, final_rate, remarks
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (scheduler_id, *values),
            )
            kept.add(cursor.lastrowid)
    removed = list(existing_ids - kept)
    if removed:
        delete_files_for_details(cursor, removed)
        placeholders = ", ".join(["%s"] * len(removed))
        cursor.execute(
            f"DELETE FROM scheduler_details WHERE scheduler_detail_id IN ({placeholders})",
            tuple(removed),
        )


def _build_out(cursor, scheduler_id: int) -> SchedulerOut:
    row = _fetch_header(cursor, scheduler_id)
    details = _load_details(cursor, [scheduler_id]).get(scheduler_id, [])
    return _row_to_scheduler(row, details)


@router.get("/next-code", response_model=SchedulerNextCodeOut)
def next_code(customer_id: int, work_received_date: date):
    try:
        with db_cursor() as cursor:
            customer = _ensure_customer(cursor, customer_id, "customer")
            fin_year = _fin_year(work_received_date)
            order_no = _next_order(cursor, customer["route_id"], fin_year)
            return SchedulerNextCodeOut(
                route_id=customer["route_id"],
                route_code=customer["route_code"],
                fin_year=fin_year,
                order_no=order_no,
                mdo_code=_mdo_code(customer["route_code"], fin_year, order_no),
            )
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("", response_model=list[SchedulerOut])
def list_schedulers(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            sql = f"""
                SELECT {HEADER_SELECT}
                FROM schedulers sch
                LEFT JOIN customers cu ON cu.customer_id = sch.customer_id
                LEFT JOIN customers bp ON bp.customer_id = sch.billing_party_id
                LEFT JOIN customers sp ON sp.customer_id = sch.sending_party_id
                LEFT JOIN routes rt ON rt.route_id = sch.route_id
            """
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    sql
                    + """
                    WHERE sch.mdo_code LIKE %s
                       OR cu.branch_name LIKE %s
                       OR bp.branch_name LIKE %s
                       OR sp.branch_name LIKE %s
                       OR EXISTS (
                            SELECT 1 FROM scheduler_details sd
                            WHERE sd.scheduler_id = sch.scheduler_id
                              AND (sd.patient_name LIKE %s OR sd.work_no LIKE %s)
                       )
                    ORDER BY sch.scheduler_id
                    """,
                    (term, term, term, term, term, term),
                )
            else:
                cursor.execute(sql + " ORDER BY sch.scheduler_id")
            rows = cursor.fetchall()
            grouped = _load_details(cursor, [row["scheduler_id"] for row in rows])
            return [
                _row_to_scheduler(row, grouped.get(row["scheduler_id"], []))
                for row in rows
            ]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{scheduler_id}", response_model=SchedulerOut)
def get_scheduler(scheduler_id: int):
    try:
        with db_cursor() as cursor:
            row = _fetch_header(cursor, scheduler_id)
            if not row:
                raise HTTPException(status_code=404, detail="Scheduler not found")
            details = _load_details(cursor, [scheduler_id]).get(scheduler_id, [])
            return _row_to_scheduler(row, details)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=SchedulerOut, status_code=201)
def create_scheduler(payload: SchedulerCreate):
    _validate_header(payload)
    details = _validate_details(payload.details)

    try:
        with db_cursor() as cursor:
            customer = _ensure_refs(cursor, payload)
            _ensure_detail_refs(cursor, payload.details)
            fin_year = _fin_year(payload.work_received_date)
            order_no = _next_order(cursor, customer["route_id"], fin_year)
            mdo_code = _mdo_code(customer["route_code"], fin_year, order_no)
            cursor.execute(
                """
                INSERT INTO schedulers (
                    customer_id, route_id, fin_year, order_no, mdo_code,
                    billing_party_id, sending_party_id, work_type,
                    work_received_date, completion_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    payload.customer_id,
                    customer["route_id"],
                    fin_year,
                    order_no,
                    mdo_code,
                    payload.billing_party_id,
                    payload.sending_party_id,
                    payload.work_type.value,
                    payload.work_received_date,
                    payload.completion_date,
                ),
            )
            new_id = cursor.lastrowid
            _insert_details(cursor, new_id, mdo_code, details)
            return _build_out(cursor, new_id)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="MDO code already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{scheduler_id}", response_model=SchedulerOut)
def update_scheduler(scheduler_id: int, payload: SchedulerUpdate):
    _validate_header(payload)
    details = _validate_details(payload.details)

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT scheduler_id, mdo_code FROM schedulers WHERE scheduler_id = %s",
                (scheduler_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Scheduler not found")

            _ensure_refs(cursor, payload)
            _ensure_detail_refs(cursor, payload.details)
            cursor.execute(
                """
                UPDATE schedulers
                SET customer_id = %s,
                    billing_party_id = %s,
                    sending_party_id = %s,
                    work_type = %s,
                    work_received_date = %s,
                    completion_date = %s
                WHERE scheduler_id = %s
                """,
                (
                    payload.customer_id,
                    payload.billing_party_id,
                    payload.sending_party_id,
                    payload.work_type.value,
                    payload.work_received_date,
                    payload.completion_date,
                    scheduler_id,
                ),
            )
            _sync_details(cursor, scheduler_id, existing["mdo_code"], details)
            return _build_out(cursor, scheduler_id)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Scheduler could not be updated")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{scheduler_id}", status_code=204)
def delete_scheduler(scheduler_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM schedulers WHERE scheduler_id = %s",
                (scheduler_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Scheduler not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
