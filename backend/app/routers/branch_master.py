from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import BranchCreate, BranchOut, BranchUpdate

router = APIRouter(prefix="/branches", tags=["branches"])

BRANCH_SELECT = """
SELECT b.branch_id, b.parent_company_id, c.company_name AS parent_company_name,
       b.branch_type_id, bt.branch_type_name,
       b.branch_name, b.address1, b.address2,
       b.place_id, p.place_name,
       b.region_id, r.region_name,
       b.state_id, s.state_name,
       b.country_id, co.country_name,
       b.pin, b.phone, b.mobile, b.email, b.whatsapp_no, b.gst_no,
       b.distribution_id, d.distribution_name,
       b.iso_number, b.ie_code, b.status,
       b.created_at, b.updated_at
FROM branches b
LEFT JOIN companies c ON c.company_id = b.parent_company_id
LEFT JOIN branch_types bt ON bt.branch_type_id = b.branch_type_id
LEFT JOIN places p ON p.place_id = b.place_id
LEFT JOIN regions r ON r.region_id = b.region_id
LEFT JOIN states s ON s.state_id = b.state_id
LEFT JOIN countries co ON co.country_id = b.country_id
LEFT JOIN distributions d ON d.distribution_id = b.distribution_id
"""


def _row_to_branch(row: dict) -> BranchOut:
    return BranchOut(
        branch_id=row["branch_id"],
        parent_company_id=row["parent_company_id"],
        parent_company_name=row.get("parent_company_name"),
        branch_type_id=row["branch_type_id"],
        branch_type_name=row.get("branch_type_name"),
        branch_name=row["branch_name"],
        address1=row["address1"],
        address2=row.get("address2"),
        place_id=row["place_id"],
        place_name=row.get("place_name"),
        region_id=row["region_id"],
        region_name=row.get("region_name"),
        state_id=row["state_id"],
        state_name=row.get("state_name"),
        country_id=row["country_id"],
        country_name=row.get("country_name"),
        pin=row["pin"],
        phone=row.get("phone"),
        mobile=row.get("mobile"),
        email=row.get("email"),
        whatsapp_no=row.get("whatsapp_no"),
        gst_no=row.get("gst_no"),
        distribution_id=row.get("distribution_id"),
        distribution_name=row.get("distribution_name"),
        iso_number=row.get("iso_number"),
        ie_code=row.get("ie_code"),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _ensure_refs(
    cursor,
    parent_company_id: int,
    branch_type_id: int,
    place_id: int,
    state_id: int,
    country_id: int,
    distribution_id: int | None,
) -> int:
    cursor.execute(
        "SELECT company_id FROM companies WHERE company_id = %s",
        (parent_company_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected parent company does not exist")

    cursor.execute(
        "SELECT branch_type_id FROM branch_types WHERE branch_type_id = %s",
        (branch_type_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected branch type does not exist")

    cursor.execute("SELECT country_id FROM countries WHERE country_id = %s", (country_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected country does not exist")

    cursor.execute(
        "SELECT state_id FROM states WHERE state_id = %s AND country_id = %s",
        (state_id, country_id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected state is invalid for country")

    cursor.execute(
        """
        SELECT p.place_id, p.region_id
        FROM places p
        INNER JOIN regions r ON r.region_id = p.region_id
        WHERE p.place_id = %s AND r.state_id = %s
        """,
        (place_id, state_id),
    )
    place = cursor.fetchone()
    if not place:
        raise HTTPException(status_code=400, detail="Selected place is invalid for state")

    if distribution_id is not None:
        cursor.execute(
            """
            SELECT distribution_id
            FROM distributions
            WHERE distribution_id = %s AND company_id = %s
            """,
            (distribution_id, parent_company_id),
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Selected distribution is invalid for parent company",
            )

    return place["region_id"]


def _values(payload: BranchCreate | BranchUpdate, region_id: int) -> tuple:
    return (
        payload.parent_company_id,
        payload.branch_type_id,
        payload.branch_name.strip(),
        payload.address1.strip(),
        _clean(payload.address2),
        payload.place_id,
        region_id,
        payload.state_id,
        payload.country_id,
        payload.pin.strip(),
        _clean(payload.phone),
        _clean(payload.mobile),
        _clean(payload.email),
        _clean(payload.whatsapp_no),
        _clean(payload.gst_no),
        payload.distribution_id,
        _clean(payload.iso_number),
        _clean(payload.ie_code),
        payload.status.value,
    )


@router.get("", response_model=list[BranchOut])
def list_branches(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    BRANCH_SELECT
                    + """
                    WHERE b.branch_name LIKE %s
                       OR c.company_name LIKE %s
                       OR bt.branch_type_name LIKE %s
                       OR p.place_name LIKE %s
                       OR b.email LIKE %s
                       OR b.gst_no LIKE %s
                    ORDER BY b.branch_id
                    """,
                    (term, term, term, term, term, term),
                )
            else:
                cursor.execute(BRANCH_SELECT + " ORDER BY b.branch_id")
            rows = cursor.fetchall()
            return [_row_to_branch(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{branch_id}", response_model=BranchOut)
def get_branch(branch_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(BRANCH_SELECT + " WHERE b.branch_id = %s", (branch_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Branch not found")
            return _row_to_branch(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=BranchOut, status_code=201)
def create_branch(payload: BranchCreate):
    branch_name = payload.branch_name.strip()
    address1 = payload.address1.strip()
    pin = payload.pin.strip()
    if not branch_name or not address1 or not pin:
        raise HTTPException(
            status_code=400,
            detail="Branch Name, Address1, and Pin are required",
        )

    try:
        with db_cursor() as cursor:
            region_id = _ensure_refs(
                cursor,
                payload.parent_company_id,
                payload.branch_type_id,
                payload.place_id,
                payload.state_id,
                payload.country_id,
                payload.distribution_id,
            )
            cursor.execute(
                """
                INSERT INTO branches (
                  parent_company_id, branch_type_id, branch_name, address1, address2,
                  place_id, region_id, state_id, country_id, pin,
                  phone, mobile, email, whatsapp_no, gst_no,
                  distribution_id, iso_number, ie_code, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                _values(payload, region_id),
            )
            new_id = cursor.lastrowid
            cursor.execute(BRANCH_SELECT + " WHERE b.branch_id = %s", (new_id,))
            row = cursor.fetchone()
            return _row_to_branch(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Branch already exists for this parent company",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{branch_id}", response_model=BranchOut)
def update_branch(branch_id: int, payload: BranchUpdate):
    branch_name = payload.branch_name.strip()
    address1 = payload.address1.strip()
    pin = payload.pin.strip()
    if not branch_name or not address1 or not pin:
        raise HTTPException(
            status_code=400,
            detail="Branch Name, Address1, and Pin are required",
        )

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT branch_id FROM branches WHERE branch_id = %s",
                (branch_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Branch not found")

            region_id = _ensure_refs(
                cursor,
                payload.parent_company_id,
                payload.branch_type_id,
                payload.place_id,
                payload.state_id,
                payload.country_id,
                payload.distribution_id,
            )
            cursor.execute(
                """
                UPDATE branches
                SET parent_company_id = %s,
                    branch_type_id = %s,
                    branch_name = %s,
                    address1 = %s,
                    address2 = %s,
                    place_id = %s,
                    region_id = %s,
                    state_id = %s,
                    country_id = %s,
                    pin = %s,
                    phone = %s,
                    mobile = %s,
                    email = %s,
                    whatsapp_no = %s,
                    gst_no = %s,
                    distribution_id = %s,
                    iso_number = %s,
                    ie_code = %s,
                    status = %s
                WHERE branch_id = %s
                """,
                (*_values(payload, region_id), branch_id),
            )
            cursor.execute(BRANCH_SELECT + " WHERE b.branch_id = %s", (branch_id,))
            row = cursor.fetchone()
            return _row_to_branch(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Branch already exists for this parent company",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{branch_id}", status_code=204)
def delete_branch(branch_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM branches WHERE branch_id = %s", (branch_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Branch not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
