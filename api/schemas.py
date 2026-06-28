from pydantic import BaseModel, Field
from typing import Optional, List

# Core System Baseline Health Contract
class APIHealthCheck(BaseModel):
    status: str
    warehouse: str

# Endpoint 1: Top Products Response Data Structure
class TopProductResponse(BaseModel):
    product_name: str = Field(..., description="The name of the medical or cosmetic product term")
    mention_count: int = Field(..., description="Total frequency of appearances across all channels")

    class Config:
        from_attributes = True

# Endpoint 2: Channel Activity Trends Schema
class ChannelActivityDetail(BaseModel):
    channel_name: str = Field(..., description="The unique name tracking the Telegram channel")
    total_messages: int = Field(..., description="Total messages logged inside the fact layer")
    avg_views: float = Field(..., description="Average post view velocity")
    avg_forwards: float = Field(..., description="Average post share frequency")

    class Config:
        from_attributes = True

# Endpoint 3: Case-Insensitive Search Payload Contract
class MessageSearchResponse(BaseModel):
    message_id: int
    channel_key: str
    date_key: int
    message_text: Optional[str] = None
    view_count: int
    forward_count: int

    class Config:
        from_attributes = True

# Endpoint 4: Computer Vision Joined Analytics Contract
class VisualContentStat(BaseModel):
    channel_name: str
    image_category: str = Field(..., description="YOLOv8 computed classification category")
    total_images: int = Field(..., description="Volume count of unique visual media items")
    average_views: float = Field(..., description="Mean engagement baseline for this layout format")

    class Config:
        from_attributes = True