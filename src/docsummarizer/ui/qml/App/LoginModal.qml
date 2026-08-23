import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import App

// Modal login dialog presented over the application until the user authenticates.
Rectangle {
    id: modal
    anchors.fill: parent
    color: "#D90B0D13"  // semi-transparent dark backdrop
    z: 999  // keep above all screen content

    property string errorMessage: ""

    MouseArea {
        anchors.fill: parent
        // Block mouse click events from passing through to underlying UI
    }

    Rectangle {
        id: card
        width: Math.min(parent.width - 32, 420)
        height: column.implicitHeight + 48
        anchors.centerIn: parent
        color: Theme.cardBg
        radius: 12
        border.color: Theme.borderSubtle
        border.width: 1

        ColumnLayout {
            id: column
            anchors.fill: parent
            anchors.margins: 28
            spacing: 16

            // Header Title
            RowLayout {
                spacing: 12
                Rectangle {
                    width: 8
                    height: 24
                    color: Theme.accent
                    radius: 2
                }
                Text {
                    text: "AUTHENTICATION"
                    color: Theme.fgPrimary
                    font.family: Theme.head
                    font.pixelSize: 20
                    font.weight: Font.Bold
                    font.letterSpacing: 2
                }
            }

            Text {
                text: "Please sign in to access DocSummarizer workspace."
                color: Theme.fgSecondary
                font.family: Theme.body
                font.pixelSize: 13
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.borderSubtle
            }

            // Username Input
            ColumnLayout {
                spacing: 6
                Text {
                    text: "USERNAME"
                    color: Theme.faint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                }
                TextField {
                    id: userInput
                    Layout.fillWidth: true
                    placeholderText: "admin"
                    text: "admin"
                    color: Theme.fgPrimary
                    font.family: Theme.body
                    font.pixelSize: 14
                    background: Rectangle {
                        color: Theme.fieldBg
                        radius: 6
                        border.color: userInput.activeFocus ? Theme.accent : Theme.borderSubtle
                        border.width: 1
                    }
                    onAccepted: passInput.forceActiveFocus()
                }
            }

            // Password Input
            ColumnLayout {
                spacing: 6
                Text {
                    text: "PASSWORD"
                    color: Theme.faint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                }
                TextField {
                    id: passInput
                    Layout.fillWidth: true
                    placeholderText: "admin"
                    text: "admin"
                    echoMode: TextInput.Password
                    color: Theme.fgPrimary
                    font.family: Theme.body
                    font.pixelSize: 14
                    background: Rectangle {
                        color: Theme.fieldBg
                        radius: 6
                        border.color: passInput.activeFocus ? Theme.accent : Theme.borderSubtle
                        border.width: 1
                    }
                    onAccepted: submitLogin()
                }
            }

            // Error Message Display
            Text {
                visible: modal.errorMessage !== ""
                text: modal.errorMessage
                color: Theme.dark ? "#FF6B6B" : "#D32F2F"
                font.family: Theme.body
                font.pixelSize: 13
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            // Action Button
            ConsoleButton {
                Layout.fillWidth: true
                text: "SIGN IN"
                primary: true
                onClicked: submitLogin()
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Default credentials: admin / admin"
                color: Theme.faint
                font.family: Theme.mono
                font.pixelSize: 11
            }
        }
    }

    function submitLogin() {
        modal.errorMessage = "";
        var success = bridge.authenticate(userInput.text, passInput.text);
        if (!success) {
            modal.errorMessage = "Invalid username or password. Try 'admin' / 'admin'.";
        }
    }
}
