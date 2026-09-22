from fastapi import APIRouter, HTTPException, Query
import mariadb

from app.db import db_cursor
from app.schemas import RouteCreate, RouteOut, RouteUpdate

router = APIRouter(prefix="/routes", tags=["routes"])


def _row_to_route(row: dict) -> RouteOut:
    return RouteOut(
        route_id=row["route_id"],
        route_code=row["route_code"],
        region_id=row["region_id"],
        region_name=row.get("region_name"),
        status=row["status"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _ensure_region_exists(cursor, region_id: int) -> None:
    cursor.execute(
        "SELECT region_id FROM regions WHERE region_id = %s",
        (region_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Selected region does not exist")


@router.get("", response_model=list[RouteOut])
def list_routes(search: str | None = Query(default=None)):
    try:
        with db_cursor() as cursor:
            if search and search.strip():
                term = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT rt.route_id, rt.route_code, rt.region_id, rg.region_name,
                           rt.status, rt.created_at, rt.updated_at
                    FROM routes rt
                    LEFT JOIN regions rg ON rg.region_id = rt.region_id
                    WHERE rt.route_code LIKE %s OR rg.region_name LIKE %s
                    ORDER BY rt.route_id
                    """,
                    (term, term),
                )
            else:
                cursor.execute(
                    """
                    SELECT rt.route_id, rt.route_code, rt.region_id, rg.region_name,
                           rt.status, rt.created_at, rt.updated_at
                    FROM routes rt
                    LEFT JOIN regions rg ON rg.region_id = rt.region_id
                    ORDER BY rt.route_id
                    """
                )
            rows = cursor.fetchall()
            return [_row_to_route(row) for row in rows]
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT rt.route_id, rt.route_code, rt.region_id, rg.region_name,
                       rt.status, rt.created_at, rt.updated_at
                FROM routes rt
                LEFT JOIN regions rg ON rg.region_id = rt.region_id
                WHERE rt.route_id = %s
                """,
                (route_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Route not found")
            return _row_to_route(row)
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.post("", response_model=RouteOut, status_code=201)
def create_route(payload: RouteCreate):
    route_code = payload.route_code.strip().upper()
    if not route_code:
        raise HTTPException(status_code=400, detail="Route Code is required")

    try:
        with db_cursor() as cursor:
            _ensure_region_exists(cursor, payload.region_id)
            cursor.execute(
                """
                INSERT INTO routes (route_code, region_id, status)
                VALUES (%s, %s, %s)
                """,
                (route_code, payload.region_id, payload.status.value),
            )
            new_route_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT rt.route_id, rt.route_code, rt.region_id, rg.region_name,
                       rt.status, rt.created_at, rt.updated_at
                FROM routes rt
                LEFT JOIN regions rg ON rg.region_id = rt.region_id
                WHERE rt.route_id = %s
                """,
                (new_route_id,),
            )
            row = cursor.fetchone()
            return _row_to_route(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Route Code already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.put("/{route_id}", response_model=RouteOut)
def update_route(route_id: int, payload: RouteUpdate):
    route_code = payload.route_code.strip().upper()
    if not route_code:
        raise HTTPException(status_code=400, detail="Route Code is required")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT route_id FROM routes WHERE route_id = %s",
                (route_id,),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Route not found")

            _ensure_region_exists(cursor, payload.region_id)
            cursor.execute(
                """
                UPDATE routes
                SET route_code = %s, region_id = %s, status = %s
                WHERE route_id = %s
                """,
                (route_code, payload.region_id, payload.status.value, route_id),
            )
            cursor.execute(
                """
                SELECT rt.route_id, rt.route_code, rt.region_id, rg.region_name,
                       rt.status, rt.created_at, rt.updated_at
                FROM routes rt
                LEFT JOIN regions rg ON rg.region_id = rt.region_id
                WHERE rt.route_id = %s
                """,
                (route_id,),
            )
            row = cursor.fetchone()
            return _row_to_route(row)
    except HTTPException:
        raise
    except mariadb.IntegrityError:
        raise HTTPException(status_code=409, detail="Route Code already exists")
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error


@router.delete("/{route_id}", status_code=204)
def delete_route(route_id: int):
    try:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM routes WHERE route_id = %s", (route_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Route not found")
    except HTTPException:
        raise
    except mariadb.Error as error:
        raise HTTPException(status_code=503, detail=f"Database error: {error}") from error
