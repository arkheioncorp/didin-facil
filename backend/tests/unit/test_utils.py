"""
Utils Unit Tests
Tests for integrity and security utilities
"""
import pytest
from unittest.mock import patch
import os
import tempfile

from api.utils.integrity import IntegrityChecker, CRITICAL_FILES
from api.utils.security import SecurityMonitor


# ============== IntegrityChecker Tests ==============

class TestIntegrityChecker:
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def checker(self, temp_dir):
        return IntegrityChecker(temp_dir)
    
    def test_init(self, checker, temp_dir):
        assert checker.base_path == temp_dir
    
    def test_calculate_file_hash_file_exists(self, checker, temp_dir):
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        result = checker.calculate_file_hash("test.txt")
        
        assert len(result) == 64  # SHA256 hex digest length
        assert result != ""
    
    def test_calculate_file_hash_file_not_found(self, checker):
        result = checker.calculate_file_hash("nonexistent.txt")
        
        assert result == ""
    
    def test_calculate_file_hash_consistency(self, checker, temp_dir):
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("consistent content")
        
        hash1 = checker.calculate_file_hash("test.txt")
        hash2 = checker.calculate_file_hash("test.txt")
        
        assert hash1 == hash2
    
    def test_calculate_file_hash_different_content(self, checker, temp_dir):
        # Create two different files
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        
        with open(file1, "w") as f:
            f.write("content 1")
        with open(file2, "w") as f:
            f.write("content 2")
        
        hash1 = checker.calculate_file_hash("file1.txt")
        hash2 = checker.calculate_file_hash("file2.txt")
        
        assert hash1 != hash2
    
    def test_verify_integrity_files_missing(self, checker):
        # All critical files are missing in temp dir
        result = checker.verify_integrity()
        
        # Should return False since files are missing
        assert result is False
    
    def test_verify_integrity_files_exist(self, temp_dir):
        checker = IntegrityChecker(temp_dir)
        
        # Create all critical files
        for rel_path in CRITICAL_FILES:
            full_path = os.path.join(temp_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write("file content")
        
        result = checker.verify_integrity()
        
        assert result is True
    
    def test_critical_files_list(self):
        assert len(CRITICAL_FILES) > 0
        assert "api/main.py" in CRITICAL_FILES


# ============== SecurityMonitor Tests ==============

class TestSecurityMonitor:
    
    @pytest.fixture
    def monitor(self):
        return SecurityMonitor()
    
    def test_init(self, monitor):
        assert monitor.running is False
    
    def test_start_sets_running(self, monitor):
        with patch.object(monitor, '_monitor_loop'):
            monitor.start()
            
            assert monitor.running is True
            
            monitor.stop()
    
    def test_stop_clears_running(self, monitor):
        monitor.running = True
        monitor._stop_event.clear()
        
        monitor.stop()
        
        assert monitor.running is False
        assert monitor._stop_event.is_set()
    
    def test_check_debugger_allowed(self):
        with patch.dict(os.environ, {"ALLOW_DEBUGGER": "true"}):
            result = SecurityMonitor.check_debugger()
            
            assert result is False
    
    def test_check_debugger_no_debugger(self):
        with patch.dict(
            os.environ,
            {"ALLOW_DEBUGGER": "false"},
            clear=True
        ):
            with patch("sys.gettrace", return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is False
    
    def test_check_debugger_trace_detected(self):
        with patch.dict(os.environ, {"ALLOW_DEBUGGER": "false"}):
            with patch("sys.gettrace", return_value=lambda: None):
                result = SecurityMonitor.check_debugger()
                
                assert result is True
    
    def test_check_debugger_env_var_detected(self):
        with patch.dict(
            os.environ,
            {"ALLOW_DEBUGGER": "false", "PYCHARM_HOSTED": "1"}
        ):
            with patch("sys.gettrace", return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is True
    
    def test_check_debugger_vscode_detected(self):
        with patch.dict(
            os.environ,
            {"ALLOW_DEBUGGER": "false", "VSCODE_PID": "12345"}
        ):
            with patch("sys.gettrace", return_value=None):
                result = SecurityMonitor.check_debugger()
                
                assert result is True
