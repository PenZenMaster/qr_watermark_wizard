### File: ui/designer_ui.py
"""
Module/Script Name: ui/designer_ui.py

Description:
Compiled Qt Designer UI definitions for the Watermark Wizard application.

Author(s):
George Penzenik - Rank Rocket Co

Created Date:
04-14-2025

Last Modified Date:
08-01-2025

Version:
v1.06

Comments:
- v1.06: Moved "Pick Shadow Color" button under "Pick Text Color" and added "Preview" button above Run.
"""
from PyQt6 import QtCore, QtWidgets


class Ui_WatermarkWizard(object):
    def setupUi(self, WatermarkWizard):
        WatermarkWizard.setObjectName("WatermarkWizard")
        WatermarkWizard.resize(700, 600)
        self.centralwidget = QtWidgets.QWidget(parent=WatermarkWizard)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        # Input folder row
        self.labelInput = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelInput.setObjectName("labelInput")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelInput
        )
        # Input field + button layout
        self.inputRowLayout = QtWidgets.QHBoxLayout()
        self.inputRowLayout.setObjectName("inputRowLayout")
        self.inputDir = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.inputDir.setObjectName("inputDir")
        self.inputRowLayout.addWidget(self.inputDir)
        self.browseInputBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.browseInputBtn.setObjectName("browseInputBtn")
        self.inputRowLayout.addWidget(self.browseInputBtn)
        self.formLayout.setLayout(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.inputRowLayout
        )
        # Output folder row
        self.labelOutput = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelOutput.setObjectName("labelOutput")
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelOutput
        )
        # Output field + button layout
        self.outputRowLayout = QtWidgets.QHBoxLayout()
        self.outputRowLayout.setObjectName("outputRowLayout")
        self.outputDir = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.outputDir.setObjectName("outputDir")
        self.outputRowLayout.addWidget(self.outputDir)
        self.browseOutputBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.browseOutputBtn.setObjectName("browseOutputBtn")
        self.outputRowLayout.addWidget(self.browseOutputBtn)
        self.formLayout.setLayout(
            1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.outputRowLayout
        )
        # QR link row
        self.labelQr = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelQr.setObjectName("labelQr")
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelQr
        )
        self.qrLink = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.qrLink.setObjectName("qrLink")
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.qrLink
        )
        # Overlay text row
        self.labelText = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelText.setObjectName("labelText")
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelText
        )
        self.overlayText = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.overlayText.setObjectName("overlayText")
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.overlayText
        )
        # Font size slider row
        self.labelFontSize = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelFontSize.setObjectName("labelFontSize")
        self.formLayout.setWidget(
            4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelFontSize
        )
        self.fontSizeSlider = QtWidgets.QSlider(parent=self.centralwidget)
        self.fontSizeSlider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.fontSizeSlider.setObjectName("fontSizeSlider")
        self.formLayout.setWidget(
            4, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.fontSizeSlider
        )
        # Text padding slider row
        self.labelPadding = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelPadding.setObjectName("labelPadding")
        self.formLayout.setWidget(
            5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelPadding
        )
        self.textPaddingSlider = QtWidgets.QSlider(parent=self.centralwidget)
        self.textPaddingSlider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.textPaddingSlider.setObjectName("textPaddingSlider")
        self.formLayout.setWidget(
            5, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.textPaddingSlider
        )
        # QR padding slider row
        self.labelQRPadding = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelQRPadding.setObjectName("labelQRPadding")
        self.formLayout.setWidget(
            6, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelQRPadding
        )
        self.qrPaddingSlider = QtWidgets.QSlider(parent=self.centralwidget)
        self.qrPaddingSlider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.qrPaddingSlider.setObjectName("qrPaddingSlider")
        self.formLayout.setWidget(
            6, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.qrPaddingSlider
        )
        # Text color row
        self.labelTextColor = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelTextColor.setObjectName("labelTextColor")
        self.formLayout.setWidget(
            7, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelTextColor
        )
        self.textColorBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.textColorBtn.setObjectName("textColorBtn")
        self.formLayout.setWidget(
            7, QtWidgets.QFormLayout.ItemRole.FieldRole, self.textColorBtn
        )
        # Shadow color row (moved under text color)
        self.labelShadowColor = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelShadowColor.setObjectName("labelShadowColor")
        self.formLayout.setWidget(
            8, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelShadowColor
        )
        self.shadowColorBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.shadowColorBtn.setObjectName("shadowColorBtn")
        self.formLayout.setWidget(
            8, QtWidgets.QFormLayout.ItemRole.FieldRole, self.shadowColorBtn
        )
        # SEO rename checkbox row
        self.labelSeoRename = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelSeoRename.setObjectName("labelSeoRename")
        self.formLayout.setWidget(
            9, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelSeoRename
        )
        self.seoRenameCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.seoRenameCheck.setObjectName("seoRenameCheck")
        self.formLayout.setWidget(
            9, QtWidgets.QFormLayout.ItemRole.FieldRole, self.seoRenameCheck
        )
        # Add form layout
        self.verticalLayout.addLayout(self.formLayout)
        # Preview and run buttons
        self.previewBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.previewBtn.setObjectName("previewBtn")
        self.verticalLayout.addWidget(self.previewBtn)
        self.runBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.runBtn.setObjectName("runBtn")
        self.verticalLayout.addWidget(self.runBtn)
        WatermarkWizard.setCentralWidget(self.centralwidget)

        self.retranslateUi(WatermarkWizard)
        QtCore.QMetaObject.connectSlotsByName(WatermarkWizard)

    def retranslateUi(self, WatermarkWizard):
        _translate = QtCore.QCoreApplication.translate
        WatermarkWizard.setWindowTitle(
            _translate("WatermarkWizard", "Salvo Watermark Wizard")
        )
        self.labelInput.setText(_translate("WatermarkWizard", "Input Folder"))
        self.browseInputBtn.setText(_translate("WatermarkWizard", "Browse"))
        self.labelOutput.setText(_translate("WatermarkWizard", "Output Folder"))
        self.browseOutputBtn.setText(_translate("WatermarkWizard", "Browse"))
        self.labelQr.setText(_translate("WatermarkWizard", "QR Link"))
        self.labelText.setText(_translate("WatermarkWizard", "Overlay Text"))
        self.labelFontSize.setText(_translate("WatermarkWizard", "Font Size"))
        self.labelPadding.setText(
            _translate("WatermarkWizard", "Text Padding (Bottom)")
        )
        self.labelQRPadding.setText(
            _translate("WatermarkWizard", "QR Padding (Top/Right)")
        )
        self.labelTextColor.setText(_translate("WatermarkWizard", "Text Color"))
        self.textColorBtn.setText(_translate("WatermarkWizard", "Pick"))
        self.labelShadowColor.setText(_translate("WatermarkWizard", "Shadow Color"))
        self.shadowColorBtn.setText(_translate("WatermarkWizard", "Pick Shadow Color"))
        self.labelSeoRename.setText(_translate("WatermarkWizard", "SEO Rename"))
        self.seoRenameCheck.setText(
            _translate("WatermarkWizard", "Use SEO-friendly filenames")
        )
        self.previewBtn.setText(_translate("WatermarkWizard", "Preview"))
        self.runBtn.setText(_translate("WatermarkWizard", "Run Watermark"))
