import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import App

// Application shell: persistent top bar + LCARS rail + a screen Loader. The
// 1240px design width is the minimum; the window is resizable.
ApplicationWindow {
    id: win
    visible: true
    width: 1240
    height: 760
    minimumWidth: 1000
    minimumHeight: 640
    title: "DocSummarizer — Abstract Console"
    color: Theme.pageBg

    // NB: not "screen" — ApplicationWindow already defines a `screen` (QScreen).
    property string activeScreen: "summary"

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
                currentScreen: win.activeScreen
                onNavigate: name => win.activeScreen = name
            }

            Loader {
                Layout.fillWidth: true
                Layout.fillHeight: true
                sourceComponent: win.activeScreen === "summary" ? summaryComponent : placeholderComponent
            }
        }
    }

    Component {
        id: summaryComponent
        SummaryScreen {}
    }

    // Extract / Batch / Config / First-run arrive in Phase 3.
    Component {
        id: placeholderComponent
        Item {
            Text {
                anchors.centerIn: parent
                text: win.activeScreen.toUpperCase() + " — coming soon"
                color: Theme.faint
                font.family: Theme.mono
                font.pixelSize: 14
                font.letterSpacing: 2
            }
        }
    }
}
