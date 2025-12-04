"""
Comprehensive tests for Security Monitor
Tests for debugger detection and security monitoring
"""

import os
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest


class TestSecurityMonitorInit:
    """Tests for SecurityMonitor initialization"""
    
    def test_init_sets_defaults(self):
        """Test SecurityMonitor initializes with correct defaults"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        
        assert monitor.running is False
        assert isinstance(monitor._stop_event, threading.Event)
        assert not monitor._stop_event.is_set()


class TestSecurityMonitorLifecycle:
    """Tests for start/stop lifecycle"""
    
    def test_start_sets_running_true(self):
        """Test start sets running flag to True"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        
        with patch.object(monitor, '_monitor_loop'):
            monitor.start()
            
            assert monitor.running is True
            assert hasattr(monitor, 'thread')
    
    def test_stop_sets_running_false(self):
        """Test stop sets running flag to False"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        monitor.running = True
        monitor._stop_event.clear()
        
        monitor.stop()
        
        assert monitor.running is False
        assert monitor._stop_event.is_set()
    
    def test_start_creates_daemon_thread(self):
        """Test start creates a daemon thread"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        
        with patch.object(monitor, '_monitor_loop'):
            with patch('threading.Thread') as mock_thread:
                mock_instance = MagicMock()
                mock_thread.return_value = mock_instance
                
                monitor.start()
                
                mock_thread.assert_called_once_with(
                    target=monitor._monitor_loop,
                    daemon=True
                )
                mock_instance.start.assert_called_once()


class TestCheckDebugger:
    """Tests for debugger detection"""
    
    def test_check_debugger_allows_when_env_set(self):
        """Test check_debugger returns False when ALLOW_DEBUGGER=true"""
        from api.utils.security import SecurityMonitor
        
        with patch.dict(os.environ, {'ALLOW_DEBUGGER': 'true'}):
            result = SecurityMonitor.check_debugger()
            
            assert result is False
    
    def test_check_debugger_case_insensitive(self):
        """Test ALLOW_DEBUGGER check is case insensitive"""
        from api.utils.security import SecurityMonitor
        
        for value in ['TRUE', 'True', 'true', 'TrUe']:
            with patch.dict(os.environ, {'ALLOW_DEBUGGER': value}):
                result = SecurityMonitor.check_debugger()
                assert result is False
    
    def test_check_debugger_detects_sys_gettrace(self):
        """Test check_debugger detects sys.gettrace"""
        from api.utils.security import SecurityMonitor
        
        with patch.dict(os.environ, {'ALLOW_DEBUGGER': 'false'}, clear=False):
            with patch('sys.gettrace', return_value=lambda *args: None):
                result = SecurityMonitor.check_debugger()
                
                assert result is True
    
    def test_check_debugger_no_trace_returns_false(self):
        """Test check_debugger returns False when no trace function"""
        from api.utils.security import SecurityMonitor

        # Clear debug env vars
        clean_env = {k: v for k, v in os.environ.items() 
                     if k not in ['PYCHARM_HOSTED', 'VSCODE_PID', 'DEBUG_MODE', 
                                  'PYTHONDEVMODE', 'ALLOW_DEBUGGER']}
        
        with patch.dict(os.environ, clean_env, clear=True):
            with patch('sys.gettrace', return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is False
    
    def test_check_debugger_detects_pycharm(self):
        """Test check_debugger detects PYCHARM_HOSTED=true"""
        from api.utils.security import SecurityMonitor
        
        env = {'PYCHARM_HOSTED': 'true', 'ALLOW_DEBUGGER': 'false'}
        
        with patch.dict(os.environ, env, clear=False):
            with patch('sys.gettrace', return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is True
    
    def test_check_debugger_detects_vscode(self):
        """Test check_debugger detects VSCODE_PID=true"""
        from api.utils.security import SecurityMonitor
        
        env = {'VSCODE_PID': 'true', 'ALLOW_DEBUGGER': 'false'}
        
        with patch.dict(os.environ, env, clear=False):
            with patch('sys.gettrace', return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is True
    
    def test_check_debugger_detects_debug_mode(self):
        """Test check_debugger detects DEBUG_MODE=true"""
        from api.utils.security import SecurityMonitor
        
        env = {'DEBUG_MODE': 'true', 'ALLOW_DEBUGGER': 'false'}
        
        with patch.dict(os.environ, env, clear=False):
            with patch('sys.gettrace', return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is True
    
    def test_check_debugger_ignores_non_true_values(self):
        """Test check_debugger ignores non-true env var values"""
        from api.utils.security import SecurityMonitor

        # Clear debug env vars
        clean_env = {k: v for k, v in os.environ.items() 
                     if k not in ['PYCHARM_HOSTED', 'VSCODE_PID', 'DEBUG_MODE', 
                                  'PYTHONDEVMODE', 'ALLOW_DEBUGGER']}
        clean_env['PYCHARM_HOSTED'] = 'false'
        clean_env['DEBUG_MODE'] = '0'
        
        with patch.dict(os.environ, clean_env, clear=True):
            with patch('sys.gettrace', return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is False


class TestMonitorLoop:
    """Tests for the monitor loop behavior"""
    
    def test_monitor_loop_stops_when_running_false(self):
        """Test monitor loop exits when running is False"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        monitor.running = False
        
        # Should return immediately
        with patch.object(SecurityMonitor, 'check_debugger') as mock_check:
            monitor._monitor_loop()
            mock_check.assert_not_called()
    
    def test_monitor_loop_stops_when_event_set(self):
        """Test monitor loop exits when stop event is set"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        monitor.running = True
        monitor._stop_event.set()
        
        with patch.object(SecurityMonitor, 'check_debugger') as mock_check:
            monitor._monitor_loop()
            mock_check.assert_not_called()
    
    def test_monitor_loop_checks_debugger(self):
        """Test monitor loop calls check_debugger"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        call_count = 0
        
        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                monitor.running = False
            return False
        
        with patch.object(SecurityMonitor, 'check_debugger', side_effect=side_effect):
            with patch('time.sleep'):
                monitor.running = True
                monitor._monitor_loop()
                
                assert call_count >= 1


class TestSecurityMonitorSingleton:
    """Tests for the global singleton instance"""
    
    def test_security_monitor_singleton_exists(self):
        """Test that security_monitor singleton is created"""
        from api.utils.security import SecurityMonitor, security_monitor
        
        assert security_monitor is not None
        assert isinstance(security_monitor, SecurityMonitor)


class TestSecurityMonitorIntegration:
    """Integration tests for SecurityMonitor"""
    
    def test_start_and_stop_integration(self):
        """Test starting and stopping the monitor"""
        from api.utils.security import SecurityMonitor
        
        monitor = SecurityMonitor()
        
        # Allow debugger for test
        with patch.dict(os.environ, {'ALLOW_DEBUGGER': 'true'}):
            with patch.object(SecurityMonitor, 'check_debugger', return_value=False):
                monitor.start()
                
                assert monitor.running is True
                assert monitor.thread.is_alive()
                
                # Give thread time to start
                time.sleep(0.1)
                
                monitor.stop()
                
                # Wait for thread to stop
                monitor.thread.join(timeout=1)
                
                assert monitor.running is False
                assert monitor._stop_event.is_set()
    
    def test_multiple_start_stop_cycles(self):
        """Test multiple start/stop cycles"""
        from api.utils.security import SecurityMonitor
        
        with patch.object(SecurityMonitor, 'check_debugger', return_value=False):
            for _ in range(3):
                monitor = SecurityMonitor()
                
                monitor.start()
                assert monitor.running is True
                
                time.sleep(0.05)
                
                monitor.stop()
                assert monitor.running is False
