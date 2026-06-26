// Item-rooted mirror of Main.qml's shell, for offscreen rendering via QQuickView
// (an ApplicationWindow can't be grabbed the same way). Used only by render_qml.py.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Shapes
import App

Rectangle {
    id: root
    width: 1240
    height: 820
    color: Theme.pageBg

    property string screen: "summary"
    property bool firstRun: false
    property bool darkTheme: true
    onDarkThemeChanged: Theme.dark = darkTheme
    Component.onCompleted: Theme.dark = root.darkTheme

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: -1
            fillGradient: RadialGradient {
                centerX: root.width / 2
                centerY: -root.height * 0.18
                centerRadius: root.width * 0.95
                focalX: root.width / 2
                focalY: -root.height * 0.18
                GradientStop {
                    position: 0.0
                    color: Theme.pageTop
                }
                GradientStop {
                    position: 0.56
                    color: Theme.pageBg
                }
                GradientStop {
                    position: 1.0
                    color: Theme.pageBottom
                }
            }
            startX: 0
            startY: 0
            PathLine {
                x: root.width
                y: 0
            }
            PathLine {
                x: root.width
                y: root.height
            }
            PathLine {
                x: 0
                y: root.height
            }
        }
    }
    Canvas {
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0, 0, width, height);
            ctx.strokeStyle = Theme.dark ? "rgba(111,195,216,0.03)" : "rgba(40,80,100,0.05)";
            ctx.lineWidth = 1;
            for (var x = 40; x < width; x += 40) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }
            for (var y = 40; y < height; y += 40) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        TopBar {
            Layout.fillWidth: true
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            Rail {
                Layout.fillHeight: true
                currentScreen: root.screen
            }
            Loader {
                Layout.fillWidth: true
                Layout.fillHeight: true
                sourceComponent: {
                    switch (root.screen) {
                    case "extract":
                        return extractC;
                    case "batch":
                        return batchC;
                    case "config":
                        return configC;
                    default:
                        return summaryC;
                    }
                }
            }
        }
    }
    Component {
        id: summaryC
        SummaryScreen {}
    }
    Component {
        id: extractC
        ExtractScreen {}
    }
    Component {
        id: batchC
        BatchScreen {}
    }
    Component {
        id: configC
        ConfigScreen {}
    }
    FirstRunOverlay {
        anchors.fill: parent
        shown: root.firstRun
        visible: shown
    }

    Toast {
        id: toast
    }
    Connections {
        target: bridge
        function onToast(message) {
            toast.show(message);
        }
    }
}
