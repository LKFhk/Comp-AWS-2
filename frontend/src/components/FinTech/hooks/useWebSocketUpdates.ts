/**
 * Custom hook for WebSocket real-time updates
 * Integrates with existing WebSocket system for real-time dashboard updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { FinancialAlert } from '../../../types/fintech';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface UseWebSocketUpdatesProps {
  enabled?: boolean;
  onAlert?: (alert: FinancialAlert) => void;
  onDataUpdate?: (data: any) => void;
  reconnectInterval?: number;
}

interface WebSocketState {
  connected: boolean;
  lastMessage: WebSocketMessage | null;
  error: string | null;
}

export const useWebSocketUpdates = (
  channel?: string,
  {
    enabled = true,
    onAlert,
    onDataUpdate,
    reconnectInterval = 5000,
  }: UseWebSocketUpdatesProps = {}
) => {
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    lastMessage: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Use existing WebSocket endpoint from the application
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setState(prev => ({ ...prev, connected: true, error: null }));
        reconnectAttemptsRef.current = 0;
        
        // Subscribe to fintech updates
        const channels = channel ? [channel] : ['fraud_alerts', 'compliance_updates', 'market_data', 'kyc_updates', 'business_value', 'performance', 'competition_demo'];
        wsRef.current?.send(JSON.stringify({
          type: 'subscribe',
          channels,
        }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setState(prev => ({ ...prev, lastMessage: message }));

          // Handle different message types
          switch (message.type) {
            case 'fraud_alert':
              if (onAlert) {
                const alert: FinancialAlert = {
                  alert_id: message.data.alert_id || `FRAUD-${Date.now()}`,
                  alert_type: 'fraud_detection',
                  severity: message.data.severity || 'medium',
                  title: message.data.title || 'Fraud Alert',
                  description: message.data.description || 'Fraud detected',
                  created_at: message.timestamp,
                  metadata: message.data,
                };
                onAlert(alert);
              }
              break;

            case 'compliance_alert':
              if (onAlert) {
                const alert: FinancialAlert = {
                  alert_id: message.data.alert_id || `COMP-${Date.now()}`,
                  alert_type: 'compliance',
                  severity: message.data.severity || 'medium',
                  title: message.data.title || 'Compliance Alert',
                  description: message.data.description || 'Compliance issue detected',
                  created_at: message.timestamp,
                  metadata: message.data,
                };
                onAlert(alert);
              }
              break;

            case 'kyc_alert':
              if (onAlert) {
                const alert: FinancialAlert = {
                  alert_id: message.data.alert_id || `KYC-${Date.now()}`,
                  alert_type: 'kyc_verification',
                  severity: message.data.severity || 'medium',
                  title: message.data.title || 'KYC Alert',
                  description: message.data.description || 'KYC verification required',
                  created_at: message.timestamp,
                  metadata: message.data,
                };
                onAlert(alert);
              }
              break;

            case 'market_update':
            case 'performance_update':
            case 'system_health':
            case 'business_value_update':
            case 'demo_progress':
              if (onDataUpdate) {
                onDataUpdate(message.data);
              }
              break;

            default:
              console.log('Unknown WebSocket message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        setState(prev => ({ ...prev, connected: false }));
        
        if (enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval * reconnectAttemptsRef.current);
        }
      };

      wsRef.current.onerror = (error) => {
        setState(prev => ({ 
          ...prev, 
          error: 'WebSocket connection error',
          connected: false 
        }));
      };

    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Connection failed',
        connected: false 
      }));
    }
  }, [enabled, onAlert, onDataUpdate, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(prev => ({ ...prev, connected: false }));
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  // Connect on mount if enabled
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected: state.connected,
    connected: state.connected,
    lastMessage: state.lastMessage,
    error: state.error,
    connect,
    disconnect,
    sendMessage,
    reconnectAttempts: reconnectAttemptsRef.current,
  };
};