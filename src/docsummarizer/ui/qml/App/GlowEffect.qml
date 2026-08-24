import QtQuick
import App

// A soft accent halo using a clean rounded rectangle (software backend safe)
Rectangle {
    id: glow
    property color glowColor: Theme.accent
    property real intensity: 0.35

    radius: 4
    color: Qt.rgba(glow.glowColor.r, glow.glowColor.g, glow.glowColor.b, glow.intensity * 0.35)
}
