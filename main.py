#!/usr/bin/env python3
"""
Medical Image Viewer - Main Entry Point
Fixed version with proper error handling and debugging
"""

import sys
import os
from pathlib import Path


def setup_environment():
    """Setup the Python environment for the application"""
    # Add src directory to Python path
    current_dir = Path(__file__).parent
    src_path = current_dir / "src"

    print(f"Current directory: {current_dir}")
    print(f"Looking for src at: {src_path}")

    if src_path.exists():
        sys.path.insert(0, str(src_path))
        print(f"Added to Python path: {src_path}")

        # Also add individual component paths
        core_path = src_path / "core"
        if core_path.exists():
            sys.path.insert(0, str(core_path))
            print(f"Added core path: {core_path}")
    else:
        print(f"WARNING: src directory not found at {src_path}")
        # Try current directory
        sys.path.insert(0, str(current_dir))
        print(f"Using current directory: {current_dir}")

    # Set up environment variables for Qt
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

    print("Environment setup complete")


def check_dependencies():
    """Check if all required dependencies are available"""
    print("Checking dependencies...")

    missing_deps = []

    try:
        from PyQt6.QtCore import QObject
        print("✓ PyQt6 available")
    except ImportError as e:
        print(f"✗ PyQt6 not available: {e}")
        missing_deps.append("PyQt6")

    try:
        import vtk
        print("✓ VTK available")
    except ImportError as e:
        print(f"✗ VTK not available: {e}")
        missing_deps.append("vtk")

    try:
        import SimpleITK
        print("✓ SimpleITK available")
    except ImportError as e:
        print(f"✗ SimpleITK not available: {e}")
        missing_deps.append("SimpleITK")

    try:
        import numpy
        print("✓ NumPy available")
    except ImportError as e:
        print(f"✗ NumPy not available: {e}")
        missing_deps.append("numpy")

    if missing_deps:
        print(f"\nMissing dependencies: {missing_deps}")
        print("Please install them with:")
        print("pip install " + " ".join(missing_deps))
        return False

    print("All dependencies available!")
    return True


def test_imports():
    """Test importing our modules"""
    print("Testing module imports...")

    try:
        from medical_logger import MedicalLogger
        print("✓ MedicalLogger imported")
    except ImportError as e:
        print(f"✗ Failed to import MedicalLogger: {e}")
        return False

    try:
        from image_processor import ImageProcessor
        print("✓ ImageProcessor imported")
    except ImportError as e:
        print(f"✗ Failed to import ImageProcessor: {e}")
        return False

    try:
        from vtk_renderer import VTKRenderer
        print("✓ VTKRenderer imported")
    except ImportError as e:
        print(f"✗ Failed to import VTKRenderer: {e}")
        return False

    try:
        from main_application import MedicalImageViewerApp
        print("✓ MedicalImageViewerApp imported")
    except ImportError as e:
        print(f"✗ Failed to import MedicalImageViewerApp: {e}")
        return False

    print("All modules imported successfully!")
    return True


def find_qml_file():
    """Find the QML file"""
    current_dir = Path(__file__).parent

    # Possible locations for QML file
    qml_locations = [
        current_dir / "src" / "ui" / "MedicalViewer.qml",
        current_dir / "src" / "MedicalViewer.qml",
        current_dir / "ui" / "MedicalViewer.qml",
        current_dir / "MedicalViewer.qml",
    ]

    for qml_path in qml_locations:
        print(f"Looking for QML at: {qml_path}")
        if qml_path.exists():
            print(f"✓ Found QML file at: {qml_path}")
            return qml_path

    print("✗ QML file not found in any expected location")
    return None


def main():
    """Main entry point with comprehensive error handling"""
    print("=== Medical Image Viewer Starting ===")

    try:
        # Setup environment
        setup_environment()

        # Check dependencies
        if not check_dependencies():
            print("Cannot start application due to missing dependencies")
            input("Press Enter to exit...")
            sys.exit(1)

        # Test imports
        if not test_imports():
            print("Cannot start application due to import errors")
            input("Press Enter to exit...")
            sys.exit(1)

        # Find QML file
        qml_file = find_qml_file()
        if not qml_file:
            print("Cannot start application: QML file not found")
            input("Press Enter to exit...")
            sys.exit(1)

        # Import and run the application
        print("Starting application...")
        from main_application import main as app_main
        app_main()

    except ImportError as e:
        print(f"Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("pip install PyQt6 vtk SimpleITK numpy")
        input("Press Enter to exit...")
        sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()