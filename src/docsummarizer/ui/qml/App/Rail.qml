import QtQuick
import QtQuick.Layouts
import App

// LCARS-style left navigation rail. Emits navigate(name) on click.
Rectangle {
    id: rail
    width: 120
    color: "transparent"

    property string currentScreen: "summary"
    signal navigate(string name)

    readonly property var items: [
        {"name": "summary", "label": "Summary"},
        {"name": "extract", "label": "Extract"},
        {"name": "batch", "label": "Batch"},
        {"name": "config", "label": "Config"}
    ]

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        // LCARS elbow accent block.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            radius: 4
            color: Theme.accent
            Text {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 8
                text: "01"
                color: Theme.onAccent
                font.family: Theme.mono
                font.pixelSize: 11
            }
        }

        Repeater {
            model: rail.items
            delegate: Rectangle {
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                radius: 3
                color: modelData.name === rail.currentScreen ? Theme.navOnBg : Theme.block
                border.width: 1
                border.color: modelData.name === rail.currentScreen ? Theme.navOnRing : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: modelData.label
                    color: modelData.name === rail.currentScreen ? Theme.label2 : Theme.navOff
                    font.family: Theme.ui
                    font.pixelSize: 12
                    font.letterSpacing: 0.4
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: rail.navigate(modelData.name)
                }
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
