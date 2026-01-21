"""
Main FastAPI application for SentinelSight
"""
import logging
import sys
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List
import psutil

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.models import (
    Camera, CameraCreate, CameraUpdate,
    Zone, ZoneCreate,
    Event,
    HealthResponse, MetricsResponse
)
from backend.services.camera_manager import get_camera_manager
from backend.services.zone_manager import get_zone_manager
from backend.services.event_store import get_event_store
from backend.services.processing_coordinator import get_processing_coordinator
from backend.services.inference_engine import get_inference_engine
from backend.services.mqtt_publisher import get_mqtt_publisher
from backend.database.db import get_db, close_db
from backend.config.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup time for uptime calculation
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info("Starting SentinelSight API...")
    
    # Initialize database
    get_db()
    
    # Start processing for existing cameras
    coordinator = get_processing_coordinator()
    coordinator.start_all_cameras()
    
    yield
    
    # Shutdown
    logger.info("Shutting down SentinelSight API...")
    coordinator.stop_all_cameras()
    get_mqtt_publisher().disconnect()
    close_db()


# Create FastAPI app
app = FastAPI(
    title="SentinelSight API",
    description="AI Video Analytics Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for snapshots
snapshot_dir = Path("../data/snapshots")
snapshot_dir.mkdir(parents=True, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=str(snapshot_dir)), name="snapshots")


# ==================== Camera Endpoints ====================

@app.get("/api/v1/cameras", response_model=dict)
async def get_cameras():
    """Get all cameras"""
    try:
        camera_manager = get_camera_manager()
        cameras = camera_manager.get_all_cameras()
        return {"cameras": cameras, "count": len(cameras)}
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cameras", response_model=dict)
async def create_camera(camera: CameraCreate):
    """Create a new camera"""
    try:
        camera_manager = get_camera_manager()
        
        # Check for duplicate URL
        existing = camera_manager.get_camera_by_url(camera.rtsp_url)
        if existing:
            raise HTTPException(status_code=400, detail="Camera with this RTSP URL already exists")
        
        # Create camera
        new_camera = camera_manager.create_camera(
            name=camera.name,
            rtsp_url=camera.rtsp_url,
            location_tag=camera.location_tag
        )
        
        # Start processing
        coordinator = get_processing_coordinator()
        coordinator.start_camera_processing(new_camera['id'])
        
        return {"camera": new_camera, "status": "created"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/cameras/{camera_id}", response_model=dict)
async def get_camera(camera_id: int):
    """Get camera by ID"""
    try:
        camera_manager = get_camera_manager()
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        return {"camera": camera}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/cameras/{camera_id}", response_model=dict)
async def update_camera(camera_id: int, camera: CameraUpdate):
    """Update camera"""
    try:
        camera_manager = get_camera_manager()
        
        # Check if camera exists
        existing = camera_manager.get_camera(camera_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Update camera
        updated_camera = camera_manager.update_camera(
            camera_id,
            **camera.dict(exclude_unset=True)
        )
        
        return {"camera": updated_camera, "status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/cameras/{camera_id}")
async def delete_camera(camera_id: int):
    """Delete camera"""
    try:
        camera_manager = get_camera_manager()
        coordinator = get_processing_coordinator()
        
        # Stop processing
        coordinator.stop_camera_processing(camera_id)
        
        # Delete camera
        camera_manager.delete_camera(camera_id)
        
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Zone Endpoints ====================

@app.get("/api/v1/zones", response_model=dict)
async def get_zones(camera_id: Optional[int] = Query(None)):
    """Get zones, optionally filtered by camera"""
    try:
        zone_manager = get_zone_manager()
        if camera_id:
            zones = zone_manager.get_zones_by_camera(camera_id)
        else:
            zones = zone_manager.get_all_zones()
        return {"zones": zones, "count": len(zones)}
    except Exception as e:
        logger.error(f"Error getting zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/zones", response_model=dict)
async def create_zone(zone: ZoneCreate):
    """Create a new zone"""
    try:
        zone_manager = get_zone_manager()
        new_zone = zone_manager.create_zone(
            camera_id=zone.camera_id,
            name=zone.name,
            zone_type=zone.type,
            coordinates=zone.coordinates
        )
        return {"zone": new_zone, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/zones/{zone_id}", response_model=dict)
async def update_zone(zone_id: int, zone: ZoneCreate):
    """Update zone"""
    try:
        zone_manager = get_zone_manager()
        updated_zone = zone_manager.update_zone(
            zone_id,
            name=zone.name,
            type=zone.type,
            coordinates=zone.coordinates
        )
        if not updated_zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        return {"zone": updated_zone, "status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/zones/{zone_id}")
async def delete_zone(zone_id: int):
    """Delete zone"""
    try:
        zone_manager = get_zone_manager()
        zone_manager.delete_zone(zone_id)
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Event Endpoints ====================

@app.get("/api/v1/events", response_model=dict)
async def get_events(
    camera_id: Optional[int] = Query(None),
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
    rule: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """Query events with filters"""
    try:
        event_store = get_event_store()
        
        # Parse datetime strings
        from_dt = datetime.fromisoformat(from_time) if from_time else None
        to_dt = datetime.fromisoformat(to_time) if to_time else None
        
        events, total = event_store.query_events(
            camera_id=camera_id,
            from_time=from_dt,
            to_time=to_dt,
            rule_type=rule,
            priority=priority,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return {
            "events": events,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error querying events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/events/stats", response_model=dict)
async def get_event_stats(
    camera_id: Optional[int] = None,
    hours: int = 24
):
    """Get event statistics"""
    try:
        event_store = get_event_store()
        stats = event_store.get_event_stats(camera_id=camera_id, hours=hours)
        return stats
    except Exception as e:
        logger.error(f"Error getting event stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/events/{event_id}", response_model=dict)
async def get_event(event_id: int):
    """Get event by ID"""
    try:
        event_store = get_event_store()
        event = event_store.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"event": event}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))





# ==================== System Endpoints ====================

@app.get("/api/v1/health", response_model=dict)
async def health_check():
    """System health check"""
    try:
        camera_manager = get_camera_manager()
        inference_engine = get_inference_engine()
        mqtt_publisher = get_mqtt_publisher()
        
        cameras = camera_manager.get_all_cameras()
        online_cameras = [c for c in cameras if c['status'] == 'online']
        
        health = {
            "status": "healthy",
            "subsystems": {
                "database": "ok",
                "mqtt": "ok" if mqtt_publisher.is_connected() else "disconnected",
                "cameras": {
                    "total": len(cameras),
                    "online": len(online_cameras),
                    "offline": len(cameras) - len(online_cameras)
                },
                "inference": {
                    "model_loaded": inference_engine.is_model_loaded(),
                    "avg_inference_time_ms": round(inference_engine.get_avg_inference_time(), 2)
                }
            },
            "uptime_seconds": round(time.time() - startup_time, 2)
        }
        
        return health
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/v1/metrics", response_model=dict)
async def get_metrics():
    """Get system metrics"""
    try:
        camera_manager = get_camera_manager()
        inference_engine = get_inference_engine()
        coordinator = get_processing_coordinator()
        
        cameras = camera_manager.get_all_cameras()
        processing_status = coordinator.get_processing_status()
        
        camera_metrics = []
        for camera in cameras:
            camera_id = camera['id']
            status = processing_status.get(camera_id, {})
            
            camera_metrics.append({
                "id": camera_id,
                "name": camera['name'],
                "status": camera['status'],
                "fps": round(camera.get('fps', 0), 2),
                "queue_depth": status.get('queue_depth', 0),
                "inference_time_ms": round(inference_engine.get_avg_inference_time(), 2)
            })
        
        # System metrics
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
        
        return {
            "cameras": camera_metrics,
            "system": system_metrics
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SentinelSight API",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
