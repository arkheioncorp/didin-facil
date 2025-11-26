import sys
import os
import time
import threading
import logging

logger = logging.getLogger(__name__)

class SecurityMonitor:
    def __init__(self):
        self.running = False
        self._stop_event = threading.Event()

    def start(self):
        """Start security monitoring in a background thread"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self._stop_event.set()

    def _monitor_loop(self):
        while self.running and not self._stop_event.is_set():
            if self.check_debugger():
                logger.critical("Debugger detected! Terminating...")
                os._exit(1)  # Force exit
            
            time.sleep(2)  # Check every 2 seconds

    @staticmethod
    def check_debugger() -> bool:
        """Check if the application is being debugged"""
        if os.environ.get("ALLOW_DEBUGGER", "false").lower() == "true":
            return False

        # Check sys.gettrace
        if sys.gettrace() is not None:
            return True

        # Check for common debugger environment variables
        debug_vars = [
            "PYCHARM_HOSTED",
            "VSCODE_PID",
            "DEBUG_MODE",
            "PYTHONDEVMODE"
        ]
        for var in debug_vars:
            if os.environ.get(var):
                return True

        return False

security_monitor = SecurityMonitor()
