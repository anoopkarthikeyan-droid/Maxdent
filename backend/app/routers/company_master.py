import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
import mariadb

from app.db import db_cursor
from app.schemas import CompanyOut, RecordStatus

router = APIRouter(prefix="/companies", tags=["companies"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "logos"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def _row_to_company(row: dict) -> CompanyOut:
    return CompanyOut(
        company_id=row["company_id"],
        company_name=row["company_name"],
        company_code=row["company_code"],
        address=row["address"],
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
        ie_code=row.get("ie_code"),
        iso_number=row.get("iso_number"),
        logo_path=row.get("logo_path"),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


COMPANY_SELECT = """
SELECT c.company_id, c.company_name, c.company_code, c.address, c.address2,
       c.place_id, p.place_name,
       c.region_id, r.region_name,
       c.state_id, s.state_name,
       c.country_id, co.country_name,
       c.pin, c.phone, c.mobile, c.email, c.whatsapp_no,
       c.gst_no, c.ie_code, c.iso_number, c.logo_path, c.status,
       c.created_at, c.updated_at
FROM companies c
LEFT JOIN places p ON p.place_id = c.place_id
LEFT JOIN regions r ON r.region_id = c.region_id
LEFT JOIN states s ON s.state_id = c.state_id
LEFT JOIN countries co ON co.country_id = c.country_id
"""


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _ensure_refs(cursor, place_id: int, region_id: int, state_id: int, country_id: int) -> None:
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


async def _save_logo(logo: UploadFile | None) -> str | None:
    if logo is None or not logo.filename:
        return None

    extension = Path(logo.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Logo must be an image file (png, jpg, jpeg, gif, webp, svg)",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename
    content = await logo.read()
    if not content:
        raise HTTPException(status_code=400, detail="Logo file is empty")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Logo file must be 5MB or smaller")

    destination.write_bytes(content)
    return f"/uploads/logos/{filename}"


def _delete_logo_file(logo_path: str | None) -> None:
    if not logo_path:
        return
    filename = Path(logo_path).name
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        file_path.unlink()


@router.get("", response_model=list[CompanyOut])
def list_companies(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    COMPANY_SELECT
                    + """
                    WHERE c.company_name LIKE %s
                       OR c.company_code LIKE %s
                       OR c.email LIKE %s
                       OR c.gst_no LIKE %s
                       OR p.place_name LIKE %s
                    ORDER BY c.company_id
                    """,
                    (term, term, term, term, term),
                )
            else:
                cursor.execute(COMPANY_SELECT + " ORDER BY c.company_id")
            rows = cursor.fetchall()
            return [_row_to_company(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                COMPANY_SELECT + " WHERE c.company_id = %s",
                (company_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Company not found")
            return _row_to_company(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=CompanyOut, status_code=201)
async def create_company(
    company_name: str = Form(...),
    company_code: str = Form(...),
    address: str = Form(...),
    address2: str = Form(""),
    place_id: int = Form(...),
    region_id: int = Form(...),
    state_id: int = Form(...),
    country_id: int = Form(...),
    pin: str = Form(...),
    phone: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    whatsapp_no: str = Form(""),
    gst_no: str = Form(""),
    ie_code: str = Form(""),
    iso_number: str = Form(""),
    status: RecordStatus = Form(RecordStatus.Active),
    logo: UploadFile | None = File(None),
):
    company_name = company_name.strip()
    company_code = company_code.strip().upper()
    address = address.strip()
    pin = pin.strip()

    if not company_name or not company_code or not address or not pin:
        raise HTTPException(
            status_code=400,
            detail="Name, Company Code, Address, and Pin are required",
        )

    logo_path = await _save_logo(logo)

    try:
        with db_cursor() as cursor:
            _ensure_refs(cursor, place_id, region_id, state_id, country_id)
            cursor.execute(
                """
                INSERT INTO companies (
                  company_name, company_code, address, address2,
                  place_id, region_id, state_id, country_id, pin,
                  phone, mobile, email, whatsapp_no, gst_no, ie_code, iso_number,
                  logo_path, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    company_name,
                    company_code,
                    address,
                    _clean(address2),
                    place_id,
                    region_id,
                    state_id,
                    country_id,
                    pin,
                    _clean(phone),
                    _clean(mobile),
                    _clean(email),
                    _clean(whatsapp_no),
                    _clean(gst_no),
                    _clean(ie_code),
                    _clean(iso_number),
                    logo_path,
                    status.value,
                ),
            )
            new_id = cursor.lastrowid
            cursor.execute(COMPANY_SELECT + " WHERE c.company_id = %s", (new_id,))
            row = cursor.fetchone()
            return _row_to_company(row)
    except HTTPException:
        _delete_logo_file(logo_path)
        raise
    except mariadb.IntegrityError:
        _delete_logo_file(logo_path)
        raise HTTPException(
            status_code=409,
            detail="Company Code or Company Name already exists",
        )
    except mariadb.Error as error:
        _delete_logo_file(logo_path)
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: int,
    company_name: str = Form(...),
    company_code: str = Form(...),
    address: str = Form(...),
    address2: str = Form(""),
    place_id: int = Form(...),
    region_id: int = Form(...),
    state_id: int = Form(...),
    country_id: int = Form(...),
    pin: str = Form(...),
    phone: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    whatsapp_no: str = Form(""),
    gst_no: str = Form(""),
    ie_code: str = Form(""),
    iso_number: str = Form(""),
    status: RecordStatus = Form(...),
    logo: UploadFile | None = File(None),
):
    company_name = company_name.strip()
    company_code = company_code.strip().upper()
    address = address.strip()
    pin = pin.strip()

    if not company_name or not company_code or not address or not pin:
        raise HTTPException(
            status_code=400,
            detail="Name, Company Code, Address, and Pin are required",
        )

    new_logo_path = await _save_logo(logo)

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT company_id, logo_path FROM companies WHERE company_id = %s",
                (company_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Company not found")

            _ensure_refs(cursor, place_id, region_id, state_id, country_id)
            logo_path = new_logo_path if new_logo_path else existing.get("logo_path")

            cursor.execute(
                """
                UPDATE companies
                SET company_name = %s,
                    company_code = %s,
                    address = %s,
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
                    ie_code = %s,
                    iso_number = %s,
                    logo_path = %s,
                    status = %s
                WHERE company_id = %s
                """,
                (
                    company_name,
                    company_code,
                    address,
                    _clean(address2),
                    place_id,
                    region_id,
                    state_id,
                    country_id,
                    pin,
                    _clean(phone),
                    _clean(mobile),
                    _clean(email),
                    _clean(whatsapp_no),
                    _clean(gst_no),
                    _clean(ie_code),
                    _clean(iso_number),
                    logo_path,
                    status.value,
                    company_id,
                ),
            )

            if new_logo_path and existing.get("logo_path"):
                _delete_logo_file(existing.get("logo_path"))

            cursor.execute(COMPANY_SELECT + " WHERE c.company_id = %s", (company_id,))
            row = cursor.fetchone()
            return _row_to_company(row)
    except HTTPException:
        _delete_logo_file(new_logo_path)
        raise
    except mariadb.IntegrityError:
        _delete_logo_file(new_logo_path)
        raise HTTPException(
            status_code=409,
            detail="Company Code or Company Name already exists",
        )
    except mariadb.Error as error:
        _delete_logo_file(new_logo_path)
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT logo_path FROM companies WHERE company_id = %s",
                (company_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Company not found")

            cursor.execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
            _delete_logo_file(existing.get("logo_path"))
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
