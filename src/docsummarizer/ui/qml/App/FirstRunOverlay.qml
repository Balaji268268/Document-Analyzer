import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import App

// First-run overlay: clean Environment & Ollama setup wizard.
// Handles Python dependency verification, local GGUF downloading, and dynamic
// Ollama status (Ready / Stopped / Not Installed / Model Missing) with non-blocking fallback.
Item {
    id: screen

    signal enter()

    property bool shown: true
    property bool started: false
    property string statusLine: "Awaiting environment initialization."

    visible: screen.shown && opacity > 0
    opacity: screen.shown ? 1 : 0
    Behavior on opacity {
        NumberAnimation {
            duration: 180
        }
    }

    Component.onCompleted: {
        if (typeof bridge !== "undefined") {
            bridge.checkDependencies();
            bridge.checkOllamaStatus();
        }
    }

    Connections {
        target: bridge
        function onProgress(pct, msg) {
            screen.statusLine = msg;
        }
    }

    // Full-bleed dimming scrim.
    Rectangle {
        anchors.fill: parent
        color: Theme.overlay
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
        }
    }

    // Centered panel ----------------------------------------------------- //
    Rectangle {
        id: panel
        anchors.centerIn: parent
        width: 540
        implicitHeight: panelCol.implicitHeight + 48
        radius: 6
        color: Theme.shellTop
        border.width: 1
        border.color: Theme.line2

        ColumnLayout {
            id: panelCol
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 24
            spacing: 14

            Text {
                text: "ENVIRONMENT & SYSTEM SETUP"
                color: Theme.label2
                font.family: Theme.mono
                font.pixelSize: 10
                font.letterSpacing: 2.4
            }

            Text {
                Layout.fillWidth: true
                text: "First-Launch Wizard"
                color: Theme.ink
                font.family: Theme.serif
                font.pixelSize: 28
                wrapMode: Text.WordWrap
            }

            Text {
                Layout.fillWidth: true
                text: "DocSummarizer runs 100% offline on your device. We verify your Python "
                    + "environment, local model engine, and Ollama service before starting."
                color: Theme.text
                font.family: Theme.body
                font.pixelSize: 14
                lineHeight: 1.3
                wrapMode: Text.WordWrap
            }

            // --- 1. Python Dependencies Card --- //
            Rectangle {
                Layout.fillWidth: true
                radius: 4
                color: Theme.block
                border.width: 1
                border.color: bridge.dependenciesOk ? "#10B981" : Theme.line
                implicitHeight: depRow.implicitHeight + 20

                RowLayout {
                    id: depRow
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 10

                    Text {
                        text: bridge.dependenciesOk ? "🟢" : "⚠️"
                        font.pixelSize: 16
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Text {
                            text: bridge.dependenciesOk ? "Python Dependencies Ready" : "Missing Python Packages Detected"
                            color: Theme.inkSoft
                            font.family: Theme.ui
                            font.pixelSize: 14
                        }

                        Text {
                            text: bridge.dependenciesOk ? "All core packages are installed and verified." : "Click below to auto-install missing packages via pip."
                            color: Theme.faint
                            font.family: Theme.mono
                            font.pixelSize: 10
                        }
                    }

                    Button {
                        visible: !bridge.dependenciesOk
                        text: "Install Packages"
                        onClicked: bridge.installMissingDependencies()
                    }
                }
            }

            // --- 2. Dynamic Ollama Status Card --- //
            Rectangle {
                Layout.fillWidth: true
                radius: 4
                color: Theme.block
                border.width: 1
                border.color: bridge.ollamaStatusCode === "READY" ? "#10B981" : (bridge.ollamaStatusCode === "STOPPED" || bridge.ollamaStatusCode === "MODEL_MISSING" ? "#F59E0B" : Theme.line)
                implicitHeight: ollamaCol.implicitHeight + 24

                ColumnLayout {
                    id: ollamaCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 14
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Text {
                            text: bridge.ollamaStatusCode === "READY" ? "🟢" : (bridge.ollamaStatusCode === "STOPPED" || bridge.ollamaStatusCode === "MODEL_MISSING" ? "🟡" : "🔴")
                            font.pixelSize: 16
                        }

                        Text {
                            Layout.fillWidth: true
                            text: bridge.ollamaStatusCode === "READY" ? "Ollama Ready" : (bridge.ollamaStatusCode === "STOPPED" ? "Ollama Installed but Stopped" : (bridge.ollamaStatusCode === "MODEL_MISSING" ? "Ollama Model Missing" : "Ollama Not Installed"))
                            color: Theme.inkSoft
                            font.family: Theme.serif
                            font.pixelSize: 16
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: bridge.ollamaStatusMessage || "Detecting Ollama status..."
                        color: Theme.text
                        font.family: Theme.body
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Button {
                            visible: bridge.ollamaStatusCode === "STOPPED"
                            text: "Start Ollama Service"
                            onClicked: bridge.startOllamaService()
                        }

                        Button {
                            visible: bridge.ollamaStatusCode === "NOT_INSTALLED"
                            text: "Install Ollama Now"
                            onClicked: bridge.installOllamaNow()
                        }

                        Button {
                            visible: bridge.ollamaStatusCode === "MODEL_MISSING"
                            text: "Download Model (" + bridge.ollamaModelName + ")"
                            onClicked: bridge.pullOllamaModel("")
                        }

                        Button {
                            text: "Check Again"
                            onClicked: bridge.checkOllamaStatus()
                        }
                    }
                }
            }

            // --- 3. Local GGUF Model Card --- //
            Rectangle {
                Layout.fillWidth: true
                radius: 4
                color: Theme.block
                border.width: 1
                border.color: Theme.line
                implicitHeight: cardRow.implicitHeight + 20

                RowLayout {
                    id: cardRow
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 10

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            Layout.fillWidth: true
                            text: "Local GGUF Core: " + bridge.modelName
                            color: Theme.inkSoft
                            font.family: Theme.serif
                            font.pixelSize: 16
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: bridge.modelQuant + " · " + bridge.modelSizeGb + " GB · OFFLINE CACHE"
                            color: Theme.faint
                            font.family: Theme.mono
                            font.pixelSize: 10
                        }
                    }

                    Text {
                        text: Math.round(bridge.downloadPercent) + "%"
                        color: Theme.accent
                        font.family: Theme.mono
                        font.pixelSize: 22
                        Layout.alignment: Qt.AlignVCenter
                    }
                }
            }

            ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: 1
                value: bridge.downloadPercent / 100
            }

            Text {
                Layout.fillWidth: true
                text: screen.statusLine
                color: Theme.faint
                font.family: Theme.mono
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }

            // Primary actions --------------------------------------------- //
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Button {
                    id: action
                    Layout.fillWidth: true
                    enabled: !(screen.started && bridge.downloadPercent < 100)
                    text: bridge.downloadPercent >= 100
                        ? "Enter Console"
                        : (screen.started
                            ? "Downloading… " + Math.round(bridge.downloadPercent) + "%"
                            : "Begin Download")
                    onClicked: {
                        if (!screen.started && bridge.downloadPercent < 100) {
                            screen.started = true;
                            bridge.beginDownload();
                        } else {
                            screen.enter();
                        }
                    }

                    contentItem: Text {
                        text: action.text
                        color: action.enabled ? Theme.onAccent : Theme.dim
                        font.family: Theme.ui
                        font.pixelSize: 13
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitHeight: 40
                        radius: 3
                        color: action.enabled ? Theme.accent : Theme.block
                        border.width: 1
                        border.color: action.enabled ? Theme.accentDeep : Theme.line2
                    }
                }

                Button {
                    Layout.preferredWidth: 160
                    text: "Set Up Later / Continue"
                    onClicked: screen.enter()

                    contentItem: Text {
                        text: "Set Up Later"
                        color: Theme.text
                        font.family: Theme.ui
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitHeight: 40
                        radius: 3
                        color: Theme.block
                        border.width: 1
                        border.color: Theme.line2
                    }
                }
            }
        }
    }
}
