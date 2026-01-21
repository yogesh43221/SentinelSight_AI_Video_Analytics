import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
    CssBaseline,
    AppBar,
    Toolbar,
    Typography,
    Container,
    Box,
    Drawer,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    ListItemButton,
} from '@mui/material';
import {
    Videocam,
    Event,
    Analytics,
    Settings,
} from '@mui/icons-material';

import CameraManagement from './pages/CameraManagement';
import EventFeed from './pages/EventFeed';
import AnalyticsDashboard from './pages/AnalyticsDashboard';

const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#2196f3',
        },
        secondary: {
            main: '#f50057',
        },
        background: {
            default: '#0a1929',
            paper: '#132f4c',
        },
    },
});

const drawerWidth = 240;

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Router>
                <Box sx={{ display: 'flex' }}>
                    <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
                        <Toolbar>
                            <Typography variant="h6" noWrap component="div">
                                🛡️ SentinelSight - AI Video Analytics
                            </Typography>
                        </Toolbar>
                    </AppBar>

                    <Drawer
                        variant="permanent"
                        sx={{
                            width: drawerWidth,
                            flexShrink: 0,
                            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
                        }}
                    >
                        <Toolbar />
                        <Box sx={{ overflow: 'auto' }}>
                            <List>
                                <ListItem disablePadding>
                                    <ListItemButton component={Link} to="/">
                                        <ListItemIcon>
                                            <Videocam />
                                        </ListItemIcon>
                                        <ListItemText primary="Cameras" />
                                    </ListItemButton>
                                </ListItem>

                                <ListItem disablePadding>
                                    <ListItemButton component={Link} to="/events">
                                        <ListItemIcon>
                                            <Event />
                                        </ListItemIcon>
                                        <ListItemText primary="Events" />
                                    </ListItemButton>
                                </ListItem>

                                <ListItem disablePadding>
                                    <ListItemButton component={Link} to="/analytics">
                                        <ListItemIcon>
                                            <Analytics />
                                        </ListItemIcon>
                                        <ListItemText primary="Analytics" />
                                    </ListItemButton>
                                </ListItem>
                            </List>
                        </Box>
                    </Drawer>

                    <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
                        <Toolbar />
                        <Container maxWidth="xl">
                            <Routes>
                                <Route path="/" element={<CameraManagement />} />
                                <Route path="/events" element={<EventFeed />} />
                                <Route path="/analytics" element={<AnalyticsDashboard />} />
                            </Routes>
                        </Container>
                    </Box>
                </Box>
            </Router>
        </ThemeProvider>
    );
}

export default App;
