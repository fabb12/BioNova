#!/usr/bin/env python3
"""
Medical Logger Component - IEC 62304 Compliant Logging
Provides audit trail and event logging for medical device software
"""

import os
import logging
import datetime
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import threading


class MedicalLogger:
    """
    IEC 62304 compliant logging system for medical device software
    Provides audit trail, event logging, and regulatory compliance
    """

    def __init__(self, log_dir: str = "logs", max_file_size: int = 10485760, backup_count: int = 5):
        """
        Initialize the medical logger

        Args:
            log_dir: Directory for log files
            max_file_size: Maximum size of each log file in bytes (default 10MB)
            backup_count: Number of backup files to keep
        """
        print(f"Initializing MedicalLogger with log_dir: {log_dir}")

        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self._lock = threading.Lock()

        try:
            # Create log directory if it doesn't exist
            self.log_dir.mkdir(exist_ok=True)
            print(f"✓ Log directory created/verified: {self.log_dir}")
        except Exception as e:
            print(f"✗ Failed to create log directory: {e}")
            raise

        try:
            # Set up loggers
            self._setup_loggers()
            print("✓ Loggers set up successfully")
        except Exception as e:
            print(f"✗ Failed to set up loggers: {e}")
            raise

        try:
            # Log initialization
            self.log_event("SYSTEM", "Medical Logger initialized", "INFO")
            print("✓ Initial log event recorded")
        except Exception as e:
            print(f"✗ Failed to record initial log event: {e}")
            # Don't raise here, logger is mostly working

    def _setup_loggers(self):
        """Set up different loggers for different purposes"""

        # Main event logger
        self.event_logger = logging.getLogger("medical_events")
        self.event_logger.setLevel(logging.INFO)

        # Error logger
        self.error_logger = logging.getLogger("medical_errors")
        self.error_logger.setLevel(logging.ERROR)

        # Audit logger (for regulatory compliance)
        self.audit_logger = logging.getLogger("medical_audit")
        self.audit_logger.setLevel(logging.INFO)

        # Clear existing handlers
        for logger in [self.event_logger, self.error_logger, self.audit_logger]:
            logger.handlers.clear()

        # Create custom formatter with microseconds
        class MicrosecondFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                import datetime
                ct = datetime.datetime.fromtimestamp(record.created)
                if datefmt:
                    # Replace %f with microseconds manually
                    if '%f' in datefmt:
                        datefmt = datefmt.replace('%f', f'{ct.microsecond:06d}')
                    s = ct.strftime(datefmt)
                else:
                    s = ct.strftime('%Y-%m-%d %H:%M:%S')
                return s

        # Create formatters
        detailed_formatter = MicrosecondFormatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )

        audit_formatter = MicrosecondFormatter(
            '%(asctime)s | AUDIT | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )

        # Set up rotating file handlers
        event_handler = RotatingFileHandler(
            self.log_dir / "medical_events.log",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        event_handler.setFormatter(detailed_formatter)
        self.event_logger.addHandler(event_handler)

        error_handler = RotatingFileHandler(
            self.log_dir / "medical_errors.log",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        error_handler.setFormatter(detailed_formatter)
        self.error_logger.addHandler(error_handler)

        audit_handler = RotatingFileHandler(
            self.log_dir / "medical_audit.log",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        audit_handler.setFormatter(audit_formatter)
        self.audit_logger.addHandler(audit_handler)

    def log_event(self, event_type: str, message: str, severity: str = "INFO"):
        """
        Log an event with specified type and severity

        Args:
            event_type: Type of event (e.g., 'FILE_LOAD', 'USER_ACTION', 'SYSTEM')
            message: Event description
            severity: Severity level ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        with self._lock:
            formatted_message = f"{event_type} | {message}"

            if severity.upper() == "INFO":
                self.event_logger.info(formatted_message)
            elif severity.upper() == "WARNING":
                self.event_logger.warning(formatted_message)
            elif severity.upper() == "ERROR":
                self.event_logger.error(formatted_message)
                self.error_logger.error(formatted_message)
            elif severity.upper() == "CRITICAL":
                self.event_logger.critical(formatted_message)
                self.error_logger.critical(formatted_message)

    def log_user_action(self, action: str, details: str = ""):
        """
        Log user actions for audit trail

        Args:
            action: User action performed
            details: Additional details about the action
        """
        message = f"USER_ACTION | {action}"
        if details:
            message += f" | {details}"

        with self._lock:
            self.audit_logger.info(message)
            self.log_event("USER_ACTION", f"{action} - {details}", "INFO")

    def log_file_operation(self, operation: str, filepath: str, result: str = "SUCCESS"):
        """
        Log file operations for regulatory compliance

        Args:
            operation: Type of file operation (LOAD, SAVE, DELETE, etc.)
            filepath: Path to the file
            result: Result of the operation (SUCCESS, ERROR, etc.)
        """
        message = f"FILE_OP | {operation} | {filepath} | {result}"

        with self._lock:
            self.audit_logger.info(message)

            if result == "SUCCESS":
                self.log_event("FILE_OPERATION", message, "INFO")
            else:
                self.log_event("FILE_OPERATION", message, "ERROR")

    def log_image_processing(self, operation: str, image_info: str, result: str = "SUCCESS"):
        """
        Log image processing operations

        Args:
            operation: Type of processing (2D_DISPLAY, 3D_RENDER, WINDOW_LEVEL, etc.)
            image_info: Information about the image being processed
            result: Result of the operation
        """
        message = f"IMAGE_PROC | {operation} | {image_info} | {result}"

        with self._lock:
            self.audit_logger.info(message)

            if result == "SUCCESS":
                self.log_event("IMAGE_PROCESSING", message, "INFO")
            else:
                self.log_event("IMAGE_PROCESSING", message, "ERROR")

    def log_system_event(self, event: str, details: str = ""):
        """
        Log system events

        Args:
            event: System event type
            details: Additional details
        """
        message = f"SYSTEM | {event}"
        if details:
            message += f" | {details}"

        with self._lock:
            self.audit_logger.info(message)
            self.log_event("SYSTEM", f"{event} - {details}", "INFO")

    def log_error(self, error_type: str, error_message: str, stack_trace: Optional[str] = None):
        """
        Log errors with detailed information

        Args:
            error_type: Type of error
            error_message: Error description
            stack_trace: Optional stack trace
        """
        message = f"ERROR | {error_type} | {error_message}"
        if stack_trace:
            message += f" | STACK: {stack_trace}"

        with self._lock:
            self.error_logger.error(message)
            self.audit_logger.error(message)
            self.log_event("ERROR", message, "ERROR")

    def get_log_files(self) -> list:
        """
        Get list of all log files

        Returns:
            List of log file paths
        """
        log_files = []
        for file_path in self.log_dir.glob("*.log*"):
            if file_path.is_file():
                log_files.append(str(file_path))
        return sorted(log_files)

    def get_recent_events(self, count: int = 100) -> list:
        """
        Get recent events from the log

        Args:
            count: Number of recent events to retrieve

        Returns:
            List of recent log entries
        """
        events = []
        try:
            event_log_path = self.log_dir / "medical_events.log"
            if event_log_path.exists():
                with open(event_log_path, 'r') as f:
                    lines = f.readlines()
                    events = lines[-count:] if len(lines) > count else lines
        except Exception as e:
            self.log_error("LOG_READ", f"Failed to read recent events: {str(e)}")

        return events

    def cleanup_old_logs(self, days_to_keep: int = 365):
        """
        Clean up log files older than specified days
        IEC 62304 requires maintaining logs for at least 1 year

        Args:
            days_to_keep: Number of days to keep logs (default 365)
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)

        for log_file in self.log_dir.glob("*.log*"):
            try:
                file_time = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    self.log_system_event("LOG_CLEANUP", f"Removed old log file: {log_file}")
            except Exception as e:
                self.log_error("LOG_CLEANUP", f"Failed to remove old log file {log_file}: {str(e)}")

    def __del__(self):
        """Cleanup when logger is destroyed"""
        try:
            self.log_event("SYSTEM", "Medical Logger shutting down", "INFO")
        except:
            pass