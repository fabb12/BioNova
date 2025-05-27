#!/usr/bin/env python3
"""
Test individual imports to find the blocking component
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(src_path / "core"))


def test_basic_imports():
    """Test basic Python imports"""
    print("=== Testing Basic Imports ===")

    try:
        import os
        print("✓ os")
    except Exception as e:
        print(f"✗ os: {e}")

    try:
        import pathlib
        print("✓ pathlib")
    except Exception as e:
        print(f"✗ pathlib: {e}")

    try:
        import threading
        print("✓ threading")
    except Exception as e:
        print(f"✗ threading: {e}")

    try:
        import logging
        print("✓ logging")
    except Exception as e:
        print(f"✗ logging: {e}")


def test_scientific_imports():
    """Test scientific library imports"""
    print("\n=== Testing Scientific Libraries ===")

    try:
        import numpy
        print("✓ numpy")
    except Exception as e:
        print(f"✗ numpy: {e}")

    try:
        print("Importing SimpleITK...")
        import SimpleITK as sitk
        print("✓ SimpleITK")
    except Exception as e:
        print(f"✗ SimpleITK: {e}")

    try:
        print("Importing VTK...")
        import vtk
        print("✓ VTK")
    except Exception as e:
        print(f"✗ VTK: {e}")


def test_qt_imports():
    """Test Qt imports"""
    print("\n=== Testing Qt Libraries ===")

    try:
        print("Importing PyQt6.QtCore...")
        from PyQt6.QtCore import QObject, pyqtSignal
        print("✓ PyQt6.QtCore")
    except Exception as e:
        print(f"✗ PyQt6.QtCore: {e}")

    try:
        print("Importing PyQt6.QtGui...")
        from PyQt6.QtGui import QGuiApplication
        print("✓ PyQt6.QtGui")
    except Exception as e:
        print(f"✗ PyQt6.QtGui: {e}")

    try:
        print("Importing PyQt6.QtQml...")
        from PyQt6.QtQml import QQmlApplicationEngine
        print("✓ PyQt6.QtQml")
    except Exception as e:
        print(f"✗ PyQt6.QtQml: {e}")


def test_our_modules():
    """Test our custom modules"""
    print("\n=== Testing Our Modules ===")

    try:
        print("Importing medical_logger...")
        from medical_logger import MedicalLogger
        print("✓ medical_logger")
    except Exception as e:
        print(f"✗ medical_logger: {e}")
        return False

    try:
        print("Creating MedicalLogger instance...")
        logger = MedicalLogger()
        print("✓ MedicalLogger instance created")
    except Exception as e:
        print(f"✗ MedicalLogger instance: {e}")
        return False

    try:
        print("Importing image_processor...")
        from image_processor import ImageProcessor
        print("✓ image_processor imported")
    except Exception as e:
        print(f"✗ image_processor import: {e}")
        return False

    try:
        print("Creating ImageProcessor instance...")
        processor = ImageProcessor(logger)
        print("✓ ImageProcessor instance created")
    except Exception as e:
        print(f"✗ ImageProcessor instance: {e}")
        return False

    return True


def test_step_by_step():
    """Test each step that might be blocking"""
    print("\n=== Step by Step Test ===")

    # Test 1: Basic imports
    print("Step 1: Basic imports")
    test_basic_imports()

    # Test 2: Scientific libraries
    print("\nStep 2: Scientific libraries")
    test_scientific_imports()

    # Test 3: Qt libraries
    print("\nStep 3: Qt libraries")
    test_qt_imports()

    # Test 4: Our modules
    print("\nStep 4: Our modules")
    success = test_our_modules()

    if success:
        print("\n✓ All components can be imported and created!")
    else:
        print("\n✗ Some components failed to import or create")

    return success


def main():
    """Main test function"""
    print("Testing individual imports to find blocking component...\n")

    try:
        success = test_step_by_step()

        if success:
            print("\n" + "=" * 50)
            print("SUCCESS: All imports working!")
            print("The blocking issue is likely in the main application loop.")
            print("Try running python main.py again.")
        else:
            print("\n" + "=" * 50)
            print("ISSUE FOUND: Check the failed imports above.")

    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        import traceback
        traceback.print_exc()

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()