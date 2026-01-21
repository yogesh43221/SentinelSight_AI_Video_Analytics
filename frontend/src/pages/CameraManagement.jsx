import React, { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Chip,
    IconButton,
    Alert,
} from '@mui/material';
import {
    Add,
    Delete,
    FiberManualRecord,
} from '@mui/icons-material';
import { cameraAPI, zoneAPI } from '../services/api';

export default function CameraManagement() {
    const [cameras, setCameras] = useState([]);
    const [openDialog, setOpenDialog] = useState(false);
    const [openZoneDialog, setOpenZoneDialog] = useState(false);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [newCamera, setNewCamera] = useState({ name: '', rtsp_url: '', location_tag: '' });
    const [newZone, setNewZone] = useState({ name: '', coordinates: '' });
    const [error, setError] = useState('');

    useEffect(() => {
        loadCameras();
        const interval = setInterval(loadCameras, 5000); // Refresh every 5s
        return () => clearInterval(interval);
    }, []);

    const loadCameras = async () => {
        try {
            const response = await cameraAPI.getAll();
            setCameras(response.data.cameras);
        } catch (err) {
            console.error('Error loading cameras:', err);
        }
    };

    const handleAddCamera = async () => {
        try {
            await cameraAPI.create(newCamera);
            setOpenDialog(false);
            setNewCamera({ name: '', rtsp_url: '', location_tag: '' });
            loadCameras();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error adding camera');
        }
    };

    const handleDeleteCamera = async (id) => {
        if (window.confirm('Delete this camera?')) {
            try {
                await cameraAPI.delete(id);
                loadCameras();
            } catch (err) {
                setError('Error deleting camera');
            }
        }
    };

    const handleAddZone = async () => {
        try {
            const coordinates = JSON.parse(newZone.coordinates);
            await zoneAPI.create({
                camera_id: selectedCamera.id,
                name: newZone.name,
                type: 'polygon',
                coordinates,
            });
            setOpenZoneDialog(false);
            setNewZone({ name: '', coordinates: '' });
            alert('Zone added successfully!');
        } catch (err) {
            setError('Invalid coordinates format. Use: [[x1,y1],[x2,y2],...]');
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'online':
                return 'success';
            case 'offline':
                return 'default';
            case 'error':
                return 'error';
            default:
                return 'default';
        }
    };

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h4">Camera Management</Typography>
                <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setOpenDialog(true)}
                >
                    Add Camera
                </Button>
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

            <Grid container spacing={3}>
                {cameras.map((camera) => (
                    <Grid item xs={12} sm={6} md={4} key={camera.id}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <Typography variant="h6" gutterBottom>
                                        {camera.name}
                                    </Typography>
                                    <IconButton size="small" onClick={() => handleDeleteCamera(camera.id)}>
                                        <Delete />
                                    </IconButton>
                                </Box>

                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    {camera.location_tag || 'No location'}
                                </Typography>

                                <Box sx={{ mt: 2 }}>
                                    <Chip
                                        icon={<FiberManualRecord />}
                                        label={camera.status}
                                        color={getStatusColor(camera.status)}
                                        size="small"
                                        sx={{ mr: 1 }}
                                    />
                                    <Chip label={`${camera.fps?.toFixed(1) || 0} FPS`} size="small" />
                                </Box>

                                <Typography variant="caption" display="block" sx={{ mt: 2 }}>
                                    URL: {camera.rtsp_url}
                                </Typography>

                                <Button
                                    size="small"
                                    sx={{ mt: 2 }}
                                    onClick={() => {
                                        setSelectedCamera(camera);
                                        setOpenZoneDialog(true);
                                    }}
                                >
                                    Add Zone
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {/* Add Camera Dialog */}
            <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
                <DialogTitle>Add New Camera</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Camera Name"
                        fullWidth
                        value={newCamera.name}
                        onChange={(e) => setNewCamera({ ...newCamera, name: e.target.value })}
                    />
                    <TextField
                        margin="dense"
                        label="RTSP URL"
                        fullWidth
                        value={newCamera.rtsp_url}
                        onChange={(e) => setNewCamera({ ...newCamera, rtsp_url: e.target.value })}
                        placeholder="rtsp://..."
                    />
                    <TextField
                        margin="dense"
                        label="Location Tag (optional)"
                        fullWidth
                        value={newCamera.location_tag}
                        onChange={(e) => setNewCamera({ ...newCamera, location_tag: e.target.value })}
                        placeholder="Building A - Floor 1"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
                    <Button onClick={handleAddCamera} variant="contained">Add</Button>
                </DialogActions>
            </Dialog>

            {/* Add Zone Dialog */}
            <Dialog open={openZoneDialog} onClose={() => setOpenZoneDialog(false)}>
                <DialogTitle>Add Zone for {selectedCamera?.name}</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Zone Name"
                        fullWidth
                        value={newZone.name}
                        onChange={(e) => setNewZone({ ...newZone, name: e.target.value })}
                    />
                    <TextField
                        margin="dense"
                        label="Coordinates (JSON)"
                        fullWidth
                        multiline
                        rows={4}
                        value={newZone.coordinates}
                        onChange={(e) => setNewZone({ ...newZone, coordinates: e.target.value })}
                        placeholder='[[100,100],[200,100],[200,200],[100,200]]'
                    />
                    <Typography variant="caption" color="text.secondary">
                        Enter polygon coordinates as JSON array of [x, y] points
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenZoneDialog(false)}>Cancel</Button>
                    <Button onClick={handleAddZone} variant="contained">Add Zone</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
