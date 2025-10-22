import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { Snackbar, Alert, AlertColor } from '@mui/material';
import { useAuth } from './AuthContext';
import { websocketService } from '../services/websocket';

interface Notification {
  id: string;
  type: AlertColor;
  message: string;
  autoHide?: boolean;
  duration?: number;
}

interface NotificationContextType {
  showNotification: (message: string, type?: AlertColor, autoHide?: boolean, duration?: number) => void;
  clearNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { user } = useAuth();

  useEffect(() => {
    // WebSocket notifications disabled in development to reduce console noise
    // TODO: Enable WebSocket notifications when backend WebSocket server is ready
    
    // if (user) {
    //   const token = localStorage.getItem('auth_token');
    //   if (token) {
    //     websocketService.connectToNotifications(token, (notification) => {
    //       showNotification(
    //         notification.message,
    //         notification.type as AlertColor || 'info',
    //         true,
    //         6000
    //       );
    //     });
    //   }
    //   return () => {
    //     websocketService.disconnect();
    //   };
    // }
  }, [user]);

  const showNotification = useCallback((
    message: string,
    type: AlertColor = 'info',
    autoHide: boolean = true,
    duration: number = 6000
  ) => {
    // Generate truly unique ID using timestamp + random number to avoid duplicates
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const notification: Notification = {
      id,
      type,
      message,
      autoHide,
      duration,
    };

    setNotifications(prev => [...prev, notification]);

    if (autoHide) {
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== id));
      }, duration);
    }
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const handleClose = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const value: NotificationContextType = {
    showNotification,
    clearNotifications,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      
      {/* Render notifications */}
      {notifications.map((notification, index) => (
        <Snackbar
          key={notification.id}
          open={true}
          autoHideDuration={notification.autoHide ? notification.duration : null}
          onClose={() => handleClose(notification.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          style={{ 
            marginTop: `${index * 60}px`,
            zIndex: 9999 + index 
          }}
        >
          <Alert
            onClose={() => handleClose(notification.id)}
            severity={notification.type}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </NotificationContext.Provider>
  );
};