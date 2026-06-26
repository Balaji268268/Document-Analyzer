import QtQuick
import QtQuick.Layouts
import App

// Persistent top bar: identity + secure badge + live model/compute readout +
// theme toggle. Model strings come from the bridge (driven by DEFAULT_MODEL),
// never hardcoded.
Rectangle {
    id: bar
    height: 66
    color: "transparent"

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 22
        anchors.rightMargin: 22
        spacing: 16

        ColumnLayout {
            spacing: 0
            Text {
                text: "DocSummarizer"
                color: Theme.ink
                font.family: Theme.serif
                font.pixelSize: 17
                font.weight: Font.DemiBold
            }
            Text {
                text: "ABSTRACT CONSOLE · v2.4"
                color: Theme.faint
                font.family: Theme.mono
                font.pixelSize: 9
                font.letterSpacing: 2
            }
        }

        Rectangle {
            Layout.preferredWidth: badge.implicitWidth + 28
            Layout.preferredHeight: 26
            radius: 2
            color: Qt.rgba(0.78, 0.66, 0.42, 0.05)
            border.width: 1
            border.color: Theme.brass
            Row {
                id: badge
                anchors.centerIn: parent
                spacing: 8
                Rectangle {
                    width: 6
                    height: 6
                    radius: 3
                    anchors.verticalCenter: parent.verticalCenter
                    color: Theme.brassDot
                }
                Text {
                    text: "SECURE · AIRGAPPED · LOCAL CORE"
                    color: Theme.brass
                    font.family: Theme.ui
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                }
            }
        }

        Item {
            Layout.fillWidth: true
        }

        Text {
            text: bridge.modelName.toUpperCase() + "  |  " + bridge.computeLabel + "  |  ONLINE·LOCAL"
            color: Theme.faint
            font.family: Theme.mono
            font.pixelSize: 10
            font.letterSpacing: 1
        }

        Rectangle {
            Layout.preferredWidth: 30
            Layout.preferredHeight: 30
            radius: 2
            color: Theme.block
            border.width: 1
            border.color: Theme.line2
            Text {
                anchors.centerIn: parent
                text: Theme.dark ? "☾" : "☀"
                color: Theme.accent
                font.pixelSize: 15
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    Theme.dark = !Theme.dark;
                    bridge.setAppearance(Theme.dark ? "Dark" : "Light");
                }
            }
        }
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: Theme.line
    }
}
