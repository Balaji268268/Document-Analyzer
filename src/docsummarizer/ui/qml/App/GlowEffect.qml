import QtQuick
import QtQuick.Shapes
import App

// A soft accent halo, drawn with a radial gradient so it renders on the software
// backend too (no GPU/shader dependency — better for a portable app). Place it
// behind an element, sized a little larger.
Shape {
    id: glow
    property color glowColor: Theme.accent
    property real intensity: 0.35

    antialiasing: true
    preferredRendererType: Shape.CurveRenderer
    ShapePath {
        strokeWidth: -1
        fillGradient: RadialGradient {
            centerX: glow.width / 2
            centerY: glow.height / 2
            focalX: glow.width / 2
            focalY: glow.height / 2
            centerRadius: Math.max(glow.width, glow.height) * 0.55
            GradientStop {
                position: 0.0
                color: Qt.rgba(glow.glowColor.r, glow.glowColor.g, glow.glowColor.b, glow.intensity)
            }
            GradientStop {
                position: 0.6
                color: Qt.rgba(glow.glowColor.r, glow.glowColor.g, glow.glowColor.b, glow.intensity * 0.25)
            }
            GradientStop {
                position: 1.0
                color: "transparent"
            }
        }
        startX: 0
        startY: 0
        PathLine {
            x: glow.width
            y: 0
        }
        PathLine {
            x: glow.width
            y: glow.height
        }
        PathLine {
            x: 0
            y: glow.height
        }
    }
}
