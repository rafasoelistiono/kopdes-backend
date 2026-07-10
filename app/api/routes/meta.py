from fastapi import APIRouter, HTTPException
from app.repositories.schema_repository import list_tables, list_columns

router = APIRouter()


@router.get("/meta/tables")
def get_tables():
    tables = list_tables()
    return {"success": True, "data": [{"table_name": t} for t in tables]}


@router.get("/meta/tables/{table_name}/columns")
def get_table_columns(table_name: str):
    tables = list_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    cols = list_columns(table_name)
    return {"success": True, "data": cols}
