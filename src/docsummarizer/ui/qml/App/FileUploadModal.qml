import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import QtQuick.Dialogs
import QtCore
import App

// In-app modal for direct file upload & isolated per-user upload/summary history.
Rectangle {
    id: modal
    anchors.fill: parent
    color: "#D90B0D13"  // semi-transparent dark backdrop
    z: 998

    signal closed()

    property int activeTab: 0  // 0: Upload, 1: History

    FileDialog {
        id: nativeFileDialog
        title: "Select Document from Computer"
        currentFolder: StandardPaths.writableLocation(StandardPaths.DocumentsLocation)
        nameFilters: ["All Supported Documents (*.pdf *.docx *.rtf *.txt *.md *.png *.jpg *.jpeg *.webp)", "PDF Files (*.pdf)", "Word Documents (*.docx)", "Text Files (*.txt *.md)", "Images (*.png *.jpg *.jpeg *.webp)"]
        onAccepted: {
            bridge.loadDocument(selectedFile.toString());
            modal.closed();
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: modal.closed()
    }

    Rectangle {
        id: card
        width: Math.min(parent.width - 40, 680)
        height: Math.min(parent.height - 60, 560)
        anchors.centerIn: parent
        color: Theme.block
        radius: 12
        border.color: Theme.line2
        border.width: 1

        MouseArea {
            anchors.fill: parent
            // Prevent clicks inside card from closing modal
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            // Header Row: Title + Close Button
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 8
                    height: 24
                    color: Theme.accent
                    radius: 2
                }

                Text {
                    text: "DOCUMENT MANAGER"
                    color: Theme.ink
                    font.family: Theme.serif
                    font.pixelSize: 18
                    font.weight: Font.Bold
                    font.letterSpacing: 1.5
                }

                Item {
                    Layout.fillWidth: true
                }

                // Close Button
                Rectangle {
                    width: 28
                    height: 28
                    radius: 4
                    color: "transparent"
                    border.color: Theme.line2
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: Theme.faint
                        font.pixelSize: 13
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: modal.closed()
                    }
                }
            }

            // Tab Selector
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Rectangle {
                    Layout.fillWidth: true
                    height: 32
                    radius: 6
                    color: modal.activeTab === 0 ? Theme.accent : Theme.pageBg
                    border.color: modal.activeTab === 0 ? Theme.accent : Theme.line2
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "📁 UPLOAD FILE"
                        color: modal.activeTab === 0 ? Theme.onAccent : Theme.text
                        font.family: Theme.mono
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: modal.activeTab = 0
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 32
                    radius: 6
                    color: modal.activeTab === 1 ? Theme.accent : Theme.pageBg
                    border.color: modal.activeTab === 1 ? Theme.accent : Theme.line2
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "🕒 MY HISTORY (" + bridge.userHistory.length + ")"
                        color: modal.activeTab === 1 ? Theme.onAccent : Theme.text
                        font.family: Theme.mono
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: modal.activeTab = 1
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.line2
            }

            // Tab 0: Upload View
            ColumnLayout {
                visible: modal.activeTab === 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 16

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 10
                    color: Theme.pageBg
                    border.color: Theme.line2
                    border.width: 1

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 12

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "📄"
                            font.pixelSize: 42
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Upload or Select Document"
                            color: Theme.ink
                            font.family: Theme.serif
                            font.pixelSize: 16
                            font.weight: Font.Bold
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Supported: PDF · DOCX · RTF · TXT · MD · PNG · JPG"
                            color: Theme.faint
                            font.family: Theme.mono
                            font.pixelSize: 11
                        }

                        Item { height: 8 }

                        RowLayout {
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 12

                            ConsoleButton {
                                text: "BROWSE FILES"
                                primary: true
                                onClicked: nativeFileDialog.open()
                            }
                        }
                    }
                }

                Text {
                    text: "👤 Authenticated as: " + (bridge.currentUser ? bridge.currentUser : "admin") + " (All uploads and summaries are saved to your private history)"
                    color: Theme.dim
                    font.family: Theme.mono
                    font.pixelSize: 10
                }
            }

            // Tab 1: User History View
            ColumnLayout {
                visible: modal.activeTab === 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ListView {
                        id: historyList
                        width: parent.width
                        spacing: 8
                        model: bridge.userHistory

                        delegate: Rectangle {
                            width: historyList.width
                            height: delegateCol.implicitHeight + 20
                            radius: 8
                            color: Theme.pageBg
                            border.color: Theme.line2
                            border.width: 1

                            ColumnLayout {
                                id: delegateCol
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Text {
                                        text: modelData.filename ? modelData.filename : "Untitled Document"
                                        color: Theme.ink
                                        font.family: Theme.mono
                                        font.pixelSize: 13
                                        font.weight: Font.Bold
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }

                                    Rectangle {
                                        height: 18
                                        width: typeText.implicitWidth + 12
                                        radius: 3
                                        color: Theme.block
                                        border.color: Theme.line2
                                        border.width: 1
                                        Text {
                                            id: typeText
                                            anchors.centerIn: parent
                                            text: (modelData.summaryType ? modelData.summaryType : "summary").toUpperCase()
                                            color: Theme.accent
                                            font.family: Theme.mono
                                            font.pixelSize: 9
                                            font.weight: Font.Bold
                                        }
                                    }

                                    Text {
                                        text: modelData.timestamp ? modelData.timestamp : ""
                                        color: Theme.faint
                                        font.family: Theme.mono
                                        font.pixelSize: 10
                                    }
                                }

                                Text {
                                    text: modelData.summaryText ? modelData.summaryText : "No summary text."
                                    color: Theme.text
                                    font.family: Theme.body
                                    font.pixelSize: 12
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Text {
                                        text: (modelData.wordCount ? modelData.wordCount : 0) + " words"
                                        color: Theme.dim
                                        font.family: Theme.mono
                                        font.pixelSize: 10
                                    }

                                    Item { Layout.fillWidth: true }

                                    ConsoleButton {
                                        text: "LOAD SUMMARY"
                                        primary: true
                                        onClicked: {
                                            bridge.loadHistoryItem(modelData.id);
                                            modal.closed();
                                        }
                                    }

                                    ConsoleButton {
                                        text: "DELETE"
                                        onClicked: {
                                            bridge.deleteHistoryItem(modelData.id);
                                        }
                                    }
                                }
                            }
                        }

                        // Empty State
                        Rectangle {
                            visible: bridge.userHistory.length === 0
                            anchors.centerIn: parent
                            width: parent.width
                            height: 160
                            color: "transparent"

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 8

                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: "🕒"
                                    font.pixelSize: 32
                                }

                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: "No upload history for " + (bridge.currentUser ? bridge.currentUser : "this user") + "."
                                    color: Theme.faint
                                    font.family: Theme.mono
                                    font.pixelSize: 12
                                }

                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: "Upload a document to start building your private history."
                                    color: Theme.dim
                                    font.family: Theme.body
                                    font.pixelSize: 11
                                }
                            }
                        }
                    }
                }

                // History bottom bar
                RowLayout {
                    Layout.fillWidth: true
                    visible: bridge.userHistory.length > 0

                    Item { Layout.fillWidth: true }

                    ConsoleButton {
                        text: "CLEAR ALL HISTORY"
                        onClicked: bridge.clearUserHistory()
                    }
                }
            }
        }
    }
}
