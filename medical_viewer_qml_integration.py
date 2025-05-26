#!/usr/bin/env python3
"""
Medical Image Viewer - QML Integration
Bridges Python/VTK backend with QML frontend
"""

import sys
import os
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl, QTimer
from PyQt5.QtGui import QGuiApplication, QSurfaceFormat
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.QtQuick import QQuickWindow
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

# Import our main modules
from medical_image_viewer import ImageProcessor, VTKWidget, MedicalLogger


class Backend(QObject):
    """Backend bridge between QML and Python/VTK"""
    
    # Signals to QML
    imageLoaded = pyqtSignal(str, arguments=['imageType'])
    errorOccurred = pyqtSignal(str, arguments=['message'])
    statusUpdate = pyqtSignal(str, arguments=['message'])
    coordinatesUpdate = pyqtSignal(str, arguments=['coords'])
    pixelValueUpdate = pyqtSignal(str, arguments=['value'])
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.logger = MedicalLogger()
        self.processor = ImageProcessor(self.logger)
        self.vtk_widget = None
        self.render_window = None
        
        # Connect processor signals
        self.processor.imageLoaded.connect(self.imageLoaded)
        self.processor.errorOccurred.connect(self.errorOccurred)
        
        # Current state
        self.current_vtk_image = None
        self.current_polydata = None
        self.current_image_type = None
        
    def set_vtk_render_window(self, window_id):
        """Set up VTK rendering in QML window"""
        try:
            # Create VTK render window
            self.render_window = vtk.vtkRenderWindow()
            self.render_window.SetWindowInfo(str(window_id))
            
            # Create renderer
            self.renderer = vtk.vtkRenderer()
            self.renderer.SetBackground(0.1, 0.1, 0.1)
            self.render_window.AddRenderer(self.renderer)
            
            # Create interactor
            self.interactor = vtk.vtkRenderWindowInteractor()
            self.interactor.SetRenderWindow(self.render_window)
            
            # Set interactor style
            self.style = vtk.vtkInteractorStyleImage()
            self.interactor.SetInteractorStyle(self.style)
            
            self.logger.log_event("VTK_INIT", "VTK render window initialized")
            
        except Exception as e:
            self.logger.log_event("VTK_INIT", f"Failed to initialize VTK: {str(e)}", "ERROR")
            self.errorOccurred.emit(f"Failed to initialize rendering: {str(e)}")
    
    @pyqtSlot(str)
    def loadDicomSeries(self, directory_url):
        """Load DICOM series from directory"""
        try:
            # Convert QUrl to path
            directory = QUrl(directory_url).toLocalFile()
            self.statusUpdate.emit("Loading DICOM series...")
            
            image = self.processor.load_dicom_series(directory)
            if image:
                self.current_vtk_image = self.processor.convert_sitk_to_vtk(image)
                self.current_image_type = "DICOM"
                
                if self.current_vtk_image:
                    self.display_2d_image()
                    self.statusUpdate.emit("DICOM series loaded successfully")
                    
        except Exception as e:
            self.errorOccurred.emit(str(e))
    
    @pyqtSlot(str)
    def loadStlFile(self, file_url):
        """Load STL file"""
        try:
            # Convert QUrl to path
            filepath = QUrl(file_url).toLocalFile()
            self.statusUpdate.emit("Loading STL file...")
            
            polydata = self.processor.load_stl_file(filepath)
            if polydata:
                self.current_polydata = polydata
                self.current_image_type = "STL"
                self.display_stl_model()
                self.statusUpdate.emit("STL file loaded successfully")
                
        except Exception as e:
            self.errorOccurred.emit(str(e))
    
    @pyqtSlot()
    def switchTo2DView(self):
        """Switch to 2D view"""
        if self.current_vtk_image and self.current_image_type == "DICOM":
            self.display_2d_image()
            self.statusUpdate.emit("Switched to 2D view")
    
    @pyqtSlot()
    def switchTo3DView(self):
        """Switch to 3D view"""
        if self.current_vtk_image and self.current_image_type == "DICOM":
            self.display_3d_volume()
            self.statusUpdate.emit("Switched to 3D view")
    
    @pyqtSlot(float, float)
    def updateWindowLevel(self, window, level):
        """Update window/level for DICOM display"""
        if hasattr(self, 'window_level') and self.window_level:
            self.window_level.SetWindow(window)
            self.window_level.SetLevel(level)
            self.render_window.Render()
    
    def display_2d_image(self):
        """Display 2D medical image"""
        try:
            # Clear renderer
            self.renderer.RemoveAllViewProps()
            
            # Create image actor
            image_actor = vtk.vtkImageActor()
            
            # Set up window/level
            self.window_level = vtk.vtkImageMapToWindowLevelColors()
            self.window_level.SetInputData(self.current_vtk_image)
            
            # Calculate appropriate window/level
            scalar_range = self.current_vtk_image.GetScalarRange()
            window = scalar_range[1] - scalar_range[0]
            level = (scalar_range[1] + scalar_range[0]) / 2
            
            self.window_level.SetWindow(window)
            self.window_level.SetLevel(level)
            self.window_level.Update()
            
            image_actor.GetMapper().SetInputConnection(self.window_level.GetOutputPort())
            
            # Add to renderer
            self.renderer.AddActor(image_actor)
            self.renderer.ResetCamera()
            
            # Set up 2D interactor style
            self.style = vtk.vtkInteractorStyleImage()
            self.interactor.SetInteractorStyle(self.style)
            
            self.render_window.Render()
            
        except Exception as e:
            self.logger.log_event("DISPLAY", f"Failed to display 2D image: {str(e)}", "ERROR")
            self.errorOccurred.emit(f"Failed to display 2D image: {str(e)}")
    
    def display_3d_volume(self):
        """Display 3D volume rendering"""
        try:
            # Clear renderer
            self.renderer.RemoveAllViewProps()
            
            # Create volume mapper
            volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
            volume_mapper.SetInputData(self.current_vtk_image)
            
            # Create transfer functions
            color_func = vtk.vtkColorTransferFunction()
            opacity_func = vtk.vtkPiecewiseFunction()
            
            # Set up transfer functions
            scalar_range = self.current_vtk_image.GetScalarRange()
            
            color_func.AddRGBPoint(scalar_range[0], 0.0, 0.0, 0.0)
            color_func.AddRGBPoint(scalar_range[1] * 0.3, 0.5, 0.2, 0.1)
            color_func.AddRGBPoint(scalar_range[1] * 0.6, 1.0, 0.7, 0.6)
            color_func.AddRGBPoint(scalar_range[1], 1.0, 1.0, 1.0)
            
            opacity_func.AddPoint(scalar_range[0], 0.0)
            opacity_func.AddPoint(scalar_range[1] * 0.1, 0.0)
            opacity_func.AddPoint(scalar_range[1] * 0.3, 0.3)
            opacity_func.AddPoint(scalar_range[1], 1.0)
            
            # Create volume property
            volume_property = vtk.vtkVolumeProperty()
            volume_property.SetColor(color_func)
            volume_property.SetScalarOpacity(opacity_func)
            volume_property.ShadeOn()
            volume_property.SetInterpolationTypeToLinear()
            
            # Create volume actor
            volume = vtk.vtkVolume()
            volume.SetMapper(volume_mapper)
            volume.SetProperty(volume_property)
            
            # Add to renderer
            self.renderer.AddViewProp(volume)
            self.renderer.ResetCamera()
            
            # Set up 3D interactor style
            self.style = vtk.vtkInteractorStyleTrackballCamera()
            self.interactor.SetInteractorStyle(self.style)
            
            self.render_window.Render()
            
        except Exception as e:
            self.logger.log_event("DISPLAY", f"Failed to display 3D volume: {str(e)}", "ERROR")
            self.errorOccurred.emit(f"Failed to display 3D volume: {str(e)}")
    
    def display_stl_model(self):
        """Display STL 3D model"""
        try:
            # Clear renderer
            self.renderer.RemoveAllViewProps()
            
            # Create mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(self.current_polydata)
            
            # Create actor
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.8, 0.8, 0.9)
            actor.GetProperty().SetSpecular(0.5)
            actor.GetProperty().SetSpecularPower(20)
            
            # Add to renderer
            self.renderer.AddActor(actor)
            self.renderer.ResetCamera()
            
            # Set up 3D interactor style
            self.style = vtk.vtkInteractorStyleTrackballCamera()
            self.interactor.SetInteractorStyle(self.style)
            
            self.render_window.Render()
            
        except Exception as e:
            self.logger.log_event("DISPLAY", f"Failed to display STL model: {str(e)}", "ERROR")
            self.errorOccurred.emit(f"Failed to display STL model: {str(e)}")


def main():
    """Main application entry point"""
    # Set up OpenGL format
    QSurfaceFormat.setDefaultFormat(QVTKRenderWindowInteractor.defaultFormat())
    
    # Create application
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("MedicalSoftware")
    app.setOrganizationDomain("medical.software")
    app.setApplicationName("Medical Image Viewer")
    
    # Create backend
    backend = Backend()
    
    # Create QML engine
    engine = QQmlApplicationEngine()
    
    # Register backend with QML
    engine.rootContext().setContextProperty("backend", backend)
    
    # Load QML file
    qml_file = Path(__file__).parent / "MedicalViewer.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    
    # Check if loading was successful
    if not engine.rootObjects():
        sys.exit(-1)
    
    # Get the main window
    window = engine.rootObjects()[0]
    
    # Set up VTK rendering window
    # Note: In a real application, you would need to properly integrate
    # VTK with the QML scene graph. This is a simplified example.
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()