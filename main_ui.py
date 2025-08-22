"""
Module/Script Name: main_ui.py

Description:
Loads and connects the Watermark Wizard GUI built in Qt Designer with the watermark logic
and config file. Allows user to select folders, edit overlay text and QR data, preview,
and run the watermarking tool.

Author(s):
George Penzenik - Rank Rocket Co

Created Date:
04-14-2025

Last Modified Date:
08-01-2025

Version:
v1.07.31

Comments:
- v1.07.31: Fixed all Pylance errors including method definitions, syntax issues, and removed obsolete method references.
"""

import sys
import os
import json
import subprocess
import io
from typing import Optional, cast, Any
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QFileDialog,
    QColorDialog,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QProgressDialog,
    QSlider,
    QWidget,
    QLayout,
    QComboBox,
    QFontComboBox,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtGui import QColor, QPixmap, QFont
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PIL import Image
from PIL.ImageQt import ImageQt
from ui.designer_ui import Ui_WatermarkWizard
import qr_watermark


def load_config(path: str = "config/settings.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict, path: str = "config/settings.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class WatermarkThread(QThread):
    """Thread for running watermark processing without blocking UI"""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def run(self) -> None:
        try:
            # Instead of running subprocess, call the watermark function directly
            import qr_watermark

            # Refresh config to ensure latest settings
            qr_watermark.refresh_config()

            input_dir = qr_watermark.INPUT_DIR
            output_dir = qr_watermark.OUTPUT_DIR

            if not input_dir or not os.path.isdir(input_dir):
                self.error.emit("Input directory is not set or does not exist.")
                return

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Build list of images (recursive if enabled)
            paths = []
            recursive = bool(qr_watermark.PROCESS_RECURSIVE)
            if recursive:
                for root, _dirs, files in os.walk(input_dir):
                    for f in files:
                        if f.lower().endswith(
                            (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
                        ):
                            paths.append(os.path.join(root, f))
            else:
                for f in os.listdir(input_dir):
                    if f.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
                    ):
                        paths.append(os.path.join(input_dir, f))

            if not paths:
                self.error.emit("No image files found in input directory.")
                return

            processed_count = 0
            error_count = 0

            self.progress.emit(f"Starting processing of {len(paths)} images...")

            for full in paths:
                try:
                    if recursive:
                        rel = os.path.relpath(os.path.dirname(full), input_dir)
                        out_dir = (
                            os.path.join(qr_watermark.OUTPUT_DIR, rel)
                            if rel != "."
                            else qr_watermark.OUTPUT_DIR
                        )
                    else:
                        out_dir = qr_watermark.OUTPUT_DIR
                    qr_watermark.apply_watermark(
                        full, return_image=False, out_dir=out_dir
                    )
                    processed_count += 1
                    self.progress.emit(f"Processed: {os.path.basename(full)}")
                except Exception as e:
                    error_count += 1
                    self.progress.emit(
                        f"Error processing {os.path.basename(full)}: {str(e)}"
                    )

            if error_count == 0:
                self.progress.emit(
                    f"Successfully processed all {processed_count} images!"
                )
                self.finished.emit()
            else:
                self.error.emit(
                    f"Completed with errors. Processed: {processed_count}, Errors: {error_count}"
                )

        except Exception as e:
            self.error.emit(f"Critical error during processing: {str(e)}")


class WatermarkWizard(QtWidgets.QMainWindow):
    # Class-level attribute stubs for Pylance/typing
    recursiveCheck: Optional[Any]
    collisionCombo: Optional[Any]
    previewSeoBtn: Optional[Any]
    exportMapBtn: Optional[Any]

    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_WatermarkWizard()
        self.ui.setupUi(self)
        self.config = load_config()
        self.watermark_thread: Optional[WatermarkThread] = None
        self.progress_dialog: Optional[QProgressDialog] = None
        self.font_size_label: Optional[QLabel] = None
        self.text_padding_label: Optional[QLabel] = None
        self.qr_padding_label: Optional[QLabel] = None
        self.font_family_combo: Optional[QFontComboBox] = None
        self.font_size_combo: Optional[QComboBox] = None
        self.tick_labels: list[QLabel] = []  # Store tick labels for cleanup

        # Improve overall UI appearance
        self.improve_ui_styling()

        self.bind_widgets()
        self.setup_font_controls()  # Replace with font family + size controls
        self.setup_slider_labels()
        # Predeclare dynamic UI attrs for type-checkers/runtime safety
        self.recursiveCheck: Optional[Any] = None
        self.collisionCombo: Optional[Any] = None
        self.previewSeoBtn: Optional[Any] = None
        self.exportMapBtn: Optional[Any] = None
        self.load_values()
        self.add_extra_controls()

        # Use timer to add tick labels after UI is fully rendered
        QTimer.singleShot(100, self.add_tick_labels)

    def improve_ui_styling(self) -> None:
        """Improve overall UI styling and spacing"""
        try:
            # Set overall application font size
            app_font = self.font()
            app_font.setPointSize(10)  # Increase from default 8-9pt to 10pt
            self.setFont(app_font)

            # Style the main window
            self.setStyleSheet(
                """
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QLabel {
                    font-size: 10pt;
                    color: #333;
                }
                QPushButton {
                    font-size: 10pt;
                    padding: 6px 12px;
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e6f3ff;
                    border-color: #0078d4;
                }
                QPushButton:pressed {
                    background-color: #cce7ff;
                }
                QLineEdit, QTextEdit {
                    font-size: 10pt;
                    padding: 4px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                }
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #ddd;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #0078d4;
                    border: 1px solid #005a9e;
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    margin: -4px 0;
                }
                QSlider::handle:horizontal:hover {
                    background: #106ebe;
                }
            """
            )

        except Exception as e:
            print(f"Could not apply UI styling: {e}")

    def setup_font_controls(self) -> None:
        """Replace font size slider with QFontComboBox and size selector"""
        try:
            # Create font family combo box
            self.font_family_combo = QFontComboBox()

            # Set up font for the combo box
            combo_font = QFont()
            combo_font.setPointSize(10)
            self.font_family_combo.setFont(combo_font)

            # Set default to a common font
            self.font_family_combo.setCurrentFont(QFont("Arial"))

            # Style the font family combo
            self.font_family_combo.setStyleSheet(
                """
                QFontComboBox {
                    padding: 4px 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background: white;
                    min-width: 120px;
                }
                QFontComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
            """
            )

            # Create font size combo box
            self.font_size_combo = QComboBox()
            self.font_size_combo.setFont(combo_font)

            # Standard font sizes
            font_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 60, 72]
            for size in font_sizes:
                self.font_size_combo.addItem(f"{size}pt", size)

            # Style the font size combo
            self.font_size_combo.setStyleSheet(
                """
                QComboBox {
                    padding: 4px 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background: white;
                    min-width: 80px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
            """
            )

            # Find the font size slider's parent and replace it with a horizontal layout
            font_slider = self.ui.fontSizeSlider
            font_parent = cast(Optional[QWidget], font_slider.parent())

            if font_parent and font_parent.layout():
                layout = font_parent.layout()
                if layout and hasattr(layout, "replaceWidget"):
                    # Create a horizontal layout for font controls
                    font_layout = QHBoxLayout()
                    font_layout.addWidget(self.font_family_combo)
                    font_layout.addWidget(self.font_size_combo)
                    font_layout.addStretch()  # Push everything to the left

                    # Create a widget to hold the layout
                    font_widget = QWidget()
                    font_widget.setLayout(font_layout)

                    # Replace slider with the new widget
                    cast(QVBoxLayout, layout).replaceWidget(font_slider, font_widget)
                    font_slider.hide()  # Hide the old slider
                elif layout and hasattr(layout, "insertWidget"):
                    # Alternative: insert font controls in sequence
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == font_slider:
                            cast(QVBoxLayout, layout).insertWidget(
                                i, self.font_family_combo
                            )
                            cast(QVBoxLayout, layout).insertWidget(
                                i + 1, self.font_size_combo
                            )
                            font_slider.hide()
                            break

            # Connect the combo box signals
            self.font_family_combo.currentFontChanged.connect(self.on_font_changed)
            self.font_size_combo.currentTextChanged.connect(self.on_font_size_changed)

            print("Font controls created successfully")

        except Exception as e:
            print(f"Could not create font controls: {e}")
            import traceback

            traceback.print_exc()

    def on_font_changed(self, font: QFont) -> None:
        """Handle font family changes"""
        try:
            family = font.family()
            current_size = "12pt"
            if self.font_size_combo:
                current_size = self.font_size_combo.currentText()

            if self.font_size_label:
                self.font_size_label.setText(f"Font: {family} {current_size}")
            print(f"Font family changed to: {family}")
        except Exception as e:
            print(f"Error handling font change: {e}")

    def on_font_size_changed(self, text: str) -> None:
        """Handle font size combo box changes"""
        try:
            # Extract the point size from text like "12pt"
            if text.endswith("pt"):
                size = int(text[:-2])
                family = "Arial"
                if self.font_family_combo:
                    family = self.font_family_combo.currentFont().family()

                if self.font_size_label:
                    self.font_size_label.setText(f"Font: {family} {size}pt")
                print(f"Font size changed to: {size}pt")
        except (ValueError, Exception) as e:
            print(f"Invalid font size format or error: {text} - {e}")

    def setup_slider_labels(self) -> None:
        """Setup remaining sliders (padding) to work with concrete units"""
        try:
            # Only setup sliders for padding - font size is now a combo box

            # Text Padding Slider: 0px to 500px
            self.ui.textPaddingSlider.setMinimum(0)
            self.ui.textPaddingSlider.setMaximum(500)
            self.ui.textPaddingSlider.setTickInterval(50)
            self.ui.textPaddingSlider.setTickPosition(QSlider.TickPosition.TicksBelow)

            # QR Padding Slider: 0px to 300px
            self.ui.qrPaddingSlider.setMinimum(0)
            self.ui.qrPaddingSlider.setMaximum(300)
            self.ui.qrPaddingSlider.setTickInterval(30)
            self.ui.qrPaddingSlider.setTickPosition(QSlider.TickPosition.TicksBelow)

            # Create labels for controls with proper QFont
            self.font_size_label = QLabel(
                "Font: Arial 12pt"
            )  # Shows both family and size
            self.text_padding_label = QLabel("Text Padding: 50px")
            self.qr_padding_label = QLabel("QR Padding: 20px")

            # Style the labels with QFont instead of CSS
            label_font = QFont()
            label_font.setPointSize(11)
            label_font.setBold(True)

            self.font_size_label.setFont(label_font)
            self.text_padding_label.setFont(label_font)
            self.qr_padding_label.setFont(label_font)

            # Simple styling without font CSS
            label_style = """
                color: #333; 
                margin-bottom: 4px;
                padding: 2px;
            """
            self.font_size_label.setStyleSheet(label_style)
            self.text_padding_label.setStyleSheet(label_style)
            self.qr_padding_label.setStyleSheet(label_style)

            # Try to insert labels above remaining controls
            text_padding_parent = cast(
                Optional[QWidget], self.ui.textPaddingSlider.parent()
            )
            qr_padding_parent = cast(
                Optional[QWidget], self.ui.qrPaddingSlider.parent()
            )

            # Font controls label goes with the font widgets
            if self.font_family_combo:
                font_combo_parent = cast(
                    Optional[QWidget], self.font_family_combo.parent()
                )
                if font_combo_parent:
                    layout = font_combo_parent.layout()
                    if layout and hasattr(layout, "insertWidget"):
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            if (
                                item
                                and item.widget()
                                and (
                                    item.widget() == self.font_family_combo
                                    or item.widget() == self.font_size_combo
                                )
                            ):
                                cast(QVBoxLayout, layout).insertWidget(
                                    i, self.font_size_label
                                )
                                break

            if text_padding_parent:
                layout = text_padding_parent.layout()
                if layout and hasattr(layout, "insertWidget"):
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == self.ui.textPaddingSlider:
                            cast(QVBoxLayout, layout).insertWidget(
                                i, self.text_padding_label
                            )
                            break

            if qr_padding_parent:
                layout = qr_padding_parent.layout()
                if layout and hasattr(layout, "insertWidget"):
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == self.ui.qrPaddingSlider:
                            cast(QVBoxLayout, layout).insertWidget(
                                i, self.qr_padding_label
                            )
                            break

        except Exception as e:
            print(f"Could not add slider labels to layout: {e}")
            self.setup_slider_labels_alternative()

    def setup_slider_labels_alternative(self) -> None:
        """Alternative method to add slider labels"""
        try:
            # Create labels and position them manually
            text_parent = cast(Optional[QWidget], self.ui.textPaddingSlider.parent())
            qr_parent = cast(Optional[QWidget], self.ui.qrPaddingSlider.parent())

            self.text_padding_label = QLabel("Text Padding: 50px", text_parent)
            self.qr_padding_label = QLabel("QR Padding: 20px", qr_parent)

            # Position labels above sliders
            if self.text_padding_label:
                text_pos = self.ui.textPaddingSlider.pos()
                self.text_padding_label.move(text_pos.x(), text_pos.y() - 20)
                self.text_padding_label.show()

            if self.qr_padding_label:
                qr_pos = self.ui.qrPaddingSlider.pos()
                self.qr_padding_label.move(qr_pos.x(), qr_pos.y() - 20)
                self.qr_padding_label.show()

        except Exception as e:
            print(f"Could not position slider labels manually: {e}")

    def bind_widgets(self) -> None:
        self.ui.browseInputBtn.clicked.connect(self.select_input_folder)
        self.ui.browseOutputBtn.clicked.connect(self.select_output_folder)
        self.ui.textColorBtn.clicked.connect(self.pick_text_color)
        self.ui.shadowColorBtn.clicked.connect(self.pick_shadow_color)
        self.ui.previewBtn.clicked.connect(self.preview)
        self.ui.runBtn.clicked.connect(self.save_and_run)

        # Connect remaining sliders to update their labels (font size now uses combo)
        self.ui.textPaddingSlider.valueChanged.connect(self.update_text_padding_label)
        self.ui.qrPaddingSlider.valueChanged.connect(self.update_qr_padding_label)

    def update_text_padding_label(self, value: int) -> None:
        """Update text padding label when slider changes"""
        if self.text_padding_label is not None:
            self.text_padding_label.setText(f"Text Padding: {value}px")

    def update_qr_padding_label(self, value: int) -> None:
        """Update QR padding label when slider changes"""
        if self.qr_padding_label is not None:
            self.qr_padding_label.setText(f"QR Padding: {value}px")

    def load_values(self) -> None:
        cfg = self.config
        self.ui.inputDir.setText(cfg.get("input_dir", ""))
        self.ui.outputDir.setText(cfg.get("output_dir", ""))
        self.ui.overlayText.setPlainText(cfg.get("text_overlay", ""))
        self.ui.qrLink.setText(cfg.get("qr_link", ""))

        # Load font family and size
        font_ratio = cfg.get("font_size_ratio", 0.02)  # Default 2%
        font_pt = int(font_ratio * 1920 * 0.75)  # Convert to approx points
        font_pt = max(8, min(72, font_pt))  # Clamp to reasonable range

        # Get font family from config (add this to config if not present)
        font_family = cfg.get("font_family", "Arial")

        # Set font family combo box
        if self.font_family_combo:
            font = QFont(font_family)
            self.font_family_combo.setCurrentFont(font)

        # Set font size combo box to closest standard size
        if self.font_size_combo:
            font_text = f"{font_pt}pt"
            index = self.font_size_combo.findText(font_text)
            if index >= 0:
                self.font_size_combo.setCurrentIndex(index)
            else:
                # Find closest size if exact match not found
                closest_index = 0
                closest_diff = float("inf")
                for i in range(self.font_size_combo.count()):
                    item_text = self.font_size_combo.itemText(i)
                    if item_text.endswith("pt"):
                        item_size = int(item_text[:-2])
                        diff = abs(item_size - font_pt)
                        if diff < closest_diff:
                            closest_diff = diff
                            closest_index = i
                self.font_size_combo.setCurrentIndex(closest_index)

        # Load padding values for sliders
        text_ratio = cfg.get("text_padding_bottom_ratio", 0.05)  # Default 5%
        text_px = int(text_ratio * 1080)
        text_px = max(0, min(500, text_px))  # Clamp to slider range

        qr_ratio = cfg.get("qr_padding_vh_ratio", 0.02)  # Default 2%
        qr_px = int(qr_ratio * 1080)
        qr_px = max(0, min(300, qr_px))  # Clamp to slider range

        # Set slider values
        self.ui.textPaddingSlider.setValue(text_px)
        self.ui.qrPaddingSlider.setValue(qr_px)

        # Load SEO rename setting
        self.ui.seoRenameCheck.setChecked(cfg.get("seo_rename", False))

        # Update labels with current values
        if self.font_family_combo and self.font_size_combo:
            family = self.font_family_combo.currentFont().family()
            size_text = self.font_size_combo.currentText()
            if self.font_size_label:
                self.font_size_label.setText(f"Font: {family} {size_text}")
        self.update_text_padding_label(text_px)
        self.update_qr_padding_label(qr_px)

    def select_input_folder(self) -> None:
        start = self.ui.inputDir.text() or os.getcwd()
        folder = QFileDialog.getExistingDirectory(self, "Select Input Directory", start)
        if folder:
            self.ui.inputDir.setText(folder)

    def select_output_folder(self) -> None:
        start = self.ui.outputDir.text() or os.getcwd()
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", start
        )
        if folder:
            self.ui.outputDir.setText(folder)

    def pick_text_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            self.config["text_color"] = [color.red(), color.green(), color.blue()]

    def pick_shadow_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            self.config["shadow_color"] = [
                color.red(),
                color.green(),
                color.blue(),
                128,
            ]

    def preview(self) -> None:
        print("Preview button clicked - starting preview process...")
        try:
            # Update config and validate
            print("Updating config from UI...")
            self.update_config_from_ui()
            input_dir = self.config.get("input_dir", "")
            print(f"Input directory: {input_dir}")

            if not input_dir or not os.path.isdir(input_dir):
                print("Input directory validation failed")
                QMessageBox.warning(
                    self, "Preview", "Input directory is not set or does not exist."
                )
                return

            # Save config first
            print("Saving config...")
            save_config(self.config)
            print("Config saved successfully")

            # Collect image files
            print("Collecting image files...")
            try:
                files = sorted(
                    [
                        f
                        for f in os.listdir(input_dir)
                        if f.lower().endswith((".jpg", ".jpeg", ".png"))
                    ]
                )
                print(f"Found {len(files)} image files")
            except Exception as e:
                print(f"Error listing directory: {e}")
                QMessageBox.critical(
                    self, "Preview Error", f"Failed to list directory: {e}"
                )
                return

            if not files:
                print("No image files found")
                QMessageBox.warning(
                    self, "Preview", "No image files found in the input directory."
                )
                return

            first_path = os.path.join(input_dir, files[0])
            print(f"Processing first image: {first_path}")

            # Generate preview image using direct function call
            try:
                print("Refreshing qr_watermark config...")
                qr_watermark.refresh_config()
                print("Calling apply_watermark...")
                img = qr_watermark.apply_watermark(first_path, return_image=True)
                print(f"apply_watermark returned: {type(img)}")
                if img is None:
                    raise ValueError("apply_watermark returned None")
                print("Preview image generated successfully")
            except Exception as e:
                print(f"Error in apply_watermark: {e}")
                QMessageBox.critical(
                    self, "Preview Error", f"Error generating preview: {e}"
                )
                return

            # Display in modal dialog
            print("Showing preview dialog...")
            self.show_preview_dialog(img)
            print("Preview dialog completed")

        except Exception as e:
            print(f"Critical error in preview: {e}")
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Critical Error",
                f"Unexpected error in preview: {str(e)}\n\nCheck console for details.",
            )

    def show_preview_dialog(self, img: Image.Image) -> None:
        """Show preview dialog with proper button handling"""
        try:
            print("Creating dialog...")
            dlg = QDialog(self)
            dlg.setWindowTitle("Preview")
            dlg.setModal(True)
            print("Dialog created successfully")

            print("Creating layout...")
            layout = QVBoxLayout(dlg)
            print("Layout created")

            # Image display
            print("Creating image label...")
            lbl = QLabel(parent=dlg)
            print("Converting PIL image to QPixmap...")
            # Alternative conversion method that might be more stable
            try:
                # Convert PIL image to bytes and then to QPixmap
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                pix = QPixmap()
                pix.loadFromData(img_bytes.getvalue())
                print(f"QPixmap created via bytes: {pix.width()}x{pix.height()}")
            except Exception as convert_error:
                print(f"Bytes conversion failed: {convert_error}")
                print("Trying ImageQt conversion...")
                pix = QPixmap.fromImage(ImageQt(img))
                print(f"QPixmap created via ImageQt: {pix.width()}x{pix.height()}")

            # Scale image if too large
            if pix.width() > 800 or pix.height() > 600:
                print("Scaling image...")
                pix = pix.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)
                print(f"Image scaled to: {pix.width()}x{pix.height()}")

            print("Setting pixmap to label...")
            lbl.setPixmap(pix)
            print("Adding label to layout...")
            layout.addWidget(lbl)
            print("Label added to layout")

            # Buttons
            print("Creating button layout...")
            hbox = QHBoxLayout()
            print("Creating buttons...")
            process_btn = QPushButton("Process All Images", dlg)
            close_btn = QPushButton("Close", dlg)
            print("Buttons created")

            hbox.addWidget(process_btn)
            hbox.addWidget(close_btn)
            layout.addLayout(hbox)
            print("Buttons added to layout")

            # Connect buttons
            print("Connecting button signals...")
            process_btn.clicked.connect(lambda: self.handle_process_from_preview(dlg))
            close_btn.clicked.connect(dlg.close)
            print("Button signals connected")

            # Auto-size to content
            print("Adjusting dialog size...")
            dlg.adjustSize()
            print("Dialog size adjusted")

            print("Executing dialog...")
            result = dlg.exec()
            print(f"Dialog closed with result: {result}")

        except Exception as e:
            print(f"Error in show_preview_dialog: {e}")
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Dialog Error",
                f"Error showing preview dialog: {str(e)}\n\nCheck console for details.",
            )

    def handle_process_from_preview(self, dialog: QDialog) -> None:
        """Handle processing request from preview dialog"""
        dialog.close()  # Close preview dialog first
        self.run_watermarking()  # Run processing

    def save_and_run(self) -> None:
        """Save config and run watermarking"""
        self.update_config_from_ui()
        save_config(self.config)
        self.run_watermarking()

    def run_watermarking(self) -> None:
        """Run watermarking in separate thread"""
        if self.watermark_thread and self.watermark_thread.isRunning():
            QMessageBox.information(
                self, "Processing", "Watermarking is already running!"
            )
            return

        # Disable the run button to prevent multiple runs
        self.ui.runBtn.setEnabled(False)
        self.ui.previewBtn.setEnabled(False)

        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Starting watermark processing...", "Cancel", 0, 0, self
        )
        self.progress_dialog.setWindowTitle("Processing Images")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()

        # Create and start thread
        self.watermark_thread = WatermarkThread()
        self.watermark_thread.finished.connect(self.on_watermarking_finished)
        self.watermark_thread.error.connect(self.on_watermarking_error)
        self.watermark_thread.progress.connect(self.on_watermarking_progress)
        self.watermark_thread.start()

    def on_watermarking_progress(self, message: str) -> None:
        """Handle progress updates"""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)
        print(f"Progress: {message}")

    def on_watermarking_finished(self) -> None:
        """Handle successful watermarking completion"""
        self.ui.runBtn.setEnabled(True)
        self.ui.previewBtn.setEnabled(True)
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        QMessageBox.information(
            self, "Complete", "Watermarking completed successfully!"
        )

    def on_watermarking_error(self, error_msg: str) -> None:
        """Handle watermarking errors"""
        self.ui.runBtn.setEnabled(True)
        self.ui.previewBtn.setEnabled(True)
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        QMessageBox.critical(self, "Error", f"Watermarking failed:\n{error_msg}")

    def update_config_from_ui(self) -> None:
        self.config["input_dir"] = self.ui.inputDir.text()
        self.config["output_dir"] = self.ui.outputDir.text()
        self.config["text_overlay"] = self.ui.overlayText.toPlainText()
        self.config["qr_link"] = self.ui.qrLink.text()

        # Get font family and size from combo boxes
        font_family = "Arial"  # Default
        if self.font_family_combo:
            font_family = self.font_family_combo.currentFont().family()
            self.config["font_family"] = font_family

        if self.font_size_combo:
            font_text = self.font_size_combo.currentText()
            if font_text.endswith("pt"):
                font_pt = int(font_text[:-2])
                font_px = font_pt / 0.75  # Convert pt to px
                self.config["font_size_ratio"] = font_px / 1920

        # Convert pixels to ratios for padding sliders
        text_px = self.ui.textPaddingSlider.value()
        self.config["text_padding_bottom_ratio"] = text_px / 1080

        qr_px = self.ui.qrPaddingSlider.value()
        self.config["qr_padding_vh_ratio"] = qr_px / 1080

        # Update SEO rename setting
        self.config["seo_rename"] = self.ui.seoRenameCheck.isChecked()
        # New slug controls
        recursive_check = getattr(self, "recursiveCheck", None)
        self.config["process_recursive"] = bool(
            recursive_check and recursive_check.isChecked()
        )
        collision_combo = getattr(self, "collisionCombo", None)
        if collision_combo:
            self.config["collision_strategy"] = collision_combo.currentText()
        # Optional advanced fields (keep if already present)
        self.config.setdefault("slug_max_words", 6)
        self.config.setdefault("slug_min_len", 3)
        self.config.setdefault("slug_stopwords", [])
        self.config.setdefault("slug_whitelist", [])
        self.config.setdefault("slug_prefix", "")
        self.config.setdefault("slug_location", "")

    def add_tick_labels(self) -> None:
        """Clean up any existing tick labels (range indicators removed to prevent UI artifacts)"""
        try:
            # Clear existing tick labels
            for label in self.tick_labels:
                label.deleteLater()
            self.tick_labels.clear()
            print("Cleaned up tick labels")

        except Exception as e:
            print(f"Could not clean up tick labels: {e}")

    def add_extra_controls(self) -> None:
        """Dynamically add extra controls without touching the .ui file."""
        try:
            from PyQt6.QtWidgets import (
                QCheckBox,
                QPushButton,
                QComboBox,
                QBoxLayout,
                QGridLayout,
                QFormLayout,
            )

            host = self.ui.runBtn.parentWidget()
            layout = host.layout() if host else None
            if not layout:
                print("add_extra_controls: no layout host found")
                return

            # Controls
            self.recursiveCheck = QCheckBox("Process subfolders", host)
            self.recursiveCheck.setChecked(
                bool(self.config.get("process_recursive", False))
            )

            self.collisionCombo = QComboBox(host)
            self.collisionCombo.addItems(["counter", "timestamp"])
            current = self.config.get("collision_strategy", "counter")
            idx = self.collisionCombo.findText(current) if current else 0
            self.collisionCombo.setCurrentIndex(idx if idx >= 0 else 0)

            self.previewSeoBtn = QPushButton("Preview SEO Names", host)
            self.exportMapBtn = QPushButton("Export Mapping CSV", host)

            # Insert before Run button when we can; otherwise append
            run_index = None
            if isinstance(layout, QBoxLayout):
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() is self.ui.runBtn:
                        run_index = i
                        break
                if run_index is None:
                    run_index = layout.count()
                layout.insertWidget(run_index, self.previewSeoBtn)
                layout.insertWidget(run_index + 1, self.exportMapBtn)
                layout.insertWidget(run_index + 2, self.collisionCombo)
                layout.insertWidget(run_index + 3, self.recursiveCheck)
            else:
                # Generic layouts (QGridLayout/QFormLayout/unknown): just append
                for w in (
                    self.previewSeoBtn,
                    self.exportMapBtn,
                    self.collisionCombo,
                    self.recursiveCheck,
                ):
                    layout.addWidget(w)

            # Wire signals
            self.previewSeoBtn.clicked.connect(self.preview_seo_names)
            self.exportMapBtn.clicked.connect(self.export_mapping_csv)
            print("add_extra_controls: controls added")

        except Exception as e:
            print(f"add_extra_controls error: {e}")

    def preview_seo_names(self) -> None:
        """Show a small dialog listing first 10 filename → SEO slug mappings (no writes)."""
        try:
            self.update_config_from_ui()
            save_config(self.config)
            import os, rename_img
            from PyQt6.QtWidgets import (
                QDialog,
                QVBoxLayout,
                QTableWidget,
                QTableWidgetItem,
                QPushButton,
                QHBoxLayout,
                QMessageBox,
            )

            # Configure slug per current settings
            rename_img.configure_slug(
                max_words=self.config.get("slug_max_words", 6),
                min_len=self.config.get("slug_min_len", 3),
                stopwords=self.config.get("slug_stopwords", []),
                whitelist=self.config.get("slug_whitelist", []),
                prefix=self.config.get("slug_prefix", ""),
                location=self.config.get("slug_location", ""),
            )

            input_dir = self.config.get("input_dir", "")
            if not input_dir or not os.path.isdir(input_dir):
                QMessageBox.information(
                    self,
                    "Preview SEO Names",
                    "Input directory is not set or does not exist.",
                )
                return

            paths = []
            recursive = bool(self.config.get("process_recursive", False))
            if recursive:
                for root, _dirs, files in os.walk(input_dir):
                    for f in files:
                        if f.lower().endswith(
                            (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
                        ):
                            paths.append(os.path.join(root, f))
                    if len(paths) >= 10:
                        break
            else:
                for f in os.listdir(input_dir):
                    if f.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
                    ):
                        paths.append(os.path.join(input_dir, f))
                        if len(paths) >= 10:
                            break

            if not paths:
                QMessageBox.information(
                    self, "Preview SEO Names", "No images found to preview."
                )
                return

            table = QTableWidget(len(paths), 3, self)
            table.setHorizontalHeaderLabels(
                ["Original", "Actual Output Name", "Relative Folder"]
            )
            
            # Track used names to simulate collision resolution
            used_names = set()
            output_dir = self.config.get("output_dir", "")
            collision_strategy = self.config.get("collision_strategy", "counter")
            
            for r, full in enumerate(paths):
                stem = os.path.splitext(os.path.basename(full))[0]
                rel = os.path.relpath(os.path.dirname(full), input_dir)
                
                # Generate base SEO name
                base_seo_name = rename_img.seo_friendly_name(stem)
                
                # Determine output directory for this file
                if self.config.get("process_recursive", False) and rel != ".":
                    file_output_dir = os.path.join(output_dir, rel)
                else:
                    file_output_dir = output_dir
                
                # Simulate collision resolution
                full_path = os.path.join(file_output_dir, base_seo_name)
                import qr_watermark
                actual_path = qr_watermark.ensure_unique_path(full_path, strategy=collision_strategy)
                actual_name = os.path.basename(actual_path)
                
                # Also check against our preview tracking for duplicates within this preview
                counter = 2
                while actual_name in used_names:
                    base, ext = os.path.splitext(base_seo_name)
                    actual_name = f"{base}-{counter}{ext}"
                    counter += 1
                
                used_names.add(actual_name)
                
                table.setItem(r, 0, QTableWidgetItem(os.path.basename(full)))
                table.setItem(r, 1, QTableWidgetItem(actual_name))
                table.setItem(r, 2, QTableWidgetItem("" if rel == "." else rel))

            dlg = QDialog(self)
            dlg.setWindowTitle("SEO Filename Preview")
            vbox = QVBoxLayout(dlg)
            vbox.addWidget(table)
            btns = QHBoxLayout()
            export_btn = QPushButton("Export CSV…", dlg)
            close_btn = QPushButton("Close", dlg)
            btns.addWidget(export_btn)
            btns.addWidget(close_btn)
            vbox.addLayout(btns)
            export_btn.clicked.connect(self.export_mapping_csv)
            close_btn.clicked.connect(dlg.close)
            dlg.resize(800, 400)
            dlg.exec()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Preview SEO Names", f"Error: {e}")

    def export_mapping_csv(self) -> None:
        """Export a CSV of original path → proposed filename (no writes)."""
        try:
            self.update_config_from_ui()
            save_config(self.config)
            import os, csv, rename_img
            from PyQt6.QtWidgets import QFileDialog, QMessageBox

            # Configure slug per current settings
            rename_img.configure_slug(
                max_words=self.config.get("slug_max_words", 6),
                min_len=self.config.get("slug_min_len", 3),
                stopwords=self.config.get("slug_stopwords", []),
                whitelist=self.config.get("slug_whitelist", []),
                prefix=self.config.get("slug_prefix", ""),
                location=self.config.get("slug_location", ""),
            )

            input_dir = self.config.get("input_dir", "")
            if not input_dir or not os.path.isdir(input_dir):
                QMessageBox.information(
                    self,
                    "Export Mapping",
                    "Input directory is not set or does not exist.",
                )
                return

            out_csv, _ = QFileDialog.getSaveFileName(
                self,
                "Save mapping CSV",
                os.path.join(self.config.get("output_dir", ""), "rename_map.csv"),
                "CSV Files (*.csv)",
            )
            if not out_csv:
                return

            rows = []
            if self.config.get("process_recursive", False):
                for root, _dirs, files in os.walk(input_dir):
                    for f in files:
                        if f.lower().endswith(
                            (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
                        ):
                            full = os.path.join(root, f)
                            stem = os.path.splitext(os.path.basename(full))[0]
                            slug = rename_img.seo_friendly_name(stem)
                            rel = os.path.relpath(root, input_dir)
                            rows.append(
                                [full, os.path.join(rel, slug) if rel != "." else slug]
                            )
            else:
                for f in os.listdir(input_dir):
                    if f.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
                    ):
                        full = os.path.join(input_dir, f)
                        stem = os.path.splitext(os.path.basename(full))[0]
                        slug = rename_img.seo_friendly_name(stem)
                        rows.append([full, slug])

            with open(out_csv, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["original_path", "proposed_name_or_relpath"])
                writer.writerows(rows)

            QMessageBox.information(
                self, "Export Mapping", f"Saved mapping to:\n{out_csv}"
            )

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Export Mapping", f"Error: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wizard = WatermarkWizard()
    wizard.show()
    sys.exit(app.exec())
