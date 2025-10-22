import { Socket } from 'socket.io-client';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface ProgressCallback {
  (update: any): void;
}

interface NotificationCallback {
  (notification: any): void;
}

class WebSocketService {
  private socket: Socket | null = null;
  private progressCallbacks: Map<string, ProgressCallback[]> = new Map();
  private notificationCallback: NotificationCallback | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor() {
    this.handleConnect = this.handleConnect.bind(this);
    this.handleDisconnect = this.handleDisconnect.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.handleError = this.handleError.bind(this);
  }

  // Connect to validation progress WebSocket
  connectToValidationProgress(validationId: string, token: string, callback: ProgressCallback): void {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const url = `${wsUrl}/ws/validation/${validationId}/progress`;
    
    try {
      // Create WebSocket connection
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        // Silently connected
        this.reconnectAttempts = 0;
        
        // Send authentication if needed
        ws.send(JSON.stringify({
          type: 'auth',
          token: token
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleProgressMessage(validationId, message, callback);
        } catch (error) {
          // Silently handle parse errors
        }
      };
      
      ws.onclose = (event) => {
        // Silently handle close - no reconnect attempts
        // this.handleReconnect(validationId, token, callback);
      };
      
      ws.onerror = (error) => {
        // Silently handle errors - WebSocket not available in dev
      };
      
      // Store WebSocket reference
      if (!this.progressCallbacks.has(validationId)) {
        this.progressCallbacks.set(validationId, []);
      }
      this.progressCallbacks.get(validationId)!.push(callback);
      
    } catch (error) {
      console.error('Failed to connect to validation progress WebSocket:', error);
    }
  }

  // Connect to user notifications WebSocket
  connectToNotifications(token: string, callback: NotificationCallback): void {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const url = `${wsUrl}/ws/notifications?token=${encodeURIComponent(token)}`;
    
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('Connected to notifications WebSocket');
        this.reconnectAttempts = 0;
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleNotificationMessage(message, callback);
        } catch (error) {
          console.error('Failed to parse notification WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        console.log('Notifications WebSocket connection closed:', event.code, event.reason);
        this.handleNotificationReconnect(token, callback);
      };
      
      ws.onerror = (error) => {
        console.error('Notifications WebSocket error:', error);
      };
      
      this.notificationCallback = callback;
      
    } catch (error) {
      console.error('Failed to connect to notifications WebSocket:', error);
    }
  }

  private handleProgressMessage(validationId: string, message: any, callback: ProgressCallback): void {
    switch (message.type) {
      case 'status_update':
        console.log(`Progress WebSocket connected for ${validationId}`);
        callback({
          validation_id: validationId,
          status: message.status,
          progress_percentage: message.progress_percentage,
          message: message.message
        });
        break;
        
      case 'progress_update':
        callback({
          validation_id: validationId,
          status: message.status,
          progress_percentage: message.progress_percentage,
          current_agent: message.current_phase,
          message: message.message,
          agent_results: message.agent_results
        });
        break;
        
      case 'completion':
        callback({
          validation_id: validationId,
          status: 'completed',
          progress_percentage: 100,
          message: 'Validation completed successfully'
        });
        break;
        
      case 'heartbeat':
        console.log('Received heartbeat from server');
        break;
        
      case 'pong':
        console.log('Received pong from server');
        break;
        
      default:
        console.log('Unknown progress message type:', message.type, message);
        // Still try to handle as progress update
        if (message.progress_percentage !== undefined) {
          callback({
            validation_id: validationId,
            status: message.status || 'running',
            progress_percentage: message.progress_percentage,
            current_agent: message.current_agent || message.current_phase,
            message: message.message || 'Processing...'
          });
        }
    }
  }

  private handleNotificationMessage(message: WebSocketMessage, callback: NotificationCallback): void {
    switch (message.type) {
      case 'notifications_connected':
        console.log('Notifications WebSocket connected');
        break;
        
      case 'user_notification':
        callback({
          message: message.data.message,
          type: message.data.type || 'info',
          timestamp: message.timestamp,
        });
        break;
        
      case 'validation_completed':
        callback({
          message: `Validation ${message.data.validation_id} completed successfully`,
          type: 'success',
          timestamp: message.timestamp,
        });
        break;
        
      case 'validation_failed':
        callback({
          message: `Validation ${message.data.validation_id} failed: ${message.data.error}`,
          type: 'error',
          timestamp: message.timestamp,
        });
        break;
        
      case 'ping':
        console.log('Received ping from notifications server');
        break;
        
      default:
        console.log('Unknown notification message type:', message.type);
    }
  }

  private handleReconnect(validationId: string, token: string, callback: ProgressCallback): void {
    // Reconnection disabled - WebSocket not available in development
    // if (this.reconnectAttempts < this.maxReconnectAttempts) {
    //   this.reconnectAttempts++;
    //   const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    //   setTimeout(() => {
    //     this.connectToValidationProgress(validationId, token, callback);
    //   }, delay);
    // }
  }

  private handleNotificationReconnect(token: string, callback: NotificationCallback): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect to notifications WebSocket (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      setTimeout(() => {
        this.connectToNotifications(token, callback);
      }, delay);
    } else {
      console.error('Max reconnection attempts reached for notifications WebSocket');
    }
  }

  private handleConnect(): void {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;
  }

  private handleDisconnect(reason: string): void {
    console.log('WebSocket disconnected:', reason);
  }

  private handleMessage(data: any): void {
    console.log('WebSocket message received:', data);
  }

  private handleError(error: Error): void {
    console.error('WebSocket error:', error);
  }

  // Disconnect from all WebSocket connections
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.progressCallbacks.clear();
    this.notificationCallback = null;
    // Silently disconnect - no console log needed
  }

  // Send message to validation progress WebSocket
  sendProgressMessage(validationId: string, message: any): void {
    // In a real implementation, we'd send this through the WebSocket
    console.log(`Sending message to validation ${validationId}:`, message);
  }

  // Check if connected to validation progress
  isConnectedToValidation(validationId: string): boolean {
    return this.progressCallbacks.has(validationId);
  }

  // Check if connected to notifications
  isConnectedToNotifications(): boolean {
    return this.notificationCallback !== null;
  }
}

export const websocketService = new WebSocketService();
export default websocketService;