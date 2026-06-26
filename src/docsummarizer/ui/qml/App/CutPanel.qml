import QtQuick
import QtQuick.Shapes
import App

// A panel with clipped corners (top-right + bottom-left notch) — the signature
// "instrument console" silhouette. Children render on top of the cut surface.
Item {
    id: panel
    property real cut: 14
    property color fill: "transparent"
    property color stroke: Theme.line
    property real strokeWidth: 1
    default property alias content: holder.data

    Shape {
        anchors.fill: parent
        antialiasing: true
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: panel.fill
            strokeColor: panel.stroke
            strokeWidth: panel.strokeWidth
            startX: panel.cut
            startY: 0
            PathLine {
                x: panel.width
                y: 0
            }
            PathLine {
                x: panel.width
                y: panel.height - panel.cut
            }
            PathLine {
                x: panel.width - panel.cut
                y: panel.height
            }
            PathLine {
                x: 0
                y: panel.height
            }
            PathLine {
                x: 0
                y: panel.cut
            }
            PathLine {
                x: panel.cut
                y: 0
            }
        }
    }
    Item {
        id: holder
        anchors.fill: parent
    }
}
