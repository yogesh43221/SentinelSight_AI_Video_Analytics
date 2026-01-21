import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Grid,
    Chip,
    TextField,
    MenuItem,
    Dialog,
    DialogTitle,
    DialogContent,
    Button,
} from '@mui/material';
import { format } from 'date-fns';
import { eventAPI, cameraAPI } from '../services/api';

export default function EventFeed() {
    const [events, setEvents] = useState([]);
    const [cameras, setCameras] = useState([]);
    const [filters, setFilters] = useState({
        camera_id: '',
        rule: '',
        priority: '',
        limit: 50,
    });
    const [selectedEvent, setSelectedEvent] = useState(null);
    const [openDialog, setOpenDialog] = useState(false);

    useEffect(() => {
        loadCameras();
        loadEvents();
        const interval = setInterval(loadEvents, 3000); // Refresh every 3s
        return () => clearInterval(interval);
    }, [filters]);

    const loadCameras = async () => {
        try {
            const response = await cameraAPI.getAll();
            setCameras(response.data.cameras);
        } catch (err) {
            console.error('Error loading cameras:', err);
        }
    };

    const loadEvents = async () => {
        try {
            const params = {};
            if (filters.camera_id) params.camera_id = filters.camera_id;
            if (filters.rule) params.rule = filters.rule;
            if (filters.priority) params.priority = filters.priority;
            params.limit = filters.limit;

            const response = await eventAPI.getAll(params);
            setEvents(response.data.events);
        } catch (err) {
            console.error('Error loading events:', err);
        }
    };

    const handleEventClick = async (event) => {
        try {
            const response = await eventAPI.getById(event.id);
            setSelectedEvent(response.data.event);
            setOpenDialog(true);
        } catch (err) {
            console.error('Error loading event details:', err);
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'critical':
                return 'error';
            case 'high':
                return 'warning';
            case 'medium':
                return 'info';
            case 'low':
                return 'default';
            default:
                return 'default';
        }
    };

    const getRuleColor = (rule) => {
        return rule === 'intrusion' ? 'error' : 'warning';
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Event Feed
            </Typography>

            {/* Filters */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={3}>
                            <TextField
                                select
                                fullWidth
                                label="Camera"
                                value={filters.camera_id}
                                onChange={(e) => setFilters({ ...filters, camera_id: e.target.value })}
                            >
                                <MenuItem value="">All Cameras</MenuItem>
                                {cameras.map((cam) => (
                                    <MenuItem key={cam.id} value={cam.id}>
                                        {cam.name}
                                    </MenuItem>
                                ))}
                            </TextField>
                        </Grid>

                        <Grid item xs={12} sm={3}>
                            <TextField
                                select
                                fullWidth
                                label="Rule Type"
                                value={filters.rule}
                                onChange={(e) => setFilters({ ...filters, rule: e.target.value })}
                            >
                                <MenuItem value="">All Rules</MenuItem>
                                <MenuItem value="intrusion">Intrusion</MenuItem>
                                <MenuItem value="loitering">Loitering</MenuItem>
                            </TextField>
                        </Grid>

                        <Grid item xs={12} sm={3}>
                            <TextField
                                select
                                fullWidth
                                label="Priority"
                                value={filters.priority}
                                onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
                            >
                                <MenuItem value="">All Priorities</MenuItem>
                                <MenuItem value="critical">Critical</MenuItem>
                                <MenuItem value="high">High</MenuItem>
                                <MenuItem value="medium">Medium</MenuItem>
                                <MenuItem value="low">Low</MenuItem>
                            </TextField>
                        </Grid>

                        <Grid item xs={12} sm={3}>
                            <TextField
                                select
                                fullWidth
                                label="Limit"
                                value={filters.limit}
                                onChange={(e) => setFilters({ ...filters, limit: e.target.value })}
                            >
                                <MenuItem value={25}>25</MenuItem>
                                <MenuItem value={50}>50</MenuItem>
                                <MenuItem value={100}>100</MenuItem>
                            </TextField>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>

            {/* Event List */}
            <Grid container spacing={2}>
                {events.map((event) => (
                    <Grid item xs={12} key={event.id}>
                        <Card
                            sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                            onClick={() => handleEventClick(event)}
                        >
                            <CardContent>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <Box>
                                        <Typography variant="h6">
                                            Event #{event.id}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {event.timestamp ? format(new Date(event.timestamp), 'PPpp') : 'N/A'}
                                        </Typography>
                                    </Box>
                                    <Box>
                                        <Chip
                                            label={event.priority}
                                            color={getPriorityColor(event.priority)}
                                            size="small"
                                            sx={{ mr: 1 }}
                                        />
                                        <Chip
                                            label={event.rule_type}
                                            color={getRuleColor(event.rule_type)}
                                            size="small"
                                        />
                                    </Box>
                                </Box>

                                <Box sx={{ mt: 2 }}>
                                    <Typography variant="body2">
                                        <strong>Camera:</strong> Camera {event.camera_id} |{' '}
                                        <strong>Object:</strong> {event.object_type} |{' '}
                                        <strong>Confidence:</strong> {(event.confidence * 100).toFixed(1)}%
                                    </Typography>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {/* Event Details Dialog */}
            <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
                <DialogTitle>Event Details</DialogTitle>
                <DialogContent>
                    {selectedEvent && (
                        <Box>
                            <Grid container spacing={2}>
                                <Grid item xs={12}>
                                    {selectedEvent.snapshot_path && (
                                        <Box
                                            component="img"
                                            src={`/snapshots/${selectedEvent.snapshot_path.replace(/^.*[\\\/]/, '')}`}
                                            alt="Event snapshot"
                                            sx={{ width: '100%', borderRadius: 1 }}
                                        />
                                    )}
                                </Grid>

                                <Grid item xs={6}>
                                    <Typography variant="body2">
                                        <strong>Event ID:</strong> {selectedEvent.id}
                                    </Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2">
                                        <strong>Camera ID:</strong> {selectedEvent.camera_id}
                                    </Typography>
                                </Grid>

                                <Grid item xs={6}>
                                    <Typography variant="body2">
                                        <strong>Rule Type:</strong> {selectedEvent.rule_type}
                                    </Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2">
                                        <strong>Priority:</strong> {selectedEvent.priority}
                                    </Typography>
                                </Grid>

                                <Grid item xs={6}>
                                    <Typography variant="body2">
                                        <strong>Object Type:</strong> {selectedEvent.object_type}
                                    </Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2">
                                        <strong>Confidence:</strong> {(selectedEvent.confidence * 100).toFixed(1)}%
                                    </Typography>
                                </Grid>

                                <Grid item xs={12}>
                                    <Typography variant="body2">
                                        <strong>Timestamp:</strong>{' '}
                                        {selectedEvent.timestamp ? format(new Date(selectedEvent.timestamp), 'PPpp') : 'N/A'}
                                    </Typography>
                                </Grid>

                                {selectedEvent.metadata && (
                                    <Grid item xs={12}>
                                        <Typography variant="body2">
                                            <strong>Metadata:</strong>
                                        </Typography>
                                        <pre style={{ fontSize: '0.875rem' }}>
                                            {JSON.stringify(selectedEvent.metadata, null, 2)}
                                        </pre>
                                    </Grid>
                                )}
                            </Grid>

                            <Button
                                variant="contained"
                                sx={{ mt: 2 }}
                                onClick={() => setOpenDialog(false)}
                            >
                                Close
                            </Button>
                        </Box>
                    )}
                </DialogContent>
            </Dialog>
        </Box>
    );
}
