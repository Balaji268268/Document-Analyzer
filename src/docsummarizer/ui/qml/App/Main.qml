import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import App

// Application shell: persistent top bar + LCARS rail + a screen Loader.
// First-run wizard removed per user requirement; status & progress bar
// integrated into the main responsive workspace.
ApplicationWindow {
    id: win
    visible: true
    visibility: Window.Maximized
    width: 1920
    height: 1080
    minimumWidth: 1000
    minimumHeight: 640
    title: "DocSummarizer — Abstract Console"
    color: Theme.pageBg

    property string activeScreen: "summary"
    property bool forceFirstRun: false
    property bool showUploadModal: false
    property int uploadModalTab: 0

    Component.onCompleted: {
        Theme.applyMode(bridge.appearance);
        bridge.checkDependencies();
        bridge.checkOllamaStatus();
    }

    // Clean solid page background (prevents software-rendering curve artifacts)
    Rectangle {
        anchors.fill: parent
        color: Theme.pageBg
    }

    // Faint instrument grid
    Canvas {
        id: gridCanvas
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        Connections {
            target: Theme
            function onDarkChanged() { gridCanvas.requestPaint(); }
        }
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0, 0, width, height);
            ctx.strokeStyle = Theme.dark ? "rgba(111,195,216,0.03)" : "rgba(40,80,100,0.05)";
            ctx.lineWidth = 1;
            for (var x = 40; x < width; x += 40) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
            }
            for (var y = 40; y < height; y += 40) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TopBar {
            Layout.fillWidth: true
        }

        // Live Real-Time Responsive Progress & Task Description Bar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: (bridge.busy || bridge.downloadPercent > 0 || liveProgressText.text !== "") ? 48 : 0
            visible: Layout.preferredHeight > 0
            color: Theme.block
            border.width: 1
            border.color: Theme.line2
            clip: true

            Behavior on Layout.preferredHeight {
                NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                anchors.topMargin: 6
                anchors.bottomMargin: 6
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        id: liveProgressText
                        Layout.fillWidth: true
                        text: bridge.progressMessage || (bridge.busy ? "Processing document intelligence task..." : "")
                        color: Theme.inkSoft
                        font.family: Theme.mono
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }

                    Text {
                        text: Math.round(bridge.downloadPercent > 0 ? bridge.downloadPercent : (bridge.busy ? 65 : 100)) + "%"
                        color: Theme.accent
                        font.family: Theme.mono
                        font.pixelSize: 11
                        font.weight: Font.Bold
                    }
                }

                // Smooth responsive progress bar
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 5
                    radius: 2.5
                    color: Theme.line2

                    Rectangle {
                        height: parent.height
                        radius: 2.5
                        width: parent.width * (Math.max(0, Math.min(100, bridge.downloadPercent > 0 ? bridge.downloadPercent : (bridge.busy ? 65 : 0))) / 100)
                        color: Theme.accent

                        Behavior on width {
                            NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rail {
                Layout.fillHeight: true
                currentScreen: win.activeScreen
                onNavigate: name => win.activeScreen = name
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: {
                    switch (win.activeScreen) {
                    case "extract": return 1;
                    case "batch": return 2;
                    case "config": return 3;
                    default: return 0;
                    }
                }
                SummaryScreen {}
                ExtractScreen {}
                BatchScreen {}
                ConfigScreen {
                    onReinitialize: win.forceFirstRun = true
                }
            }
        }
    }

    // First-Run Wizard Overlay (Deactivated per user request)
    FirstRunOverlay {
        anchors.fill: parent
        shown: false
        visible: false
    }

    // Document Manager & User Upload History Modal
    FileUploadModal {
        anchors.fill: parent
        visible: win.showUploadModal
        activeTab: win.uploadModalTab
        onClosed: win.showUploadModal = false
    }

    // Login Modal Overlay (shown whenever user is not authenticated)
    LoginModal {
        anchors.fill: parent
        visible: !bridge.authenticated
    }

    Toast {
        id: toast
    }
    Connections {
        target: bridge
        function onToast(message) {
            toast.show(message);
        }
    }
}
