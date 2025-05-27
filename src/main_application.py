#!/usr/bin/env python3
"""
Medical Image Viewer - Main Application
IEC 62304 Compliant Medical Device Software - Class B
"""

import sys
import os
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl, QTimer
from PyQt6.QtGui import QGuiApplication, QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtQuick import QQuickWindow

# Import our components
from medical_logger import MedicalLogger
from image_processor import ImageProcessor
from vtk_renderer import VTKRenderer

try:
    import vtk
    from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False


class MedicalImageViewerApp(QObject):
    """
    Main application controller for Medical Image Viewer
    Coordinates between UI, image processing, and rendering components
    """

    # Signals to QML
    imageLoaded = pyqtSignal(str, str, arguments=['imageType', 'imageInfo'])
    errorOccurred = pyqtSignal(str, arguments=['message'])
    statusUpdate = pyqtSignal(str, arguments=['message'])
    coordinatesUpdate = pyqtSignal(str, arguments=['coords'])
    pixelValueUpdate = pyqtSignal(str, arguments=['value'])
    progressUpdate = pyqtSignal(int, arguments=['percentage'])

    def __init__(self):
        """Initialize the medical image viewer application"""
        super().__init__()

        print("Initializing MedicalImageViewerApp...")

        # Initialize core components with error handling
        try:
            print("Creating logger...")
            self.logger = MedicalLogger()
            print("✓ Logger created successfully")
        except Exception as e:
            print(f"✗ Failed to create logger: {e}")
            # Use a dummy logger for now
            self.logger = None

        try:
            print("Creating image processor...")
            self.image_processor = ImageProcessor(self.logger)
            print("✓ Image processor created successfully")
        except Exception as e:
            print(f"✗ Failed to create image processor: {e}")
            if self.logger:
                self.logger.log_error("IMAGE_PROCESSOR_INIT", str(e))
            self.image_processor = None

        try:
            print("Creating VTK renderer...")
            self.vtk_renderer = VTKRenderer(self.logger)
            print("✓ VTK renderer created successfully")
        except Exception as e:
            print(f"✗ Failed to create VTK renderer: {e}")
            if self.logger:
                self.logger.log_error("VTK_RENDERER_INIT", str(e))
            self.vtk_renderer = None

        # Application state
        self.current_image_type = None
        self.current_file_path = None
        self.is_3d_view = False

        # Connect signals
        try:
            print("Connecting signals...")
            self._connect_signals()
            print("✓ Signals connected successfully")
        except Exception as e:
            print(f"✗ Failed to connect signals: {e}")
            if self.logger:
                self.logger.log_error("SIGNAL_CONNECTION", str(e))

        # Log application startup
        try:
            if self.logger:
                self.logger.log_system_event("APPLICATION_START", "Medical Image Viewer started")
                self.logger.log_user_action("APPLICATION_LAUNCH", "User launched the application")
            print("✓ Application initialization complete")
        except Exception as e:
            print(f"⚠ Warning during startup logging: {e}")

    def _connect_signals(self):
        """Connect signals between components"""

        # Image processor signals
        if self.image_processor:
            try:
                self.image_processor.imageLoaded.connect(self._on_image_loaded)
                self.image_processor.errorOccurred.connect(self._on_error_occurred)
                self.image_processor.progressUpdate.connect(self.progressUpdate)
                print("✓ Image processor signals connected")
            except Exception as e:
                print(f"✗ Failed to connect image processor signals: {e}")

        # VTK renderer signals
        if self.vtk_renderer:
            try:
                self.vtk_renderer.renderingComplete.connect(self._on_rendering_complete)
                self.vtk_renderer.errorOccurred.connect(self._on_error_occurred)
                self.vtk_renderer.coordinatesChanged.connect(self._on_coordinates_changed)
                self.vtk_renderer.pixelValueChanged.connect(self._on_pixel_value_changed)
                print("✓ VTK renderer signals connected")
            except Exception as e:
                print(f"✗ Failed to connect VTK renderer signals: {e}")

    @pyqtSlot(str)
    def loadDicomSeries(self, directory_url: str):
        """
        Load DICOM series from directory

        Args:
            directory_url: QML file URL of the directory
        """
        try:
            # Convert QUrl to local path
            directory = QUrl(directory_url).toLocalFile()

            if not directory:
                self.errorOccurred.emit("Invalid directory path")
                return

            # Log user action
            self.logger.log_user_action("LOAD_DICOM_SERIES", f"Loading from: {directory}")
            self.statusUpdate.emit("Loading DICOM series...")

            # Validate directory first
            is_valid, error_msg = self.image_processor.validate_dicom_integrity(directory)
            if not is_valid:
                self.errorOccurred.emit(f"DICOM validation failed: {error_msg}")
                return

            # Load the series
            sitk_image = self.image_processor.load_dicom_series(directory)
            if sitk_image:
                # Convert to VTK format
                vtk_image = self.image_processor.convert_sitk_to_vtk(sitk_image)
                if vtk_image:
                    # Display in 2D mode by default
                    success = self.vtk_renderer.display_2d_image(vtk_image)
                    if success:
                        self.current_image_type = "DICOM"
                        self.current_file_path = directory
                        self.is_3d_view = False
                        self.statusUpdate.emit("DICOM series loaded successfully")
                    else:
                        self.errorOccurred.emit("Failed to display DICOM image")
                else:
                    self.errorOccurred.emit("Failed to convert DICOM to display format")
            else:
                self.errorOccurred.emit("Failed to load DICOM series")

        except Exception as e:
            error_msg = f"Unexpected error loading DICOM: {str(e)}"
            self.logger.log_error("DICOM_LOAD_UNEXPECTED", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot(str)
    def loadStlFile(self, file_url: str):
        """
        Load STL file

        Args:
            file_url: QML file URL of the STL file
        """
        try:
            # Convert QUrl to local path
            filepath = QUrl(file_url).toLocalFile()

            if not filepath:
                self.errorOccurred.emit("Invalid file path")
                return

            # Log user action
            self.logger.log_user_action("LOAD_STL_FILE", f"Loading: {filepath}")
            self.statusUpdate.emit("Loading STL file...")

            # Load the STL file
            polydata = self.image_processor.load_stl_file(filepath)
            if polydata:
                # Display the STL model
                success = self.vtk_renderer.display_stl_model(polydata)
                if success:
                    self.current_image_type = "STL"
                    self.current_file_path = filepath
                    self.is_3d_view = True  # STL is always 3D
                    self.statusUpdate.emit("STL file loaded successfully")
                else:
                    self.errorOccurred.emit("Failed to display STL model")
            else:
                self.errorOccurred.emit("Failed to load STL file")

        except Exception as e:
            error_msg = f"Unexpected error loading STL: {str(e)}"
            self.logger.log_error("STL_LOAD_UNEXPECTED", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot()
    def switchTo2DView(self):
        """Switch to 2D view mode"""
        if self.current_image_type != "DICOM":
            self.errorOccurred.emit("2D view only available for DICOM images")
            return

        try:
            # Log user action
            self.logger.log_user_action("SWITCH_2D_VIEW", "User switched to 2D view")

            # Get current VTK image
            vtk_image = self.image_processor.current_vtk_image
            if vtk_image:
                success = self.vtk_renderer.display_2d_image(vtk_image)
                if success:
                    self.is_3d_view = False
                    self.statusUpdate.emit("Switched to 2D view")
                else:
                    self.errorOccurred.emit("Failed to switch to 2D view")
            else:
                self.errorOccurred.emit("No image data available for 2D view")

        except Exception as e:
            error_msg = f"Error switching to 2D view: {str(e)}"
            self.logger.log_error("VIEW_SWITCH_2D", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot()
    def switchTo3DView(self):
        """Switch to 3D view mode"""
        if self.current_image_type != "DICOM":
            self.errorOccurred.emit("3D view only available for DICOM images")
            return

        try:
            # Log user action
            self.logger.log_user_action("SWITCH_3D_VIEW", "User switched to 3D view")

            # Get current VTK image
            vtk_image = self.image_processor.current_vtk_image
            if vtk_image:
                success = self.vtk_renderer.display_3d_volume(vtk_image)
                if success:
                    self.is_3d_view = True
                    self.statusUpdate.emit("Switched to 3D view")
                else:
                    self.errorOccurred.emit("Failed to switch to 3D view")
            else:
                self.errorOccurred.emit("No image data available for 3D view")

        except Exception as e:
            error_msg = f"Error switching to 3D view: {str(e)}"
            self.logger.log_error("VIEW_SWITCH_3D", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot(float, float)
    def updateWindowLevel(self, window: float, level: float):
        """
        Update window/level for DICOM display

        Args:
            window: Window width
            level: Window level
        """
        if self.current_image_type != "DICOM" or self.is_3d_view:
            return

        try:
            # Log user action
            self.logger.log_user_action("WINDOW_LEVEL_ADJUST", f"Window: {window}, Level: {level}")

            success = self.vtk_renderer.update_window_level(window, level)
            if not success:
                self.errorOccurred.emit("Failed to update window/level")

        except Exception as e:
            error_msg = f"Error updating window/level: {str(e)}"
            self.logger.log_error("WINDOW_LEVEL_UPDATE", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot(str)
    def update3DPreset(self, preset: str):
        """
        Update 3D volume rendering preset

        Args:
            preset: Transfer function preset name
        """
        if self.current_image_type != "DICOM" or not self.is_3d_view:
            return

        try:
            # Log user action
            self.logger.log_user_action("3D_PRESET_CHANGE", f"Preset: {preset}")

            success = self.vtk_renderer.update_3d_transfer_function(preset)
            if success:
                self.statusUpdate.emit(f"Applied 3D preset: {preset}")
            else:
                self.errorOccurred.emit("Failed to update 3D preset")

        except Exception as e:
            error_msg = f"Error updating 3D preset: {str(e)}"
            self.logger.log_error("3D_PRESET_UPDATE", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot()
    def resetCamera(self):
        """Reset camera view"""
        try:
            self.logger.log_user_action("RESET_CAMERA", "User reset camera view")
            self.vtk_renderer.reset_camera()
            self.statusUpdate.emit("Camera view reset")

        except Exception as e:
            error_msg = f"Error resetting camera: {str(e)}"
            self.logger.log_error("CAMERA_RESET", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot()
    def clearDisplay(self):
        """Clear current display"""
        try:
            self.logger.log_user_action("CLEAR_DISPLAY", "User cleared display")

            # Clear renderer
            self.vtk_renderer.clear_display()

            # Clear processor data
            self.image_processor.clear_current_data()

            # Reset state
            self.current_image_type = None
            self.current_file_path = None
            self.is_3d_view = False

            self.statusUpdate.emit("Display cleared")

        except Exception as e:
            error_msg = f"Error clearing display: {str(e)}"
            self.logger.log_error("CLEAR_DISPLAY", error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot(result=str)
    def getImageMetadata(self) -> str:
        """
        Get metadata for current image

        Returns:
            JSON string containing image metadata
        """
        try:
            metadata = self.image_processor.get_metadata()

            # Convert to string representation for QML
            metadata_str = "Image Metadata:\n"
            for key, value in metadata.items():
                metadata_str += f"{key}: {value}\n"

            return metadata_str

        except Exception as e:
            error_msg = f"Error getting metadata: {str(e)}"
            self.logger.log_error("METADATA_GET", error_msg)
            return f"Error: {error_msg}"

    @pyqtSlot(result=str)
    def getImageStatistics(self) -> str:
        """
        Get statistics for current image

        Returns:
            String containing image statistics
        """
        try:
            stats = self.image_processor.get_image_statistics()

            if not stats:
                return "No statistics available"

            # Convert to string representation for QML
            stats_str = "Image Statistics:\n"
            for key, value in stats.items():
                if isinstance(value, float):
                    stats_str += f"{key}: {value:.2f}\n"
                else:
                    stats_str += f"{key}: {value}\n"

            return stats_str

        except Exception as e:
            error_msg = f"Error getting statistics: {str(e)}"
            self.logger.log_error("STATISTICS_GET", error_msg)
            return f"Error: {error_msg}"

    def _on_image_loaded(self, image_type: str, image_info: str):
        """Handle image loaded signal"""
        self.imageLoaded.emit(image_type, image_info)

    def _on_error_occurred(self, error_message: str):
        """Handle error signal"""
        self.errorOccurred.emit(error_message)

    def _on_rendering_complete(self, rendering_type: str):
        """Handle rendering complete signal"""
        self.statusUpdate.emit(f"{rendering_type} rendering complete")

    def _on_coordinates_changed(self, x: float, y: float, z: float):
        """Handle coordinate change signal"""
        coords_str = f"X: {x:.1f}, Y: {y:.1f}, Z: {z:.1f}"
        self.coordinatesUpdate.emit(coords_str)

    def _on_pixel_value_changed(self, pixel_value: float):
        """Handle pixel value change signal"""
        value_str = f"{pixel_value:.2f}"
        self.pixelValueUpdate.emit(value_str)

    def initialize_vtk_widget(self, parent_widget=None):
        """Initialize VTK rendering widget"""
        return self.vtk_renderer.initialize_render_window(parent_widget)

    def get_vtk_render_window(self):
        """Get VTK render window for QML integration"""
        return self.vtk_renderer.get_render_window()

    def get_vtk_interactor(self):
        """Get VTK interactor for QML integration"""
        return self.vtk_renderer.get_interactor()

    def shutdown(self):
        """Shutdown the application gracefully"""
        try:
            self.logger.log_user_action("APPLICATION_SHUTDOWN", "User closed the application")
            self.logger.log_system_event("APPLICATION_SHUTDOWN", "Medical Image Viewer shutting down")

            # Clear any loaded data
            self.image_processor.clear_current_data()
            self.vtk_renderer.clear_display()

            # Cleanup old logs (keep 1 year as per IEC 62304)
            self.logger.cleanup_old_logs(365)

        except Exception as e:
            self.logger.log_error("APPLICATION_SHUTDOWN", f"Error during shutdown: {str(e)}")


def setup_application():
    """Set up the PyQt6 application with proper OpenGL support"""

    # Set up OpenGL format for VTK
    if VTK_AVAILABLE:
        surface_format = QSurfaceFormat()
        surface_format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        surface_format.setVersion(3, 3)
        surface_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        surface_format.setDepthBufferSize(24)
        surface_format.setStencilBufferSize(8)
        surface_format.setSamples(4)  # Anti-aliasing
        QSurfaceFormat.setDefaultFormat(surface_format)

    # Create application
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("MedicalSoftware")
    app.setOrganizationDomain("medical.software")
    app.setApplicationName("Medical Image Viewer")
    app.setApplicationVersion("1.0.0")

    return app


def main():
    """Main application entry point"""

    print("Setting up PyQt6 application...")

    # Set up application
    app = setup_application()

    print("Creating application controller...")

    # Create main application controller
    try:
        medical_app = MedicalImageViewerApp()
        print("✓ Application controller created")
    except Exception as e:
        print(f"✗ Failed to create application controller: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("Setting up QML engine...")

    # Create QML engine
    engine = QQmlApplicationEngine()

    # Register the application controller with QML
    engine.rootContext().setContextProperty("backend", medical_app)
    print("✓ Backend registered with QML")

    # Find QML file
    current_dir = Path(__file__).parent
    qml_locations = [
        current_dir / "ui" / "MedicalViewer.qml",
        current_dir / "MedicalViewer.qml",
        current_dir.parent / "MedicalViewer.qml",
        current_dir.parent / "ui" / "MedicalViewer.qml",
    ]

    qml_file = None
    for location in qml_locations:
        print(f"Looking for QML at: {location}")
        if location.exists():
            qml_file = location
            print(f"✓ Found QML file: {qml_file}")
            break

    if not qml_file:
        # Create a basic QML file if not found
        print("QML file not found, creating basic interface...")
        qml_file = current_dir / "basic_interface.qml"
        create_basic_qml(qml_file)

    print(f"Loading QML file: {qml_file}")
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    # Check if QML loading was successful
    if not engine.rootObjects():
        medical_app.logger.log_error("QML_LOAD", "Failed to load QML interface")
        print("✗ Failed to load QML interface")

        # Try to show a basic Qt widget as fallback
        try:
            from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

            app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()

            window = QMainWindow()
            window.setWindowTitle("Medical Image Viewer - Basic Mode")
            window.setGeometry(100, 100, 800, 600)

            central_widget = QWidget()
            layout = QVBoxLayout()

            label = QLabel(
                "Medical Image Viewer\n\nQML interface failed to load.\nBasic mode active.\n\nPlease check console for errors.")
            label.setStyleSheet("font-size: 16px; padding: 50px; text-align: center;")

            layout.addWidget(label)
            central_widget.setLayout(layout)
            window.setCentralWidget(central_widget)

            window.show()

            print("✓ Fallback widget interface shown")

        except Exception as e:
            print(f"✗ Failed to show fallback interface: {e}")
            sys.exit(-1)
    else:
        print("✓ QML interface loaded successfully")

    # Initialize VTK rendering
    print("Initializing VTK...")
    try:
        if hasattr(medical_app, 'vtk_renderer') and medical_app.vtk_renderer:
            medical_app.initialize_vtk_widget()
            print("✓ VTK initialized")
        else:
            print("⚠ VTK renderer not available")
    except Exception as e:
        print(f"⚠ VTK initialization failed: {e}")

    # Set up graceful shutdown
    def handle_shutdown():
        print("Application shutting down...")
        medical_app.shutdown()

    app.aboutToQuit.connect(handle_shutdown)

    print("Starting application event loop...")

    # Run the application
    try:
        exit_code = app.exec()
        print(f"Application exited with code: {exit_code}")
        medical_app.logger.log_system_event("APPLICATION_EXIT", f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error in application event loop: {e}")
        medical_app.logger.log_error("APPLICATION_RUN", f"Fatal error: {str(e)}")
        sys.exit(-1)


def create_basic_qml(qml_file):
    """Create a basic QML interface if the main one is not found"""
    basic_qml_content = '''
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 1000
    height: 700
    title: qsTr("Medical Image Viewer - Basic Interface")

    Rectangle {
        anchors.fill: parent
        color: "#2d2d2d"

        Column {
            anchors.centerIn: parent
            spacing: 30

            Text {
                text: "Medical Image Viewer"
                font.pixelSize: 28
                font.bold: true
                color: "white"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "Basic Interface Loaded"
                font.pixelSize: 16
                color: "lightgray"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Row {
                spacing: 20
                anchors.horizontalCenter: parent.horizontalCenter

                Button {
                    text: "Load DICOM"
                    onClicked: {
                        console.log("DICOM button clicked")
                        backend.loadDicomSeries("file:///")
                    }
                }

                Button {
                    text: "Load STL"
                    onClicked: {
                        console.log("STL button clicked")
                        backend.loadStlFile("file:///")
                    }
                }
            }

            Text {
                id: statusText
                text: "Ready"
                color: "lightblue"
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    Connections {
        target: backend

        function onStatusUpdate(message) {
            statusText.text = message
        }

        function onErrorOccurred(message) {
            statusText.text = "Error: " + message
        }
    }
}
'''

    qml_file.parent.mkdir(parents=True, exist_ok=True)
    with open(qml_file, 'w') as f:
        f.write(basic_qml_content)

    print(f"✓ Created basic QML interface at: {qml_file}")


if __name__ == "__main__":
    main()