import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import App

// Application shell: persistent top bar + LCARS rail + a screen Loader, with the
// first-run download overlay on top. The 1240px design width is the minimum;
// the window is resizable.
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
    property bool forceFirstRun: false

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
                sourceComponent: {
                    switch (win.activeScreen) {
                    case "extract":
                        return extractComponent;
                    case "batch":
                        return batchComponent;
                    case "config":
                        return configComponent;
                    default:
                        return summaryComponent;
                    }
                }
            }
        }
    }

    Component {
        id: summaryComponent
        SummaryScreen {}
    }
    Component {
        id: extractComponent
        ExtractScreen {}
    }
    Component {
        id: batchComponent
        BatchScreen {}
    }
    Component {
        id: configComponent
        ConfigScreen {
            onReinitialize: win.forceFirstRun = true
        }
    }

    // One-time model download, shown on first run or when re-initialized.
    FirstRunOverlay {
        anchors.fill: parent
        shown: !bridge.modelDownloaded || win.forceFirstRun
        visible: shown
        onEnter: {
            win.forceFirstRun = false;
            bridge.checkModel();
        }
    }
}
