/**
 * Log Viewer Component
 * Displays application logs with filtering and download capabilities
 */

import React, { useState, useEffect } from 'react';
import logger, { LogLevel, LogEntry } from '../../utils/logger';

interface LogViewerProps {
  maxHeight?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const LogViewer: React.FC<LogViewerProps> = ({
  maxHeight = '500px',
  autoRefresh = true,
  refreshInterval = 2000
}) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filterLevel, setFilterLevel] = useState<LogLevel | 'ALL'>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    // Initial load
    updateLogs();

    // Auto-refresh if enabled
    if (autoRefresh) {
      const interval = setInterval(updateLogs, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const updateLogs = () => {
    setLogs(logger.getLogs());
  };

  const filteredLogs = logs.filter(log => {
    const levelMatch = filterLevel === 'ALL' || log.level === filterLevel;
    const searchMatch = searchTerm === '' || 
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.context?.toLowerCase().includes(searchTerm.toLowerCase());
    return levelMatch && searchMatch;
  });

  const getLogLevelColor = (level: LogLevel): string => {
    switch (level) {
      case LogLevel.DEBUG:
        return '#6c757d';
      case LogLevel.INFO:
        return '#0dcaf0';
      case LogLevel.WARN:
        return '#ffc107';
      case LogLevel.ERROR:
        return '#dc3545';
      case LogLevel.CRITICAL:
        return '#8b0000';
      default:
        return '#000';
    }
  };

  const handleDownload = () => {
    logger.downloadLogs();
  };

  const handleClear = () => {
    if (window.confirm('Are you sure you want to clear all logs?')) {
      logger.clearLogs();
      updateLogs();
    }
  };

  const summary = logger.getLogSummary();

  return (
    <div style={{ 
      fontFamily: 'monospace', 
      border: '1px solid #ddd', 
      borderRadius: '4px',
      backgroundColor: '#f8f9fa'
    }}>
      {/* Header */}
      <div style={{ 
        padding: '12px', 
        borderBottom: '1px solid #ddd',
        backgroundColor: '#fff'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>
          Application Logs
        </h3>
        
        {/* Summary */}
        <div style={{ 
          display: 'flex', 
          gap: '16px', 
          marginBottom: '12px',
          fontSize: '12px'
        }}>
          <span>Total: {summary.totalLogs}</span>
          <span style={{ color: getLogLevelColor(LogLevel.ERROR) }}>
            Errors: {summary.errorCount}
          </span>
          <span>
            Session: {Math.floor(summary.sessionDuration / 1000)}s
          </span>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <select 
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value as LogLevel | 'ALL')}
            style={{ padding: '4px 8px', fontSize: '12px' }}
          >
            <option value="ALL">All Levels</option>
            <option value={LogLevel.DEBUG}>Debug</option>
            <option value={LogLevel.INFO}>Info</option>
            <option value={LogLevel.WARN}>Warning</option>
            <option value={LogLevel.ERROR}>Error</option>
            <option value={LogLevel.CRITICAL}>Critical</option>
          </select>

          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ 
              padding: '4px 8px', 
              fontSize: '12px',
              flex: '1',
              minWidth: '200px'
            }}
          />

          <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>

          <button
            onClick={updateLogs}
            style={{ 
              padding: '4px 12px', 
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Refresh
          </button>

          <button
            onClick={handleDownload}
            style={{ 
              padding: '4px 12px', 
              fontSize: '12px',
              cursor: 'pointer',
              backgroundColor: '#0d6efd',
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
          >
            Download
          </button>

          <button
            onClick={handleClear}
            style={{ 
              padding: '4px 12px', 
              fontSize: '12px',
              cursor: 'pointer',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div 
        style={{ 
          maxHeight,
          overflowY: 'auto',
          padding: '8px',
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4'
        }}
      >
        {filteredLogs.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#888' }}>
            No logs to display
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div
              key={index}
              style={{
                padding: '4px 8px',
                marginBottom: '2px',
                fontSize: '11px',
                lineHeight: '1.4',
                borderLeft: `3px solid ${getLogLevelColor(log.level)}`,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                wordBreak: 'break-word'
              }}
            >
              <div>
                <span style={{ color: '#888' }}>{log.timestamp}</span>
                {' '}
                <span style={{ 
                  color: getLogLevelColor(log.level),
                  fontWeight: 'bold'
                }}>
                  [{log.level}]
                </span>
                {log.context && (
                  <span style={{ color: '#4ec9b0' }}> [{log.context}]</span>
                )}
                {' '}
                <span>{log.message}</span>
              </div>
              {log.data && (
                <div style={{ 
                  marginTop: '4px', 
                  paddingLeft: '12px',
                  color: '#ce9178'
                }}>
                  {JSON.stringify(log.data, null, 2)}
                </div>
              )}
              {log.stack && (
                <div style={{ 
                  marginTop: '4px', 
                  paddingLeft: '12px',
                  color: '#f48771',
                  fontSize: '10px'
                }}>
                  {log.stack}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LogViewer;
