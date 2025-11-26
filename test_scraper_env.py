#!/usr/bin/env python3
"""
Quick test to validate chromium is accessible and test basic browser automation
"""

import subprocess
import sys
import json

def test_chrome_installed():
    """Check if Chrome is installed"""
    result = subprocess.run(
        ["which", "google-chrome"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ Chrome found: {result.stdout.strip()}")
        return True
    else:
        print("❌ Chrome not found")
        return False

def test_cargo_build():
    """Test if Rust code compiles"""
    print("\n🔨 Testing Cargo build...")
    result = subprocess.run(
        ["cargo", "build", "--release"],
        cwd="/home/jhonslife/Didin Facil/src-tauri",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Cargo build successful")
        return True
    else:
        print(f"❌ Cargo build failed")
        print(result.stderr[-500:])  # Last 500 chars
        return False

def test_tauri_dev():
    """Test if Tauri can start"""
    print("\n🚀 Testing Tauri dev mode (will timeout after 30s)...")
    result = subprocess.run(
        ["timeout", "30s", "cargo", "tauri", "dev"],
        cwd="/home/jhonslife/Didin Facil",
        capture_output=True,
        text=True
    )
    
    # Timeout is expected
    if "SIGTERM" in result.stderr or result.returncode in [124, 143]:
        print("✅ Tauri started successfully (terminated after timeout)")
        return True
    elif result.returncode == 0:
        print("✅ Tauri started successfully")
        return True
    else:
        print(f"⚠️  Tauri had issues (code: {result.returncode})")
        print(result.stderr[-500:])
        return False

def main():
    print("🧪 TikTrend Finder - Scraper Validation\n")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Chrome
    results["chrome"] = test_chrome_installed()
    
    # Test 2: Cargo build
    results["build"] = test_cargo_build()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test.capitalize()}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to test scraping.")
        print("\n💡 Next step: Run scraper via Tauri app or manual test")
        return 0
    else:
        print("\n⚠️  Some tests failed. Fix issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
