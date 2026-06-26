import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import App

// Raw extraction view: shows the verbatim text the parser pulled out of the
// loaded document, with a live case-insensitive search that highlights every
// match inline. Mirrors SummaryScreen's escapeHtml/cssRgba idioms; the feed is
// a read-only RichText TextEdit so highlights render as <span> backgrounds.
Item {
    id: screen

    property int matchCount: 0

    function cssRgba(c, a) {
        return "rgba(" + Math.round(c.r * 255) + "," + Math.round(c.g * 255) + "," + Math.round(c.b * 255) + "," + a + ")";
    }

    function escapeHtml(s) {
        return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function renderFeed() {
        var raw = bridge.extractedText;
        var term = search.text;
        if (raw === "") {
            screen.matchCount = 0;
            return "";
        }
        if (term === "") {
            screen.matchCount = 0;
            return escapeHtml(raw);
        }
        var lowerRaw = raw.toLowerCase();
        var lowerTerm = term.toLowerCase();
        var style = "background-color:" + cssRgba(Theme.accent, 0.28) + ";color:" + cssRgba(Theme.onAccent, 1.0);
        var out = "";
        var from = 0;
        var count = 0;
        var idx = lowerRaw.indexOf(lowerTerm, from);
        while (idx !== -1) {
            out += escapeHtml(raw.substring(from, idx));
            var hit = escapeHtml(raw.substring(idx, idx + term.length));
            out += "<span style='" + style + "'>" + hit + "</span>";
            count += 1;
            from = idx + term.length;
            idx = lowerRaw.indexOf(lowerTerm, from);
        }
        out += escapeHtml(raw.substring(from));
        screen.matchCount = count;
        return out;
    }

    function refresh() {
        feed.text = screen.renderFeed();
    }

    Component.onCompleted: screen.refresh()

    Connections {
        target: bridge
        function onDocChanged() {
            screen.refresh();
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
                    text: "RAW EXTRACTION"
                    color: Theme.label
                    font.family: Theme.ui
                    font.pixelSize: 10
                    font.letterSpacing: 2.2
                }
                Text {
                    text: bridge.currentFileName !== "" ? bridge.currentFileName : "No document loaded"
                    color: Theme.ink
                    font.family: Theme.serif
                    font.pixelSize: 28
                }
                Text {
                    text: {
                        var t = bridge.extractedText;
                        return t.split(/\s+/).filter(Boolean).length + " WORDS · " + t.length + " CHARS";
                    }
                    color: Theme.faint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1.2
                }
            }

            Item {
                Layout.fillWidth: true
            }

            ColumnLayout {
                spacing: 6
                RowLayout {
                    spacing: 10
                    Rectangle {
                        Layout.preferredWidth: 220
                        Layout.preferredHeight: 34
                        radius: 3
                        color: Theme.srcPane
                        border.width: 1
                        border.color: search.activeFocus ? Theme.ring : Theme.line
                        TextField {
                            id: search
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            verticalAlignment: TextInput.AlignVCenter
                            placeholderText: "Search…"
                            placeholderTextColor: Theme.dim
                            color: Theme.inkSoft
                            font.family: Theme.body
                            font.pixelSize: 13
                            background: Item {}
                            onTextChanged: screen.refresh()
                        }
                    }
                    Button {
                        text: "Copy All"
                        enabled: bridge.extractedText !== ""
                        onClicked: {
                            feed.selectAll();
                            feed.copy();
                            feed.deselect();
                        }
                    }
                }
                Text {
                    Layout.alignment: Qt.AlignRight
                    text: screen.matchCount + " MATCHES"
                    color: screen.matchCount > 0 ? Theme.accent : Theme.faint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1
                }
            }
        }

        // -- Feed ---------------------------------------------------------- //
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 3
            color: Theme.srcPane
            border.width: 1
            border.color: Theme.line

            Flickable {
                id: flick
                anchors.fill: parent
                anchors.margins: 16
                clip: true
                contentWidth: width
                contentHeight: feed.implicitHeight

                TextEdit {
                    id: feed
                    width: parent.width
                    readOnly: true
                    selectByMouse: true
                    wrapMode: Text.WordWrap
                    textFormat: TextEdit.RichText
                    color: Theme.text
                    font.family: Theme.body
                    font.pixelSize: 15
                }
            }
        }

        // -- Footer -------------------------------------------------------- //
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Text {
                text: bridge.statusText !== "" ? "● " + bridge.statusText : ""
                color: Theme.statusColorFor(bridge.statusColor)
                font.family: Theme.mono
                font.pixelSize: 10
                font.letterSpacing: 1
            }
            Item {
                Layout.fillWidth: true
            }
            Button {
                text: "Summarize"
                enabled: bridge.canSummarize && !bridge.busy
                onClicked: bridge.summarize()
            }
        }
    }
}
