/**
 * Customizable Dashboard Layout Component
 * Supports drag-and-drop widget arrangement and layout persistence
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Tooltip,
  Fab,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  DragIndicator as DragIcon,
  MoreVert as MoreVertIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  Dashboard as DashboardIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Save as SaveIcon,
  Restore as RestoreIcon,
  GridView as GridViewIcon,
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';

export interface DashboardWidget {
  id: string;
  title: string;
  component: React.ComponentType<any>;
  props?: Record<string, any>;
  size: 'small' | 'medium' | 'large' | 'full';
  category: string;
  description?: string;
  isVisible: boolean;
  isResizable?: boolean;
  minHeight?: number;
  maxHeight?: number;
}

export interface DashboardLayout {
  id: string;
  name: string;
  widgets: DashboardWidget[];
  columns: number;
  spacing: number;
  savedAt?: string;
}

export interface CustomizableDashboardLayoutProps {
  initialLayout?: DashboardLayout;
  availableWidgets: DashboardWidget[];
  onLayoutChange?: (layout: DashboardLayout) => void;
  onSaveLayout?: (layout: DashboardLayout) => void;
  onLoadLayout?: (layoutId: string) => Promise<DashboardLayout>;
  enablePersistence?: boolean;
  maxColumns?: number;
  minColumns?: number;
}

export const CustomizableDashboardLayout: React.FC<CustomizableDashboardLayoutProps> = ({
  initialLayout,
  availableWidgets,
  onLayoutChange,
  onSaveLayout,
  onLoadLayout,
  enablePersistence = true,
  maxColumns = 4,
  minColumns = 1,
}) => {
  const [layout, setLayout] = useState<DashboardLayout>(
    initialLayout || {
      id: 'default',
      name: 'Default Layout',
      widgets: availableWidgets.filter(w => w.isVisible),
      columns: 3,
      spacing: 2,
    }
  );
  
  const [isEditMode, setIsEditMode] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [widgetMenuAnchor, setWidgetMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedWidget, setSelectedWidget] = useState<DashboardWidget | null>(null);
  const [addWidgetDrawerOpen, setAddWidgetDrawerOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Load layout from localStorage on mount
  useEffect(() => {
    if (enablePersistence && !initialLayout) {
      const savedLayout = localStorage.getItem('dashboard-layout');
      if (savedLayout) {
        try {
          const parsedLayout = JSON.parse(savedLayout);
          setLayout(parsedLayout);
        } catch (error) {
          console.error('Error loading saved layout:', error);
        }
      }
    }
  }, [enablePersistence, initialLayout]);

  // Save layout to localStorage when it changes
  useEffect(() => {
    if (enablePersistence) {
      localStorage.setItem('dashboard-layout', JSON.stringify(layout));
    }
    onLayoutChange?.(layout);
  }, [layout, enablePersistence, onLayoutChange]);

  const handleDragEnd = useCallback((result: DropResult) => {
    if (!result.destination) return;

    const newWidgets = Array.from(layout.widgets);
    const [reorderedWidget] = newWidgets.splice(result.source.index, 1);
    newWidgets.splice(result.destination.index, 0, reorderedWidget);

    setLayout(prev => ({
      ...prev,
      widgets: newWidgets,
    }));
  }, [layout.widgets]);

  const handleWidgetMenuClick = (event: React.MouseEvent<HTMLElement>, widget: DashboardWidget) => {
    setWidgetMenuAnchor(event.currentTarget);
    setSelectedWidget(widget);
  };

  const handleWidgetMenuClose = () => {
    setWidgetMenuAnchor(null);
    setSelectedWidget(null);
  };

  const handleToggleWidgetVisibility = (widgetId: string) => {
    setLayout(prev => ({
      ...prev,
      widgets: prev.widgets.map(widget =>
        widget.id === widgetId
          ? { ...widget, isVisible: !widget.isVisible }
          : widget
      ),
    }));
    handleWidgetMenuClose();
  };

  const handleRemoveWidget = (widgetId: string) => {
    setLayout(prev => ({
      ...prev,
      widgets: prev.widgets.filter(widget => widget.id !== widgetId),
    }));
    handleWidgetMenuClose();
  };

  const handleAddWidget = (widget: DashboardWidget) => {
    const newWidget = {
      ...widget,
      id: `${widget.id}-${Date.now()}`, // Ensure unique ID
      isVisible: true,
    };

    setLayout(prev => ({
      ...prev,
      widgets: [...prev.widgets, newWidget],
    }));
    setAddWidgetDrawerOpen(false);
    setSnackbarMessage(`Added ${widget.title} to dashboard`);
    setSnackbarOpen(true);
  };

  const handleSaveLayout = () => {
    const savedLayout = {
      ...layout,
      savedAt: new Date().toISOString(),
    };
    setLayout(savedLayout);
    onSaveLayout?.(savedLayout);
    setSnackbarMessage('Layout saved successfully');
    setSnackbarOpen(true);
  };

  const handleResetLayout = () => {
    const defaultLayout: DashboardLayout = {
      id: 'default',
      name: 'Default Layout',
      widgets: availableWidgets.filter(w => w.isVisible),
      columns: 3,
      spacing: 2,
    };
    setLayout(defaultLayout);
    setSnackbarMessage('Layout reset to default');
    setSnackbarOpen(true);
  };

  const handleColumnsChange = (columns: number) => {
    setLayout(prev => ({
      ...prev,
      columns: Math.max(minColumns, Math.min(maxColumns, columns)),
    }));
  };

  const handleSpacingChange = (spacing: number) => {
    setLayout(prev => ({
      ...prev,
      spacing: Math.max(0, Math.min(4, spacing)),
    }));
  };

  const getWidgetGridSize = (size: DashboardWidget['size'], columns: number) => {
    switch (size) {
      case 'small':
        return Math.max(1, Math.floor(columns / 4));
      case 'medium':
        return Math.max(1, Math.floor(columns / 2));
      case 'large':
        return Math.max(1, Math.floor((columns * 3) / 4));
      case 'full':
        return columns;
      default:
        return Math.max(1, Math.floor(columns / 2));
    }
  };

  const getWidgetsByCategory = () => {
    const categories: Record<string, DashboardWidget[]> = {};
    availableWidgets.forEach(widget => {
      if (!categories[widget.category]) {
        categories[widget.category] = [];
      }
      categories[widget.category].push(widget);
    });
    return categories;
  };

  const visibleWidgets = layout.widgets.filter(widget => widget.isVisible);

  return (
    <Box sx={{ position: 'relative', minHeight: '100vh' }}>
      {/* Edit Mode Toggle */}
      <Box sx={{ position: 'fixed', top: 16, right: 16, zIndex: 1000 }}>
        <Tooltip title={isEditMode ? 'Exit Edit Mode' : 'Enter Edit Mode'}>
          <Fab
            color={isEditMode ? 'secondary' : 'primary'}
            size="medium"
            onClick={() => setIsEditMode(!isEditMode)}
          >
            {isEditMode ? <DashboardIcon /> : <SettingsIcon />}
          </Fab>
        </Tooltip>
      </Box>

      {/* Edit Mode Controls */}
      {isEditMode && (
        <Box sx={{ 
          position: 'fixed', 
          top: 80, 
          right: 16, 
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}>
          <Tooltip title="Add Widget">
            <Fab
              size="small"
              onClick={() => setAddWidgetDrawerOpen(true)}
            >
              <AddIcon />
            </Fab>
          </Tooltip>
          <Tooltip title="Layout Settings">
            <Fab
              size="small"
              onClick={() => setSettingsOpen(true)}
            >
              <GridViewIcon />
            </Fab>
          </Tooltip>
          <Tooltip title="Save Layout">
            <Fab
              size="small"
              onClick={handleSaveLayout}
            >
              <SaveIcon />
            </Fab>
          </Tooltip>
          <Tooltip title="Reset Layout">
            <Fab
              size="small"
              onClick={handleResetLayout}
            >
              <RestoreIcon />
            </Fab>
          </Tooltip>
        </Box>
      )}

      {/* Edit Mode Alert */}
      {isEditMode && (
        <Alert 
          severity="info" 
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={() => setIsEditMode(false)}>
              Exit Edit Mode
            </Button>
          }
        >
          Dashboard is in edit mode. Drag widgets to reorder, click menu buttons to configure.
        </Alert>
      )}

      {/* Dashboard Grid */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="dashboard" isDropDisabled={!isEditMode}>
          {(provided, snapshot) => (
            <Box
              ref={provided.innerRef}
              {...provided.droppableProps}
              sx={{
                display: 'grid',
                gridTemplateColumns: `repeat(${layout.columns}, 1fr)`,
                gap: layout.spacing,
                p: layout.spacing,
                backgroundColor: snapshot.isDraggingOver ? 'action.hover' : 'transparent',
                minHeight: '100vh',
                transition: 'background-color 0.2s ease',
              }}
            >
              {visibleWidgets.map((widget, index) => (
                <Draggable
                  key={widget.id}
                  draggableId={widget.id}
                  index={index}
                  isDragDisabled={!isEditMode}
                >
                  {(provided, snapshot) => (
                    <Box
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      sx={{
                        gridColumn: `span ${getWidgetGridSize(widget.size, layout.columns)}`,
                        transform: snapshot.isDragging ? 'rotate(5deg)' : 'none',
                        transition: 'transform 0.2s ease',
                        opacity: snapshot.isDragging ? 0.8 : 1,
                      }}
                    >
                      <Card
                        sx={{
                          height: '100%',
                          border: isEditMode ? '2px dashed' : '1px solid',
                          borderColor: isEditMode ? 'primary.main' : 'divider',
                          '&:hover': isEditMode ? {
                            borderColor: 'primary.dark',
                            boxShadow: 2,
                          } : {},
                        }}
                      >
                        {isEditMode && (
                          <CardHeader
                            avatar={
                              <Box {...provided.dragHandleProps}>
                                <DragIcon sx={{ cursor: 'grab' }} />
                              </Box>
                            }
                            title={widget.title}
                            action={
                              <IconButton
                                onClick={(e) => handleWidgetMenuClick(e, widget)}
                              >
                                <MoreVertIcon />
                              </IconButton>
                            }
                            sx={{ pb: 1 }}
                          />
                        )}
                        <CardContent sx={{ pt: isEditMode ? 0 : 2 }}>
                          <widget.component {...(widget.props || {})} />
                        </CardContent>
                      </Card>
                    </Box>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </Box>
          )}
        </Droppable>
      </DragDropContext>

      {/* Widget Context Menu */}
      <Menu
        anchorEl={widgetMenuAnchor}
        open={Boolean(widgetMenuAnchor)}
        onClose={handleWidgetMenuClose}
      >
        <MenuItem onClick={() => selectedWidget && handleToggleWidgetVisibility(selectedWidget.id)}>
          {selectedWidget?.isVisible ? <VisibilityOffIcon sx={{ mr: 1 }} /> : <VisibilityIcon sx={{ mr: 1 }} />}
          {selectedWidget?.isVisible ? 'Hide Widget' : 'Show Widget'}
        </MenuItem>
        <MenuItem onClick={() => selectedWidget && handleRemoveWidget(selectedWidget.id)}>
          Remove Widget
        </MenuItem>
      </Menu>

      {/* Add Widget Drawer */}
      <Drawer
        anchor="right"
        open={addWidgetDrawerOpen}
        onClose={() => setAddWidgetDrawerOpen(false)}
        PaperProps={{ sx: { width: 350 } }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Add Widgets
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Select widgets to add to your dashboard
          </Typography>
          
          {Object.entries(getWidgetsByCategory()).map(([category, widgets]) => (
            <Box key={category} sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
                {category}
              </Typography>
              <List dense>
                {widgets.map(widget => (
                  <ListItem
                    key={widget.id}
                    button
                    onClick={() => handleAddWidget(widget)}
                    disabled={layout.widgets.some(w => w.id === widget.id)}
                  >
                    <ListItemIcon>
                      <DashboardIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={widget.title}
                      secondary={widget.description}
                    />
                  </ListItem>
                ))}
              </List>
              <Divider />
            </Box>
          ))}
        </Box>
      </Drawer>

      {/* Layout Settings Dialog */}
      <Dialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Layout Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography gutterBottom>
              Columns: {layout.columns}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
              {Array.from({ length: maxColumns - minColumns + 1 }, (_, i) => minColumns + i).map(cols => (
                <Button
                  key={cols}
                  variant={layout.columns === cols ? 'contained' : 'outlined'}
                  onClick={() => handleColumnsChange(cols)}
                  size="small"
                >
                  {cols}
                </Button>
              ))}
            </Box>

            <Typography gutterBottom>
              Spacing: {layout.spacing}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
              {[0, 1, 2, 3, 4].map(spacing => (
                <Button
                  key={spacing}
                  variant={layout.spacing === spacing ? 'contained' : 'outlined'}
                  onClick={() => handleSpacingChange(spacing)}
                  size="small"
                >
                  {spacing}
                </Button>
              ))}
            </Box>

            <Typography variant="subtitle2" gutterBottom>
              Widget Visibility
            </Typography>
            {layout.widgets.map(widget => (
              <FormControlLabel
                key={widget.id}
                control={
                  <Switch
                    checked={widget.isVisible}
                    onChange={() => handleToggleWidgetVisibility(widget.id)}
                  />
                }
                label={widget.title}
              />
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>
            Close
          </Button>
          <Button onClick={handleSaveLayout} variant="contained">
            Save Layout
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default CustomizableDashboardLayout;