from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from api.database import get_db
from api.schemas import (
    APIHealthCheck,
    TopProductResponse,
    ChannelActivityDetail,
    MessageSearchResponse,
    VisualContentStat
)

app = FastAPI(
    title="Medical Warehouse Analytical API",
    description="Production REST API layer exposing transformed dbt star schema metrics and object detection data.",
    version="1.0.0"
)

@app.get("/", response_model=APIHealthCheck, tags=["System Health"])
def check_api_and_warehouse_health(db: Session = Depends(get_db)):
    """Verifies that the API instance and backend database warehouse are fully active."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "warehouse": "connected and accessible"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Database warehouse connection layer failure: {str(e)}"
        )

# Endpoint 1 — Top Products
@app.get("/api/reports/top-products", response_model=List[TopProductResponse], tags=["Analytics Reports"])
def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top records to pull"),
    db: Session = Depends(get_db)
):
    """Parses message text to isolate high-frequency medical or cosmetic product names."""
    query = text("""
        SELECT 
            word as product_name,
            COUNT(*) as mention_count
        FROM (
            SELECT regexp_split_to_table(lower(message_text), '\s+') as word 
            FROM staging.fct_messages 
            WHERE message_text IS NOT NULL
        ) sub
        WHERE length(word) > 4 
          AND word IN ('paracetamol', 'amoxicillin', 'ibuprofen', 'capsule', 'syrup', 'tablet', 'vitamin', 'cosmetics', 'serum', 'gel')
        GROUP BY word
        ORDER BY mention_count DESC
        LIMIT :limit;
    """)
    try:
        result = db.execute(query, {"limit": limit}).fetchall()
        return [{"product_name": r.product_name, "mention_count": r.mention_count} for r in result]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Endpoint 2 — Channel Activity
@app.get("/api/channels/{channel_name}/activity", response_model=ChannelActivityDetail, tags=["Channel Metrics"])
def get_channel_activity(
    channel_name: str = Path(..., description="The exact string name of the target channel folder"),
    db: Session = Depends(get_db)
):
    """Fetches total message counts and transaction performance for a specific isolated channel."""
    query = text("""
        SELECT 
            dc.channel_name,
            COUNT(fm.message_id) as total_messages,
            COALESCE(AVG(fm.view_count), 0)::float as avg_views,
            COALESCE(AVG(fm.forward_count), 0)::float as avg_forwards
        FROM staging.fct_messages fm
        JOIN staging.dim_channels dc ON fm.channel_key = dc.channel_key
        WHERE LOWER(dc.channel_name) = LOWER(:channel_name)
        GROUP BY dc.channel_name;
    """)
    try:
        row = db.execute(query, {"channel_name": channel_name}).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Channel tracking name '{channel_name}' could not be located inside our warehouse staging logs."
            )
        return {
            "channel_name": row.channel_name,
            "total_messages": row.total_messages,
            "avg_views": round(row.avg_views, 2),
            "avg_forwards": round(row.avg_forwards, 2)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Endpoint 3 — Message Search
@app.get("/api/search/messages", response_model=List[MessageSearchResponse], tags=["Warehouse Search"])
def search_messages(
    query: str = Query(..., alias="query", description="Keyword search string parameter (e.g. paracetamol)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Executes full-text keyword searches against production warehouse tables using safe parameter bindings."""
    sql = text("""
        SELECT message_id, channel_key, date_key, message_text, view_count, forward_count
        FROM staging.fct_messages
        WHERE message_text ILIKE :search_pattern
        LIMIT :limit;
    """)
    try:
        result = db.execute(sql, {"search_pattern": f"%{query}%", "limit": limit}).fetchall()
        return [
            {
                "message_id": r.message_id,
                "channel_key": r.channel_key,
                "date_key": r.date_key,
                "message_text": r.message_text,
                "view_count": r.view_count,
                "forward_count": r.forward_count
            }
            for r in result
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Endpoint 4 — Visual Content Stats
@app.get("/api/reports/visual-content", response_model=List[VisualContentStat], tags=["Analytics Reports"])
def get_visual_content_stats(db: Session = Depends(get_db)):
    """Computes distribution densities and view trends grouped by YOLOv8 visual classification tags."""
    query = text("""
        SELECT 
            dc.channel_name,
            fid.image_category,
            COUNT(*) as total_images,
            COALESCE(AVG(fm.view_count), 0)::float as average_views
        FROM staging.fct_image_detections fid
        JOIN staging.fct_messages fm ON fid.message_id = fm.message_id
        JOIN staging.dim_channels dc ON fm.channel_key = dc.channel_key
        GROUP BY dc.channel_name, fid.image_category
        ORDER BY dc.channel_name, total_images DESC;
    """)
    try:
        result = db.execute(query).fetchall()
        return [
            {
                "channel_name": r.channel_name,
                "image_category": r.image_category,
                "total_images": r.total_images,
                "average_views": round(r.average_views, 2)
            }
            for r in result
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))