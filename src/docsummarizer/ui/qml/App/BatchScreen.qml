import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import QtQuick.Dialogs
import App

// Batch view: pick an input folder + an output folder, then run the model
// across every document in the queue. Overall progress + the current file
// name stream in from the bridge's batchProgress / batchComplete signals.
Item {
    id: screen

    property string folder: ""
    property string outDir: ""
    property int total: 0
    property int done: 0
    property real progress: 0
    property string currentName: ""

    function urlToPath(url) {
        var s = String(url);
        if (s.indexOf("file://") === 0)
            return s.substring(7);
        return s;
    }

    Connections {
        target: bridge
        function onBatchProgress(done, total, name) {
            screen.done = done;
            screen.total = total;
            screen.currentName = name;
            screen.progress = total > 0 ? done / total : 0;
        }
        function onBatchComplete(done, total, failures, outDir) {
            screen.done = done;
            screen.total = total;
            screen.progress = 1;
        }
    }

    FolderDialog {
        id: inputDialog
        title: "Choose input folder"
        onAccepted: screen.folder = screen.urlToPath(selectedFolder)
    }

    FolderDialog {
        id: outputDialog
        title: "Choose output folder"
        onAccepted: screen.outDir = screen.urlToPath(selectedFolder)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 18

        // -- Header -------------------------------------------------------- //
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Text {
                    text: "BATCH QUEUE"
                    color: Theme.label
                    font.family: Theme.ui
                    font.pixelSize: 10
                    font.letterSpacing: 2.2
                }
                Text {
                    Layout.fillWidth: true
                    text: screen.folder !== "" ? screen.folder : "Choose a folder…"
                    color: Theme.ink
                    font.family: Theme.serif
                    font.pixelSize: 28
                    elide: Text.ElideMiddle
                }
                Text {
                    Layout.fillWidth: true
                    text: screen.total + " DOCUMENTS · OUTPUT → " + (screen.outDir !== "" ? screen.outDir : "—") + " · " + String(bridge.summaryType).toUpperCase()
                    color: Theme.faint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1.2
                    elide: Text.ElideMiddle
                }
            }

            ColumnLayout {
                spacing: 8
                Layout.alignment: Qt.AlignTop
                Text {
                    Layout.alignment: Qt.AlignRight
                    text: screen.done + "/" + screen.total
                    color: Theme.accent2
                    font.family: Theme.mono
                    font.pixelSize: 22
                    font.letterSpacing: 1
                }
                RowLayout {
                    spacing: 8
                    Button {
                        text: "Add Folder"
                        onClicked: inputDialog.open()
                    }
                    Button {
                        text: "Output…"
                        onClicked: outputDialog.open()
                    }
                    Button {
                        text: "Process All"
                        enabled: screen.folder !== "" && screen.outDir !== "" && bridge.modelReady && !bridge.busy
                        onClicked: bridge.batchProcess(screen.folder, screen.outDir)
                    }
                }
            }
        }

        // -- Overall progress ---------------------------------------------- //
        Rectangle {
            Layout.fillWidth: true
            radius: 3
            color: Theme.srcPane
            border.width: 1
            border.color: Theme.line
            implicitHeight: progressCol.implicitHeight + 32

            ColumnLayout {
                id: progressCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    Text {
                        text: "OVERALL"
                        color: Theme.label
                        font.family: Theme.ui
                        font.pixelSize: 10
                        font.letterSpacing: 2.2
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Text {
                        text: Math.round(screen.progress * 100) + "%"
                        color: Theme.accent
                        font.family: Theme.mono
                        font.pixelSize: 12
                        font.letterSpacing: 1
                    }
                }

                ProgressBar {
                    id: overallBar
                    Layout.fillWidth: true
                    from: 0
                    to: 1
                    value: screen.progress

                    background: Rectangle {
                        implicitHeight: 6
                        radius: 3
                        color: Theme.block
                        border.width: 1
                        border.color: Theme.line
                    }
                    contentItem: Item {
                        implicitHeight: 6
                        Rectangle {
                            width: overallBar.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            color: Theme.accent
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: screen.currentName !== "" ? "▸ " + screen.currentName : (bridge.busy ? "● PROCESSING…" : "Idle — select folders and press Process All")
                    color: Theme.text
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1
                    elide: Text.ElideMiddle
                }
            }
        }

        // -- Status footer ------------------------------------------------- //
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Text {
                text: bridge.statusText !== "" ? "● " + bridge.statusText : ""
                color: Theme.statusColorFor(bridge.statusColor)
                font.family: Theme.mono
                font.pixelSize: 10
                font.letterSpacing: 1
            }
            Item {
                Layout.fillWidth: true
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }
}
