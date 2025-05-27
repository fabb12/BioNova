import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 1400
    height: 900
    title: qsTr("Medical Image Viewer v1.0.0 - IEC 62304 Class B")
    
    Material.theme: Material.Dark
    Material.accent: Material.Cyan
    Material.primary: Material.Blue
    
    // Properties for state management
    property bool imageLoaded: false
    property string currentImageType: ""
    property bool is3DView: false
    property bool isProcessing: false
    
    // Header with main controls
    header: ToolBar {
        height: 70
        Material.elevation: 4
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 15
            
            // File operations group
            GroupBox {
                title: qsTr("Load Data")
                
                RowLayout {
                    ToolButton {
                        id: loadDicomButton
                        text: qsTr("DICOM Series")
                        icon.source: "qrc:/icons/dicom.png"
                        enabled: !isProcessing
                        onClicked: fileDialogDicom.open()
                        
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Load DICOM series from folder (Ctrl+D)")
                    }
                    
                    ToolButton {
                        id: loadStlButton
                        text: qsTr("STL Model")
                        icon.source: "qrc:/icons/stl.png"
                        enabled: !isProcessing
                        onClicked: fileDialogStl.open()
                        
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Load STL 3D model file (Ctrl+S)")
                    }
                }
            }
            
            ToolSeparator {}
            
            // View controls group
            GroupBox {
                title: qsTr("View Mode")
                visible: imageLoaded && currentImageType === "DICOM"
                
                RowLayout {
                    ToolButton {
                        id: view2DButton
                        text: qsTr("2D View")
                        icon.source: "qrc:/icons/2d.png"
                        enabled: imageLoaded && currentImageType === "DICOM" && !isProcessing
                        checkable: true
                        checked: !is3DView
                        onClicked: {
                            if (!checked) return
                            is3DView = false
                            backend.switchTo2DView()
                        }
                        
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Switch to 2D slice view (Key: 2)")
                    }
                    
                    ToolButton {
                        id: view3DButton
                        text: qsTr("3D Volume")
                        icon.source: "qrc:/icons/3d.png"
                        enabled: imageLoaded && currentImageType === "DICOM" && !isProcessing
                        checkable: true
                        checked: is3DView
                        onClicked: {
                            if (!checked) return
                            is3DView = true
                            backend.switchTo3DView()
                        }
                        
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Switch to 3D volume rendering (Key: 3)")
                    }
                }
            }
            
            Item { Layout.fillWidth: true }
            
            // Window/Level controls for 2D DICOM
            GroupBox {
                title: qsTr("Window/Level")
                visible: imageLoaded && currentImageType === "DICOM" && !is3DView
                
                GridLayout {
                    columns: 2
                    
                    Label { text: qsTr("Window:") }
                    RowLayout {
                        Slider {
                            id: windowSlider
                            from: 1
                            to: 4000
                            value: 400
                            stepSize: 10
                            Layout.preferredWidth: 150
                            
                            onValueChanged: {
                                if (pressed) {
                                    backend.updateWindowLevel(value, levelSlider.value)
                                }
                            }
                        }
                        
                        SpinBox {
                            from: windowSlider.from
                            to: windowSlider.to
                            value: windowSlider.value
                            onValueChanged: windowSlider.value = value
                        }
                    }
                    
                    Label { text: qsTr("Level:") }
                    RowLayout {
                        Slider {
                            id: levelSlider
                            from: -1000
                            to: 3000
                            value: 40
                            stepSize: 10
                            Layout.preferredWidth: 150
                            
                            onValueChanged: {
                                if (pressed) {
                                    backend.updateWindowLevel(windowSlider.value, value)
                                }
                            }
                        }
                        
                        SpinBox {
                            from: levelSlider.from
                            to: levelSlider.to
                            value: levelSlider.value
                            onValueChanged: levelSlider.value = value
                        }
                    }
                }
            }
            
            // 3D preset controls
            GroupBox {
                title: qsTr("3D Presets")
                visible: imageLoaded && currentImageType === "DICOM" && is3DView
                
                RowLayout {
                    ComboBox {
                        id: presetComboBox
                        model: ["default", "ct_bone", "ct_soft_tissue"]
                        currentIndex: 0
                        
                        onCurrentTextChanged: {
                            if (currentText) {
                                backend.update3DPreset(currentText)
                            }
                        }
                    }
                }
            }
            
            ToolSeparator {}
            
            // Utility controls
            RowLayout {
                ToolButton {
                    text: qsTr("Reset View")
                    icon.source: "qrc:/icons/reset.png"
                    enabled: imageLoaded && !isProcessing
                    onClicked: backend.resetCamera()
                    
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Reset camera view (Key: R)")
                }
                
                ToolButton {
                    text: qsTr("Clear")
                    icon.source: "qrc:/icons/clear.png"
                    enabled: imageLoaded && !isProcessing
                    onClicked: backend.clearDisplay()
                    
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Clear current display (Ctrl+C)")
                }
                
                ToolButton {
                    text: qsTr("Info")
                    icon.source: "qrc:/icons/info.png"
                    enabled: imageLoaded
                    onClicked: infoDialog.open()
                    
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Show image information (Ctrl+I)")
                }
                
                ToolButton {
                    text: qsTr("About")
                    icon.source: "qrc:/icons/about.png"
                    onClicked: aboutDialog.open()
                }
            }
        }
    }
    
    // Main content area
    Item {
        id: contentArea
        anchors.fill: parent
        
        // Welcome screen when no image is loaded
        Rectangle {
            anchors.fill: parent
            color: "#2d2d2d"
            visible: !imageLoaded && !isProcessing
            
            Column {
                anchors.centerIn: parent
                spacing: 30
                
                Image {
                    source: "qrc:/icons/medical_large.png"
                    width: 160
                    height: 160
                    anchors.horizontalCenter: parent.horizontalCenter
                    opacity: 0.6
                }
                
                Label {
                    text: qsTr("Medical Image Viewer")
                    font.pixelSize: 28
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: Material.accent
                }
                
                Label {
                    text: qsTr("IEC 62304 Compliant - Class B Medical Device Software")
                    font.pixelSize: 16
                    anchors.horizontalCenter: parent.horizontalCenter
                    opacity: 0.8
                }
                
                Rectangle {
                    width: 300
                    height: 1
                    color: Material.accent
                    anchors.horizontalCenter: parent.horizontalCenter
                    opacity: 0.5
                }
                
                Column {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10
                    
                    Label {
                        text: qsTr("Supported Formats:")
                        font.pixelSize: 14
                        anchors.horizontalCenter: parent.horizontalCenter
                        opacity: 0.9
                    }
                    
                    Label {
                        text: qsTr("• DICOM series (.dcm) - 2D/3D medical images")
                        font.pixelSize: 12
                        anchors.horizontalCenter: parent.horizontalCenter
                        opacity: 0.7
                    }
                    
                    Label {
                        text: qsTr("• STL models (.stl) - 3D surface models")
                        font.pixelSize: 12
                        anchors.horizontalCenter: parent.horizontalCenter
                        opacity: 0.7
                    }
                }
                
                Button {
                    text: qsTr("Load DICOM Series")
                    anchors.horizontalCenter: parent.horizontalCenter
                    Material.background: Material.accent
                    onClicked: loadDicomButton.clicked()
                }
            }
        }
        
        // Processing indicator
        Rectangle {
            anchors.fill: parent
            color: "#aa000000"
            visible: isProcessing
            
            Column {
                anchors.centerIn: parent
                spacing: 20
                
                BusyIndicator {
                    anchors.horizontalCenter: parent.horizontalCenter
                    running: isProcessing
                }
                
                Label {
                    text: qsTr("Processing...")
                    font.pixelSize: 18
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }
        
        // VTK render area placeholder
        Rectangle {
            id: vtkContainer
            anchors.fill: parent
            color: "#1a1a1a"
            visible: imageLoaded && !isProcessing
            
            Label {
                anchors.centerIn: parent
                text: qsTr("VTK Rendering Area")
                opacity: 0.3
                visible: imageLoaded
            }
            
            // This will be replaced by actual VTK widget integration
            // In a real implementation, you would use QQuickVTKRenderItem
            // or similar Qt-VTK integration component
        }
    }
    
    // Status bar
    footer: ToolBar {
        height: 35
        Material.elevation: 2
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 8
            
            Label {
                id: statusLabel
                text: qsTr("Ready - Load DICOM series or STL files to begin")
                Layout.fillWidth: true
                font.pixelSize: 11
            }
            
            Label {
                id: coordinatesLabel
                text: ""
                visible: imageLoaded
                font.pixelSize: 11
                opacity: 0.8
            }
            
            Rectangle {
                width: 1
                height: 20
                color: Material.accent
                visible: coordinatesLabel.visible && pixelValueLabel.visible
            }
            
            Label {
                id: pixelValueLabel
                text: ""
                visible: imageLoaded && currentImageType === "DICOM"
                font.pixelSize: 11
                opacity: 0.8
            }
            
            Rectangle {
                width: 1
                height: 20
                color: Material.accent
                visible: pixelValueLabel.visible
            }
            
            Label {
                text: qsTr("v1.0.0")
                font.pixelSize: 10
                opacity: 0.6
            }
        }
    }
    
    // File dialogs
    FileDialog {
        id: fileDialogDicom
        title: qsTr("Select DICOM Directory")
        fileMode: FileDialog.SaveFile  // This will be used to select folder
        
        onAccepted: {
            backend.loadDicomSeries(selectedFile)
        }
    }
    
    FileDialog {
        id: fileDialogStl
        title: qsTr("Select STL File")
        nameFilters: ["STL files (*.stl)", "All files (*)"]
        
        onAccepted: {
            backend.loadStlFile(selectedFile)
        }
    }
    
    // About dialog
    Dialog {
        id: aboutDialog
        title: qsTr("About Medical Image Viewer")
        width: 500
        height: 400
        anchors.centerIn: parent
        
        contentItem: ScrollView {
            ColumnLayout {
                spacing: 20
                width: parent.width
                
                Image {
                    source: "qrc:/icons/medical_large.png"
                    width: 80
                    height: 80
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Label {
                    text: qsTr("Medical Image Viewer")
                    font.pixelSize: 24
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Label {
                    text: qsTr("Version 1.0.0")
                    font.pixelSize: 16
                    Layout.alignment: Qt.AlignHCenter
                    opacity: 0.8
                }
                
                Rectangle {
                    width: 200
                    height: 1
                    color: Material.accent
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Label {
                    text: qsTr("IEC 62304 Compliant Medical Device Software")
                    font.pixelSize: 14
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                    color: Material.accent
                }
                
                Label {
                    text: qsTr("Classification: Class B - Non-life-supporting")
                    font.pixelSize: 12
                    Layout.alignment: Qt.AlignHCenter
                    opacity: 0.9
                }
                
                Label {
                    text: qsTr("Intended Use: Visualization of medical images for healthcare professionals")
                    font.pixelSize: 10
                    Layout.alignment: Qt.AlignHCenter
                    wrapMode: Text.Wrap
                    Layout.maximumWidth: 400
                    opacity: 0.7
                }
                
                Rectangle {
                    width: 150
                    height: 1
                    color: Material.accent
                    Layout.alignment: Qt.AlignHCenter
                    opacity: 0.5
                }
                
                Label {
                    text: qsTr("Powered by:")
                    font.pixelSize: 12
                    Layout.alignment: Qt.AlignHCenter
                    opacity: 0.8
                }
                
                Label {
                    text: qsTr("• VTK (Visualization Toolkit)\n• ITK (Insight Toolkit)\n• Qt Framework\n• Python")
                    font.pixelSize: 10
                    Layout.alignment: Qt.AlignHCenter
                    opacity: 0.7
                }
            }
        }
        
        standardButtons: Dialog.Ok
    }
    
    // Image information dialog
    Dialog {
        id: infoDialog
        title: qsTr("Image Information")
        width: 600
        height: 500
        anchors.centerIn: parent
        
        contentItem: ScrollView {
            ColumnLayout {
                spacing: 15
                width: parent.width
                
                GroupBox {
                    title: qsTr("Metadata")
                    Layout.fillWidth: true
                    
                    ScrollView {
                        anchors.fill: parent
                        height: 150
                        
                        Label {
                            id: metadataLabel
                            text: backend.getImageMetadata()
                            wrapMode: Text.Wrap
                            font.family: "monospace"
                            font.pixelSize: 10
                        }
                    }
                }
                
                GroupBox {
                    title: qsTr("Statistics")
                    Layout.fillWidth: true
                    visible: currentImageType === "DICOM"
                    
                    ScrollView {
                        anchors.fill: parent
                        height: 100
                        
                        Label {
                            id: statisticsLabel
                            text: backend.getImageStatistics()
                            wrapMode: Text.Wrap
                            font.family: "monospace"
                            font.pixelSize: 10
                        }
                    }
                }
            }
        }
        
        standardButtons: Dialog.Ok
        
        onAboutToShow: {
            metadataLabel.text = backend.getImageMetadata()
            if (currentImageType === "DICOM") {
                statisticsLabel.text = backend.getImageStatistics()
            }
        }
    }
    
    // Error dialog
    Dialog {
        id: errorDialog
        title: qsTr("Error")
        width: 400
        anchors.centerIn: parent
        
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
                Layout.maximumWidth: 350
                Layout.alignment: Qt.AlignHCenter
            }
        }
        
        standardButtons: Dialog.Ok
    }
    
    // Progress dialog
    Dialog {
        id: progressDialog
        title: qsTr("Processing")
        width: 300
        height: 150
        anchors.centerIn: parent
        modal: true
        closePolicy: Dialog.NoAutoClose
        
        property int progressValue: 0
        
        contentItem: ColumnLayout {
            spacing: 20
            
            BusyIndicator {
                Layout.alignment: Qt.AlignHCenter
                running: progressDialog.visible
            }
            
            ProgressBar {
                Layout.fillWidth: true
                value: progressDialog.progressValue / 100.0
                visible: progressDialog.progressValue > 0
            }
            
            Label {
                text: qsTr("Please wait...")
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
    
    // Connections to backend
    Connections {
        target: backend
        
        function onImageLoaded(imageType, imageInfo) {
            imageLoaded = true
            currentImageType = imageType
            isProcessing = false
            statusLabel.text = qsTr("Loaded: ") + imageType + " - " + imageInfo
            progressDialog.close()
        }
        
        function onErrorOccurred(message) {
            isProcessing = false
            errorDialog.errorMessage = message
            errorDialog.open()
            statusLabel.text = qsTr("Error: ") + message
            progressDialog.close()
        }
        
        function onStatusUpdate(message) {
            statusLabel.text = message
            if (message.includes("Loading") || message.includes("Processing")) {
                isProcessing = true
            } else {
                isProcessing = false
            }
        }
        
        function onCoordinatesUpdate(coords) {
            coordinatesLabel.text = coords
        }
        
        function onPixelValueUpdate(value) {
            pixelValueLabel.text = qsTr("Value: ") + value
        }
        
        function onProgressUpdate(percentage) {
            progressDialog.progressValue = percentage
            if (percentage > 0 && !progressDialog.visible) {
                progressDialog.open()
            }
            if (percentage >= 100) {
                progressDialog.close()
            }
        }
    }
    
    // Keyboard shortcuts
    Shortcut {
        sequence: "Ctrl+D"
        onActivated: loadDicomButton.clicked()
    }
    
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: loadStlButton.clicked()
    }
    
    Shortcut {
        sequence: "Ctrl+C"
        enabled: imageLoaded
        onActivated: backend.clearDisplay()
    }
    
    Shortcut {
        sequence: "Ctrl+I"
        enabled: imageLoaded
        onActivated: infoDialog.open()
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
        sequence: "R"
        enabled: imageLoaded
        onActivated: backend.resetCamera()
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
    
    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (visibility === Window.FullScreen) {
                visibility = Window.Windowed
            }
        }
    }
}