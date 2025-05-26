import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 1.3
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 1200
    height: 800
    title: qsTr("Medical Image Viewer - IEC 62304 Compliant")
    
    Material.theme: Material.Dark
    Material.accent: Material.Cyan
    
    // Properties for state management
    property bool imageLoaded: false
    property string currentImageType: ""
    property bool is3DView: false
    
    // Header with controls
    header: ToolBar {
        height: 60
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            
            ToolButton {
                id: loadDicomButton
                text: qsTr("Load DICOM")
                icon.source: "qrc:/icons/dicom.png"
                onClicked: fileDialogDicom.open()
                
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Load DICOM series from folder")
            }
            
            ToolButton {
                id: loadStlButton
                text: qsTr("Load STL")
                icon.source: "qrc:/icons/stl.png"
                onClicked: fileDialogStl.open()
                
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Load STL 3D model file")
            }
            
            ToolSeparator {}
            
            ToolButton {
                id: view2DButton
                text: qsTr("2D View")
                icon.source: "qrc:/icons/2d.png"
                enabled: imageLoaded && currentImageType === "DICOM"
                checkable: true
                checked: !is3DView
                onClicked: {
                    is3DView = false
                    backend.switchTo2DView()
                }
            }
            
            ToolButton {
                id: view3DButton
                text: qsTr("3D View")
                icon.source: "qrc:/icons/3d.png"
                enabled: imageLoaded && currentImageType === "DICOM"
                checkable: true
                checked: is3DView
                onClicked: {
                    is3DView = true
                    backend.switchTo3DView()
                }
            }
            
            Item { Layout.fillWidth: true }
            
            // Window/Level controls for DICOM
            GroupBox {
                title: qsTr("Window/Level")
                visible: imageLoaded && currentImageType === "DICOM"
                
                RowLayout {
                    Label { text: qsTr("Window:") }
                    
                    Slider {
                        id: windowSlider
                        from: 1
                        to: 4000
                        value: 400
                        stepSize: 10
                        
                        onValueChanged: {
                            if (pressed) {
                                backend.updateWindowLevel(value, levelSlider.value)
                            }
                        }
                    }
                    
                    Label {
                        text: Math.round(windowSlider.value)
                        Layout.preferredWidth: 50
                    }
                    
                    Label { text: qsTr("Level:") }
                    
                    Slider {
                        id: levelSlider
                        from: -1000
                        to: 3000
                        value: 40
                        stepSize: 10
                        
                        onValueChanged: {
                            if (pressed) {
                                backend.updateWindowLevel(windowSlider.value, value)
                            }
                        }
                    }
                    
                    Label {
                        text: Math.round(levelSlider.value)
                        Layout.preferredWidth: 50
                    }
                }
            }
            
            ToolButton {
                text: qsTr("About")
                icon.source: "qrc:/icons/info.png"
                onClicked: aboutDialog.open()
            }
        }
    }
    
    // Main content area
    Item {
        id: contentArea
        anchors.fill: parent
        
        // Placeholder when no image is loaded
        Rectangle {
            anchors.fill: parent
            color: "#1e1e1e"
            visible: !imageLoaded
            
            Column {
                anchors.centerIn: parent
                spacing: 20
                
                Image {
                    source: "qrc:/icons/medical.png"
                    width: 128
                    height: 128
                    anchors.horizontalCenter: parent.horizontalCenter
                    opacity: 0.5
                }
                
                Label {
                    text: qsTr("Medical Image Viewer")
                    font.pixelSize: 24
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                
                Label {
                    text: qsTr("Load DICOM series or STL files to begin")
                    opacity: 0.7
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }
        
        // VTK render area (integrated via backend)
        Item {
            id: vtkContainer
            anchors.fill: parent
            visible: imageLoaded
            
            // This will be populated by the Python backend
        }
    }
    
    // Status bar
    footer: ToolBar {
        height: 30
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 5
            
            Label {
                id: statusLabel
                text: qsTr("Ready")
                Layout.fillWidth: true
            }
            
            Label {
                id: coordinatesLabel
                text: ""
                visible: imageLoaded
            }
            
            Label {
                id: pixelValueLabel
                text: ""
                visible: imageLoaded && currentImageType === "DICOM"
            }
        }
    }
    
    // File dialogs
    FileDialog {
        id: fileDialogDicom
        title: qsTr("Select DICOM Directory")
        selectFolder: true
        
        onAccepted: {
            backend.loadDicomSeries(folder)
        }
    }
    
    FileDialog {
        id: fileDialogStl
        title: qsTr("Select STL File")
        nameFilters: ["STL files (*.stl)", "All files (*)"]
        
        onAccepted: {
            backend.loadStlFile(fileUrl)
        }
    }
    
    // About dialog
    Dialog {
        id: aboutDialog
        title: qsTr("About Medical Image Viewer")
        width: 400
        height: 300
        
        contentItem: ColumnLayout {
            spacing: 20
            
            Image {
                source: "qrc:/icons/medical.png"
                width: 64
                height: 64
                Layout.alignment: Qt.AlignHCenter
            }
            
            Label {
                text: qsTr("Medical Image Viewer")
                font.pixelSize: 20
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }
            
            Label {
                text: qsTr("Version 1.0.0")
                Layout.alignment: Qt.AlignHCenter
            }
            
            Label {
                text: qsTr("IEC 62304 Compliant Medical Device Software\nClass B - Non-life-supporting")
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Label {
                text: qsTr("Powered by VTK, ITK, and Qt")
                opacity: 0.7
                Layout.alignment: Qt.AlignHCenter
            }
        }
        
        standardButtons: Dialog.Ok
    }
    
    // Error dialog
    Dialog {
        id: errorDialog
        title: qsTr("Error")
        
        property string errorMessage: ""
        
        contentItem: ColumnLayout {
            spacing: 20
            
            Image {
                source: "qrc:/icons/error.png"
                width: 48
                height: 48
                Layout.alignment: Qt.AlignHCenter
            }
            
            Label {
                text: errorDialog.errorMessage
                wrapMode: Text.Wrap
                Layout.maximumWidth: 400
            }
        }
        
        standardButtons: Dialog.Ok
    }
    
    // Connections to backend
    Connections {
        target: backend
        
        function onImageLoaded(imageType) {
            imageLoaded = true
            currentImageType = imageType
            statusLabel.text = qsTr("Image loaded successfully")
        }
        
        function onErrorOccurred(message) {
            errorDialog.errorMessage = message
            errorDialog.open()
            statusLabel.text = qsTr("Error: ") + message
        }
        
        function onStatusUpdate(message) {
            statusLabel.text = message
        }
        
        function onCoordinatesUpdate(coords) {
            coordinatesLabel.text = coords
        }
        
        function onPixelValueUpdate(value) {
            pixelValueLabel.text = qsTr("Value: ") + value
        }
    }
    
    // Keyboard shortcuts
    Shortcut {
        sequence: "Ctrl+O"
        onActivated: loadDicomButton.clicked()
    }
    
    Shortcut {
        sequence: "Ctrl+L"
        onActivated: loadStlButton.clicked()
    }
    
    Shortcut {
        sequence: "2"
        enabled: view2DButton.enabled
        onActivated: view2DButton.clicked()
    }
    
    Shortcut {
        sequence: "3"
        enabled: view3DButton.enabled
        onActivated: view3DButton.clicked()
    }
    
    Shortcut {
        sequence: "F11"
        onActivated: {
            if (visibility === Window.FullScreen) {
                visibility = Window.Windowed
            } else {
                visibility = Window.FullScreen
            }
        }
    }
}