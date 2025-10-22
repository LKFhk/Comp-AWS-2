/**
 * Frontend Logging Utility for RiskIntel360
 * Provides structured logging with file output and console display
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL'
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: string;
  data?: any;
  stack?: string;
}

class Logger {
  private logs: LogEntry[] = [];
  private maxLogs: number = 1000;
  private sessionId: string;
  private startTime: Date;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.startTime = new Date();
    this.initializeLogger();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeLogger(): void {
    // Log session start
    this.info('Logger initialized', 'Logger', {
      sessionId: this.sessionId,
      startTime: this.startTime.toISOString(),
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language
    });

    // Setup global error handler
    window.addEventListener('error', (event) => {
      this.error(
        `Uncaught error: ${event.message}`,
        'GlobalErrorHandler',
        {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          error: event.error?.stack
        }
      );
    });

    // Setup unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.error(
        `Unhandled promise rejection: ${event.reason}`,
        'GlobalErrorHandler',
        {
          reason: event.reason,
          promise: event.promise
        }
      );
    });

    // Periodically save logs to localStorage
    setInterval(() => this.saveLogsToStorage(), 30000); // Every 30 seconds

    // Save logs before page unload
    window.addEventListener('beforeunload', () => {
      this.saveLogsToStorage();
    });
  }

  private formatTimestamp(): string {
    const now = new Date();
    return now.toISOString();
  }

  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: string,
    data?: any,
    stack?: string
  ): LogEntry {
    return {
      timestamp: this.formatTimestamp(),
      level,
      message,
      context,
      data,
      stack
    };
  }

  private addLog(entry: LogEntry): void {
    this.logs.push(entry);

    // Keep only the last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Output to console
    this.outputToConsole(entry);
  }

  private outputToConsole(entry: LogEntry): void {
    const prefix = `[${entry.timestamp}] [${entry.level}]${entry.context ? ` [${entry.context}]` : ''}`;
    const message = `${prefix} ${entry.message}`;

    switch (entry.level) {
      case LogLevel.DEBUG:
        console.debug(message, entry.data || '');
        break;
      case LogLevel.INFO:
        console.info(message, entry.data || '');
        break;
      case LogLevel.WARN:
        console.warn(message, entry.data || '');
        break;
      case LogLevel.ERROR:
      case LogLevel.CRITICAL:
        console.error(message, entry.data || '', entry.stack || '');
        break;
    }
  }

  private saveLogsToStorage(): void {
    try {
      const filename = `riskintel360_frontend_${this.formatFilename()}.json`;
      const logData = {
        sessionId: this.sessionId,
        startTime: this.startTime.toISOString(),
        endTime: new Date().toISOString(),
        logs: this.logs
      };

      // Save to localStorage
      localStorage.setItem('riskintel360_current_logs', JSON.stringify(logData));
      
      // Also save to sessionStorage as backup
      sessionStorage.setItem('riskintel360_current_logs', JSON.stringify(logData));

      // Store filename for easy retrieval
      localStorage.setItem('riskintel360_log_filename', filename);
    } catch (error) {
      console.error('Failed to save logs to storage:', error);
    }
  }

  private formatFilename(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    return `${year}${month}${day}_${hours}${minutes}${seconds}`;
  }

  public debug(message: string, context?: string, data?: any): void {
    const entry = this.createLogEntry(LogLevel.DEBUG, message, context, data);
    this.addLog(entry);
  }

  public info(message: string, context?: string, data?: any): void {
    const entry = this.createLogEntry(LogLevel.INFO, message, context, data);
    this.addLog(entry);
  }

  public warn(message: string, context?: string, data?: any): void {
    const entry = this.createLogEntry(LogLevel.WARN, message, context, data);
    this.addLog(entry);
  }

  public error(message: string, context?: string, data?: any, error?: Error): void {
    const stack = error?.stack || new Error().stack;
    const entry = this.createLogEntry(LogLevel.ERROR, message, context, data, stack);
    this.addLog(entry);
  }

  public critical(message: string, context?: string, data?: any, error?: Error): void {
    const stack = error?.stack || new Error().stack;
    const entry = this.createLogEntry(LogLevel.CRITICAL, message, context, data, stack);
    this.addLog(entry);
  }

  public getLogs(): LogEntry[] {
    return [...this.logs];
  }

  public getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  public getRecentLogs(count: number = 50): LogEntry[] {
    return this.logs.slice(-count);
  }

  public clearLogs(): void {
    this.logs = [];
    localStorage.removeItem('riskintel360_current_logs');
    sessionStorage.removeItem('riskintel360_current_logs');
    this.info('Logs cleared', 'Logger');
  }

  public downloadLogs(): void {
    try {
      const filename = `riskintel360_frontend_${this.formatFilename()}.json`;
      const logData = {
        sessionId: this.sessionId,
        startTime: this.startTime.toISOString(),
        endTime: new Date().toISOString(),
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        logs: this.logs
      };

      const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      this.info('Logs downloaded', 'Logger', { filename });
    } catch (error) {
      console.error('Failed to download logs:', error);
    }
  }

  public getLogSummary(): {
    totalLogs: number;
    byLevel: Record<LogLevel, number>;
    sessionDuration: number;
    errorCount: number;
  } {
    const byLevel = {
      [LogLevel.DEBUG]: 0,
      [LogLevel.INFO]: 0,
      [LogLevel.WARN]: 0,
      [LogLevel.ERROR]: 0,
      [LogLevel.CRITICAL]: 0
    };

    this.logs.forEach(log => {
      byLevel[log.level]++;
    });

    const sessionDuration = Date.now() - this.startTime.getTime();
    const errorCount = byLevel[LogLevel.ERROR] + byLevel[LogLevel.CRITICAL];

    return {
      totalLogs: this.logs.length,
      byLevel,
      sessionDuration,
      errorCount
    };
  }
}

// Create singleton instance
const logger = new Logger();

// Export logger instance and types
export { logger, type LogEntry };

// Export convenience functions
export const logDebug = (message: string, context?: string, data?: any) => 
  logger.debug(message, context, data);

export const logInfo = (message: string, context?: string, data?: any) => 
  logger.info(message, context, data);

export const logWarn = (message: string, context?: string, data?: any) => 
  logger.warn(message, context, data);

export const logError = (message: string, context?: string, data?: any, error?: Error) => 
  logger.error(message, context, data, error);

export const logCritical = (message: string, context?: string, data?: any, error?: Error) => 
  logger.critical(message, context, data, error);

export default logger;
