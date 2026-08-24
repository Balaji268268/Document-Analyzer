import QtQuick
import App

// A sleek console panel with subtle border and fill (100% software & hardware backend safe)
Rectangle {
    id: panel
    property real cut: 14
    property color fill: "transparent"
    property color stroke: Theme.line
    property real strokeWidth: 1
    default property alias content: holder.data

    radius: 4
    color: panel.fill
    border.width: panel.strokeWidth
    border.color: panel.stroke

    Item {
        id: holder
        anchors.fill: parent
    }
}
