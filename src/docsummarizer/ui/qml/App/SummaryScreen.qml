import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import App

// Summary view: doc header + summary-type segmented + two panes. Left = the
// full extracted source; right = the distilled summary. Clicking a point
// highlights the source sentence it was grounded in (provenance), using the
// citation offsets the bridge marshalled from the StructuredSummary.
Item {
    id: screen

    property var summary: ({"summaryType": "detailed", "lead": "", "points": [], "sections": ({}), "text": ""})
    property int activePoint: -1
    property int hlStart: -1
    property int hlEnd: -1

    function cssRgba(c, a) {
        return "rgba(" + Math.round(c.r * 255) + "," + Math.round(c.g * 255) + "," + Math.round(c.b * 255) + "," + a + ")";
    }

    function escapeHtml(s) {
        return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function renderSource() {
        var raw = bridge.extractedText;
        if (raw === "")
            return "";
        if (screen.hlStart >= 0 && screen.hlEnd > screen.hlStart) {
            var pre = escapeHtml(raw.substring(0, screen.hlStart));
            var hit = escapeHtml(raw.substring(screen.hlStart, screen.hlEnd));
            var post = escapeHtml(raw.substring(screen.hlEnd));
            var style = "background-color:" + cssRgba(Theme.accent, 0.18) + ";color:" + cssRgba(Theme.accent2, 1.0);
            return pre + "<span style='" + style + "'>" + hit + "</span>" + post;
        }
        return escapeHtml(raw);
    }

    function trace(point, index) {
        screen.activePoint = index;
        if (point.hasCitation) {
            screen.hlStart = point.start;
            screen.hlEnd = point.end;
        } else {
            screen.hlStart = -1;
            screen.hlEnd = -1;
        }
        srcText.text = screen.renderSource();
    }

    Connections {
        target: bridge
        function onSummaryReady(variant) {
            screen.summary = variant;
            screen.activePoint = -1;
            screen.hlStart = -1;
            screen.hlEnd = -1;
            srcText.text = screen.renderSource();
        }
        function onDocChanged() {
            srcText.text = screen.renderSource();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 14

        // -- Header -------------------------------------------------------- //
        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            ColumnLayout {
                spacing: 4
                Text {
                    text: bridge.currentFileName !== "" ? bridge.currentFileName : "No document loaded"
                    color: Theme.ink
                    font.family: Theme.serif
                    font.pixelSize: 28
                }
                Text {
                    text: bridge.hasDoc ? "EXTRACTED · READY" : "Drop or open a document to summarize"
                    color: Theme.faint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1.2
                }
            }
            Item {
                Layout.fillWidth: true
            }
            SegmentedControl {
                options: bridge.summaryTypes
                current: bridge.summaryType
                onSelected: value => bridge.setSummaryType(value)
            }
        }

        // -- Two panes ----------------------------------------------------- //
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            Rectangle {
                Layout.preferredWidth: parent.width * 0.45
                Layout.fillHeight: true
                radius: 3
                color: Theme.srcPane
                border.width: 1
                border.color: Theme.line
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10
                    Text {
                        text: "SOURCE"
                        color: Theme.label
                        font.family: Theme.ui
                        font.pixelSize: 10
                        font.letterSpacing: 2.2
                    }
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: width
                        contentHeight: srcText.implicitHeight
                        TextEdit {
                            id: srcText
                            width: parent.width
                            readOnly: true
                            wrapMode: Text.WordWrap
                            selectByMouse: false
                            textFormat: TextEdit.RichText
                            color: Theme.text
                            font.family: Theme.body
                            font.pixelSize: 15
                            text: screen.renderSource()
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 3
                color: "transparent"
                border.width: 1
                border.color: Theme.line
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10
                    Text {
                        text: "DISTILLED · " + String(screen.summary.summaryType).toUpperCase()
                        color: Theme.label
                        font.family: Theme.ui
                        font.pixelSize: 10
                        font.letterSpacing: 2.2
                    }
                    Text {
                        visible: String(screen.summary.lead) !== ""
                        Layout.fillWidth: true
                        text: screen.summary.lead
                        wrapMode: Text.WordWrap
                        color: Theme.ink
                        font.family: Theme.serif
                        font.pixelSize: 19
                        lineHeight: 1.3
                    }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 8
                        model: screen.summary.points
                        delegate: Rectangle {
                            required property var modelData
                            required property int index
                            width: ListView.view ? ListView.view.width : 0
                            height: pointCol.implicitHeight + 22
                            radius: 3
                            color: index === screen.activePoint ? Theme.navOnBg : "transparent"
                            border.width: 1
                            border.color: index === screen.activePoint ? Theme.navOnRing : Theme.line
                            ColumnLayout {
                                id: pointCol
                                x: 12
                                y: 11
                                width: parent.width - 24
                                spacing: 4
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.text
                                    color: Theme.inkSoft
                                    font.family: Theme.body
                                    font.pixelSize: 13
                                    wrapMode: Text.WordWrap
                                }
                                Text {
                                    visible: modelData.hasCitation
                                    text: "▸ TRACE TO SOURCE"
                                    color: Theme.accent
                                    font.family: Theme.mono
                                    font.pixelSize: 9
                                    font.letterSpacing: 1
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: screen.trace(modelData, index)
                            }
                        }
                    }
                }
            }
        }

        // -- Footer -------------------------------------------------------- //
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Text {
                text: bridge.busy ? "● GENERATING…" : (bridge.statusText !== "" ? "● " + bridge.statusText : "")
                color: Theme.statusColorFor(bridge.statusColor)
                font.family: Theme.mono
                font.pixelSize: 10
                font.letterSpacing: 1
            }
            Item {
                Layout.fillWidth: true
            }
            Button {
                text: "Regenerate"
                enabled: bridge.canSummarize && !bridge.busy
                onClicked: bridge.regenerate()
            }
            Button {
                text: "Summarize"
                enabled: bridge.canSummarize && !bridge.busy
                onClicked: bridge.summarize()
            }
        }
    }
}
