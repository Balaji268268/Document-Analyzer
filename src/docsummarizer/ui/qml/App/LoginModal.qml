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

    property bool isRegister: false
    property string errorMessage: ""
    property string successMessage: ""

    MouseArea {
        anchors.fill: parent
        // Block mouse click events from passing through to underlying UI
    }

    Rectangle {
        id: card
        width: Math.min(parent.width - 32, 440)
        height: column.implicitHeight + 48
        anchors.centerIn: parent
        color: Theme.block
        radius: 12
        border.color: Theme.line2
        border.width: 1

        ColumnLayout {
            id: column
            anchors.fill: parent
            anchors.margins: 28
            spacing: 16

            // Mode Selector Tabs (Sign In / Register)
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Rectangle {
                    Layout.fillWidth: true
                    height: 34
                    radius: 6
                    color: !modal.isRegister ? Theme.accent : Theme.pageBg
                    border.color: !modal.isRegister ? Theme.accent : Theme.line2
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "SIGN IN"
                        color: !modal.isRegister ? Theme.onAccent : Theme.text
                        font.family: Theme.mono
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            modal.isRegister = false;
                            modal.errorMessage = "";
                            modal.successMessage = "";
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 34
                    radius: 6
                    color: modal.isRegister ? Theme.accent : Theme.pageBg
                    border.color: modal.isRegister ? Theme.accent : Theme.line2
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "REGISTER"
                        color: modal.isRegister ? Theme.onAccent : Theme.text
                        font.family: Theme.mono
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            modal.isRegister = true;
                            modal.errorMessage = "";
                            modal.successMessage = "";
                        }
                    }
                }
            }

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
                    text: modal.isRegister ? "CREATE ACCOUNT" : "AUTHENTICATION"
                    color: Theme.ink
                    font.family: Theme.serif
                    font.pixelSize: 20
                    font.weight: Font.Bold
                    font.letterSpacing: 2
                }
            }

            Text {
                text: modal.isRegister
                    ? "Register a new local account to access DocSummarizer workspace."
                    : "Please sign in to access DocSummarizer workspace."
                color: Theme.text
                font.family: Theme.body
                font.pixelSize: 13
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.line2
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
                    placeholderText: "Enter username"
                    text: modal.isRegister ? "" : "admin"
                    color: Theme.ink
                    font.family: Theme.body
                    font.pixelSize: 14
                    background: Rectangle {
                        color: Theme.pageBg
                        radius: 6
                        border.color: userInput.activeFocus ? Theme.accent : Theme.line2
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
                    placeholderText: "Enter password"
                    text: modal.isRegister ? "" : "admin"
                    echoMode: TextInput.Password
                    color: Theme.ink
                    font.family: Theme.body
                    font.pixelSize: 14
                    background: Rectangle {
                        color: Theme.pageBg
                        radius: 6
                        border.color: passInput.activeFocus ? Theme.accent : Theme.line2
                        border.width: 1
                    }
                    onAccepted: {
                        if (modal.isRegister) {
                            confirmPassInput.forceActiveFocus();
                        } else {
                            submitAuth();
                        }
                    }
                }
            }

            // Confirm Password Input (Register mode only)
            ColumnLayout {
                visible: modal.isRegister
                spacing: 6
                Text {
                    text: "CONFIRM PASSWORD"
                    color: Theme.faint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                }
                TextField {
                    id: confirmPassInput
                    Layout.fillWidth: true
                    placeholderText: "Re-enter password"
                    text: ""
                    echoMode: TextInput.Password
                    color: Theme.ink
                    font.family: Theme.body
                    font.pixelSize: 14
                    background: Rectangle {
                        color: Theme.pageBg
                        radius: 6
                        border.color: confirmPassInput.activeFocus ? Theme.accent : Theme.line2
                        border.width: 1
                    }
                    onAccepted: submitAuth()
                }
            }

            // Success Message Display
            Text {
                visible: modal.successMessage !== ""
                text: modal.successMessage
                color: Theme.dark ? "#4ECCA3" : "#2E7D32"
                font.family: Theme.body
                font.pixelSize: 13
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
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
                text: modal.isRegister ? "CREATE ACCOUNT" : "SIGN IN"
                primary: true
                onClicked: submitAuth()
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: modal.isRegister ? "Already registered? Click SIGN IN above." : "Default credentials: admin / admin"
                color: Theme.faint
                font.family: Theme.mono
                font.pixelSize: 11
            }
        }
    }

    function submitAuth() {
        modal.errorMessage = "";
        modal.successMessage = "";

        if (modal.isRegister) {
            if (userInput.text.trim().length < 2) {
                modal.errorMessage = "Username must be at least 2 characters.";
                return;
            }
            if (passInput.text.length < 3) {
                modal.errorMessage = "Password must be at least 3 characters.";
                return;
            }
            if (passInput.text !== confirmPassInput.text) {
                modal.errorMessage = "Passwords do not match.";
                return;
            }

            var registered = bridge.registerUser(userInput.text, passInput.text);
            if (registered) {
                modal.isRegister = false;
                modal.successMessage = "Account created successfully! You can now sign in.";
                confirmPassInput.text = "";
            } else {
                modal.errorMessage = "Account registration failed. Username may already exist.";
            }
        } else {
            var success = bridge.authenticate(userInput.text, passInput.text);
            if (!success) {
                modal.errorMessage = "Invalid username or password. Try 'admin' / 'admin'.";
            }
        }
    }
}
