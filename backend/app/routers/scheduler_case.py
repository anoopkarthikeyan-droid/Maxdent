import uuid
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
import mariadb

from app.db import db_cursor
from app.schemas import CaseApprovalStatus, CaseFileKind, CaseFileOut, CaseStudyIn, CaseStudyOut

router = APIRouter(prefix="/schedulers", tags=["scheduler-cases"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "cases"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
VIDEO_KINDS = {CaseFileKind.video, CaseFileKind.concern_video}
IMAGE_MAX_BYTES = 10 * 1024 * 1024
VIDEO_MAX_BYTES = 80 * 1024 * 1024
FILE_KINDS = [item.value for item in CaseFileKind]

CASE_COLUMNS = [
    "working_doctor_name",
    "clinic_name",
    "mobile_no",
    "email_id",
    "patient_name",
    "age",
    "sex",
    "patient_availability",
    "next_appointment_date",
    "stl_model_quality",
    "chief_complaint",
    "other_concerns",
    "type_of_plan",
    "type_of_case_study",
    "suggestions_from_doctor",
    "deciduous_tooth",
    "rotation",
    "molar_relation",
    "overjet",
    "overbite",
    "missing_teeth",
    "midline_shift",
    "crossbite",
    "arch_shape",
    "deepbite",
    "open_bite",
    "spacing",
    "caries_decay_root_stump",
    "impaction",
    "periodontal_status",
    "extraction",
    "rct",
    "crown_bridge_implant",
    "tongue_thrusting",
    "bruxism",
    "mouth_breathing",
    "thumb_sucking",
    "lip_biting",
    "medications",
    "allergies",
    "remarks",
]

BOOL_COLUMNS = {
    "tongue_thrusting",
    "mouth_breathing",
    "thumb_sucking",
    "lip_biting",
}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _enum_value(value):
    return value.value if value is not None else None


def _delete_upload(file_path: str | None) -> None:
    if not file_path:
        return
    filename = Path(file_path).name
    destination = UPLOAD_DIR / filename
    if destination.exists():
        destination.unlink()


def delete_files_for_details(cursor, detail_ids: list[int]) -> None:
    if not detail_ids:
        return
    placeholders = ", ".join(["%s"] * len(detail_ids))
    cursor.execute(
        f"SELECT file_path FROM scheduler_case_files WHERE scheduler_detail_id IN ({placeholders})",
        tuple(detail_ids),
    )
    for row in cursor.fetchall():
        _delete_upload(row.get("file_path"))


def _empty_files() -> dict[str, list[CaseFileOut]]:
    return {kind: [] for kind in FILE_KINDS}


def _row_to_file(row: dict) -> CaseFileOut:
    return CaseFileOut(
        file_id=row["file_id"],
        scheduler_detail_id=row["scheduler_detail_id"],
        file_kind=row["file_kind"],
        file_path=row["file_path"],
        original_name=row.get("original_name"),
        content_type=row.get("content_type"),
    )


def _load_files(cursor, detail_id: int) -> dict[str, list[CaseFileOut]]:
    grouped = _empty_files()
    cursor.execute(
        """
        SELECT file_id, scheduler_detail_id, file_kind, file_path, original_name, content_type
        FROM scheduler_case_files
        WHERE scheduler_detail_id = %s
        ORDER BY file_id
        """,
        (detail_id,),
    )
    for row in cursor.fetchall():
        grouped[row["file_kind"]].append(_row_to_file(row))
    return grouped


def _payload_values(payload: CaseStudyIn) -> tuple:
    values = []
    for column in CASE_COLUMNS:
        value = getattr(payload, column)
        if column in BOOL_COLUMNS:
            values.append(int(bool(value)))
        elif column in {
            "sex",
            "stl_model_quality",
            "type_of_plan",
            "type_of_case_study",
            "allergies",
        }:
            values.append(_enum_value(value))
        elif column == "next_appointment_date":
            values.append(value)
        elif column == "medications":
            values.append(_clean(value) if isinstance(value, str) else value)
        else:
            values.append(_clean(value) if isinstance(value, str) else value)
    return tuple(values)


def _row_to_case(row: dict, files: dict[str, list[CaseFileOut]], exists: bool) -> CaseStudyOut:
    return CaseStudyOut(
        exists=exists,
        case_id=row.get("case_id"),
        scheduler_detail_id=row["scheduler_detail_id"],
        work_no=row.get("work_no"),
        working_doctor_name=row.get("working_doctor_name"),
        clinic_name=row.get("clinic_name"),
        mobile_no=row.get("mobile_no"),
        email_id=row.get("email_id"),
        patient_name=row.get("patient_name"),
        age=row.get("age"),
        sex=row.get("sex"),
        patient_availability=row.get("patient_availability"),
        next_appointment_date=_as_date(row.get("next_appointment_date")),
        stl_model_quality=row.get("stl_model_quality"),
        chief_complaint=row.get("chief_complaint"),
        other_concerns=row.get("other_concerns"),
        type_of_plan=row.get("type_of_plan"),
        type_of_case_study=row.get("type_of_case_study"),
        suggestions_from_doctor=row.get("suggestions_from_doctor"),
        deciduous_tooth=row.get("deciduous_tooth"),
        rotation=row.get("rotation"),
        molar_relation=row.get("molar_relation"),
        overjet=row.get("overjet"),
        overbite=row.get("overbite"),
        missing_teeth=row.get("missing_teeth"),
        midline_shift=row.get("midline_shift"),
        crossbite=row.get("crossbite"),
        arch_shape=row.get("arch_shape"),
        deepbite=row.get("deepbite"),
        open_bite=row.get("open_bite"),
        spacing=row.get("spacing"),
        caries_decay_root_stump=row.get("caries_decay_root_stump"),
        impaction=row.get("impaction"),
        periodontal_status=row.get("periodontal_status"),
        extraction=row.get("extraction"),
        rct=row.get("rct"),
        crown_bridge_implant=row.get("crown_bridge_implant"),
        tongue_thrusting=bool(row.get("tongue_thrusting")),
        bruxism=row.get("bruxism"),
        mouth_breathing=bool(row.get("mouth_breathing")),
        thumb_sucking=bool(row.get("thumb_sucking")),
        lip_biting=bool(row.get("lip_biting")),
        medications=row.get("medications"),
        allergies=row.get("allergies"),
        remarks=row.get("remarks"),
        approval_status=row.get("approval_status") or CaseApprovalStatus.Pending,
        approved_at=row.get("approved_at"),
        files=files,
    )


def _load_context(cursor, scheduler_id: int, detail_id: int) -> dict:
    cursor.execute(
        """
        SELECT sd.scheduler_detail_id, sd.work_no, sd.patient_name AS detail_patient_name,
               cu.branch_name AS clinic_name, cu.mobile, cu.email
        FROM scheduler_details sd
        JOIN schedulers sch ON sch.scheduler_id = sd.scheduler_id
        JOIN customers cu ON cu.customer_id = sch.customer_id
        WHERE sd.scheduler_id = %s AND sd.scheduler_detail_id = %s
        """,
        (scheduler_id, detail_id),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scheduler work detail not found")
    return row


def _fetch_case(cursor, detail_id: int) -> dict | None:
    cursor.execute(
        f"""
        SELECT case_id, scheduler_detail_id, {", ".join(CASE_COLUMNS)},
               approval_status, approved_at
        FROM scheduler_case_studies
        WHERE scheduler_detail_id = %s
        """,
        (detail_id,),
    )
    return cursor.fetchone()


def _is_approved(row: dict | None) -> bool:
    return bool(row) and row.get("approval_status") == CaseApprovalStatus.Approved.value


def _require_pending(row: dict | None) -> None:
    if _is_approved(row):
        raise HTTPException(
            status_code=409,
            detail="Approved case studies cannot be changed. Unlock them first.",
        )


@router.get("/{scheduler_id}/details/{detail_id}/case", response_model=CaseStudyOut)
def get_case_study(scheduler_id: int, detail_id: int):
    try:
        with db_cursor() as cursor:
            context = _load_context(cursor, scheduler_id, detail_id)
            files = _load_files(cursor, detail_id)
            saved = _fetch_case(cursor, detail_id)
            if saved:
                saved["work_no"] = context["work_no"]
                return _row_to_case(saved, files, True)
            return _row_to_case(
                {
                    "case_id": None,
                    "scheduler_detail_id": detail_id,
                    "work_no": context["work_no"],
                    "clinic_name": context.get("clinic_name"),
                    "mobile_no": context.get("mobile"),
                    "email_id": context.get("email"),
                    "patient_name": context.get("detail_patient_name"),
                },
                files,
                False,
            )
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{scheduler_id}/details/{detail_id}/case", response_model=CaseStudyOut)
def save_case_study(scheduler_id: int, detail_id: int, payload: CaseStudyIn):
    try:
        with db_cursor() as cursor:
            context = _load_context(cursor, scheduler_id, detail_id)
            values = _payload_values(payload)
            assignments = ", ".join(f"{column} = %s" for column in CASE_COLUMNS)
            existing = _fetch_case(cursor, detail_id)
            _require_pending(existing)
            if existing:
                cursor.execute(
                    f"""
                    UPDATE scheduler_case_studies
                    SET {assignments}
                    WHERE scheduler_detail_id = %s
                    """,
                    (*values, detail_id),
                )
            else:
                cursor.execute(
                    f"""
                    INSERT INTO scheduler_case_studies (
                        scheduler_detail_id, {", ".join(CASE_COLUMNS)}
                    )
                    VALUES (%s, {", ".join(["%s"] * len(CASE_COLUMNS))})
                    """,
                    (detail_id, *values),
                )
            saved = _fetch_case(cursor, detail_id)
            saved["work_no"] = context["work_no"]
            return _row_to_case(saved, _load_files(cursor, detail_id), True)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


async def _store_upload(kind: CaseFileKind, upload: UploadFile) -> tuple[str, str | None, str | None]:
    if not upload.filename:
        raise HTTPException(status_code=400, detail="A file is required")
    extension = Path(upload.filename).suffix.lower()
    allowed = VIDEO_EXTENSIONS if kind in VIDEO_KINDS else IMAGE_EXTENSIONS
    if extension not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Video must be mp4, webm, mov, avi, or mkv"
            if kind in VIDEO_KINDS
            else "Image must be png, jpg, jpeg, gif, or webp",
        )
    content = await upload.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    limit = VIDEO_MAX_BYTES if kind in VIDEO_KINDS else IMAGE_MAX_BYTES
    if len(content) > limit:
        raise HTTPException(
            status_code=400,
            detail="Video must be 80MB or smaller"
            if kind in VIDEO_KINDS
            else "Image must be 10MB or smaller",
        )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(content)
    return f"/uploads/cases/{filename}", upload.filename, upload.content_type


@router.post(
    "/{scheduler_id}/details/{detail_id}/case/files",
    response_model=list[CaseFileOut],
)
async def upload_case_files(
    scheduler_id: int,
    detail_id: int,
    kind: CaseFileKind,
    files: list[UploadFile] = File(...),
):
    saved_paths: list[str] = []
    try:
        with db_cursor() as cursor:
            _load_context(cursor, scheduler_id, detail_id)
            _require_pending(_fetch_case(cursor, detail_id))
            stored: list[CaseFileOut] = []
            for upload in files:
                file_path, original_name, content_type = await _store_upload(kind, upload)
                saved_paths.append(file_path)
                cursor.execute(
                    """
                    INSERT INTO scheduler_case_files (
                        scheduler_detail_id, file_kind, file_path, original_name, content_type
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (detail_id, kind.value, file_path, original_name, content_type),
                )
                stored.append(
                    CaseFileOut(
                        file_id=cursor.lastrowid,
                        scheduler_detail_id=detail_id,
                        file_kind=kind,
                        file_path=file_path,
                        original_name=original_name,
                        content_type=content_type,
                    )
                )
            return stored
    except HTTPException:
        for path in saved_paths:
            _delete_upload(path)
        raise
    except mariadb.Error as error:
        for path in saved_paths:
            _delete_upload(path)
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete(
    "/{scheduler_id}/details/{detail_id}/case/files/{file_id}",
    status_code=204,
)
def delete_case_file(scheduler_id: int, detail_id: int, file_id: int):
    try:
        with db_cursor() as cursor:
            _load_context(cursor, scheduler_id, detail_id)
            _require_pending(_fetch_case(cursor, detail_id))
            cursor.execute(
                """
                SELECT file_id, file_path
                FROM scheduler_case_files
                WHERE file_id = %s AND scheduler_detail_id = %s
                """,
                (file_id, detail_id),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="File not found")
            cursor.execute(
                "DELETE FROM scheduler_case_files WHERE file_id = %s",
                (file_id,),
            )
            _delete_upload(row.get("file_path"))
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


def _set_approval(cursor, scheduler_id: int, detail_id: int, status: CaseApprovalStatus) -> CaseStudyOut:
    context = _load_context(cursor, scheduler_id, detail_id)
    saved = _fetch_case(cursor, detail_id)
    if not saved:
        raise HTTPException(status_code=400, detail="Save the case study before approval")
    current = saved.get("approval_status")
    if status == CaseApprovalStatus.Approved and current == CaseApprovalStatus.Approved.value:
        raise HTTPException(status_code=400, detail="Case study is already approved")
    if status == CaseApprovalStatus.Pending and current != CaseApprovalStatus.Approved.value:
        raise HTTPException(status_code=400, detail="Case study is not approved")
    cursor.execute(
        """
        UPDATE scheduler_case_studies
        SET approval_status = %s, approved_at = %s
        WHERE scheduler_detail_id = %s
        """,
        (
            status.value,
            datetime.now() if status == CaseApprovalStatus.Approved else None,
            detail_id,
        ),
    )
    updated = _fetch_case(cursor, detail_id)
    updated["work_no"] = context["work_no"]
    return _row_to_case(updated, _load_files(cursor, detail_id), True)


@router.post(
    "/{scheduler_id}/details/{detail_id}/case/approve",
    response_model=CaseStudyOut,
)
def approve_case_study(scheduler_id: int, detail_id: int):
    try:
        with db_cursor() as cursor:
            return _set_approval(cursor, scheduler_id, detail_id, CaseApprovalStatus.Approved)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post(
    "/{scheduler_id}/details/{detail_id}/case/unapprove",
    response_model=CaseStudyOut,
)
def unapprove_case_study(scheduler_id: int, detail_id: int):
    try:
        with db_cursor() as cursor:
            return _set_approval(cursor, scheduler_id, detail_id, CaseApprovalStatus.Pending)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
