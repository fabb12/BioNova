# Medical Image Viewer - IEC 62304 Documentation

**Document ID**: DOC-MIV-001  
**Version**: 1.0  
**Date**: 2025-05-26  
**Status**: Released  
**Classification**: IEC 62304 Class B Medical Device Software  

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 0.1 | 2025-05-20 | Development Team | Initial draft |
| 0.5 | 2025-05-23 | Development Team | Added risk analysis |
| 1.0 | 2025-05-26 | Development Team | First release |

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared by | Development Lead | _________________ | __________ |
| Reviewed by | Quality Manager | _________________ | __________ |
| Approved by | Project Manager | _________________ | __________ |

## Table of Contents

1. [Software Development Plan (SDP)](#1-software-development-plan-sdp)
2. [Software Requirements Specification (SRS)](#2-software-requirements-specification-srs)
3. [Software Design Specification (SDS)](#3-software-design-specification-sds)
4. [Risk Analysis](#4-risk-analysis)
5. [Verification and Validation Plan](#5-verification-and-validation-plan)
6. [Installation and Deployment](#6-installation-and-deployment)
7. [Maintenance and Support](#7-maintenance-and-support)
8. [Regulatory Compliance](#8-regulatory-compliance)
9. [Version History](#9-version-history)
10. [Appendices](#10-appendices)

---

## 1. Software Development Plan (SDP)

### 1.1 Purpose
This document describes the development plan for the Medical Image Viewer software according to IEC 62304 standard for medical device software lifecycle processes.

### 1.2 Scope
- **Software Name**: Medical Image Viewer
- **Version**: 1.0.0
- **Classification**: Class B (Non-life-supporting software)
- **Intended Use**: Visualization of medical images (DICOM, STL) for diagnostic support
- **Intended Users**: Healthcare professionals, radiologists, medical technicians

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| DICOM | Digital Imaging and Communications in Medicine |
| STL | Stereolithography file format |
| VTK | Visualization Toolkit |
| ITK | Insight Segmentation and Registration Toolkit |
| SDP | Software Development Plan |
| SRS | Software Requirements Specification |
| SDS | Software Design Specification |
| V&V | Verification and Validation |

### 1.4 Development Model
The software follows an iterative development model with the following phases:
- Planning
- Requirements Analysis
- Design
- Implementation
- Testing
- Release

### 1.5 Development Team

| Role | Responsibilities |
|------|------------------|
| Project Manager | Overall project coordination, timeline management |
| Software Architect | System design, architecture decisions |
| Developer | Implementation, unit testing |
| Quality Assurance | Test planning, execution, validation |
| Regulatory Affairs | IEC 62304 compliance, documentation |

---

## 2. Software Requirements Specification (SRS)

### 2.1 Functional Requirements

| ID | Requirement | Priority | Rationale | Traceability |
|----|-------------|----------|-----------|--------------|
| REQ-001 | The system shall load and display DICOM image series from a selected directory | High | Core functionality for medical imaging | TC-001, RISK-001 |
| REQ-002 | The system shall load and display STL 3D models from selected files | High | Support for 3D anatomical models | TC-002 |
| REQ-003 | The system shall provide 2D visualization mode for DICOM images | High | Standard medical image viewing | TC-003 |
| REQ-004 | The system shall provide 3D volume rendering for DICOM series | High | Advanced visualization capability | TC-003 |
| REQ-005 | The system shall allow window/level adjustment for DICOM images | Medium | Essential for diagnostic quality | TC-004 |
| REQ-006 | The system shall log all file operations with timestamps | High | IEC 62304 traceability requirement | TC-005 |
| REQ-007 | The system shall display error messages for invalid files | High | User safety and guidance | TC-006 |
| REQ-008 | The system shall support zoom and pan operations | Medium | Basic image manipulation | TC-007 |

### 2.2 Non-Functional Requirements

| ID | Requirement | Priority | Rationale | Traceability |
|----|-------------|----------|-----------|--------------|
| NFR-001 | The system shall respond to user input within 100ms | Medium | User experience | PT-001 |
| NFR-002 | The system shall handle errors gracefully without crashing | High | Safety and reliability | TC-008 |
| NFR-003 | The system shall maintain audit logs for minimum 1 year | High | Regulatory compliance | Code Review |
| NFR-004 | The system shall support image files up to 1GB in size | Medium | Clinical dataset support | PT-002 |
| NFR-005 | The system shall run on Windows 10/11, macOS 12+, Ubuntu 20.04+ | High | Platform compatibility | IT-001 |
| NFR-006 | The system shall use no more than 4GB RAM for typical operations | Medium | Resource efficiency | PT-003 |

### 2.3 Interface Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| IFR-001 | User Interface | Graphical interface with menu bar, toolbar, and viewport |
| IFR-002 | File Interface | Support for DICOM (.dcm) and STL (.stl) file formats |
| IFR-003 | System Interface | OpenGL 3.3+ for rendering |

---

## 3. Software Design Specification (SDS)

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Medical Image Viewer                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Presentation  │    Business     │      Data Access        │
│     Layer       │     Logic       │        Layer            │
├─────────────────┼─────────────────┼─────────────────────────┤
│  ┌───────────┐  │  ┌───────────┐  │  ┌─────────────────┐  │
│  │    QML    │  │  │  Image    │  │  │  DICOM Reader   │  │
│  │    UI     │  │  │ Processor │  │  │   (SimpleITK)   │  │
│  └───────────┘  │  └───────────┘  │  └─────────────────┘  │
│  ┌───────────┐  │  ┌───────────┐  │  ┌─────────────────┐  │
│  │   PyQt5   │  │  │    VTK    │  │  │   STL Reader    │  │
│  │  Widgets  │  │  │  Render   │  │  │     (VTK)       │  │
│  └───────────┘  │  │  Engine   │  │  └─────────────────┘  │
│                 │  └───────────┘  │  ┌─────────────────┐  │
│                 │  ┌───────────┐  │  │   Logger        │  │
│                 │  │  Medical  │  │  │   (IEC 62304)   │  │
│                 │  │  Logger   │  │  └─────────────────┘  │
│                 │  └───────────┘  │                       │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 3.2 Component Specifications

#### 3.2.1 MedicalLogger Component
- **Purpose**: Provides IEC 62304 compliant logging functionality
- **Interface**:
  ```python
  class MedicalLogger:
      def __init__(self, log_dir: str = "logs")
      def log_event(self, event_type: str, message: str, severity: str = "INFO")
  ```
- **Responsibilities**:
  - Create timestamped log files
  - Categorize events by severity (INFO, WARNING, ERROR)
  - Ensure log persistence and rotation
  - Implement thread-safe logging

#### 3.2.2 ImageProcessor Component
- **Purpose**: Handle medical image loading and conversion
- **Interface**:
  ```python
  class ImageProcessor(QObject):
      def load_dicom_series(self, directory: str) -> Optional[sitk.Image]
      def load_stl_file(self, filepath: str) -> Optional[vtk.vtkPolyData]
      def convert_sitk_to_vtk(self, image: sitk.Image) -> vtk.vtkImageData
  ```
- **Responsibilities**:
  - Load DICOM series using SimpleITK
  - Load STL files using VTK readers
  - Convert between ITK and VTK image formats
  - Emit signals for successful loads and errors

#### 3.2.3 VTKWidget Component
- **Purpose**: Render medical images using VTK
- **Interface**:
  ```python
  class VTKWidget(QVTKRenderWindowInteractor):
      def display_2d_image(self, vtk_image: vtk.vtkImageData)
      def display_3d_volume(self, vtk_image: vtk.vtkImageData)
      def display_stl_model(self, polydata: vtk.vtkPolyData)
  ```
- **Responsibilities**:
  - 2D image display with window/level adjustment
  - 3D volume rendering with transfer functions
  - 3D surface rendering for STL models
  - Handle user interactions (zoom, pan, rotate)

### 3.3 Data Flow Diagram

```
User Input → UI Layer → Image Processor → File Reader
                ↓                              ↓
           Event Logger                   Image Data
                ↓                              ↓
            Log Files                    VTK Converter
                                              ↓
                                         VTK Renderer
                                              ↓
                                      Display Output
```

### 3.4 Error Handling Strategy
- All file operations wrapped in try-catch blocks
- User-friendly error messages displayed in UI
- Detailed error information logged to file
- Graceful degradation for non-critical errors

---

## 4. Risk Analysis

### 4.1 Risk Assessment Matrix

| Risk ID | Description | Probability | Severity | Risk Level | Mitigation Strategy |
|---------|-------------|-------------|----------|------------|-------------------|
| RISK-001 | Incorrect image display leading to misdiagnosis | Low | High | Medium | Validation testing, comparison with reference viewer |
| RISK-002 | Memory overflow with large DICOM series | Medium | Medium | Medium | Memory limits, progressive loading |
| RISK-003 | UI freezing during file loading | Medium | Low | Low | Asynchronous loading with progress indicator |
| RISK-004 | Logging system failure | Low | Medium | Low | Redundant logging, daily log rotation |
| RISK-005 | Corrupted file causing application crash | Medium | Medium | Medium | Input validation, exception handling |
| RISK-006 | Window/level settings producing non-diagnostic images | Low | High | Medium | Preset values, user training |
| RISK-007 | STL rendering orientation incorrect | Low | Medium | Low | Validation against reference models |
| RISK-008 | Performance degradation with complex 3D rendering | Medium | Low | Low | GPU acceleration, level-of-detail |

### 4.2 Risk Mitigation Measures

1. **Validation Testing**: Comprehensive test suite with reference images
2. **Memory Management**: Implement memory limits and monitoring
3. **Asynchronous Operations**: Use Qt threading for file operations
4. **Robust Logging**: Multiple log destinations, automatic rotation
5. **Input Validation**: File format verification before processing
6. **User Training**: Comprehensive user manual and tooltips
7. **Performance Optimization**: GPU acceleration, caching strategies

---

## 5. Verification and Validation Plan

### 5.1 Test Strategy
- Unit Testing: Individual component testing
- Integration Testing: Component interaction testing
- System Testing: End-to-end functionality
- Performance Testing: Load and stress testing
- User Acceptance Testing: Clinical validation

### 5.2 Test Cases

| Test ID | Test Description | Prerequisites | Test Steps | Expected Result | Pass/Fail |
|---------|------------------|---------------|------------|-----------------|-----------|
| TC-001 | Load valid DICOM series | DICOM test data | 1. Click Load DICOM<br>2. Select folder<br>3. Click Open | Images displayed correctly | Pending |
| TC-002 | Load valid STL file | STL test file | 1. Click Load STL<br>2. Select file<br>3. Click Open | 3D model displayed | Pending |
| TC-003 | Switch between 2D/3D views | DICOM loaded | 1. Click 3D View<br>2. Click 2D View | Smooth transition, no data loss | Pending |
| TC-004 | Adjust window/level | DICOM in 2D view | 1. Move Window slider<br>2. Move Level slider | Image contrast changes appropriately | Pending |
| TC-005 | Verify logging functionality | Application running | 1. Perform various operations<br>2. Check log file | All operations logged with timestamps | Pending |
| TC-006 | Load corrupted file | Corrupted test file | 1. Attempt to load bad file | Error message displayed, no crash | Pending |
| TC-007 | Zoom and pan operations | Image displayed | 1. Use mouse to zoom<br>2. Use mouse to pan | Image zooms and pans smoothly | Pending |
| TC-008 | Error recovery | Various error conditions | 1. Trigger various errors<br>2. Continue using app | Application remains stable | Pending |

### 5.3 Performance Tests

| Test ID | Test Description | Target | Method | Pass Criteria |
|---------|------------------|--------|--------|---------------|
| PT-001 | UI responsiveness | <100ms | Automated timing | 95% of operations <100ms |
| PT-002 | Large file loading | 1GB file | Load test file | Loads without error |
| PT-003 | Memory usage | <4GB | Resource monitor | Peak usage <4GB |

### 5.4 Validation Protocol
1. Clinical image dataset validation
2. Comparison with predicate device
3. User acceptance testing with clinicians
4. Documentation review

---

## 6. Installation and Deployment

### 6.1 System Requirements

#### 6.1.1 Hardware Requirements
- **Minimum**:
  - CPU: Intel Core i5 or AMD Ryzen 5
  - RAM: 8GB
  - GPU: OpenGL 3.3 compatible
  - Storage: 500MB free space
- **Recommended**:
  - CPU: Intel Core i7 or AMD Ryzen 7
  - RAM: 16GB
  - GPU: Dedicated graphics card with 2GB VRAM
  - Storage: 2GB free space

#### 6.1.2 Software Requirements
- **Operating Systems**:
  - Windows 10/11 (64-bit)
  - macOS 12.0+
  - Ubuntu 20.04+ / Debian 11+
- **Python**: 3.8 or higher
- **Dependencies**: See requirements.txt

### 6.2 Installation Instructions

#### 6.2.1 Windows Installation
```batch
# 1. Install Python 3.8+ from python.org
# 2. Open Command Prompt as Administrator
# 3. Navigate to installation directory
cd C:\MedicalImageViewer

# 4. Create virtual environment
python -m venv venv

# 5. Activate virtual environment
venv\Scripts\activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Run the application
python medical_image_viewer.py
```

#### 6.2.2 macOS Installation
```bash
# 1. Install Python 3.8+ using Homebrew
brew install python@3.8

# 2. Navigate to installation directory
cd /Applications/MedicalImageViewer

# 3. Create virtual environment
python3 -m venv venv

# 4. Activate virtual environment
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run the application
python medical_image_viewer.py
```

#### 6.2.3 Linux Installation
```bash
# 1. Install Python and dependencies
sudo apt-get update
sudo apt-get install python3.8 python3-pip python3-venv
sudo apt-get install libgl1-mesa-glx libglib2.0-0

# 2. Navigate to installation directory
cd /opt/MedicalImageViewer

# 3. Create virtual environment
python3 -m venv venv

# 4. Activate virtual environment
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run the application
python medical_image_viewer.py
```

### 6.3 Configuration
- Log directory: `./logs/` (created automatically)
- Configuration file: Not required for basic operation
- GPU acceleration: Enabled automatically if available

---

## 7. Maintenance and Support

### 7.1 Change Control Process

1. **Change Request Submission**
   - Submit change request form with justification
   - Include risk assessment for the change

2. **Impact Analysis**
   - Analyze impact on existing functionality
   - Update risk analysis if needed
   - Determine testing requirements

3. **Implementation**
   - Implement changes in development branch
   - Perform unit testing
   - Update documentation

4. **Verification**
   - Execute regression testing
   - Perform specific tests for the change
   - Review code changes

5. **Release**
   - Update version number
   - Generate release notes
   - Archive previous version

### 7.2 Version Numbering
- Format: MAJOR.MINOR.PATCH (e.g., 1.0.0)
- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality
- PATCH: Backwards-compatible bug fixes

### 7.3 Known Limitations
- GPU volume rendering requires OpenGL 3.3+ compatible graphics card
- Large DICOM series (>1000 slices) may experience slower loading times
- STL files must be in binary format (ASCII STL not supported)
- Maximum supported image resolution: 4096x4096 pixels
- Window/level presets not available in version 1.0

### 7.4 Troubleshooting Guide

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Application won't start | Missing dependencies | Reinstall requirements.txt |
| Black screen in viewer | GPU driver issue | Update graphics drivers |
| Cannot load DICOM | Invalid file format | Verify DICOM compliance |
| High memory usage | Large dataset | Reduce image resolution |
| Slow performance | Insufficient GPU | Disable 3D rendering |

---

## 8. Regulatory Compliance

### 8.1 Standards Compliance
- **IEC 62304:2006/AMD1:2015**: Medical device software - Software life cycle processes
- **ISO 13485:2016**: Medical devices - Quality management systems
- **ISO 14971:2019**: Medical devices - Application of risk management
- **IEC 62366-1:2015**: Medical devices - Usability engineering
- **21 CFR Part 11**: Electronic records and signatures (if applicable)

### 8.2 Classification Rationale
The Medical Image Viewer is classified as **Class B** software according to IEC 62304 because:
- It is not life-supporting or life-sustaining
- Failure cannot result in serious injury or death
- It provides visualization only, not diagnosis
- Healthcare professionals make final decisions

### 8.3 Declaration of Conformity
This software has been developed in accordance with:
- IEC 62304 standard for medical device software lifecycle
- Applicable regulatory requirements for the intended markets
- Quality management system procedures

### 8.4 Intended Use Statement
The Medical Image Viewer is intended for use by qualified healthcare professionals for visualization of medical images in DICOM and STL formats. It is not intended to be used as the sole means of diagnosis. All clinical decisions must be made by qualified healthcare professionals based on their professional judgment.

### 8.5 Warnings and Precautions
- **WARNING**: This software is not intended for primary diagnosis
- **WARNING**: Always verify image orientation and patient information
- **CAUTION**: Ensure monitor is properly calibrated for medical use
- **CAUTION**: Do not use for emergency or critical care situations

---

## 9. Version History

| Version | Date | Changes | Author | Approval |
|---------|------|---------|--------|----------|
| 0.1.0 | 2025-05-01 | Initial development version | Dev Team | N/A |
| 0.5.0 | 2025-05-15 | Added 3D rendering capability | Dev Team | N/A |
| 0.9.0 | 2025-05-22 | Beta release for testing | Dev Team | QA Manager |
| 1.0.0 | 2025-05-26 | First production release | Dev Team | Project Manager |

---

## 10. Appendices

### 10.1 Glossary

| Term | Definition |
|------|------------|
| **DICOM** | Digital Imaging and Communications in Medicine - International standard for medical images |
| **STL** | Stereolithography - File format for 3D surface geometry |
| **VTK** | Visualization Toolkit - Open-source software for 3D graphics and visualization |
| **ITK** | Insight Segmentation and Registration Toolkit - Open-source software for medical image analysis |
| **Window/Level** | Contrast adjustment technique for displaying medical images |
| **Volume Rendering** | Technique for displaying 3D volumetric data |
| **Transfer Function** | Mapping of data values to color and opacity for volume rendering |
| **Voxel** | Volume element - 3D equivalent of a pixel |
| **HU** | Hounsfield Units - Quantitative scale for radiodensity in CT images |

### 10.2 References

1. IEC 62304:2006/AMD1:2015 Medical device software - Software life cycle processes
2. FDA Guidance: General Principles of Software Validation (2002)
3. FDA Guidance: Off-The-Shelf Software Use in Medical Devices (2019)
4. VTK Documentation: https://vtk.org/doc/
5. ITK Software Guide: https://itk.org/ItkSoftwareGuide.pdf
6. DICOM Standard: https://www.dicomstandard.org/
7. Python Medical Imaging: https://pypi.org/project/SimpleITK/

### 10.3 Acronyms

| Acronym | Expansion |
|---------|-----------|
| API | Application Programming Interface |
| CPU | Central Processing Unit |
| CT | Computed Tomography |
| DICOM | Digital Imaging and Communications in Medicine |
| FDA | Food and Drug Administration |
| GPU | Graphics Processing Unit |
| GUI | Graphical User Interface |
| IEC | International Electrotechnical Commission |
| ISO | International Organization for Standardization |
| ITK | Insight Toolkit |
| MRI | Magnetic Resonance Imaging |
| PDF | Portable Document Format |
| QA | Quality Assurance |
| RAM | Random Access Memory |
| STL | Stereolithography |
| UI | User Interface |
| V&V | Verification and Validation |
| VTK | Visualization Toolkit |

### 10.4 Document Control

This document is controlled and maintained according to the quality management system procedures. Any printed copies are for reference only. Always refer to the electronic version for the latest revision.

**End of Document**

---

*This document is proprietary and confidential. Unauthorized reproduction or distribution is prohibited.*

*© 2025 Medical Image Viewer Project. All rights reserved.*