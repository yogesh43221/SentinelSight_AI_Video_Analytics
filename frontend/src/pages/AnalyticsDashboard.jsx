import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Grid,
} from '@mui/material';
import {
    BarChart,
    Bar,
    LineChart,
    Line,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import { eventAPI, systemAPI } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function AnalyticsDashboard() {
    const [stats, setStats] = useState(null);
    const [metrics, setMetrics] = useState(null);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 5000);
        return () => clearInterval(interval);
    }, []);

    const loadData = async () => {
        try {
            const [statsRes, metricsRes] = await Promise.all([
                eventAPI.getStats({ hours: 24 }),
                systemAPI.metrics(),
            ]);
            setStats(statsRes.data);
            setMetrics(metricsRes.data);
        } catch (err) {
            console.error('Error loading analytics:', err);
        }
    };

    if (!stats || !metrics) {
        return <Typography>Loading...</Typography>;
    }

    // Prepare data for charts
    const ruleData = Object.entries(stats.by_rule || {}).map(([name, value]) => ({
        name,
        count: value,
    }));

    const priorityData = Object.entries(stats.by_priority || {}).map(([name, value]) => ({
        name,
        count: value,
    }));

    const cameraData = metrics.cameras.map((cam) => ({
        name: cam.name,
        fps: cam.fps,
        queue: cam.queue_depth,
    }));

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Analytics Dashboard
            </Typography>

            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Total Events (24h)
                            </Typography>
                            <Typography variant="h4">{stats.total}</Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Active Cameras
                            </Typography>
                            <Typography variant="h4">
                                {metrics.cameras.filter((c) => c.status === 'online').length}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                CPU Usage
                            </Typography>
                            <Typography variant="h4">
                                {metrics.system.cpu_percent.toFixed(1)}%
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Memory Usage
                            </Typography>
                            <Typography variant="h4">
                                {metrics.system.memory_mb.toFixed(0)} MB
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3}>
                {/* Events by Rule Type */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Events by Rule Type
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={ruleData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="name" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Bar dataKey="count" fill="#8884d8" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Events by Priority */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Events by Priority
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={priorityData}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={(entry) => `${entry.name}: ${entry.count}`}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        dataKey="count"
                                    >
                                        {priorityData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Camera Performance */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Camera Performance (FPS)
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={cameraData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="name" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Bar dataKey="fps" fill="#82ca9d" name="FPS" />
                                    <Bar dataKey="queue" fill="#ffc658" name="Queue Depth" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}
