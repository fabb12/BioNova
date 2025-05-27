#!/usr/bin/env python3
"""
Medical Image Processor Component - IEC 62304 Compliant
Handles loading and processing of medical images (DICOM, STL)
"""

import os
import traceback
from pathlib import Path
from typing import Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np

try:
    import SimpleITK as sitk
    SIMPLEITK_AVAILABLE = True
except ImportError:
    SIMPLEITK_AVAILABLE = False
    print("Warning: SimpleITK not available. DICOM functionality will be limited.")

try:
    import vtk
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    print("Warning: VTK not available. 3D functionality will be limited.")

from core.medical_logger  import MedicalLogger


class ImageProcessor(QObject):
    """
    Medical image processing component that handles loading and conversion
    of medical images according to IEC 62304 requirements
    """
    
    # Signals for communication with UI
    imageLoaded = pyqtSignal(str, str)  # image_type, image_info
    errorOccurred = pyqtSignal(str)     # error_message
    progressUpdate = pyqtSignal(int)    # progress_percentage
    
    def __init__(self, logger: Optional[MedicalLogger] = None):
        """
        Initialize the image processor
        
        Args:
            logger: Medical logger instance for audit trail
        """
        super().__init__()
        
        self.logger = logger or MedicalLogger()
        
        # Current loaded data
        self.current_sitk_image = None
        self.current_vtk_image = None
        self.current_polydata = None
        
        # Image metadata
        self.image_metadata = {}
        
        self.logger.log_system_event("IMAGE_PROCESSOR_INIT", "Image processor initialized")
    
    def load_dicom_series(self, directory: str) -> Optional[object]:
        """
        Load DICOM series from directory using SimpleITK
        
        Args:
            directory: Path to directory containing DICOM files
            
        Returns:
            SimpleITK Image object or None if failed
        """
        if not SIMPLEITK_AVAILABLE:
            error_msg = "SimpleITK not available. Cannot load DICOM files."
            self.logger.log_error("DICOM_LOAD", error_msg)
            self.errorOccurred.emit(error_msg)
            return None
        
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                error_msg = f"Directory does not exist: {directory}"
                self.logger.log_error("DICOM_LOAD", error_msg)
                self.errorOccurred.emit(error_msg)
                return None
            
            self.logger.log_file_operation("DICOM_LOAD_START", directory)
            
            # Get DICOM series UIDs
            series_reader = sitk.ImageSeriesReader()
            series_ids = series_reader.GetGDCMSeriesIDs(directory)
            
            if not series_ids:
                error_msg = f"No DICOM series found in directory: {directory}"
                self.logger.log_error("DICOM_LOAD", error_msg)
                self.errorOccurred.emit(error_msg)
                return None
            
            # Use the first series (in a production system, you might want to let user choose)
            series_id = series_ids[0]
            dicom_names = series_reader.GetGDCMSeriesFileNames(directory, series_id)
            
            if not dicom_names:
                error_msg = f"No DICOM files found for series: {series_id}"
                self.logger.log_error("DICOM_LOAD", error_msg)
                self.errorOccurred.emit(error_msg)
                return None
            
            # Load the series
            series_reader.SetFileNames(dicom_names)
            
            # Read the image
            image = series_reader.Execute()
            
            # Store the image
            self.current_sitk_image = image
            
            # Extract metadata
            self._extract_dicom_metadata(image, len(dicom_names))
            
            # Log successful load
            image_info = f"Size: {image.GetSize()}, Spacing: {image.GetSpacing()}, Files: {len(dicom_names)}"
            self.logger.log_file_operation("DICOM_LOAD_SUCCESS", directory, "SUCCESS")
            self.logger.log_image_processing("DICOM_LOADED", image_info, "SUCCESS")
            
            # Emit signal
            self.imageLoaded.emit("DICOM", image_info)
            
            return image
            
        except Exception as e:
            error_msg = f"Failed to load DICOM series: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.log_error("DICOM_LOAD", error_msg, stack_trace)
            self.errorOccurred.emit(error_msg)
            return None
    
    def load_stl_file(self, filepath: str) -> Optional[object]:
        """
        Load STL file using VTK
        
        Args:
            filepath: Path to STL file
            
        Returns:
            VTK PolyData object or None if failed
        """
        if not VTK_AVAILABLE:
            error_msg = "VTK not available. Cannot load STL files."
            self.logger.log_error("STL_LOAD", error_msg)
            self.errorOccurred.emit(error_msg)
            return None
        
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                error_msg = f"STL file does not exist: {filepath}"
                self.logger.log_error("STL_LOAD", error_msg)
                self.errorOccurred.emit(error_msg)
                return None
            
            self.logger.log_file_operation("STL_LOAD_START", filepath)
            
            # Create STL reader
            reader = vtk.vtkSTLReader()
            reader.SetFileName(filepath)
            reader.Update()
            
            # Get the polydata
            polydata = reader.GetOutput()
            
            if not polydata or polydata.GetNumberOfPoints() == 0:
                error_msg = f"Invalid or empty STL file: {filepath}"
                self.logger.log_error("STL_LOAD", error_msg)
                self.errorOccurred.emit(error_msg)
                return None
            
            # Store the polydata
            self.current_polydata = polydata
            
            # Extract metadata
            self._extract_stl_metadata(polydata, filepath)
            
            # Log successful load
            model_info = f"Points: {polydata.GetNumberOfPoints()}, Cells: {polydata.GetNumberOfCells()}"
            self.logger.log_file_operation("STL_LOAD_SUCCESS", filepath, "SUCCESS")
            self.logger.log_image_processing("STL_LOADED", model_info, "SUCCESS")
            
            # Emit signal
            self.imageLoaded.emit("STL", model_info)
            
            return polydata
            
        except Exception as e:
            error_msg = f"Failed to load STL file: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.log_error("STL_LOAD", error_msg, stack_trace)
            self.errorOccurred.emit(error_msg)
            return None
    
    def convert_sitk_to_vtk(self, sitk_image) -> Optional[object]:
        """
        Convert SimpleITK image to VTK image data
        
        Args:
            sitk_image: SimpleITK Image object
            
        Returns:
            VTK ImageData object or None if failed
        """
        if not VTK_AVAILABLE or not SIMPLEITK_AVAILABLE:
            error_msg = "VTK or SimpleITK not available for conversion"
            self.logger.log_error("IMAGE_CONVERSION", error_msg)
            self.errorOccurred.emit(error_msg)
            return None
        
        try:
            # Get image properties
            size = sitk_image.GetSize()
            spacing = sitk_image.GetSpacing()
            origin = sitk_image.GetOrigin()
            direction = sitk_image.GetDirection()
            
            # Convert to numpy array
            np_array = sitk.GetArrayFromImage(sitk_image)
            
            # Convert to VTK
            vtk_image = vtk.vtkImageData()
            vtk_image.SetDimensions(size)
            vtk_image.SetSpacing(spacing)
            vtk_image.SetOrigin(origin)
            
            # Convert numpy array to VTK array
            vtk_array = vtk.util.numpy_support.numpy_to_vtk(
                np_array.ravel(),
                deep=True,
                array_type=vtk.VTK_FLOAT
            )
            vtk_image.GetPointData().SetScalars(vtk_array)
            
            # Store the VTK image
            self.current_vtk_image = vtk_image
            
            conversion_info = f"Converted SITK to VTK: {size}"
            self.logger.log_image_processing("SITK_TO_VTK_CONVERSION", conversion_info, "SUCCESS")
            
            return vtk_image
            
        except Exception as e:
            error_msg = f"Failed to convert SimpleITK to VTK: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.log_error("IMAGE_CONVERSION", error_msg, stack_trace)
            self.errorOccurred.emit(error_msg)
            return None
    
    def get_image_statistics(self) -> dict:
        """
        Get statistics for the currently loaded image
        
        Returns:
            Dictionary containing image statistics
        """
        stats = {}
        
        if self.current_sitk_image:
            try:
                stats_filter = sitk.StatisticsImageFilter()
                stats_filter.Execute(self.current_sitk_image)
                
                stats.update({
                    'mean': stats_filter.GetMean(),
                    'std': stats_filter.GetSigma(),
                    'min': stats_filter.GetMinimum(),
                    'max': stats_filter.GetMaximum(),
                    'sum': stats_filter.GetSum(),
                    'count': stats_filter.GetCount()
                })
                
                self.logger.log_image_processing("IMAGE_STATISTICS", f"Calculated statistics: {stats}", "SUCCESS")
                
            except Exception as e:
                error_msg = f"Failed to calculate image statistics: {str(e)}"
                self.logger.log_error("IMAGE_STATISTICS", error_msg)
        
        return stats
    
    def _extract_dicom_metadata(self, image, num_files: int):
        """Extract metadata from DICOM image"""
        try:
            metadata = {
                'image_type': 'DICOM',
                'size': image.GetSize(),
                'spacing': image.GetSpacing(),
                'origin': image.GetOrigin(),
                'direction': image.GetDirection(),
                'pixel_type': str(image.GetPixelIDTypeAsString()),
                'number_of_components': image.GetNumberOfComponentsPerPixel(),
                'num_files': num_files
            }
            
            # Try to get DICOM tags
            try:
                for key in image.GetMetaDataKeys():
                    metadata[key] = image.GetMetaData(key)
            except:
                pass  # Some images might not have metadata
            
            self.image_metadata = metadata
            
        except Exception as e:
            self.logger.log_error("METADATA_EXTRACTION", f"Failed to extract DICOM metadata: {str(e)}")
    
    def _extract_stl_metadata(self, polydata, filepath: str):
        """Extract metadata from STL polydata"""
        try:
            bounds = polydata.GetBounds()
            
            metadata = {
                'image_type': 'STL',
                'filepath': filepath,
                'num_points': polydata.GetNumberOfPoints(),
                'num_cells': polydata.GetNumberOfCells(),
                'bounds': bounds,
                'file_size': Path(filepath).stat().st_size
            }
            
            self.image_metadata = metadata
            
        except Exception as e:
            self.logger.log_error("METADATA_EXTRACTION", f"Failed to extract STL metadata: {str(e)}")
    
    def get_metadata(self) -> dict:
        """
        Get metadata for the currently loaded image
        
        Returns:
            Dictionary containing image metadata
        """
        return self.image_metadata.copy()
    
    def validate_dicom_integrity(self, directory: str) -> Tuple[bool, str]:
        """
        Validate DICOM series integrity
        
        Args:
            directory: Directory containing DICOM files
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not SIMPLEITK_AVAILABLE:
                return False, "SimpleITK not available for validation"
            
            series_reader = sitk.ImageSeriesReader()
            series_ids = series_reader.GetGDCMSeriesIDs(directory)
            
            if not series_ids:
                return False, "No DICOM series found"
            
            # Check each series
            for series_id in series_ids:
                dicom_names = series_reader.GetGDCMSeriesFileNames(directory, series_id)
                if not dicom_names:
                    return False, f"No files found for series {series_id}"
            
            self.logger.log_image_processing("DICOM_VALIDATION", f"Validated {len(series_ids)} series", "SUCCESS")
            return True, "DICOM series validation successful"
            
        except Exception as e:
            error_msg = f"DICOM validation failed: {str(e)}"
            self.logger.log_error("DICOM_VALIDATION", error_msg)
            return False, error_msg
    
    def clear_current_data(self):
        """Clear currently loaded data"""
        self.current_sitk_image = None
        self.current_vtk_image = None
        self.current_polydata = None
        self.image_metadata = {}
        
        self.logger.log_system_event("DATA_CLEARED", "Cleared current image data")