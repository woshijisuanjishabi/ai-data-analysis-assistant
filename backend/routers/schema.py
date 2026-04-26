"""
/db/schema — 业务数据库 schema 概览（前端可用于侧边提示）。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database.connection import get_business_db


router = APIRouter(prefix="/db", tags=["database"])


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool


class TableInfo(BaseModel):
    name: str
    row_count: int
    columns: list[ColumnInfo]


@router.get("/schema", response_model=list[TableInfo])
def get_schema(db: Session = Depends(get_business_db)):
    inspector = inspect(db.bind)
    out: list[TableInfo] = []
    for tbl in sorted(inspector.get_table_names()):
        cols = [
            ColumnInfo(
                name=c["name"],
                type=str(c["type"]),
                nullable=bool(c.get("nullable", True)),
                primary_key=bool(c.get("primary_key", False)),
            )
            for c in inspector.get_columns(tbl)
        ]
        n = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
        out.append(TableInfo(name=tbl, row_count=int(n), columns=cols))
    return out
