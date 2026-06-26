import QtQuick
import QtQuick.Shapes
import App

// A hexagon marker (clip-path polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%))
// with an optional centered glyph — used for the logo, key-point numbers, batch rows.
Item {
    id: hex
    property real size: 24
    property string glyph: ""
    property real glyphSize: 10
    property bool accentInner: false
    property color fill: Theme.hexBg
    property color stroke: Theme.line2

    implicitWidth: size
    implicitHeight: size

    Shape {
        anchors.fill: parent
        antialiasing: true
        ShapePath {
            fillColor: hex.fill
            strokeColor: hex.stroke
            strokeWidth: 1
            startX: hex.size / 2
            startY: 0
            PathLine {
                x: hex.size
                y: hex.size * 0.25
            }
            PathLine {
                x: hex.size
                y: hex.size * 0.75
            }
            PathLine {
                x: hex.size / 2
                y: hex.size
            }
            PathLine {
                x: 0
                y: hex.size * 0.75
            }
            PathLine {
                x: 0
                y: hex.size * 0.25
            }
            PathLine {
                x: hex.size / 2
                y: 0
            }
        }
    }
    Text {
        anchors.centerIn: parent
        visible: hex.glyph !== ""
        text: hex.glyph
        color: hex.accentInner ? Theme.accent : Theme.label2
        font.family: Theme.mono
        font.pixelSize: hex.glyphSize
    }
}
