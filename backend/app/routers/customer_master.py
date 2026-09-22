from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])

CUSTOMER_SELECT = """
SELECT cu.customer_id, cu.branch_name, cu.contact_person, cu.address, cu.address1,
       cu.place_id, p.place_name,
       cu.route_id, rt.route_code,
       cu.region_id, rg.region_name,
       cu.state_id, s.state_name,
       cu.country_id, co.country_name,
       cu.currency_id, cy.currency_name,
       cu.distribution_id, d.distribution_name,
       cu.linked_branch_id, b.branch_name AS linked_branch_name,
       cu.gst_no, cu.phone, cu.mobile, cu.email, cu.whatsapp_no,
       cu.current_balance, cu.inclusive_tax, cu.remarks,
       cu.head_office_id, ho.branch_name AS head_office_name,
       cu.billing_office_id, bo.branch_name AS billing_office_name,
       cu.created_at, cu.updated_at
FROM customers cu
LEFT JOIN places p ON p.place_id = cu.place_id
LEFT JOIN routes rt ON rt.route_id = cu.route_id
LEFT JOIN regions rg ON rg.region_id = cu.region_id
LEFT JOIN states s ON s.state_id = cu.state_id
LEFT JOIN countries co ON co.country_id = cu.country_id
LEFT JOIN currencies cy ON cy.currency_id = cu.currency_id
LEFT JOIN distributions d ON d.distribution_id = cu.distribution_id
LEFT JOIN branches b ON b.branch_id = cu.linked_branch_id
LEFT JOIN customers ho ON ho.customer_id = cu.head_office_id
LEFT JOIN customers bo ON bo.customer_id = cu.billing_office_id
"""


def _flag(value) -> bool:
    return bool(value)


def _row_to_customer(row: dict) -> CustomerOut:
    return CustomerOut(
        customer_id=row["customer_id"],
        branch_name=row["branch_name"],
        contact_person=row.get("contact_person"),
        address=row["address"],
        address1=row.get("address1"),
        place_id=row["place_id"],
        place_name=row.get("place_name"),
        route_id=row["route_id"],
        route_code=row.get("route_code"),
        region_id=row["region_id"],
        region_name=row.get("region_name"),
        state_id=row["state_id"],
        state_name=row.get("state_name"),
        country_id=row["country_id"],
        country_name=row.get("country_name"),
        currency_id=row["currency_id"],
        currency_name=row.get("currency_name"),
        distribution_id=row["distribution_id"],
        distribution_name=row.get("distribution_name"),
        linked_branch_id=row["linked_branch_id"],
        linked_branch_name=row.get("linked_branch_name"),
        gst_no=row.get("gst_no"),
        phone=row.get("phone"),
        mobile=row.get("mobile"),
        email=row.get("email"),
        whatsapp_no=row.get("whatsapp_no"),
        current_balance=float(row.get("current_balance") or 0),
        inclusive_tax=_flag(row.get("inclusive_tax")),
        remarks=row.get("remarks"),
        head_office_id=row.get("head_office_id"),
        head_office_name=row.get("head_office_name"),
        billing_office_id=row.get("billing_office_id"),
        billing_office_name=row.get("billing_office_name"),
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
    place_id: int,
    route_id: int,
    region_id: int,
    state_id: int,
    country_id: int,
    currency_id: int,
    distribution_id: int,
    linked_branch_id: int,
) -> None:
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
        "SELECT region_id FROM regions WHERE region_id = %s AND state_id = %s",
        (region_id, state_id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected region is invalid for state")

    cursor.execute(
        "SELECT place_id FROM places WHERE place_id = %s AND region_id = %s",
        (place_id, region_id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected place is invalid for region")

    cursor.execute(
        "SELECT route_id FROM routes WHERE route_id = %s AND region_id = %s",
        (route_id, region_id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected route is invalid for region")

    cursor.execute(
        "SELECT currency_id FROM currencies WHERE currency_id = %s",
        (currency_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected currency does not exist")

    cursor.execute(
        "SELECT branch_id, parent_company_id FROM branches WHERE branch_id = %s",
        (linked_branch_id,),
    )
    branch = cursor.fetchone()
    if not branch:
        raise HTTPException(status_code=400, detail="Selected linked branch does not exist")

    cursor.execute(
        """
        SELECT distribution_id
        FROM distributions
        WHERE distribution_id = %s AND company_id = %s
        """,
        (distribution_id, branch["parent_company_id"]),
    )
    if not cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail="Selected distribution is invalid for linked branch",
        )


def _ensure_office_refs(cursor, head_office_id: int | None, billing_office_id: int | None) -> None:
    for office_id, label in (
        (head_office_id, "Head Office"),
        (billing_office_id, "Billing Office"),
    ):
        if office_id is None:
            continue
        cursor.execute(
            "SELECT customer_id FROM customers WHERE customer_id = %s",
            (office_id,),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Selected {label} does not exist")


def _values(payload: CustomerCreate | CustomerUpdate) -> tuple:
    return (
        payload.branch_name.strip(),
        _clean(payload.contact_person),
        payload.address.strip(),
        _clean(payload.address1),
        payload.place_id,
        payload.route_id,
        payload.region_id,
        payload.state_id,
        payload.country_id,
        payload.currency_id,
        payload.distribution_id,
        payload.linked_branch_id,
        _clean(payload.gst_no),
        _clean(payload.phone),
        _clean(payload.mobile),
        _clean(payload.email),
        _clean(payload.whatsapp_no),
        payload.current_balance,
        int(payload.inclusive_tax),
        _clean(payload.remarks),
    )


@router.get("", response_model=list[CustomerOut])
def list_customers(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    CUSTOMER_SELECT
                    + """
                    WHERE cu.branch_name LIKE %s
                       OR cu.contact_person LIKE %s
                       OR p.place_name LIKE %s
                       OR b.branch_name LIKE %s
                       OR cu.email LIKE %s
                       OR cu.gst_no LIKE %s
                    ORDER BY cu.customer_id
                    """,
                    (term, term, term, term, term, term),
                )
            else:
                cursor.execute(CUSTOMER_SELECT + " ORDER BY cu.customer_id")
            rows = cursor.fetchall()
            return [_row_to_customer(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                CUSTOMER_SELECT + " WHERE cu.customer_id = %s",
                (customer_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Customer not found")
            return _row_to_customer(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate):
    branch_name = payload.branch_name.strip()
    address = payload.address.strip()
    if not branch_name or not address:
        raise HTTPException(status_code=400, detail="Branch Name and Address are required")

    try:
        with db_cursor() as cursor:
            _ensure_refs(
                cursor,
                payload.place_id,
                payload.route_id,
                payload.region_id,
                payload.state_id,
                payload.country_id,
                payload.currency_id,
                payload.distribution_id,
                payload.linked_branch_id,
            )
            cursor.execute(
                """
                INSERT INTO customers (
                  branch_name, contact_person, address, address1,
                  place_id, route_id, region_id, state_id, country_id,
                  currency_id, distribution_id, linked_branch_id,
                  gst_no, phone, mobile, email, whatsapp_no,
                  current_balance, inclusive_tax, remarks
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                _values(payload),
            )
            new_id = cursor.lastrowid
            cursor.execute(
                CUSTOMER_SELECT + " WHERE cu.customer_id = %s",
                (new_id,),
            )
            row = cursor.fetchone()
            return _row_to_customer(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Customer already exists for this linked branch",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, payload: CustomerUpdate):
    branch_name = payload.branch_name.strip()
    address = payload.address.strip()
    if not branch_name or not address:
        raise HTTPException(status_code=400, detail="Branch Name and Address are required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT customer_id FROM customers WHERE customer_id = %s",
                (customer_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Customer not found")

            _ensure_refs(
                cursor,
                payload.place_id,
                payload.route_id,
                payload.region_id,
                payload.state_id,
                payload.country_id,
                payload.currency_id,
                payload.distribution_id,
                payload.linked_branch_id,
            )
            _ensure_office_refs(cursor, payload.head_office_id, payload.billing_office_id)
            cursor.execute(
                """
                UPDATE customers
                SET branch_name = %s,
                    contact_person = %s,
                    address = %s,
                    address1 = %s,
                    place_id = %s,
                    route_id = %s,
                    region_id = %s,
                    state_id = %s,
                    country_id = %s,
                    currency_id = %s,
                    distribution_id = %s,
                    linked_branch_id = %s,
                    gst_no = %s,
                    phone = %s,
                    mobile = %s,
                    email = %s,
                    whatsapp_no = %s,
                    current_balance = %s,
                    inclusive_tax = %s,
                    remarks = %s,
                    head_office_id = %s,
                    billing_office_id = %s
                WHERE customer_id = %s
                """,
                (
                    *_values(payload),
                    payload.head_office_id,
                    payload.billing_office_id,
                    customer_id,
                ),
            )
            cursor.execute(
                CUSTOMER_SELECT + " WHERE cu.customer_id = %s",
                (customer_id,),
            )
            row = cursor.fetchone()
            return _row_to_customer(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Customer already exists for this linked branch",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM customers WHERE customer_id = %s",
                (customer_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Customer not found")
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Customer is used as Head Office or Billing Office and cannot be deleted",
        )
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
