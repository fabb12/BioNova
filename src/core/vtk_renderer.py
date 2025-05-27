#!/usr/bin/env python3
"""
VTK Renderer Component - Medical Image Visualization
Handles 2D/3D rendering of medical images using VTK
"""

import traceback
from typing import Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal

try:
    import vtk
    from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    print("Warning: VTK not available. Rendering functionality will be limited.")

from core.medical_logger import MedicalLogger


class VTKRenderer(QObject):
    """
    VTK-based renderer for medical images
    Supports 2D image display, 3D volume rendering, and STL model display
    """

    # Signals for communication
    renderingComplete = pyqtSignal(str)  # rendering_type
    errorOccurred = pyqtSignal(str)  # error_message
    coordinatesChanged = pyqtSignal(float, float, float)  # x, y, z
    pixelValueChanged = pyqtSignal(float)  # pixel_value

    def __init__(self, logger: Optional[MedicalLogger] = None):
        """
        Initialize the VTK renderer

        Args:
            logger: Medical logger instance
        """
        super().__init__()

        self.logger = logger or MedicalLogger()

        if not VTK_AVAILABLE:
            self.logger.log_error("VTK_INIT", "VTK not available")
            return

        # VTK components
        self.render_window = None
        self.renderer = None
        self.interactor = None
        self.current_style = None

        # Display state
        self.current_vtk_image = None
        self.current_polydata = None
        self.current_display_mode = None  # '2D', '3D_VOLUME', 'STL'

        # 2D display components
        self.image_actor = None
        self.window_level = None

        # 3D display components
        self.volume_mapper = None
        self.volume = None
        self.color_func = None
        self.opacity_func = None

        # STL display components
        self.stl_mapper = None
        self.stl_actor = None

        self.logger.log_system_event("VTK_RENDERER_INIT", "VTK renderer initialized")

    def initialize_render_window(self, parent_widget=None) -> bool:
        """
        Initialize VTK render window

        Args:
            parent_widget: Parent widget for the render window

        Returns:
            True if successful, False otherwise
        """
        if not VTK_AVAILABLE:
            return False

        try:
            # Create render window
            self.render_window = vtk.vtkRenderWindow()

            # Create renderer
            self.renderer = vtk.vtkRenderer()
            self.renderer.SetBackground(0.1, 0.1, 0.1)  # Dark gray background
            self.render_window.AddRenderer(self.renderer)

            # Create interactor if parent widget provided
            if parent_widget:
                self.interactor = QVTKRenderWindowInteractor(parent_widget)
                self.interactor.SetRenderWindow(self.render_window)
            else:
                self.interactor = vtk.vtkRenderWindowInteractor()
                self.interactor.SetRenderWindow(self.render_window)

            # Set default interactor style
            self.current_style = vtk.vtkInteractorStyleImage()
            self.interactor.SetInteractorStyle(self.current_style)

            self.logger.log_system_event("VTK_INIT_SUCCESS", "VTK render window initialized successfully")
            return True

        except Exception as e:
            error_msg = f"Failed to initialize VTK render window: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.log_error("VTK_INIT", error_msg, stack_trace)
            self.errorOccurred.emit(error_msg)
            return False

    def display_2d_image(self, vtk_image, window: float = None, level: float = None) -> bool:
        """
        Display 2D medical image with window/level adjustment

        Args:
            vtk_image: VTK ImageData object
            window: Window width for display
            level: Window level for display

        Returns:
            True if successful, False otherwise
        """
        if not VTK_AVAILABLE or not self.renderer:
            return False

        try:
            # Clear previous actors
            self.renderer.RemoveAllViewProps()

            # Store current image
            self.current_vtk_image = vtk_image
            self.current_display_mode = '2D'

            # Create image actor
            self.image_actor = vtk.vtkImageActor()

            # Set up window/level mapping
            self.window_level = vtk.vtkImageMapToWindowLevelColors()
            self.window_level.SetInputData(vtk_image)

            # Calculate default window/level if not provided
            if window is None or level is None:
                scalar_range = vtk_image.GetScalarRange()
                if window is None:
                    window = scalar_range[1] - scalar_range[0]
                if level is None:
                    level = (scalar_range[1] + scalar_range[0]) / 2

            self.window_level.SetWindow(window)
            self.window_level.SetLevel(level)
            self.window_level.Update()

            # Set up image actor
            self.image_actor.GetMapper().SetInputConnection(self.window_level.GetOutputPort())

            # Add to renderer
            self.renderer.AddActor(self.image_actor)
            self.renderer.ResetCamera()

            # Set 2D interactor style
            self.current_style = vtk.vtkInteractorStyleImage()
            self.interactor.SetInteractorStyle(self.current_style)

            # Render
            self.render_window.Render()

            # Log success
            image_info = f"2D display - Window: {window}, Level: {level}"
            self.logger.log_image_processing("2D_DISPLAY", image_info, "SUCCESS")
            self.renderingComplete.emit("2D")

            return True

        except Exception as e:
            error_msg = f"Failed to display 2D image: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.log_error("2D_DISPLAY", error_msg, stack_trace)
            self.errorOccurred.emit(error_msg)
            return False

    def display_3d_volume(self, vtk_image, preset: str = "default") -> bool:
        """
        Display 3D volume rendering

        Args:
            vtk_image: VTK ImageData object
            preset: Transfer function preset ('default', 'ct_bone', 'ct_soft_tissue')

        Returns:
            True if successful, False otherwise
        """
        if not VTK_AVAILABLE or not self.renderer:
            return False

        try:
            # Clear previous actors
            self.renderer.RemoveAllViewProps()

            # Store current image
            self.current_vtk_image = vtk_image
            self.current_display_mode = '3D_VOLUME'

            # Create volume mapper
            self.volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
            self.volume_mapper.SetInputData(vtk_image)

            # Create transfer functions
            self.color_func = vtk.vtkColorTransferFunction()
            self.opacity_func = vtk.vtkPiecewiseFunction()

            # Set up transfer functions based on preset
            self._setup_transfer_functions(vtk_image, preset)

            # Create volume property
            volume_property = vtk.vtkVolumeProperty()
            volume_property.SetColor(self.color_func)
            volume_property.SetScalarOpacity(self.opacity_func)
            volume_property.ShadeOn()
            volume_property.SetInterpolationTypeToLinear()
            volume_property.SetAmbient(0.1)
            volume_property.SetDiffuse(0.7)
            volume_property.SetSpecular(0.2)

            # Create volume actor
            self.volume = vtk.vtkVolume()
            self.volume.SetMapper(self.volume_mapper)
            self.volume.SetProperty(volume_property)

            # Add to renderer
            self.renderer.AddViewProp(self.volume)
            self.renderer.ResetCamera()

            # Set 3D interactor style
            self.current_style = vtk.vtkInteractorStyleTrackballCamera()
            self.interactor.SetInteractorStyle(self.current_style)

            # Render
            self.render_window.Render()

            # Log success
            volume_info = f"3D volume rendering - Preset: {preset}"
            self.logger.log_image_processing("3D_VOLUME_DISPLAY", volume_info, "SUCCESS")
            self.renderingComplete.emit("3D_VOLUME")

            return True

        except Exception as e:
            error_msg = f"Failed to display 3D volume: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.log_error("3D_VOLUME_DISPLAY", error_msg, stack_trace)
            self.errorOccurred.emit(error_msg)
            return False

    def display_stl_model(self, polydata, color: Tuple[float, float, float] = (0.8, 0.8, 0.9)) -> bool:
        """
        Display STL 3D model

        Args:
            polydata: VTK PolyData object
            color: RGB color tuple for the model

        Returns:
            True if successful, False otherwise
        """
        if not VTK_AVAILABLE or not self.renderer:
            return False

        try:
            # Clear previous actors
            self.renderer.RemoveAllViewProps()

            # Store current polydata
            self.current_polydata = polydata
            self.current_display_mode = 'STL'

            # Create mapper
            self.stl_mapper = vtk.vtkPolyDataMapper()
            self.stl_mapper.SetInputData(polydata)

            # Create actor
            self.stl_actor = vtk.vtkActor()
            self.stl_actor.SetMapper(self.stl_mapper)

            # Set material properties
            property = self.stl_actor.GetProperty()
            property.SetColor(color)
            property.SetSpecular(0.5)
            property.SetSpecularPower(20)
            property.SetDiffuse(0.8)
            property.SetAmbient(0.2)

            # Add to renderer
            self.renderer.AddActor(self.stl_actor)
            self.renderer.ResetCamera()

            # Set 3D interactor style
            self.current_style = vtk.vtkInteractorStyleTrackballCamera()
            self.interactor.SetInteractorStyle(self.current_style)

            # Render
            self.render_window.Render()

            # Log success
            model_info = f"STL model - Points: {polydata.GetNumberOfPoints()}, Color: {color}"
            self.logger.log_image_processing("STL_DISPLAY", model_info, "SUCCESS")
            self.renderingComplete.emit("STL")

            return True

        except Exception as e:
            error_msg = f"Failed to display STL model: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.log_error("STL_DISPLAY", error_msg, stack_trace)
            self.errorOccurred.emit(error_msg)
            return False

    def update_window_level(self, window: float, level: float) -> bool:
        """
        Update window/level for 2D image display

        Args:
            window: Window width
            level: Window level

        Returns:
            True if successful, False otherwise
        """
        if not self.window_level or self.current_display_mode != '2D':
            return False

        try:
            self.window_level.SetWindow(window)
            self.window_level.SetLevel(level)
            self.render_window.Render()

            # Log update
            wl_info = f"Window: {window}, Level: {level}"
            self.logger.log_image_processing("WINDOW_LEVEL_UPDATE", wl_info, "SUCCESS")

            return True

        except Exception as e:
            error_msg = f"Failed to update window/level: {str(e)}"
            self.logger.log_error("WINDOW_LEVEL_UPDATE", error_msg)
            return False

    def update_3d_transfer_function(self, preset: str) -> bool:
        """
        Update 3D volume transfer function

        Args:
            preset: Transfer function preset

        Returns:
            True if successful, False otherwise
        """
        if not self.current_vtk_image or self.current_display_mode != '3D_VOLUME':
            return False

        try:
            self._setup_transfer_functions(self.current_vtk_image, preset)
            self.render_window.Render()

            # Log update
            self.logger.log_image_processing("TRANSFER_FUNCTION_UPDATE", f"Preset: {preset}", "SUCCESS")

            return True

        except Exception as e:
            error_msg = f"Failed to update transfer function: {str(e)}"
            self.logger.log_error("TRANSFER_FUNCTION_UPDATE", error_msg)
            return False

    def _setup_transfer_functions(self, vtk_image, preset: str):
        """Set up color and opacity transfer functions for volume rendering"""
        scalar_range = vtk_image.GetScalarRange()
        min_val, max_val = scalar_range[0], scalar_range[1]

        # Clear existing functions
        self.color_func.RemoveAllPoints()
        self.opacity_func.RemoveAllPoints()

        if preset == "ct_bone":
            # CT Bone preset
            self.color_func.AddRGBPoint(min_val, 0.0, 0.0, 0.0)
            self.color_func.AddRGBPoint(min_val + (max_val - min_val) * 0.2, 0.2, 0.1, 0.05)
            self.color_func.AddRGBPoint(min_val + (max_val - min_val) * 0.5, 0.8, 0.7, 0.6)
            self.color_func.AddRGBPoint(max_val, 1.0, 1.0, 1.0)

            self.opacity_func.AddPoint(min_val, 0.0)
            self.opacity_func.AddPoint(min_val + (max_val - min_val) * 0.1, 0.0)
            self.opacity_func.AddPoint(min_val + (max_val - min_val) * 0.4, 0.5)
            self.opacity_func.AddPoint(max_val, 1.0)

        elif preset == "ct_soft_tissue":
            # CT Soft Tissue preset
            self.color_func.AddRGBPoint(min_val, 0.0, 0.0, 0.0)
            self.color_func.AddRGBPoint(min_val + (max_val - min_val) * 0.3, 0.8, 0.4, 0.2)
            self.color_func.AddRGBPoint(min_val + (max_val - min_val) * 0.7, 1.0, 0.8, 0.6)
            self.color_func.AddRGBPoint(max_val, 1.0, 1.0, 1.0)

            self.opacity_func.AddPoint(min_val, 0.0)
            self.opacity_func.AddPoint(min_val + (max_val - min_val) * 0.2, 0.1)
            self.opacity_func.AddPoint(min_val + (max_val - min_val) * 0.5, 0.4)
            self.opacity_func.AddPoint(max_val, 0.8)

        else:  # default
            # Default preset
            self.color_func.AddRGBPoint(min_val, 0.0, 0.0, 0.0)
            self.color_func.AddRGBPoint(min_val + (max_val - min_val) * 0.3, 0.5, 0.2, 0.1)
            self.color_func.AddRGBPoint(min_val + (max_val - min_val) * 0.6, 1.0, 0.7, 0.6)
            self.color_func.AddRGBPoint(max_val, 1.0, 1.0, 1.0)

            self.opacity_func.AddPoint(min_val, 0.0)
            self.opacity_func.AddPoint(min_val + (max_val - min_val) * 0.1, 0.0)
            self.opacity_func.AddPoint(min_val + (max_val - min_val) * 0.3, 0.3)
            self.opacity_func.AddPoint(max_val, 1.0)

    def get_display_bounds(self) -> Optional[Tuple[float, float, float, float, float, float]]:
        """
        Get bounds of currently displayed data

        Returns:
            Tuple of (xmin, xmax, ymin, ymax, zmin, zmax) or None
        """
        if self.current_display_mode == '2D' and self.image_actor:
            return self.image_actor.GetBounds()
        elif self.current_display_mode == '3D_VOLUME' and self.volume:
            return self.volume.GetBounds()
        elif self.current_display_mode == 'STL' and self.stl_actor:
            return self.stl_actor.GetBounds()
        return None

    def reset_camera(self):
        """Reset camera to fit all visible actors"""
        if self.renderer:
            self.renderer.ResetCamera()
            self.render_window.Render()

    def get_render_window(self):
        """Get the VTK render window"""
        return self.render_window

    def get_interactor(self):
        """Get the VTK interactor"""
        return self.interactor

    def clear_display(self):
        """Clear all displayed content"""
        if self.renderer:
            self.renderer.RemoveAllViewProps()
            self.render_window.Render()

        # Reset state
        self.current_vtk_image = None
        self.current_polydata = None
        self.current_display_mode = None

        self.logger.log_system_event("DISPLAY_CLEARED", "Cleared VTK display")