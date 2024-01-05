# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/profile_settings_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!

import aqt


class Ui_ProfileSettingsDialog(object):
    def setupUi(self, ProfileSettingsDialog):
        ProfileSettingsDialog.setObjectName("ProfileSettingsDialog")
        ProfileSettingsDialog.resize(380, 487)
        ProfileSettingsDialog.setMinimumSize(aqt.qt.QSize(380, 0))
        self.gridLayout_2 = aqt.qt.QGridLayout(ProfileSettingsDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.buttonBox = aqt.qt.QDialogButtonBox(ProfileSettingsDialog)
        self.buttonBox.setEnabled(True)
        self.buttonBox.setOrientation(aqt.qt.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(aqt.qt.QDialogButtonBox.StandardButton.Close)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.stackedWidget = aqt.qt.QStackedWidget(ProfileSettingsDialog)
        self.stackedWidget.setObjectName("stackedWidget")
        self.loginPage = aqt.qt.QWidget()
        self.loginPage.setObjectName("loginPage")
        self.gridLayout_6 = aqt.qt.QGridLayout(self.loginPage)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.loginGridLayout = aqt.qt.QGridLayout()
        self.loginGridLayout.setSizeConstraint(aqt.qt.QLayout.SizeConstraint.SetDefaultConstraint)
        self.loginGridLayout.setObjectName("loginGridLayout")
        self.passwordLineEdit = aqt.qt.QLineEdit(self.loginPage)
        self.passwordLineEdit.setEchoMode(aqt.qt.QLineEdit.EchoMode.Password)
        self.passwordLineEdit.setObjectName("passwordLineEdit")
        self.loginGridLayout.addWidget(self.passwordLineEdit, 3, 1, 1, 1)
        self.passwordLabel = aqt.qt.QLabel(self.loginPage)
        self.passwordLabel.setObjectName("passwordLabel")
        self.loginGridLayout.addWidget(self.passwordLabel, 3, 0, 1, 1)
        self.loginButton = aqt.qt.QPushButton(self.loginPage)
        self.loginButton.setObjectName("loginButton")
        self.loginGridLayout.addWidget(self.loginButton, 4, 0, 1, 2)
        self.statusLabel = aqt.qt.QLabel(self.loginPage)
        self.statusLabel.setText("")
        self.statusLabel.setObjectName("statusLabel")
        self.loginGridLayout.addWidget(self.statusLabel, 5, 0, 1, 2)
        self.emailLabel = aqt.qt.QLabel(self.loginPage)
        self.emailLabel.setObjectName("emailLabel")
        self.loginGridLayout.addWidget(self.emailLabel, 2, 0, 1, 1)
        self.emailLineEdit = aqt.qt.QLineEdit(self.loginPage)
        self.emailLineEdit.setObjectName("emailLineEdit")
        self.loginGridLayout.addWidget(self.emailLineEdit, 2, 1, 1, 1)
        spacerItem = aqt.qt.QSpacerItem(20, 40, aqt.qt.QSizePolicy.Policy.Minimum, aqt.qt.QSizePolicy.Policy.Expanding)
        self.loginGridLayout.addItem(spacerItem, 8, 0, 1, 2)
        self.loginLabel = aqt.qt.QLabel(self.loginPage)
        font = aqt.qt.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.loginLabel.setFont(font)
        self.loginLabel.setAlignment(aqt.qt.Qt.AlignmentFlag.AlignCenter)
        self.loginLabel.setWordWrap(False)
        self.loginLabel.setObjectName("loginLabel")
        self.loginGridLayout.addWidget(self.loginLabel, 1, 0, 1, 2)
        self.signupLabel = aqt.qt.QLabel(self.loginPage)
        self.signupLabel.setAlignment(aqt.qt.Qt.AlignmentFlag.AlignCenter)
        self.signupLabel.setObjectName("signupLabel")
        self.loginGridLayout.addWidget(self.signupLabel, 6, 0, 1, 2)
        self.textBrowser = aqt.qt.QTextBrowser(self.loginPage)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setObjectName("textBrowser")
        self.loginGridLayout.addWidget(self.textBrowser, 9, 0, 1, 2)
        self.gridLayout_6.addLayout(self.loginGridLayout, 0, 0, 1, 1)
        self.stackedWidget.addWidget(self.loginPage)
        self.logoutPage = aqt.qt.QWidget()
        self.logoutPage.setObjectName("logoutPage")
        self.gridLayout_5 = aqt.qt.QGridLayout(self.logoutPage)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.userEmailLabel = aqt.qt.QLabel(self.logoutPage)
        self.userEmailLabel.setObjectName("userEmailLabel")
        self.gridLayout_5.addWidget(self.userEmailLabel, 0, 1, 1, 1)
        self.loggedInAsLabel = aqt.qt.QLabel(self.logoutPage)
        self.loggedInAsLabel.setObjectName("loggedInAsLabel")
        self.gridLayout_5.addWidget(self.loggedInAsLabel, 0, 0, 1, 1)
        self.logoutButton = aqt.qt.QPushButton(self.logoutPage)
        self.logoutButton.setObjectName("logoutButton")
        self.gridLayout_5.addWidget(self.logoutButton, 0, 2, 1, 1)
        spacerItem1 = aqt.qt.QSpacerItem(20, 40, aqt.qt.QSizePolicy.Policy.Minimum, aqt.qt.QSizePolicy.Policy.Expanding)
        self.gridLayout_5.addItem(spacerItem1, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.logoutPage)
        self.gridLayout_2.addWidget(self.stackedWidget, 0, 0, 1, 1)

        self.retranslateUi(ProfileSettingsDialog)
        self.stackedWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(ProfileSettingsDialog.accept)
        self.buttonBox.rejected.connect(ProfileSettingsDialog.reject)
        aqt.qt.QMetaObject.connectSlotsByName(ProfileSettingsDialog)
        ProfileSettingsDialog.setTabOrder(self.emailLineEdit, self.passwordLineEdit)
        ProfileSettingsDialog.setTabOrder(self.passwordLineEdit, self.loginButton)
        ProfileSettingsDialog.setTabOrder(self.loginButton, self.textBrowser)
        ProfileSettingsDialog.setTabOrder(self.textBrowser, self.logoutButton)

    def retranslateUi(self, ProfileSettingsDialog):
        _translate = aqt.qt.QCoreApplication.translate
        ProfileSettingsDialog.setWindowTitle(_translate("ProfileSettingsDialog", "Anki Killstreaks Profile Settings"))
        self.passwordLabel.setText(_translate("ProfileSettingsDialog", "Password"))
        self.loginButton.setText(_translate("ProfileSettingsDialog", "Login"))
        self.emailLabel.setText(_translate("ProfileSettingsDialog", "Email"))
        self.loginLabel.setText(_translate("ProfileSettingsDialog", "Log in to Killstreaks/Achievements leaderboard"))
        self.signupLabel.setText(_translate("ProfileSettingsDialog", "<html><head/><body><p><a href=\"https://ankiachievements.com\"><span style=\" text-decoration: underline; color:#0068da;\">Sign Up</span></a></p></body></html>"))
        self.textBrowser.setHtml(_translate("ProfileSettingsDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Noto Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Anki Killstreaks © 2020-2021 jac241.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">It costs 20$/month to run the servers for chase mode and the leaderboards. Please consider <a href=\"https://cash.app/$jac241\"><span style=\" text-decoration: underline; color:#2980b9;\">donating</span></a> today. I really appreciate your contributions.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Links to source code: <a href=\"https://github.com/jac241/anki_killstreaks\"><span style=\" text-decoration: underline; color:#2980b9;\">Anki Killstreaks add-on source</span></a>, <a href=\"https://github.com/jac241/spaced_rep_achievements\"><span style=\" text-decoration: underline; color:#2980b9;\">AnkiAchievements.com source</span></a>.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Report issues <a href=\"https://github.com/jac241/anki_killstreaks/issues\"><span style=\" text-decoration: underline; color:#2980b9;\">here</span></a><a href=\"https://github.com/jac241/spaced_rep_achievements\"><span style=\" text-decoration: underline; color:#2980b9;\">.</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; text-decoration: underline; color:#2980b9;\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.userEmailLabel.setText(_translate("ProfileSettingsDialog", "user_email"))
        self.loggedInAsLabel.setText(_translate("ProfileSettingsDialog", "Logged in as:"))
        self.logoutButton.setText(_translate("ProfileSettingsDialog", "Log Out"))
