"""
Pydantic models for SentinelSight API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CameraBase(BaseModel):
    name: str = Field(..., description="Camera name")
    location_tag: Optional[str] = Field(None, description="Hierarchical location tag")
    rtsp_url: str = Field(..., description="RTSP stream URL")


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location_tag: Optional[str] = None
    rtsp_url: Optional[str] = None


class Camera(CameraBase):
    id: int
    status: str = "offline"
    fps: float = 0.0
    last_frame_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ZoneBase(BaseModel):
    camera_id: int
    name: str
    type: str = "polygon"  # polygon or rectangle
    coordinates: List[List[int]] = Field(..., description="Array of [x, y] points")


class ZoneCreate(ZoneBase):
    pass


class Zone(ZoneBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    camera_id: int
    timestamp: datetime
    rule_type: str
    object_type: Optional[str] = None
    confidence: Optional[float] = None
    bbox: Optional[List[int]] = None
    snapshot_path: Optional[str] = None
    priority: str = "medium"
    status: str = "new"
    metadata: Optional[dict] = None


class Event(EventBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    subsystems: dict
    uptime_seconds: float


class MetricsResponse(BaseModel):
    cameras: List[dict]
    system: dict
