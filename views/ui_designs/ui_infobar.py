# -*- coding: utf-8 -*-

from PySide2.QtCore import (QCoreApplication, QMetaObject, QSize)
from PySide2.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton)
from .resources_rc import *


class Ui_InfoBar(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(320, 45)
        Form.setMinimumSize(QSize(320, 45))
        Form.setMaximumSize(QSize(320, 45))
        Form.setStyleSheet(u"")
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setStyleSheet(
            u"QFrame#frame{background-color: rgba(17,28,46,235);"
            u"border: 1px solid #334155;border-radius: 8px;}"
        )
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.prompt_icon_label = QLabel(self.frame)
        self.prompt_icon_label.setObjectName(u"prompt_icon_label")
        self.prompt_icon_label.setMaximumSize(QSize(40, 16777215))
        self.prompt_icon_label.setStyleSheet(u"image: url(:/icons/icons/status-success.png);")

        self.horizontalLayout.addWidget(self.prompt_icon_label)

        self.prompt_type_label = QLabel(self.frame)
        self.prompt_type_label.setObjectName(u"prompt_type_label")
        self.prompt_type_label.setMinimumSize(QSize(40, 0))
        self.prompt_type_label.setMaximumSize(QSize(40, 16777215))
        self.prompt_type_label.setStyleSheet(u"color: #E2E8F0;font: 700 11pt \"Microsoft YaHei UI\";")

        self.horizontalLayout.addWidget(self.prompt_type_label)

        self.prompt_info_label = QLabel(self.frame)
        self.prompt_info_label.setObjectName(u"prompt_info_label")
        self.prompt_info_label.setStyleSheet(u"color: #CBD5E1;font: 500 10pt \"Microsoft YaHei UI\";")

        self.horizontalLayout.addWidget(self.prompt_info_label)

        self.btn_close_prompt = QPushButton(self.frame)
        self.btn_close_prompt.setObjectName(u"btn_close_prompt")
        self.btn_close_prompt.setMinimumSize(QSize(20, 20))
        self.btn_close_prompt.setMaximumSize(QSize(20, 16777215))
        self.btn_close_prompt.setStyleSheet(u"QPushButton {\n"
"    border: none;\n"
"	color: #94A3B8;\n"
"	border-radius: 4px;\n"
"}\n"
"\n"
"\n"
"QPushButton:hover {\n"
"    color: #E2E8F0;\n"
"    background-color: #162033;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #1B2940;\n"
"}\n"
"")

        self.horizontalLayout.addWidget(self.btn_close_prompt)


        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.prompt_icon_label.setText("")
        self.prompt_type_label.setText(QCoreApplication.translate("Form", u"\u63d0\u793a", None))
        self.prompt_info_label.setText(QCoreApplication.translate("Form", u"LabelText", None))
        self.btn_close_prompt.setText(QCoreApplication.translate("Form", u"X", None))
    # retranslateUi
