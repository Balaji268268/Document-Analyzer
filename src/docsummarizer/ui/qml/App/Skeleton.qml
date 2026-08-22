import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import App

// Smooth, non-interruptive progress loader for document summarization.
// Surfaces real-time status messages, animated progress bar, percentage metrics,
// and shimmering preview placeholders while the local LLM generates.
ColumnLayout {
    id: skel
    spacing: 16
    opacity: visible ? 1.0 : 0.0

    Behavior on opacity {
        NumberAnimation {
            duration: 200
        }
    }

    // -- Header: Live Status + Spinning Scanner + Percentage ------------------ //
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: statusRow.implicitHeight + 20
        radius: 4
        color: Theme.block
        border.width: 1
        border.color: Theme.line2

        RowLayout {
            id: statusRow
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            spacing: 12

            Hex {
                id: scanner
                size: 28
                glyph: "✦"
                glyphSize: 12
                accentInner: true

                NumberAnimation on rotation {
                    running: skel.visible
                    loops: Animation.Infinite
                    from: 0
                    to: 360
                    duration: 3000
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3

                RowLayout {
                    spacing: 8
                    Rectangle {
                        width: 7
                        height: 7
                        radius: 3.5
                        color: Theme.accent
                        SequentialAnimation on opacity {
                            running: skel.visible
                            loops: Animation.Infinite
                            NumberAnimation { to: 0.3; duration: 600 }
                            NumberAnimation { to: 1.0; duration: 600 }
                        }
                    }
                    Text {
                        text: "SUMMARIZING DOCUMENT"
                        color: Theme.accent
                        font.family: Theme.ui
                        font.pixelSize: 10
                        font.letterSpacing: 1.5
                        font.weight: Font.Medium
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: bridge.statusText !== "" ? bridge.statusText.toUpperCase() : "PROCESSING DOCUMENT…"
                    color: Theme.inkSoft
                    font.family: Theme.mono
                    font.pixelSize: 11
                    font.letterSpacing: 1
                    elide: Text.ElideRight
                }
            }

            Text {
                text: Math.round(bridge.summaryProgress) + "%"
                color: Theme.accent2
                font.family: Theme.mono
                font.pixelSize: 22
                font.weight: Font.Bold
                Layout.alignment: Qt.AlignVCenter
            }
        }
    }

    // -- Smooth Animated Progress Bar ---------------------------------------- //
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 6
        radius: 3
        color: Theme.block
        border.width: 1
        border.color: Theme.line
        clip: true

        Rectangle {
            id: fillBar
            height: parent.height
            radius: 3
            width: parent.width * Math.max(0.04, Math.min(1.0, bridge.summaryProgress / 100.0))

            Behavior on width {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.OutCubic
                }
            }

            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: Theme.accentDeep }
                GradientStop { position: 0.5; color: Theme.accent }
                GradientStop { position: 1.0; color: Theme.accent2 }
            }
        }
    }

    // -- Engine Details Badge ------------------------------------------------ //
    RowLayout {
        Layout.fillWidth: true
        spacing: 12

        Rectangle {
            radius: 2
            color: Theme.navOnBg
            border.width: 1
            border.color: Theme.ring
            Layout.preferredHeight: 20
            Layout.preferredWidth: engineText.implicitWidth + 16

            RowLayout {
                anchors.centerIn: parent
                spacing: 6
                Rectangle {
                    width: 5
                    height: 5
                    radius: 2.5
                    color: Theme.brassDot
                }
                Text {
                    id: engineText
                    text: "LOCAL ENGINE · " + bridge.modelName.toUpperCase() + " · " + bridge.computeLabel
                    color: Theme.brass
                    font.family: Theme.mono
                    font.pixelSize: 9
                    font.letterSpacing: 1
                }
            }
        }

        Item { Layout.fillWidth: true }

        Text {
            text: "AIRGAPPED · ZERO CLOUD EXFILTRATION"
            color: Theme.dim
            font.family: Theme.mono
            font.pixelSize: 9
            font.letterSpacing: 1
        }
    }

    // -- Shimmering Placeholder Cards --------------------------------------- //
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 10

        // Lead overview skeleton card
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 70
            radius: 3
            color: Theme.kpRest
            border.width: 1
            border.color: Theme.line
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Repeater {
                    model: [1.0, 0.85, 0.6]
                    delegate: Rectangle {
                        required property real modelData
                        Layout.fillWidth: true
                        Layout.rightMargin: parent.width * (1.0 - modelData)
                        Layout.preferredHeight: 12
                        radius: 2
                        color: Theme.block
                        clip: true

                        Rectangle {
                            height: parent.height
                            width: parent.width * 0.4
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "transparent" }
                                GradientStop { position: 0.5; color: Theme.line2 }
                                GradientStop { position: 1.0; color: "transparent" }
                            }
                            NumberAnimation on x {
                                running: skel.visible
                                loops: Animation.Infinite
                                from: -parent.width * 0.4
                                to: parent.width
                                duration: 1300
                            }
                        }
                    }
                }
            }
        }

        // Key point cards skeleton repeater
        Repeater {
            model: 3
            delegate: Rectangle {
                required property int index
                Layout.fillWidth: true
                implicitHeight: 52
                radius: 3
                color: Theme.kpRest
                border.width: 1
                border.color: Theme.line
                clip: true

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12

                    Hex {
                        size: 24
                        glyph: String(index + 1).padStart(2, "0")
                        glyphSize: 10
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.rightMargin: [40, 100, 70][index]
                            Layout.preferredHeight: 12
                            radius: 2
                            color: Theme.block
                            clip: true

                            Rectangle {
                                height: parent.height
                                width: parent.width * 0.4
                                gradient: Gradient {
                                    orientation: Gradient.Horizontal
                                    GradientStop { position: 0.0; color: "transparent" }
                                    GradientStop { position: 0.5; color: Theme.line2 }
                                    GradientStop { position: 1.0; color: "transparent" }
                                }
                                NumberAnimation on x {
                                    running: skel.visible
                                    loops: Animation.Infinite
                                    from: -parent.width * 0.4
                                    to: parent.width
                                    duration: 1300 + index * 150
                                }
                            }
                        }

                        Rectangle {
                            width: 90
                            height: 10
                            radius: 2
                            color: Theme.block
                        }
                    }
                }
            }
        }
    }
}
