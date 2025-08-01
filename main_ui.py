
"""
Module/Script Name: main_ui.py

Description:
Loads and connects the Watermark Wizard GUI built in Qt Designer with the watermark logic
and config file. Allows user to select folders, edit overlay text and QR data, and run the watermarking tool.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-14

Last Modified Date:
2025-04-14

Comments:
- Switched from uic.loadUi to compiled UI class for type-safe widget access
"""

import sys
import os
import json
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QFileDialog, QColorDialog, QMessageBox
from PyQt6.QtGui import QColor
from ui.designer_ui import Ui_WatermarkWizard

def load_config(path="config/settings.json"):
    with open(path, "r") as f:
        return json.load(f)

def save_config(data, path="config/settings.json"):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

class WatermarkWizard(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_WatermarkWizard()
        self.ui.setupUi(self)

        self.config = load_config()
        self.bind_widgets()
        self.load_values()

    def bind_widgets(self):
        self.ui.browseInputBtn.clicked.connect(self.select_input_folder)
        self.ui.browseOutputBtn.clicked.connect(self.select_output_folder)
        self.ui.textColorBtn.clicked.connect(self.pick_text_color)
        self.ui.shadowColorBtn.clicked.connect(self.pick_shadow_color)
        self.ui.runBtn.clicked.connect(self.save_and_run)

    def load_values(self):
        self.ui.inputDir.setText(self.config["input_dir"])
        self.ui.outputDir.setText(self.config["output_dir"])
        self.ui.overlayText.setPlainText(self.config["text_overlay"])
        self.ui.qrLink.setText(self.config["qr_link"])
        self.ui.fontSizeSlider.setValue(int(self.config["font_size_ratio"] * 100))
        self.ui.textPaddingSlider.setValue(int(self.config["text_padding_bottom_ratio"] * 100))
        self.ui.qrPaddingSlider.setValue(int(self.config["qr_padding_vh_ratio"] * 100))

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if folder:
            self.ui.inputDir.setText(folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.ui.outputDir.setText(folder)

    def pick_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.config["text_color"] = [color.red(), color.green(), color.blue()]

    def pick_shadow_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.config["shadow_color"] = [color.red(), color.green(), color.blue(), 128]

    def save_and_run(self):
        self.config["input_dir"] = self.ui.inputDir.text()
        self.config["output_dir"] = self.ui.outputDir.text()
        self.config["text_overlay"] = self.ui.overlayText.toPlainText()
        self.config["qr_link"] = self.ui.qrLink.text()
        self.config["font_size_ratio"] = self.ui.fontSizeSlider.value() / 100
        self.config["text_padding_bottom_ratio"] = self.ui.textPaddingSlider.value() / 100
        self.config["qr_padding_vh_ratio"] = self.ui.qrPaddingSlider.value() / 100

        save_config(self.config)

        QMessageBox.information(self, "Saved", "Configuration saved! Now running watermarking script…")
        os.system("python qr_watermark.py")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    wizard = WatermarkWizard()
    wizard.show()
    sys.exit(app.exec())
