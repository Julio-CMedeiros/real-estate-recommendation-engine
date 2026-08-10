"""FastAPI app: routes wrapping the existing rule engine."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection

from recommendation_engine.engine.runner import run_engine

from .deps import get_db, require_api_key
from .schemas import Priority, RecommendationOut, RuleType

app = FastAPI(title="Real Estate Recommendation Engine API")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "internal error"})


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get(
    "/properties/{property_id}/recommendations",
    response_model=list[RecommendationOut],
)
def get_property_recommendations(
    property_id: Annotated[int, Path(gt=0)],
    conn: Annotated[Connection, Depends(get_db)],
    _consumer: Annotated[str, Depends(require_api_key)],
):
    exists = conn.execute(
        text("SELECT 1 FROM properties WHERE id = :id"), {"id": property_id}
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="property not found")
    recs = run_engine(conn, property_id=property_id, dry_run=True)
    return [r.to_dict() for r in recs]


@app.get("/recommendations", response_model=list[RecommendationOut])
def list_recommendations(
    conn: Annotated[Connection, Depends(get_db)],
    _consumer: Annotated[str, Depends(require_api_key)],
    type: RuleType | None = Query(default=None),
    priority: Priority | None = Query(default=None),
):
    recs = run_engine(conn, dry_run=True)
    if type is not None:
        recs = [r for r in recs if r.type == type.value]
    if priority is not None:
        recs = [r for r in recs if r.priority == priority.value]
    return [r.to_dict() for r in recs]
