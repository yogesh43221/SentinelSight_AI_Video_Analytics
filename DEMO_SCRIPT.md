# SentinelSight - Demo Script (3-5 Minutes)

## Preparation (Before Demo)

1. **Start the system**:
   ```bash
   docker-compose up -d
   ```

2. **Wait for services** (30-60 seconds for YOLO model download)

3. **Prepare test stream**: Use public RTSP test stream or local video file

---

## Demo Flow

### **Minute 0:00 - 0:30: Introduction**

**Say**: "SentinelSight is an AI-powered video analytics platform that monitors CCTV cameras in real-time, detects intrusions and loitering, and generates intelligent alerts."

**Show**: 
- Navigate to http://localhost:3000
- Point out the clean, modern dashboard with navigation sidebar

---

### **Minute 0:30 - 1:30: Add Camera**

**Say**: "Let's add a camera to the system."

**Do**:
1. Click "Add Camera" button
2. Fill in:
   - Name: "Front Entrance"
   - RTSP URL: `rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4`
   - Location: "Building A - Floor 1"
3. Click "Add"

**Show**:
- Camera appears in grid with "Online" status
- FPS counter updates in real-time
- Status indicator turns green

**Say**: "The system automatically connects to the stream, starts processing frames, and displays real-time performance metrics."

---

### **Minute 1:30 - 2:30: Define Zone**

**Say**: "Now let's define a restricted zone where we want to detect intrusions."

**Do**:
1. Click "Add Zone" on the camera card
2. Enter:
   - Zone Name: "Restricted Area"
   - Coordinates: `[[200,200],[400,200],[400,400],[200,400]]`
3. Click "Add Zone"

**Show**:
- Zone successfully created confirmation

**Say**: "Zones are defined using polygon coordinates. In production, this would have a visual editor, but for the MVP, JSON input demonstrates the underlying flexibility."

---

### **Minute 2:30 - 3:30: View Events**

**Say**: "Let's check if any events have been generated."

**Do**:
1. Navigate to "Events" page
2. Show event list with color-coded priorities
3. Click on an event to view details

**Show**:
- Event feed with real-time updates
- Filters for camera, rule type, and priority
- Event details modal with:
  - Snapshot with bounding box
  - Metadata (zone name, confidence, timestamp)
  - Object type and detection confidence

**Say**: "Events are generated when objects enter restricted zones. Each event includes a snapshot with the detected object highlighted, along with full metadata for investigation."

---

### **Minute 3:30 - 4:30: Analytics Dashboard**

**Say**: "The analytics dashboard provides insights into system performance and event trends."

**Do**:
1. Navigate to "Analytics" page
2. Scroll through the dashboard

**Show**:
- Summary cards (total events, active cameras, CPU/memory usage)
- Event distribution charts (by rule type, by priority)
- Camera performance metrics (FPS, queue depth)

**Say**: "This gives operators a bird's-eye view of the entire system, helping identify patterns and optimize camera placement."

---

### **Minute 4:30 - 5:00: System Health & Wrap-up**

**Say**: "Let's verify system health."

**Do**:
1. Open http://localhost:8000/api/v1/health in browser
2. Show JSON response with subsystem status

**Show**:
```json
{
  "status": "healthy",
  "subsystems": {
    "database": "ok",
    "mqtt": "ok",
    "cameras": {"total": 1, "online": 1},
    "inference": {"model_loaded": true, "avg_inference_time_ms": 45}
  }
}
```

**Say**: "The system provides comprehensive health monitoring and metrics, essential for production deployments."

---

## Key Points to Emphasize

1. **Real-time Processing**: Live FPS updates, instant event generation
2. **Privacy-First**: All processing happens locally, no cloud uploads
3. **Scalability**: Designed to handle multiple cameras with queue management
4. **Production-Ready**: Auto-reconnect, error handling, performance monitoring
5. **Extensibility**: MQTT integration, API-first design, modular architecture

---

## Backup Talking Points

If extra time or questions:

- **MQTT Integration**: "Events are published to MQTT topics for smart home integration"
- **Event Deduplication**: "The system prevents duplicate alerts within a 5-second window"
- **Auto-Reconnect**: "If a camera stream fails, the system automatically retries with exponential backoff"
- **GDPR Compliance**: "Only events and snapshots are stored, with configurable retention policies"

---

## Common Questions & Answers

**Q: How many cameras can it handle?**
A: Current MVP supports 4 concurrent cameras on CPU. With GPU acceleration, this scales to 20+.

**Q: What about privacy concerns?**
A: All processing is local. No data leaves your network. Only events + snapshots are stored, not full video.

**Q: Can it detect other objects?**
A: Yes! The YOLO model supports 80 object classes. Currently configured for person and vehicle, but easily extensible.

**Q: How accurate is the detection?**
A: YOLOv8 achieves 95%+ accuracy on standard datasets. Confidence threshold is configurable (default: 50%).

---

## Demo Environment Checklist

- [ ] Docker services running
- [ ] Test RTSP stream accessible
- [ ] Browser tabs pre-opened (dashboard, API docs)
- [ ] Example zone coordinates ready to paste
- [ ] Network stable (for RTSP streaming)
