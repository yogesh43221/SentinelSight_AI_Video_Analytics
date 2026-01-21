# 🛡️ SentinelSight - AI Video Analytics Platform

A production-ready AI-powered video analytics platform for real-time CCTV monitoring with object detection, zone-based rules, and event management.

## 🌟 Features

### Core Capabilities
- **Multi-Camera Support**: Manage up to 4 concurrent RTSP camera streams
- **Real-Time Object Detection**: YOLOv8-powered person and vehicle detection
- **Zone-Based Rules**: Define polygon/rectangle zones with custom rules
- **Event Generation**: Intrusion and loitering detection with configurable thresholds
- **Web Dashboard**: Modern React UI with real-time updates
- **Analytics**: Event trends, heatmaps, and performance metrics
- **MQTT Integration**: Publish events for smart home/automation systems

### Technical Highlights
- ✅ Auto-reconnect with exponential backoff
- ✅ Frame queue management (prevents memory overflow)
- ✅ Event deduplication (5-second window)
- ✅ Performance monitoring (FPS, latency, queue depth)
- ✅ Privacy-first (local processing, no cloud)
- ✅ GDPR-friendly (events + snapshots only, configurable retention)
- ✅ Docker deployment with health checks

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB RAM minimum
- RTSP camera streams or test videos

### Installation

1. **Clone/Navigate to Project**
```bash
cd f:/MyProjects_YJ/Internshala/Saimax_Tech_Solutions_AI_Job
```

2. **Start Services**
```bash
docker-compose up -d
```

3. **Access Dashboard**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### First-Time Setup

The YOLO model will be downloaded automatically on first run. This may take a few minutes.

---

## 📹 Adding Cameras

### Via Web UI
1. Navigate to http://localhost:3000
2. Click "Add Camera"
3. Enter:
   - **Name**: Front Entrance
   - **RTSP URL**: `rtsp://your-camera-url`
   - **Location Tag**: Building A - Floor 1 (optional)
4. Click "Add"

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Front Entrance",
    "rtsp_url": "rtsp://admin:pass@192.168.1.100:554/stream",
    "location_tag": "Building A - Floor 1"
  }'
```

### Using Test Streams

**Public RTSP Test Stream:**
```
rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4
```

**Local Video File (using FFmpeg):**
```bash
ffmpeg -re -stream_loop -1 -i test_video.mp4 -f rtsp rtsp://localhost:8554/stream
```

---

## 🎯 Defining Zones

Zones are areas within a camera's view where rules are applied.

### Via Web UI
1. Go to Camera Management
2. Click "Add Zone" on a camera card
3. Enter:
   - **Zone Name**: Restricted Area
   - **Coordinates**: `[[100,100],[200,100],[200,200],[100,200]]`
4. Click "Add Zone"

### Coordinate Format
- **Polygon**: Array of [x, y] points (minimum 3 points)
  ```json
  [[100,100], [200,100], [200,200], [100,200]]
  ```
- **Rectangle**: Two points (top-left, bottom-right)
  ```json
  [[0,0], [640,480]]
  ```

---

## ⚙️ Configuration

Edit `config/config.yaml`:

```yaml
system:
  fps_target: 15
  max_cameras: 4
  snapshot_retention_days: 30
  log_level: INFO

inference:
  model: yolov8n.pt
  confidence_threshold: 0.5
  device: cpu  # or cuda for GPU

rules:
  intrusion:
    enabled: true
    priority: high
  loitering:
    enabled: true
    threshold_seconds: 30
    priority: medium

mqtt:
  enabled: true
  broker: localhost
  port: 1883
```

---

## 📊 API Reference

### Camera Endpoints
- `GET /api/v1/cameras` - List all cameras
- `POST /api/v1/cameras` - Add camera
- `PUT /api/v1/cameras/{id}` - Update camera
- `DELETE /api/v1/cameras/{id}` - Delete camera

### Event Endpoints
- `GET /api/v1/events` - Query events (supports filtering)
- `GET /api/v1/events/{id}` - Get event details
- `GET /api/v1/events/stats` - Get statistics

### Zone Endpoints
- `GET /api/v1/zones?camera_id={id}` - List zones
- `POST /api/v1/zones` - Create zone
- `PUT /api/v1/zones/{id}` - Update zone
- `DELETE /api/v1/zones/{id}` - Delete zone

### System Endpoints
- `GET /api/v1/health` - System health check
- `GET /api/v1/metrics` - Performance metrics

Full API documentation: http://localhost:8000/docs

---

## 🧪 Testing

### Manual Testing
1. Add a test camera (use public RTSP stream)
2. Define a zone covering part of the video
3. Wait for objects (people/vehicles) to enter the zone
4. Check Events page for generated alerts
5. View Analytics dashboard for statistics

### API Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health

# List cameras
curl http://localhost:8000/api/v1/cameras

# Query events
curl "http://localhost:8000/api/v1/events?limit=10"

# Get metrics
curl http://localhost:8000/api/v1/metrics
```

---

## 🐛 Troubleshooting

### Camera shows "Offline"
- Verify RTSP URL is correct
- Check network connectivity to camera
- Review logs: `docker-compose logs backend`

### No events generated
- Ensure zones are defined for the camera
- Check if objects (person/vehicle) are in frame
- Verify confidence threshold (default: 0.5)
- Check logs for inference errors

### High CPU usage
- Reduce `fps_target` in config
- Use smaller YOLO model (yolov8n.pt)
- Limit number of concurrent cameras

### MQTT not working
- Ensure Mosquitto container is running
- Check MQTT broker address in config
- Test with: `mosquitto_sub -h localhost -t "sentinelsight/#" -v`

---

## 📁 Project Structure

```
sentinelsight/
├── backend/
│   ├── api/              # FastAPI application
│   ├── services/         # Core services
│   ├── database/         # Database layer
│   └── config/           # Configuration
├── frontend/
│   └── src/
│       ├── pages/        # React pages
│       ├── components/   # React components
│       └── services/     # API client
├── config/               # YAML configuration
├── data/                 # Database & snapshots
├── docs/                 # Documentation
├── docker-compose.yml
└── README.md
```

---

## 🔒 Security & Privacy

### Data Minimization
- Only events + snapshots stored (no full video)
- Configurable retention period (default: 30 days)
- Automatic cleanup of old events

### Local Processing
- 100% local inference (no cloud uploads)
- All data stays on-premise
- MQTT events are opt-in

### GDPR Compliance
- ✅ Data minimization
- ✅ Local processing
- ✅ Retention policy
- ⚠️ User consent management (not implemented)
- ⚠️ Right to be forgotten (manual)

---

## 🚧 Known Limitations

1. **No Authentication**: Single-user mode (no login required)
2. **Limited Scalability**: Max 4 cameras on CPU inference
3. **Basic Tracking**: Simple centroid tracking (no persistent IDs)
4. **Zone Editor**: JSON-based (no GUI polygon drawing)
5. **No Video Recording**: Events + snapshots only

---

## 🗺️ Roadmap

### Week 1: Performance & Scalability
- [ ] PostgreSQL migration
- [ ] GPU acceleration (TensorRT/OpenVINO)
- [ ] WebSocket for real-time updates
- [ ] Multi-model support (face recognition, LPR)

### Week 2: Security & Features
- [ ] JWT authentication
- [ ] Role-based access control
- [ ] Clip recording (pre/post event buffers)
- [ ] GUI zone editor
- [ ] Email/SMS notifications

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built using:
- **YOLOv8** (Ultralytics) for object detection
- **FastAPI** for backend API
- **React** + **Material-UI** for frontend
- **OpenCV** for video processing
- **Recharts** for analytics visualization

Inspired by: Milestone VMS, BriefCam, Avigilon, Frigate NVR

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs: `docker-compose logs`
3. Check API health: http://localhost:8000/api/v1/health

---

**Built for Saimax Tech Solutions AI Job Assignment**
