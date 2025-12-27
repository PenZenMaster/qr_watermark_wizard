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
12-26-2025

Version:
v3.0.0

Comments:
- v3.0.0: Major refactor - removed all ratio-based measurements, replaced with direct pixel/point values. Added auto-save for AI generation. Added Skippy to About dialog.
- v2.1.0: Phase 3 - AI Generation UI complete. Added AI Generation tab with provider selection (Fal.ai, Ideogram, Stability AI), prompt controls, parameter tuning, async generation with progress feedback, preview grid, save/send-to-watermark functionality.
- v2.0.0: Major version bump for AI image generation feature development. Added comprehensive unit testing framework (105 tests). Semantic versioning implemented.
- v1.07.31: Fixed all Pylance errors including method definitions, syntax issues, and removed obsolete method references.
"""

import sys
import os
import json
import io
from typing import Optional, cast, Any, List
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QFileDialog,
    QColorDialog,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressDialog,
    QSlider,
    QWidget,
    QComboBox,
    QFontComboBox,
    QPushButton,
    QHBoxLayout,
    QTextEdit,
    QSpinBox,
    QGroupBox,
    QScrollArea,
    QGridLayout,
    QTabWidget,
    QLineEdit,
    QCheckBox,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QDoubleSpinBox,
    QHeaderView,
    QAbstractItemView,
    QInputDialog,
)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PIL import Image
from PIL.ImageQt import ImageQt
from ui.designer_ui import Ui_WatermarkWizard
import qr_watermark

# AI Generation imports
try:
    from qrmr.provider_adapters import (
        create_default_registry,
        load_provider_credentials,
        GenerateRequest,
        ProviderError,
    )

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: AI generation modules not available")

# Profile Management imports
try:
    from qrmr.config_store import ConfigStore
    from qrmr.config_schema import ClientProfile
    from qrmr.utils import slugify

    PROFILE_SYSTEM_AVAILABLE = True
except ImportError:
    PROFILE_SYSTEM_AVAILABLE = False
    print("Warning: Profile management modules not available")


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


class AIGenerationThread(QThread):
    """Thread for AI image generation without blocking UI"""

    finished = pyqtSignal(list)  # List of PIL Images
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(
        self,
        provider_name: str,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        num_images: int,
        seed: Optional[int] = None,
    ):
        super().__init__()
        self.provider_name = provider_name
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.width = width
        self.height = height
        self.num_images = num_images
        self.seed = seed

    def run(self) -> None:
        try:
            if not AI_AVAILABLE:
                self.error.emit("AI generation modules not available")
                return

            self.progress.emit(f"Loading {self.provider_name} provider...")

            # Load provider credentials and create registry
            try:
                credentials = load_provider_credentials()
                registry = create_default_registry(credentials)
                provider = registry.get(self.provider_name)
            except FileNotFoundError:
                self.error.emit(
                    "Provider credentials not found. Please create config/providers.yaml with your API keys."
                )
                return
            except KeyError:
                self.error.emit(
                    f"Provider '{self.provider_name}' not found in registry"
                )
                return

            self.progress.emit(f"Generating {self.num_images} image(s)...")

            # Create generation request
            request = GenerateRequest(
                prompt=self.prompt,
                negative_prompt=self.negative_prompt if self.negative_prompt else None,
                width=self.width,
                height=self.height,
                num_images=self.num_images,
                seed=self.seed,
            )

            # Generate images
            result = provider.generate(request)

            self.progress.emit("Converting images...")

            # Convert bytes to PIL Images
            images = []
            for gen_img in result.images:
                img = Image.open(io.BytesIO(gen_img.bytes))
                images.append(img)

            self.progress.emit(f"Successfully generated {len(images)} image(s)!")
            self.finished.emit(images)

        except ProviderError as e:
            self.error.emit(f"Provider error: {e.message}")
        except Exception as e:
            self.error.emit(f"Generation failed: {str(e)}")


class WatermarkWizard(QtWidgets.QMainWindow):
    # Class-level attribute stubs for Pylance/typing
    recursiveCheck: Optional[Any]
    collisionCombo: Optional[Any]
    previewSeoBtn: Optional[Any]
    exportMapBtn: Optional[Any]
    slugPrefixLabel: Optional[Any]
    slugPrefixEdit: Optional[Any]
    slugLocationLabel: Optional[Any]
    slugLocationEdit: Optional[Any]

    # Profile management attributes
    config_store: Optional[Any]
    active_profile: Optional[Any]
    profile_table: Optional[QTableWidget]
    recent_profiles_menu: Optional[QMenu]
    profile_status_label: Optional[QLabel]

    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_WatermarkWizard()
        self.ui.setupUi(self)

        # Set application title with version
        self.setWindowTitle("Rank Rocket Watermark Wizard v3.0.0")

        self.config = load_config()
        self.watermark_thread: Optional[WatermarkThread] = None
        self.progress_dialog: Optional[QProgressDialog] = None
        self.font_size_label: Optional[QLabel] = None
        self.text_padding_label: Optional[QLabel] = None
        self.qr_padding_label: Optional[QLabel] = None
        self.font_family_combo: Optional[QFontComboBox] = None
        self.font_size_combo: Optional[QComboBox] = None
        self.tick_labels: list[QLabel] = []  # Store tick labels for cleanup

        # AI Generation attributes
        self.ai_thread: Optional[AIGenerationThread] = None
        self.generated_images: List[Image.Image] = []
        self.ai_tab_widget: Optional[QTabWidget] = None
        self.ai_provider_combo: Optional[QComboBox] = None
        self.ai_prompt_text: Optional[QTextEdit] = None
        self.ai_negative_prompt_text: Optional[QTextEdit] = None
        self.ai_width_spin: Optional[QSpinBox] = None
        self.ai_height_spin: Optional[QSpinBox] = None
        self.ai_num_images_spin: Optional[QSpinBox] = None
        self.ai_seed_spin: Optional[QSpinBox] = None
        self.ai_preview_grid: Optional[QGridLayout] = None
        self.ai_generate_btn: Optional[QPushButton] = None

        # Profile Management attributes
        self.config_store: Optional[ConfigStore] = None
        self.active_profile: Optional[ClientProfile] = None
        self.profile_table: Optional[QTableWidget] = None
        self.recent_profiles_menu: Optional[QMenu] = None
        self.profile_status_label: Optional[QLabel] = None

        # Setup menu bar and status bar FIRST (before other UI setup)
        if PROFILE_SYSTEM_AVAILABLE:
            self.setup_menu_bar()
            self.setup_status_bar()
            self.setup_window_icon()

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

        # Setup AI Generation tab if available
        if AI_AVAILABLE:
            self.setup_ai_generation_tab()
            self.setup_config_tab()

        # Setup Clients tab for profile management
        if PROFILE_SYSTEM_AVAILABLE and AI_AVAILABLE:
            self.setup_clients_tab()

        # Use timer to add tick labels after UI is fully rendered
        QTimer.singleShot(100, self.add_tick_labels)

        # Check and load default profile after all UI is set up
        if PROFILE_SYSTEM_AVAILABLE:
            QTimer.singleShot(500, self.check_and_load_default_profile)

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

        # Load font family and size (in points)
        font_pt = cfg.get("font_size", 72)  # Default 72pt
        font_pt = max(8, min(200, font_pt))  # Clamp to reasonable range

        # Get font family from config
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

        # Load padding values for sliders (direct pixel values)
        text_px = cfg.get("text_padding", 40)  # Default 40px
        text_px = max(0, min(500, text_px))  # Clamp to slider range

        qr_px = cfg.get("qr_padding", 15)  # Default 15px
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
        """Save config and run watermarking (updated for profile system)"""
        # Update legacy config dict (needed for qr_watermark.py)
        self.update_config_from_ui()

        # Save to active profile if exists, otherwise fall back to settings.json
        if (
            hasattr(self, "active_profile")
            and self.active_profile
            and self.config_store
        ):
            # Update active profile from UI
            self.update_active_profile_from_ui()
            # Save profile to YAML
            self.config_store.save_profile(self.active_profile)
            print(f"[INFO] Saved to profile: {self.active_profile.profile.slug}")
        else:
            # Fallback to legacy settings.json
            save_config(self.config)
            print("[INFO] Saved to settings.json (no active profile)")

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
                self.config["font_size"] = font_pt  # Save font size in points directly

        # Save padding values directly in pixels
        text_px = self.ui.textPaddingSlider.value()
        self.config["text_padding"] = text_px

        qr_px = self.ui.qrPaddingSlider.value()
        self.config["qr_padding"] = qr_px

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

        # Slug prefix and location from UI fields
        slug_prefix_edit = getattr(self, "slugPrefixEdit", None)
        if slug_prefix_edit:
            self.config["slug_prefix"] = slug_prefix_edit.text().strip()
        else:
            self.config.setdefault("slug_prefix", "")

        slug_location_edit = getattr(self, "slugLocationEdit", None)
        if slug_location_edit:
            self.config["slug_location"] = slug_location_edit.text().strip()
        else:
            self.config.setdefault("slug_location", "")

        # Optional advanced fields (keep if already present)
        self.config.setdefault("slug_max_words", 6)
        self.config.setdefault("slug_min_len", 3)
        self.config.setdefault("slug_stopwords", [])
        self.config.setdefault("slug_whitelist", [])

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
                QLineEdit,
                QLabel,
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

            # Slug prefix and location controls
            self.slugPrefixLabel = QLabel("Slug Prefix:", host)
            self.slugPrefixEdit = QLineEdit(host)
            self.slugPrefixEdit.setText(self.config.get("slug_prefix", ""))
            self.slugPrefixEdit.setPlaceholderText("e.g., send-out-cards, company-name")

            self.slugLocationLabel = QLabel("Slug Location:", host)
            self.slugLocationEdit = QLineEdit(host)
            self.slugLocationEdit.setText(self.config.get("slug_location", ""))
            self.slugLocationEdit.setPlaceholderText("e.g., ann-arbor, new-york-city")

            self.previewSeoBtn = QPushButton("Preview SEO Names", host)
            self.exportMapBtn = QPushButton("Export Mapping CSV", host)

            # Insert before Preview button when we can; otherwise append
            preview_index = None
            if isinstance(layout, QBoxLayout):
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() is self.ui.previewBtn:
                        preview_index = i
                        break
                if preview_index is None:
                    preview_index = layout.count()
                # Insert slug controls before preview button
                layout.insertWidget(preview_index, self.slugPrefixLabel)
                layout.insertWidget(preview_index + 1, self.slugPrefixEdit)
                layout.insertWidget(preview_index + 2, self.slugLocationLabel)
                layout.insertWidget(preview_index + 3, self.slugLocationEdit)
                layout.insertWidget(preview_index + 4, self.previewSeoBtn)
                layout.insertWidget(preview_index + 5, self.exportMapBtn)
                # Insert other controls after run button
                run_index = None
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() is self.ui.runBtn:
                        run_index = i
                        break
                if run_index is not None:
                    layout.insertWidget(run_index, self.collisionCombo)
                    layout.insertWidget(run_index + 1, self.recursiveCheck)
                else:
                    layout.addWidget(self.collisionCombo)
                    layout.addWidget(self.recursiveCheck)
            else:
                # Generic layouts (QGridLayout/QFormLayout/unknown): just append
                for w in (
                    self.slugPrefixLabel,
                    self.slugPrefixEdit,
                    self.slugLocationLabel,
                    self.slugLocationEdit,
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
            import os
            import rename_img
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

                actual_path = qr_watermark.ensure_unique_path(
                    full_path, strategy=collision_strategy
                )
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
            import os
            import csv
            import rename_img
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

    def setup_ai_generation_tab(self) -> None:
        """Setup AI Image Generation tab"""
        try:
            # Create tab widget if not exists
            if not hasattr(self, "ai_tab_widget") or self.ai_tab_widget is None:
                # Get the main vertical layout
                from PyQt6.QtWidgets import QVBoxLayout as VBoxLayout

                central_widget = self.centralWidget()
                if not central_widget:
                    print("Error: No central widget found")
                    return
                main_layout = central_widget.layout()
                if not main_layout or not isinstance(main_layout, VBoxLayout):
                    print("Error: No main layout found or not QVBoxLayout")
                    return

                # Create tab widget
                self.ai_tab_widget = QTabWidget()

                # Create Watermark tab widget
                watermark_tab = QWidget()
                watermark_layout = QVBoxLayout(watermark_tab)

                # Move existing formLayout to watermark tab
                if hasattr(self.ui, "formLayout"):
                    # Remove formLayout from main layout
                    main_layout.removeItem(self.ui.formLayout)
                    watermark_layout.addLayout(self.ui.formLayout)

                # Move preview and run buttons to watermark tab
                if hasattr(self.ui, "previewBtn"):
                    main_layout.removeWidget(self.ui.previewBtn)
                    watermark_layout.addWidget(self.ui.previewBtn)

                if hasattr(self.ui, "runBtn"):
                    main_layout.removeWidget(self.ui.runBtn)
                    watermark_layout.addWidget(self.ui.runBtn)

                # Add watermark tab as first tab
                self.ai_tab_widget.addTab(watermark_tab, "Watermark")

                # Add tab widget to main layout at the top (position 0)
                main_layout.insertWidget(0, self.ai_tab_widget)

            # Create AI Generation tab
            ai_widget = QWidget()
            ai_layout = QVBoxLayout(ai_widget)

            # Provider Selection Group
            provider_group = QGroupBox("Provider Selection")
            provider_layout = QVBoxLayout()

            provider_label = QLabel("AI Provider:")
            self.ai_provider_combo = QComboBox()
            self.ai_provider_combo.addItems(["fal", "ideogram", "stability"])
            self.ai_provider_combo.setToolTip("Select AI image generation provider")

            provider_layout.addWidget(provider_label)
            provider_layout.addWidget(self.ai_provider_combo)
            provider_group.setLayout(provider_layout)
            ai_layout.addWidget(provider_group)

            # Prompt Group
            prompt_group = QGroupBox("Image Generation")
            prompt_layout = QVBoxLayout()

            # Prompt
            prompt_label = QLabel("Prompt (describe the image):")
            self.ai_prompt_text = QTextEdit()
            self.ai_prompt_text.setPlaceholderText(
                "Example: A professional business card with modern design..."
            )
            self.ai_prompt_text.setMaximumHeight(100)

            # Negative Prompt
            neg_prompt_label = QLabel("Negative Prompt (what to avoid):")
            self.ai_negative_prompt_text = QTextEdit()
            self.ai_negative_prompt_text.setPlaceholderText(
                "Example: blurry, low quality, distorted..."
            )
            self.ai_negative_prompt_text.setMaximumHeight(60)

            prompt_layout.addWidget(prompt_label)
            prompt_layout.addWidget(self.ai_prompt_text)
            prompt_layout.addWidget(neg_prompt_label)
            prompt_layout.addWidget(self.ai_negative_prompt_text)
            prompt_group.setLayout(prompt_layout)
            ai_layout.addWidget(prompt_group)

            # Parameters Group
            params_group = QGroupBox("Generation Parameters")
            params_layout = QGridLayout()

            # Width
            params_layout.addWidget(QLabel("Width:"), 0, 0)
            self.ai_width_spin = QSpinBox()
            self.ai_width_spin.setRange(256, 2048)
            self.ai_width_spin.setValue(1024)
            self.ai_width_spin.setSingleStep(64)
            params_layout.addWidget(self.ai_width_spin, 0, 1)

            # Height
            params_layout.addWidget(QLabel("Height:"), 0, 2)
            self.ai_height_spin = QSpinBox()
            self.ai_height_spin.setRange(256, 2048)
            self.ai_height_spin.setValue(1024)
            self.ai_height_spin.setSingleStep(64)
            params_layout.addWidget(self.ai_height_spin, 0, 3)

            # Number of images
            params_layout.addWidget(QLabel("Number of Images:"), 1, 0)
            self.ai_num_images_spin = QSpinBox()
            self.ai_num_images_spin.setRange(1, 4)
            self.ai_num_images_spin.setValue(1)
            params_layout.addWidget(self.ai_num_images_spin, 1, 1)

            # Seed
            params_layout.addWidget(QLabel("Seed (0 = random):"), 1, 2)
            self.ai_seed_spin = QSpinBox()
            self.ai_seed_spin.setRange(0, 999999)
            self.ai_seed_spin.setValue(0)
            params_layout.addWidget(self.ai_seed_spin, 1, 3)

            params_group.setLayout(params_layout)
            ai_layout.addWidget(params_group)

            # Generate Button
            self.ai_generate_btn = QPushButton("Generate Images")
            self.ai_generate_btn.setMinimumHeight(40)
            self.ai_generate_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    font-size: 12pt;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """
            )
            self.ai_generate_btn.clicked.connect(self.generate_ai_images)
            ai_layout.addWidget(self.ai_generate_btn)

            # Preview Area
            preview_group = QGroupBox("Generated Images")
            preview_layout = QVBoxLayout()

            # Scroll area for image grid
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_widget = QWidget()
            self.ai_preview_grid = QGridLayout(scroll_widget)
            scroll_area.setWidget(scroll_widget)

            preview_layout.addWidget(scroll_area)
            preview_group.setLayout(preview_layout)
            ai_layout.addWidget(preview_group)

            # Add AI tab to tab widget
            if self.ai_tab_widget:
                self.ai_tab_widget.addTab(ai_widget, "AI Generation")

            print("AI Generation tab setup complete")

        except Exception as e:
            print(f"Error setting up AI Generation tab: {e}")
            import traceback

            traceback.print_exc()

    def setup_config_tab(self) -> None:
        """Setup Configuration tab for API keys and settings"""
        try:
            if not self.ai_tab_widget:
                print("Error: Tab widget not initialized")
                return

            # Create Config tab
            config_widget = QWidget()
            config_layout = QVBoxLayout(config_widget)

            # Scroll area for all config controls
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)

            # === AI Provider API Keys Section ===
            api_keys_group = QGroupBox("AI Provider API Keys")
            api_keys_layout = QGridLayout()

            # Fal.ai API Key
            api_keys_layout.addWidget(QLabel("Fal.ai API Key:"), 0, 0)
            self.fal_api_key_edit = QLineEdit()
            self.fal_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.fal_api_key_edit.setPlaceholderText("Enter your Fal.ai API key")
            api_keys_layout.addWidget(self.fal_api_key_edit, 0, 1)

            self.fal_show_key_btn = QPushButton("Show")
            self.fal_show_key_btn.setCheckable(True)
            self.fal_show_key_btn.setMaximumWidth(60)
            self.fal_show_key_btn.clicked.connect(
                lambda: self._toggle_password_visibility(
                    self.fal_api_key_edit, self.fal_show_key_btn
                )
            )
            api_keys_layout.addWidget(self.fal_show_key_btn, 0, 2)

            # Ideogram API Key
            api_keys_layout.addWidget(QLabel("Ideogram API Key:"), 1, 0)
            self.ideogram_api_key_edit = QLineEdit()
            self.ideogram_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.ideogram_api_key_edit.setPlaceholderText("Enter your Ideogram API key")
            api_keys_layout.addWidget(self.ideogram_api_key_edit, 1, 1)

            self.ideogram_show_key_btn = QPushButton("Show")
            self.ideogram_show_key_btn.setCheckable(True)
            self.ideogram_show_key_btn.setMaximumWidth(60)
            self.ideogram_show_key_btn.clicked.connect(
                lambda: self._toggle_password_visibility(
                    self.ideogram_api_key_edit, self.ideogram_show_key_btn
                )
            )
            api_keys_layout.addWidget(self.ideogram_show_key_btn, 1, 2)

            # Stability AI API Key
            api_keys_layout.addWidget(QLabel("Stability AI API Key:"), 2, 0)
            self.stability_api_key_edit = QLineEdit()
            self.stability_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.stability_api_key_edit.setPlaceholderText(
                "Enter your Stability AI API key"
            )
            api_keys_layout.addWidget(self.stability_api_key_edit, 2, 1)

            self.stability_show_key_btn = QPushButton("Show")
            self.stability_show_key_btn.setCheckable(True)
            self.stability_show_key_btn.setMaximumWidth(60)
            self.stability_show_key_btn.clicked.connect(
                lambda: self._toggle_password_visibility(
                    self.stability_api_key_edit, self.stability_show_key_btn
                )
            )
            api_keys_layout.addWidget(self.stability_show_key_btn, 2, 2)

            api_keys_group.setLayout(api_keys_layout)
            scroll_layout.addWidget(api_keys_group)

            # === Application Settings Section ===
            app_settings_group = QGroupBox("Application Settings")
            app_settings_layout = QGridLayout()

            # Note about settings
            settings_note = QLabel(
                "Note: Most watermark settings are configured in the Watermark tab.\n"
                "These are advanced configuration options."
            )
            settings_note.setStyleSheet("color: #666; font-style: italic;")
            app_settings_layout.addWidget(settings_note, 0, 0, 1, 2)

            # Add a few key settings
            row = 1
            app_settings_layout.addWidget(QLabel("Collision Strategy:"), row, 0)
            self.config_collision_combo = QComboBox()
            self.config_collision_combo.addItems(["counter", "timestamp"])
            app_settings_layout.addWidget(self.config_collision_combo, row, 1)

            row += 1
            app_settings_layout.addWidget(QLabel("Process Subfolders:"), row, 0)
            self.config_recursive_check = QCheckBox()
            app_settings_layout.addWidget(self.config_recursive_check, row, 1)

            app_settings_group.setLayout(app_settings_layout)
            scroll_layout.addWidget(app_settings_group)

            # Add stretch to push everything to top
            scroll_layout.addStretch()

            scroll_area.setWidget(scroll_content)
            config_layout.addWidget(scroll_area)

            # === Save Configuration Button ===
            save_config_btn = QPushButton("Save Configuration")
            save_config_btn.setMinimumHeight(40)
            save_config_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    font-size: 11pt;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """
            )
            save_config_btn.clicked.connect(self.save_configuration)
            config_layout.addWidget(save_config_btn)

            # Add Config tab to tab widget
            self.ai_tab_widget.addTab(config_widget, "Configuration")

            # Load existing configuration
            self._load_config_tab_values()

            print("Configuration tab setup complete")

        except Exception as e:
            print(f"Error setting up Configuration tab: {e}")
            import traceback

            traceback.print_exc()

    def _toggle_password_visibility(
        self, line_edit: QLineEdit, button: QPushButton
    ) -> None:
        """Toggle password visibility in a QLineEdit"""
        if button.isChecked():
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText("Hide")
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText("Show")

    def _load_config_tab_values(self) -> None:
        """Load current configuration values into Config tab"""
        try:
            # Load API keys from providers.yaml if it exists
            import os
            import yaml

            providers_file = "config/providers.yaml"
            if os.path.exists(providers_file):
                with open(providers_file, "r") as f:
                    providers_config = yaml.safe_load(f)
                    if providers_config:
                        # Support both old and new structure
                        providers = providers_config.get("providers", providers_config)

                        # Fal.ai
                        if "fal" in providers:
                            # New structure: fal.api_key
                            fal_key = providers["fal"].get("api_key", "")
                            # Old structure fallback: fal.credentials.api_key
                            if not fal_key and "credentials" in providers["fal"]:
                                fal_key = providers["fal"]["credentials"].get(
                                    "api_key", ""
                                )
                            if fal_key:
                                self.fal_api_key_edit.setText(fal_key)

                        # Ideogram
                        if "ideogram" in providers:
                            ideogram_key = providers["ideogram"].get("api_key", "")
                            if (
                                not ideogram_key
                                and "credentials" in providers["ideogram"]
                            ):
                                ideogram_key = providers["ideogram"]["credentials"].get(
                                    "api_key", ""
                                )
                            if ideogram_key:
                                self.ideogram_api_key_edit.setText(ideogram_key)

                        # Stability AI
                        if "stability" in providers:
                            stability_key = providers["stability"].get("api_key", "")
                            if (
                                not stability_key
                                and "credentials" in providers["stability"]
                            ):
                                stability_key = providers["stability"][
                                    "credentials"
                                ].get("api_key", "")
                            if stability_key:
                                self.stability_api_key_edit.setText(stability_key)

            # Load app settings
            collision = self.config.get("collision_strategy", "counter")
            idx = self.config_collision_combo.findText(collision)
            if idx >= 0:
                self.config_collision_combo.setCurrentIndex(idx)

            self.config_recursive_check.setChecked(
                bool(self.config.get("process_recursive", False))
            )

        except Exception as e:
            print(f"Error loading config tab values: {e}")

    def save_configuration(self) -> None:
        """Save configuration from Config tab"""
        try:
            import os
            import yaml

            # === Save API Keys to providers.yaml ===
            providers_file = "config/providers.yaml"
            providers_config: dict[str, Any] = {}

            # Fal.ai
            fal_key = self.fal_api_key_edit.text().strip()
            if fal_key:
                providers_config["fal"] = {"api_key": fal_key}

            # Ideogram
            ideogram_key = self.ideogram_api_key_edit.text().strip()
            if ideogram_key:
                providers_config["ideogram"] = {"api_key": ideogram_key}

            # Stability AI
            stability_key = self.stability_api_key_edit.text().strip()
            if stability_key:
                providers_config["stability"] = {"api_key": stability_key}

            # Save providers.yaml
            os.makedirs("config", exist_ok=True)
            with open(providers_file, "w") as f:
                yaml.dump(providers_config, f, default_flow_style=False)

            # === Save app settings to config ===
            self.config["collision_strategy"] = (
                self.config_collision_combo.currentText()
            )
            self.config["process_recursive"] = self.config_recursive_check.isChecked()
            save_config(self.config)

            QMessageBox.information(
                self,
                "Configuration Saved",
                "Configuration has been saved successfully!\n\n"
                "API keys: config/providers.yaml\n"
                "Settings: config/settings.json",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save configuration: {str(e)}"
            )

    def generate_ai_images(self) -> None:
        """Start AI image generation"""
        try:
            if not AI_AVAILABLE:
                QMessageBox.warning(
                    self,
                    "AI Not Available",
                    "AI generation modules are not installed or configured.",
                )
                return

            if self.ai_thread and self.ai_thread.isRunning():
                QMessageBox.information(
                    self,
                    "Generation in Progress",
                    "AI image generation is already running!",
                )
                return

            # Validate inputs
            if not self.ai_prompt_text or not self.ai_prompt_text.toPlainText().strip():
                QMessageBox.warning(
                    self,
                    "Missing Prompt",
                    "Please enter a prompt describing the image you want to generate.",
                )
                return

            # Get parameters
            provider = (
                self.ai_provider_combo.currentText()
                if self.ai_provider_combo
                else "fal"
            )
            prompt = self.ai_prompt_text.toPlainText().strip()
            negative_prompt = (
                self.ai_negative_prompt_text.toPlainText().strip()
                if self.ai_negative_prompt_text
                else ""
            )
            width = self.ai_width_spin.value() if self.ai_width_spin else 1024
            height = self.ai_height_spin.value() if self.ai_height_spin else 1024
            num_images = (
                self.ai_num_images_spin.value() if self.ai_num_images_spin else 1
            )
            seed = self.ai_seed_spin.value() if self.ai_seed_spin else None
            if seed == 0:
                seed = None

            # Disable generate button
            if self.ai_generate_btn:
                self.ai_generate_btn.setEnabled(False)
                self.ai_generate_btn.setText("Generating...")

            # Create progress dialog
            self.progress_dialog = QProgressDialog(
                "Initializing AI generation...", "Cancel", 0, 0, self
            )
            self.progress_dialog.setWindowTitle("Generating Images")
            self.progress_dialog.setModal(True)
            self.progress_dialog.show()

            # Create and start AI generation thread
            self.ai_thread = AIGenerationThread(
                provider_name=provider,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_images=num_images,
                seed=seed,
            )
            self.ai_thread.finished.connect(self.on_ai_generation_finished)
            self.ai_thread.error.connect(self.on_ai_generation_error)
            self.ai_thread.progress.connect(self.on_ai_generation_progress)
            self.ai_thread.start()

        except Exception as e:
            QMessageBox.critical(
                self, "Generation Error", f"Failed to start generation: {str(e)}"
            )
            if self.ai_generate_btn:
                self.ai_generate_btn.setEnabled(True)
                self.ai_generate_btn.setText("Generate Images")

    def on_ai_generation_progress(self, message: str) -> None:
        """Handle AI generation progress updates"""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)
        print(f"AI Generation Progress: {message}")

    def _auto_save_generated_images(self, images: List[Image.Image]) -> List[str]:
        """
        Auto-save generated images to generation_output_dir.

        Args:
            images: List of PIL Image objects to save

        Returns:
            List of saved file paths
        """
        try:
            # Determine output directory
            output_dir = None

            # Try to get from active profile first
            if hasattr(self, "active_profile") and self.active_profile:
                output_dir = self.active_profile.paths.generation_output_dir

            # Fallback to config
            if not output_dir:
                output_dir = self.config.get("generation_output_dir", "")

            # Final fallback to current directory
            if not output_dir:
                output_dir = os.path.join(os.getcwd(), "generated_images")

            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Save each image
            saved_paths = []
            timestamp = int(__import__("time").time())

            for idx, img in enumerate(images):
                filename = f"ai_generated_{timestamp}_{idx + 1}.png"
                filepath = os.path.join(output_dir, filename)
                img.save(filepath, "PNG")
                saved_paths.append(filepath)
                print(f"[SUCCESS] Saved generated image: {filepath}")

            return saved_paths

        except Exception as e:
            print(f"[ERROR] Failed to auto-save images: {e}")
            return []

    def on_ai_generation_finished(self, images: List[Image.Image]) -> None:
        """Handle successful AI image generation"""
        if self.ai_generate_btn:
            self.ai_generate_btn.setEnabled(True)
            self.ai_generate_btn.setText("Generate Images")

        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # Store generated images
        self.generated_images = images

        # Auto-save images to generation_output_dir
        saved_paths = self._auto_save_generated_images(images)

        # Display images in preview grid
        self.display_generated_images(images)

        # Show success message with save location
        if saved_paths:
            save_dir = os.path.dirname(saved_paths[0])
            QMessageBox.information(
                self,
                "Generation Complete",
                f"Successfully generated {len(images)} image(s)!\n\n"
                f"Images saved to:\n{save_dir}",
            )
        else:
            QMessageBox.information(
                self,
                "Generation Complete",
                f"Successfully generated {len(images)} image(s)!",
            )

    def on_ai_generation_error(self, error_msg: str) -> None:
        """Handle AI generation errors"""
        if self.ai_generate_btn:
            self.ai_generate_btn.setEnabled(True)
            self.ai_generate_btn.setText("Generate Images")

        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        QMessageBox.critical(
            self, "Generation Failed", f"AI image generation failed:\n\n{error_msg}"
        )

    def display_generated_images(self, images: List[Image.Image]) -> None:
        """Display generated images in preview grid"""
        try:
            if not self.ai_preview_grid:
                return

            # Clear existing preview
            while self.ai_preview_grid.count():
                item = self.ai_preview_grid.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()

            # Display images in grid (2 columns)
            for idx, img in enumerate(images):
                row = idx // 2
                col = idx % 2

                # Create image label
                img_label = QLabel()

                # Convert PIL to QPixmap
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                pix = QPixmap()
                pix.loadFromData(img_bytes.getvalue())

                # Scale to reasonable size
                pix = pix.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio)
                img_label.setPixmap(pix)
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Create container with save button
                container = QWidget()
                container_layout = QVBoxLayout(container)
                container_layout.addWidget(img_label)

                # Save button
                save_btn = QPushButton(f"Save Image {idx + 1}")
                save_btn.clicked.connect(
                    lambda checked, i=idx: self.save_generated_image(i)
                )
                container_layout.addWidget(save_btn)

                # Send to watermark button
                watermark_btn = QPushButton("Send to Watermark")
                watermark_btn.clicked.connect(
                    lambda checked, i=idx: self.send_to_watermark(i)
                )
                container_layout.addWidget(watermark_btn)

                self.ai_preview_grid.addWidget(container, row, col)

            print(f"Displayed {len(images)} generated images")

        except Exception as e:
            print(f"Error displaying images: {e}")
            import traceback

            traceback.print_exc()

    def save_generated_image(self, index: int) -> None:
        """Save a generated image to file"""
        try:
            if index >= len(self.generated_images):
                return

            img = self.generated_images[index]

            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Generated Image",
                os.path.join(os.getcwd(), f"ai_generated_{index + 1}.png"),
                "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*.*)",
            )

            if file_path:
                img.save(file_path)
                QMessageBox.information(
                    self, "Image Saved", f"Image saved to:\n{file_path}"
                )

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save image: {str(e)}")

    def send_to_watermark(self, index: int) -> None:
        """Send generated image to input directory for watermarking"""
        try:
            if index >= len(self.generated_images):
                return

            img = self.generated_images[index]

            # Get input directory from config
            input_dir = self.config.get("input_dir", "")
            if not input_dir or not os.path.isdir(input_dir):
                QMessageBox.warning(
                    self,
                    "Input Directory Not Set",
                    "Please set an input directory first in the Watermark tab.",
                )
                return

            # Generate filename
            timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_generated_{timestamp}_{index + 1}.png"
            file_path = os.path.join(input_dir, filename)

            # Save image
            img.save(file_path)

            QMessageBox.information(
                self,
                "Image Added",
                f"Image saved to input directory:\n{filename}\n\nYou can now apply watermark to it.",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to send image to watermark: {str(e)}"
            )

    # ========== PROFILE MANAGEMENT METHODS ==========

    def setup_menu_bar(self) -> None:
        """Create application menu bar with File and Help menus"""
        try:
            menubar = self.menuBar()
            assert menubar is not None

            # File Menu
            file_menu = menubar.addMenu("&File")
            assert file_menu is not None

            # Load Profile action
            load_profile_action = file_menu.addAction("&Load Profile...")
            assert load_profile_action is not None
            load_profile_action.setShortcut("Ctrl+O")
            load_profile_action.triggered.connect(self.show_profile_selector)

            # Recent Profiles submenu
            self.recent_profiles_menu = file_menu.addMenu("Recent Profiles")
            self.update_recent_profiles_menu()

            file_menu.addSeparator()

            # Exit action
            exit_action = file_menu.addAction("E&xit")
            assert exit_action is not None
            exit_action.setShortcut("Ctrl+Q")
            exit_action.triggered.connect(self.close)

            # Help Menu (future expansion)
            help_menu = menubar.addMenu("&Help")
            assert help_menu is not None
            about_action = help_menu.addAction("&About")
            assert about_action is not None
            about_action.triggered.connect(self.show_about_dialog)

            print("Menu bar setup complete")

        except Exception as e:
            print(f"Error setting up menu bar: {e}")
            import traceback

            traceback.print_exc()

    def setup_status_bar(self) -> None:
        """Create status bar for active profile indicator"""
        try:
            status_bar = self.statusBar()
            assert status_bar is not None
            self.profile_status_label = QLabel("No profile loaded")
            status_bar.addPermanentWidget(self.profile_status_label)
            print("Status bar setup complete")

        except Exception as e:
            print(f"Error setting up status bar: {e}")

    def update_status_bar(self, profile: Optional[ClientProfile] = None) -> None:
        """Update status bar with active profile info"""
        try:
            if profile and self.profile_status_label:
                text = f"Active Profile: {profile.profile.slug} | Last Modified: {profile.profile.modified}"
                self.profile_status_label.setText(text)
            elif self.profile_status_label:
                self.profile_status_label.setText("No profile loaded")

        except Exception as e:
            print(f"Error updating status bar: {e}")

    def setup_window_icon(self) -> None:
        """Set application window icon"""
        try:
            icon_paths = [
                "assets/icon.ico",
                "assets/icon.png",
                "icon.ico",
                "icon.png",
            ]

            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    print(f"Window icon loaded from: {icon_path}")
                    return

            print(
                "No window icon found (checked: assets/icon.ico, assets/icon.png, icon.ico, icon.png)"
            )

        except Exception as e:
            print(f"Error setting window icon: {e}")

    def show_about_dialog(self) -> None:
        """Show About dialog with Skippy image"""
        dialog = QDialog(self)
        dialog.setWindowTitle("About QR Watermark Wizard")
        dialog.setModal(True)

        layout = QVBoxLayout()

        # Add Skippy image at the top
        image_path = os.path.join(
            os.path.dirname(__file__), "images", "skippy_the_magnificient.png"
        )
        if os.path.exists(image_path):
            image_label = QLabel()
            pixmap = QPixmap(image_path)
            # Scale image to reasonable size if needed (max width 400px)
            if pixmap.width() > 400:
                pixmap = pixmap.scaledToWidth(
                    400, Qt.TransformationMode.SmoothTransformation
                )
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(image_label)

        # Add version and info text
        info_label = QLabel(
            "<h2>QR Watermark Wizard v3.0.0</h2>"
            "<p>AI-powered image generation and QR code watermarking tool.</p>"
            "<p><b>Rank Rocket Co (C) Copyright 2025 - All Rights Reserved</b></p>"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Add OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec()

    def update_recent_profiles_menu(self) -> None:
        """Update Recent Profiles submenu"""
        if not self.recent_profiles_menu:
            return

        try:
            # Clear existing items
            self.recent_profiles_menu.clear()

            # Get recent profiles
            if not self.config_store:
                self.config_store = ConfigStore()

            recent = self.config_store.get_recent_profiles()

            if not recent:
                no_recent_action = self.recent_profiles_menu.addAction(
                    "No recent profiles"
                )
                if no_recent_action:
                    no_recent_action.setEnabled(False)
                return

            # Add recent profiles (max 10)
            for slug in recent[:10]:
                try:
                    profile = self.config_store.load_profile(slug)
                    action = self.recent_profiles_menu.addAction(
                        f"{profile.profile.name} ({slug})"
                    )
                    if action:
                        action.triggered.connect(
                            lambda checked, s=slug: self.load_profile_into_ui(s)
                        )
                except Exception as e:
                    print(f"Error loading recent profile {slug}: {e}")

        except Exception as e:
            print(f"Error updating recent profiles menu: {e}")

    def show_profile_selector(self) -> None:
        """Show profile selector dialog"""
        try:
            if not self.config_store:
                self.config_store = ConfigStore()

            profiles = self.config_store.list_profiles()

            if not profiles:
                reply = QMessageBox.question(
                    self,
                    "No Profiles",
                    "No profiles found. Would you like to create one?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.show_profile_editor(None)
                return

            # Show profile selector dialog
            profile_names = []
            for slug in profiles:
                try:
                    profile = self.config_store.load_profile(slug)
                    profile_names.append(f"{profile.profile.name} ({slug})")
                except Exception:
                    profile_names.append(slug)

            selected, ok = QInputDialog.getItem(
                self,
                "Select Profile",
                "Choose a profile to load:",
                profile_names,
                0,
                False,
            )

            if ok and selected:
                # Extract slug from selection (text after last '(')
                slug = selected.split("(")[-1].rstrip(")")
                self.load_profile_into_ui(slug)

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to show profile selector: {str(e)}"
            )
            import traceback

            traceback.print_exc()

    def setup_clients_tab(self) -> None:
        """Setup Clients tab for profile management"""
        try:
            if not self.ai_tab_widget:
                print("Error: Tab widget not initialized")
                return

            # Create Clients tab widget
            clients_widget = QWidget()
            clients_layout = QVBoxLayout(clients_widget)

            # Toolbar at top
            toolbar = QHBoxLayout()

            create_btn = QPushButton("Create New Profile")
            create_btn.setStyleSheet(
                "background-color: #28a745; color: white; padding: 8px 16px; font-weight: bold;"
            )
            create_btn.clicked.connect(lambda: self.show_profile_editor(None))
            toolbar.addWidget(create_btn)

            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_profile_list)
            toolbar.addWidget(refresh_btn)

            toolbar.addStretch()
            clients_layout.addLayout(toolbar)

            # Profile table
            self.profile_table = QTableWidget()
            self.profile_table.setColumnCount(5)
            self.profile_table.setHorizontalHeaderLabels(
                ["Name", "Slug", "QR Link", "Last Modified", "Actions"]
            )

            # Table properties
            self.profile_table.setSelectionBehavior(
                QAbstractItemView.SelectionBehavior.SelectRows
            )
            self.profile_table.setEditTriggers(
                QAbstractItemView.EditTrigger.NoEditTriggers
            )

            # Column sizing
            header = self.profile_table.horizontalHeader()
            assert header is not None
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
            header.setSectionResizeMode(
                1, QHeaderView.ResizeMode.ResizeToContents
            )  # Slug
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # QR Link
            header.setSectionResizeMode(
                3, QHeaderView.ResizeMode.ResizeToContents
            )  # Modified
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Actions
            self.profile_table.setColumnWidth(4, 250)

            # Double-click to load profile
            self.profile_table.cellDoubleClicked.connect(
                self.on_profile_table_double_click
            )

            # Right-click context menu
            self.profile_table.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            self.profile_table.customContextMenuRequested.connect(
                self.show_profile_context_menu
            )

            clients_layout.addWidget(self.profile_table)

            # Add Clients tab (index 3, after Configuration)
            self.ai_tab_widget.addTab(clients_widget, "Clients")

            # Initialize ConfigStore
            if not self.config_store:
                self.config_store = ConfigStore()

            # Load profile list
            self.refresh_profile_list()

            print("Clients tab setup complete")

        except Exception as e:
            print(f"Error setting up Clients tab: {e}")
            import traceback

            traceback.print_exc()

    def refresh_profile_list(self) -> None:
        """Refresh profile table with current profiles"""
        try:
            if not self.profile_table:
                return

            if not self.config_store:
                self.config_store = ConfigStore()

            # Clear table
            self.profile_table.setRowCount(0)

            # Get profile slugs
            profile_slugs = self.config_store.list_profiles()

            if not profile_slugs:
                # Show empty state message
                self.profile_table.setRowCount(1)
                empty_msg = QTableWidgetItem(
                    "No profiles found. Click 'Create New Profile' to get started."
                )
                empty_msg.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.profile_table.setItem(0, 0, empty_msg)
                self.profile_table.setSpan(0, 0, 1, 5)
                return

            # Load and display each profile
            self.profile_table.setRowCount(len(profile_slugs))

            for row, slug in enumerate(profile_slugs):
                try:
                    profile = self.config_store.load_profile(slug)

                    # Name
                    name_item = QTableWidgetItem(profile.profile.name)
                    self.profile_table.setItem(row, 0, name_item)

                    # Slug
                    slug_item = QTableWidgetItem(profile.profile.slug)
                    slug_item.setForeground(QColor("#666"))
                    self.profile_table.setItem(row, 1, slug_item)

                    # QR Link (truncated)
                    qr_link = profile.watermark.qr_link
                    if len(qr_link) > 50:
                        qr_link = qr_link[:47] + "..."
                    qr_item = QTableWidgetItem(qr_link)
                    self.profile_table.setItem(row, 2, qr_item)

                    # Last Modified
                    modified_item = QTableWidgetItem(profile.profile.modified)
                    self.profile_table.setItem(row, 3, modified_item)

                    # Actions buttons
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(4, 4, 4, 4)
                    actions_layout.setSpacing(4)

                    load_btn = QPushButton("Load")
                    load_btn.setStyleSheet(
                        "background-color: #0078d4; color: white; padding: 4px 8px;"
                    )
                    load_btn.clicked.connect(
                        lambda checked, s=slug: self.load_profile_into_ui(s)
                    )

                    edit_btn = QPushButton("Edit")
                    edit_btn.setStyleSheet("padding: 4px 8px;")
                    edit_btn.clicked.connect(
                        lambda checked, s=slug: self.show_profile_editor(s)
                    )

                    delete_btn = QPushButton("Delete")
                    delete_btn.setStyleSheet(
                        "background-color: #d32f2f; color: white; padding: 4px 8px;"
                    )
                    delete_btn.clicked.connect(
                        lambda checked, s=slug: self.delete_profile_with_confirmation(s)
                    )

                    actions_layout.addWidget(load_btn)
                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(delete_btn)
                    actions_layout.addStretch()

                    self.profile_table.setCellWidget(row, 4, actions_widget)

                except Exception as e:
                    print(f"Error loading profile {slug}: {e}")
                    error_item = QTableWidgetItem(f"Error: {slug}")
                    self.profile_table.setItem(row, 0, error_item)

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load profile list: {str(e)}"
            )
            import traceback

            traceback.print_exc()

    def on_profile_table_double_click(self, row: int, column: int) -> None:
        """Handle double-click on profile table row"""
        try:
            if not self.profile_table:
                return
            slug_item = self.profile_table.item(row, 1)
            if slug_item:
                slug = slug_item.text()
                self.load_profile_into_ui(slug)
        except Exception as e:
            print(f"Error on double-click: {e}")

    def show_profile_context_menu(self, position) -> None:
        """Show right-click context menu for profile table"""
        try:
            if not self.profile_table:
                return

            row = self.profile_table.rowAt(position.y())
            if row < 0:
                return

            slug_item = self.profile_table.item(row, 1)
            if not slug_item:
                return

            slug = slug_item.text()

            menu = QMenu()

            load_action = menu.addAction("Load Profile")
            if load_action:
                load_action.triggered.connect(lambda: self.load_profile_into_ui(slug))

            edit_action = menu.addAction("Edit Profile")
            if edit_action:
                edit_action.triggered.connect(lambda: self.show_profile_editor(slug))

            duplicate_action = menu.addAction("Duplicate Profile")
            if duplicate_action:
                duplicate_action.triggered.connect(lambda: self.duplicate_profile(slug))

            menu.addSeparator()

            delete_action = menu.addAction("Delete Profile")
            if delete_action:
                delete_action.triggered.connect(
                    lambda: self.delete_profile_with_confirmation(slug)
                )

            viewport = self.profile_table.viewport()
            if viewport:
                menu.exec(viewport.mapToGlobal(position))

        except Exception as e:
            print(f"Error showing context menu: {e}")

    def load_profile_into_ui(self, slug: str) -> None:
        """Load profile and populate all UI fields"""
        try:
            if not self.config_store:
                self.config_store = ConfigStore()

            # Load profile
            profile = self.config_store.load_profile(slug)

            # Store active profile
            self.active_profile = profile

            # Update UI from profile
            self.update_ui_from_profile(profile)

            # Update recent profiles
            self.config_store.update_recent_profiles(slug)

            # Update window title
            self.setWindowTitle(
                f"Rank Rocket Watermark Wizard v3.0.0 - {profile.profile.name}"
            )

            # Update status bar
            self.update_status_bar(profile)

            # Update recent profiles menu
            self.update_recent_profiles_menu()

            # Switch to Watermark tab
            if self.ai_tab_widget:
                self.ai_tab_widget.setCurrentIndex(0)  # Watermark tab

            QMessageBox.information(
                self,
                "Profile Loaded",
                f"Loaded profile: {profile.profile.name}\n\n"
                f"QR Link: {profile.watermark.qr_link}\n"
                f"Input Dir: {profile.paths.input_dir}",
            )

        except FileNotFoundError:
            QMessageBox.critical(
                self, "Profile Not Found", f"Profile '{slug}' does not exist."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Load Error", f"Failed to load profile: {str(e)}"
            )
            import traceback

            traceback.print_exc()

    def update_ui_from_profile(self, profile: ClientProfile) -> None:
        """Populate UI fields from ClientProfile"""
        try:
            # Paths
            self.ui.inputDir.setText(profile.paths.input_dir)
            self.ui.outputDir.setText(profile.paths.output_dir)

            # Watermark settings
            self.ui.qrLink.setText(profile.watermark.qr_link)
            self.ui.overlayText.setPlainText(profile.watermark.text_overlay)

            # Font family
            if self.font_family_combo:
                font = QFont(profile.watermark.font_family)
                self.font_family_combo.setCurrentFont(font)

            # Font size (in points)
            font_pt = profile.watermark.font_size
            font_pt = max(8, min(200, font_pt))  # Clamp to reasonable range

            if self.font_size_combo:
                font_text = f"{font_pt}pt"
                index = self.font_size_combo.findText(font_text)
                if index >= 0:
                    self.font_size_combo.setCurrentIndex(index)

            # Padding sliders (direct pixel values)
            text_px = profile.watermark.text_padding
            text_px = max(0, min(500, text_px))
            self.ui.textPaddingSlider.setValue(text_px)

            qr_px = profile.watermark.qr_padding
            qr_px = max(0, min(300, qr_px))
            self.ui.qrPaddingSlider.setValue(qr_px)

            # SEO settings
            self.ui.seoRenameCheck.setChecked(profile.seo_naming.enabled)

            # Update extra controls if they exist
            if hasattr(self, "recursiveCheck") and self.recursiveCheck:
                self.recursiveCheck.setChecked(profile.seo_naming.process_recursive)

            if hasattr(self, "collisionCombo") and self.collisionCombo:
                idx = self.collisionCombo.findText(
                    profile.seo_naming.collision_strategy
                )
                if idx >= 0:
                    self.collisionCombo.setCurrentIndex(idx)

            if hasattr(self, "slugPrefixEdit") and self.slugPrefixEdit:
                self.slugPrefixEdit.setText(profile.seo_naming.slug_prefix)

            if hasattr(self, "slugLocationEdit") and self.slugLocationEdit:
                self.slugLocationEdit.setText(profile.seo_naming.slug_location)

            # Update internal config dict for backwards compatibility
            self.config = {
                "input_dir": profile.paths.input_dir,
                "output_dir": profile.paths.output_dir,
                "qr_link": profile.watermark.qr_link,
                "text_overlay": profile.watermark.text_overlay,
                "font_family": profile.watermark.font_family,
                "font_size": profile.watermark.font_size,
                "text_padding": profile.watermark.text_padding,
                "qr_padding": profile.watermark.qr_padding,
                "seo_rename": profile.seo_naming.enabled,
                "process_recursive": profile.seo_naming.process_recursive,
                "collision_strategy": profile.seo_naming.collision_strategy,
                "slug_prefix": profile.seo_naming.slug_prefix,
                "slug_location": profile.seo_naming.slug_location,
                "slug_max_words": profile.seo_naming.slug_max_words,
                "slug_min_len": profile.seo_naming.slug_min_len,
                "slug_stopwords": profile.seo_naming.slug_stopwords,
                "slug_whitelist": profile.seo_naming.slug_whitelist,
                "text_color": profile.watermark.text_color,
                "shadow_color": profile.watermark.shadow_color,
                "qr_size": profile.watermark.qr_size,
                "qr_opacity": profile.watermark.qr_opacity,
            }

            print(f"UI updated from profile: {profile.profile.slug}")

        except Exception as e:
            print(f"Error updating UI from profile: {e}")
            import traceback

            traceback.print_exc()
            raise

    def update_active_profile_from_ui(self) -> None:
        """Update active profile fields from current UI state"""
        if not hasattr(self, "active_profile") or not self.active_profile:
            return

        try:
            from datetime import datetime

            # Update paths
            self.active_profile.paths.input_dir = self.ui.inputDir.text()
            self.active_profile.paths.output_dir = self.ui.outputDir.text()

            # Update watermark
            self.active_profile.watermark.qr_link = self.ui.qrLink.text()
            self.active_profile.watermark.text_overlay = (
                self.ui.overlayText.toPlainText()
            )

            # Font family
            if self.font_family_combo:
                self.active_profile.watermark.font_family = (
                    self.font_family_combo.currentFont().family()
                )

            # Font size (in points)
            if self.font_size_combo:
                font_text = self.font_size_combo.currentText()
                if font_text.endswith("pt"):
                    font_pt = int(font_text[:-2])
                    self.active_profile.watermark.font_size = font_pt

            # Padding (direct pixel values)
            text_px = self.ui.textPaddingSlider.value()
            self.active_profile.watermark.text_padding = text_px

            qr_px = self.ui.qrPaddingSlider.value()
            self.active_profile.watermark.qr_padding = qr_px

            # SEO settings
            self.active_profile.seo_naming.enabled = self.ui.seoRenameCheck.isChecked()

            if hasattr(self, "recursiveCheck") and self.recursiveCheck:
                self.active_profile.seo_naming.process_recursive = (
                    self.recursiveCheck.isChecked()
                )

            if hasattr(self, "collisionCombo") and self.collisionCombo:
                self.active_profile.seo_naming.collision_strategy = (
                    self.collisionCombo.currentText()
                )

            if hasattr(self, "slugPrefixEdit") and self.slugPrefixEdit:
                self.active_profile.seo_naming.slug_prefix = (
                    self.slugPrefixEdit.text().strip()
                )

            if hasattr(self, "slugLocationEdit") and self.slugLocationEdit:
                self.active_profile.seo_naming.slug_location = (
                    self.slugLocationEdit.text().strip()
                )

            # Update modified timestamp
            self.active_profile.profile.modified = datetime.now().strftime("%Y-%m-%d")

        except Exception as e:
            print(f"Error updating active profile from UI: {e}")
            import traceback

            traceback.print_exc()
            raise

    def show_profile_editor(self, slug: Optional[str]) -> None:
        """Show profile editor dialog (create or edit)"""
        try:
            from datetime import datetime

            if not self.config_store:
                self.config_store = ConfigStore()

            # Load existing profile or create new
            if slug:
                profile = self.config_store.load_profile(slug)
                dialog_title = f"Edit Profile: {profile.profile.name}"
            else:
                # Create new profile with defaults
                from qrmr.config_schema import (
                    ClientProfile,
                    GenerationConfig,
                    PathsConfig,
                    ProfileMetadata,
                    ProvidersConfig,
                    SEONamingConfig,
                    UploadConfig,
                    WatermarkConfig,
                )

                now = datetime.now().strftime("%Y-%m-%d")
                profile = ClientProfile(
                    profile=ProfileMetadata(
                        name="New Client",
                        slug="new-client",
                        client_id="new_client",
                        created=now,
                        modified=now,
                    ),
                    paths=PathsConfig(
                        generation_output_dir="",
                        input_dir="",
                        output_dir="",
                        archive_dir=None,
                    ),
                    generation=GenerationConfig(),
                    providers=ProvidersConfig(),
                    watermark=WatermarkConfig(
                        qr_link="https://example.com", text_overlay=""
                    ),
                    seo_naming=SEONamingConfig(),
                    upload=UploadConfig(),
                )
                dialog_title = "Create New Profile"

            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(dialog_title)
            dialog.setModal(True)
            dialog.resize(700, 600)

            layout = QVBoxLayout(dialog)

            # Create tab widget for sections
            tab_widget = QTabWidget()

            # Tab 1: Profile Metadata
            metadata_tab = self._create_metadata_tab(profile)
            tab_widget.addTab(metadata_tab, "Profile Info")

            # Tab 2: Paths
            paths_tab = self._create_paths_tab(profile)
            tab_widget.addTab(paths_tab, "Paths")

            # Tab 3: Watermark
            watermark_tab = self._create_watermark_tab(profile)
            tab_widget.addTab(watermark_tab, "Watermark")

            # Tab 4: SEO Naming
            seo_tab = self._create_seo_tab(profile)
            tab_widget.addTab(seo_tab, "SEO Naming")

            # Tab 5: AI Generation (optional)
            generation_tab = self._create_generation_tab(profile)
            tab_widget.addTab(generation_tab, "AI Generation")

            layout.addWidget(tab_widget)

            # Button box
            button_box = QHBoxLayout()

            save_btn = QPushButton("Save Profile")
            save_btn.setStyleSheet(
                "background-color: #28a745; color: white; padding: 8px 16px; font-weight: bold;"
            )
            save_btn.clicked.connect(
                lambda: self._save_profile_from_dialog(dialog, profile, slug)
            )

            cancel_btn = QPushButton("Cancel")
            cancel_btn.setStyleSheet("padding: 8px 16px;")
            cancel_btn.clicked.connect(dialog.reject)

            button_box.addStretch()
            button_box.addWidget(cancel_btn)
            button_box.addWidget(save_btn)

            layout.addLayout(button_box)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self, "Editor Error", f"Failed to open profile editor: {str(e)}"
            )
            import traceback

            traceback.print_exc()

    def _create_metadata_tab(self, profile: ClientProfile) -> QWidget:
        """Create Profile Metadata tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Profile Information")
        form = QGridLayout()

        # Name
        form.addWidget(QLabel("Profile Name:"), 0, 0)
        name_edit = QLineEdit(profile.profile.name)
        name_edit.setObjectName("name_edit")
        form.addWidget(name_edit, 0, 1)

        # Slug (auto-generated from name)
        form.addWidget(QLabel("Slug (URL-friendly):"), 1, 0)
        slug_edit = QLineEdit(profile.profile.slug)
        slug_edit.setObjectName("slug_edit")
        slug_edit.setPlaceholderText("Auto-generated from name")
        form.addWidget(slug_edit, 1, 1)

        # Auto-generate slug button
        auto_slug_btn = QPushButton("Auto-Generate Slug")
        auto_slug_btn.clicked.connect(
            lambda: self._auto_generate_slug(name_edit, slug_edit)
        )
        form.addWidget(auto_slug_btn, 1, 2)

        # Client ID
        form.addWidget(QLabel("Client ID:"), 2, 0)
        client_id_edit = QLineEdit(profile.profile.client_id)
        client_id_edit.setObjectName("client_id_edit")
        form.addWidget(client_id_edit, 2, 1)

        # Created/Modified (read-only)
        form.addWidget(QLabel("Created:"), 3, 0)
        created_label = QLabel(profile.profile.created)
        created_label.setStyleSheet("color: #666;")
        form.addWidget(created_label, 3, 1)

        form.addWidget(QLabel("Last Modified:"), 4, 0)
        modified_label = QLabel(profile.profile.modified)
        modified_label.setStyleSheet("color: #666;")
        form.addWidget(modified_label, 4, 1)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()

        return widget

    def _create_paths_tab(self, profile: ClientProfile) -> QWidget:
        """Create Paths Configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Directory Paths")
        form = QGridLayout()

        # Input Directory
        form.addWidget(QLabel("Input Directory:"), 0, 0)
        input_dir_edit = QLineEdit(profile.paths.input_dir)
        input_dir_edit.setObjectName("input_dir_edit")
        form.addWidget(input_dir_edit, 0, 1)
        input_browse_btn = QPushButton("Browse...")
        input_browse_btn.clicked.connect(lambda: self._browse_directory(input_dir_edit))
        form.addWidget(input_browse_btn, 0, 2)

        # Output Directory
        form.addWidget(QLabel("Output Directory:"), 1, 0)
        output_dir_edit = QLineEdit(profile.paths.output_dir)
        output_dir_edit.setObjectName("output_dir_edit")
        form.addWidget(output_dir_edit, 1, 1)
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(
            lambda: self._browse_directory(output_dir_edit)
        )
        form.addWidget(output_browse_btn, 1, 2)

        # Generation Output Directory
        form.addWidget(QLabel("AI Generation Output:"), 2, 0)
        gen_dir_edit = QLineEdit(profile.paths.generation_output_dir)
        gen_dir_edit.setObjectName("gen_dir_edit")
        form.addWidget(gen_dir_edit, 2, 1)
        gen_browse_btn = QPushButton("Browse...")
        gen_browse_btn.clicked.connect(lambda: self._browse_directory(gen_dir_edit))
        form.addWidget(gen_browse_btn, 2, 2)

        # Archive Directory (optional)
        form.addWidget(QLabel("Archive Directory (optional):"), 3, 0)
        archive_dir_edit = QLineEdit(profile.paths.archive_dir or "")
        archive_dir_edit.setObjectName("archive_dir_edit")
        form.addWidget(archive_dir_edit, 3, 1)
        archive_browse_btn = QPushButton("Browse...")
        archive_browse_btn.clicked.connect(
            lambda: self._browse_directory(archive_dir_edit)
        )
        form.addWidget(archive_browse_btn, 3, 2)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()

        return widget

    def _create_watermark_tab(self, profile: ClientProfile) -> QWidget:
        """Create Watermark Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scroll area for all settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # QR Code Settings Group
        qr_group = QGroupBox("QR Code Settings")
        qr_form = QGridLayout()

        qr_form.addWidget(QLabel("QR Link URL:"), 0, 0)
        qr_link_edit = QLineEdit(profile.watermark.qr_link)
        qr_link_edit.setObjectName("qr_link_edit")
        qr_form.addWidget(qr_link_edit, 0, 1)

        qr_form.addWidget(QLabel("QR Size (pixels):"), 1, 0)
        qr_size_spin = QSpinBox()
        qr_size_spin.setObjectName("qr_size_spin")
        qr_size_spin.setRange(50, 500)
        qr_size_spin.setSingleStep(10)
        qr_size_spin.setValue(profile.watermark.qr_size)
        qr_form.addWidget(qr_size_spin, 1, 1)

        qr_form.addWidget(QLabel("QR Opacity (0.0-1.0):"), 2, 0)
        qr_opacity_spin = QDoubleSpinBox()
        qr_opacity_spin.setObjectName("qr_opacity_spin")
        qr_opacity_spin.setRange(0.0, 1.0)
        qr_opacity_spin.setSingleStep(0.05)
        qr_opacity_spin.setValue(profile.watermark.qr_opacity)
        qr_form.addWidget(qr_opacity_spin, 2, 1)

        qr_form.addWidget(QLabel("QR Padding (pixels):"), 3, 0)
        qr_padding_spin = QSpinBox()
        qr_padding_spin.setObjectName("qr_padding_spin")
        qr_padding_spin.setRange(0, 100)
        qr_padding_spin.setSingleStep(5)
        qr_padding_spin.setValue(profile.watermark.qr_padding)
        qr_form.addWidget(qr_padding_spin, 3, 1)

        qr_group.setLayout(qr_form)
        scroll_layout.addWidget(qr_group)

        # Text Overlay Settings Group
        text_group = QGroupBox("Text Overlay Settings")
        text_form = QGridLayout()

        text_form.addWidget(QLabel("Text Overlay:"), 0, 0)
        text_overlay_edit = QTextEdit()
        text_overlay_edit.setObjectName("text_overlay_edit")
        text_overlay_edit.setPlainText(profile.watermark.text_overlay)
        text_overlay_edit.setMaximumHeight(60)
        text_form.addWidget(text_overlay_edit, 0, 1)

        text_form.addWidget(QLabel("Font Family:"), 1, 0)
        font_family_combo = QFontComboBox()
        font_family_combo.setObjectName("font_family_combo")
        font_family_combo.setCurrentFont(QFont(profile.watermark.font_family))
        text_form.addWidget(font_family_combo, 1, 1)

        text_form.addWidget(QLabel("Font Size (pt):"), 2, 0)
        font_size_spin = QSpinBox()
        font_size_spin.setObjectName("font_size_spin")
        font_size_spin.setRange(8, 200)
        font_size_spin.setSingleStep(1)
        font_size_spin.setValue(profile.watermark.font_size)
        text_form.addWidget(font_size_spin, 2, 1)

        text_form.addWidget(QLabel("Text Padding (pixels):"), 3, 0)
        text_padding_spin = QSpinBox()
        text_padding_spin.setObjectName("text_padding_spin")
        text_padding_spin.setRange(0, 500)
        text_padding_spin.setSingleStep(10)
        text_padding_spin.setValue(profile.watermark.text_padding)
        text_form.addWidget(text_padding_spin, 3, 1)

        text_group.setLayout(text_form)
        scroll_layout.addWidget(text_group)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def _create_seo_tab(self, profile: ClientProfile) -> QWidget:
        """Create SEO Naming tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("SEO Filename Settings")
        form = QGridLayout()

        # Enabled checkbox
        form.addWidget(QLabel("Enable SEO Renaming:"), 0, 0)
        seo_enabled_check = QCheckBox()
        seo_enabled_check.setObjectName("seo_enabled_check")
        seo_enabled_check.setChecked(profile.seo_naming.enabled)
        form.addWidget(seo_enabled_check, 0, 1)

        # Slug Prefix
        form.addWidget(QLabel("Slug Prefix:"), 1, 0)
        slug_prefix_edit = QLineEdit(profile.seo_naming.slug_prefix)
        slug_prefix_edit.setObjectName("slug_prefix_edit")
        slug_prefix_edit.setPlaceholderText("e.g., best-dumpster-rental")
        form.addWidget(slug_prefix_edit, 1, 1)

        # Slug Location
        form.addWidget(QLabel("Slug Location:"), 2, 0)
        slug_location_edit = QLineEdit(profile.seo_naming.slug_location)
        slug_location_edit.setObjectName("slug_location_edit")
        slug_location_edit.setPlaceholderText("e.g., Tampa, Chicago")
        form.addWidget(slug_location_edit, 2, 1)

        # Process Recursive
        form.addWidget(QLabel("Process Subfolders:"), 3, 0)
        recursive_check = QCheckBox()
        recursive_check.setObjectName("recursive_check")
        recursive_check.setChecked(profile.seo_naming.process_recursive)
        form.addWidget(recursive_check, 3, 1)

        # Collision Strategy
        form.addWidget(QLabel("Collision Strategy:"), 4, 0)
        collision_combo = QComboBox()
        collision_combo.setObjectName("collision_combo")
        collision_combo.addItems(["counter", "timestamp"])
        idx = collision_combo.findText(profile.seo_naming.collision_strategy)
        if idx >= 0:
            collision_combo.setCurrentIndex(idx)
        form.addWidget(collision_combo, 4, 1)

        # Max Words
        form.addWidget(QLabel("Max Words in Slug:"), 5, 0)
        max_words_spin = QSpinBox()
        max_words_spin.setObjectName("max_words_spin")
        max_words_spin.setRange(1, 15)
        max_words_spin.setValue(profile.seo_naming.slug_max_words)
        form.addWidget(max_words_spin, 5, 1)

        # Min Length
        form.addWidget(QLabel("Min Slug Length:"), 6, 0)
        min_len_spin = QSpinBox()
        min_len_spin.setObjectName("min_len_spin")
        min_len_spin.setRange(1, 10)
        min_len_spin.setValue(profile.seo_naming.slug_min_len)
        form.addWidget(min_len_spin, 6, 1)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()

        return widget

    def _create_generation_tab(self, profile: ClientProfile) -> QWidget:
        """Create AI Generation Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("AI Generation Settings (Optional)")
        form = QGridLayout()

        # Mode
        form.addWidget(QLabel("Generation Mode:"), 0, 0)
        gen_mode_combo = QComboBox()
        gen_mode_combo.setObjectName("gen_mode_combo")
        gen_mode_combo.addItems(["auto", "manual", "disabled"])
        idx = gen_mode_combo.findText(profile.generation.mode)
        if idx >= 0:
            gen_mode_combo.setCurrentIndex(idx)
        form.addWidget(gen_mode_combo, 0, 1)

        # Count
        form.addWidget(QLabel("Images to Generate:"), 1, 0)
        gen_count_spin = QSpinBox()
        gen_count_spin.setObjectName("gen_count_spin")
        gen_count_spin.setRange(1, 10)
        gen_count_spin.setValue(profile.generation.count)
        form.addWidget(gen_count_spin, 1, 1)

        # Dimensions
        form.addWidget(QLabel("Width:"), 2, 0)
        gen_width_spin = QSpinBox()
        gen_width_spin.setObjectName("gen_width_spin")
        gen_width_spin.setRange(256, 2048)
        gen_width_spin.setSingleStep(64)
        gen_width_spin.setValue(profile.generation.width)
        form.addWidget(gen_width_spin, 2, 1)

        form.addWidget(QLabel("Height:"), 3, 0)
        gen_height_spin = QSpinBox()
        gen_height_spin.setObjectName("gen_height_spin")
        gen_height_spin.setRange(256, 2048)
        gen_height_spin.setSingleStep(64)
        gen_height_spin.setValue(profile.generation.height)
        form.addWidget(gen_height_spin, 3, 1)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()

        return widget

    def _auto_generate_slug(self, name_edit: QLineEdit, slug_edit: QLineEdit) -> None:
        """Auto-generate slug from profile name"""
        name = name_edit.text()
        slug = slugify(name)
        slug_edit.setText(slug)

    def _browse_directory(self, line_edit: QLineEdit) -> None:
        """Browse for directory and update line edit"""
        start_dir = line_edit.text() or os.getcwd()
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", start_dir
        )
        if directory:
            line_edit.setText(directory)

    def _save_profile_from_dialog(
        self, dialog: QDialog, profile: ClientProfile, original_slug: Optional[str]
    ) -> None:
        """Save profile from dialog widgets"""
        try:
            from datetime import datetime

            # Initialize config_store if needed
            if not self.config_store:
                self.config_store = ConfigStore()

            # Extract values from dialog widgets (using findChild)

            # Metadata
            name_edit = dialog.findChild(QLineEdit, "name_edit")
            slug_edit = dialog.findChild(QLineEdit, "slug_edit")
            client_id_edit = dialog.findChild(QLineEdit, "client_id_edit")

            if not name_edit or not slug_edit or not client_id_edit:
                raise ValueError("Required metadata fields not found")

            new_slug = slug_edit.text().strip()
            if not new_slug:
                QMessageBox.warning(self, "Validation Error", "Slug cannot be empty")
                return

            # Check slug uniqueness (if creating new or slug changed)
            if new_slug != original_slug:
                if self.config_store.profile_exists(new_slug):
                    QMessageBox.warning(
                        self,
                        "Slug Exists",
                        f"Profile with slug '{new_slug}' already exists. Please choose a different slug.",
                    )
                    return

            # Update profile metadata
            profile.profile.name = name_edit.text().strip()
            profile.profile.slug = new_slug
            profile.profile.client_id = client_id_edit.text().strip()
            profile.profile.modified = datetime.now().strftime("%Y-%m-%d")

            # Paths
            input_dir_edit = dialog.findChild(QLineEdit, "input_dir_edit")
            output_dir_edit = dialog.findChild(QLineEdit, "output_dir_edit")
            gen_dir_edit = dialog.findChild(QLineEdit, "gen_dir_edit")
            archive_dir_edit = dialog.findChild(QLineEdit, "archive_dir_edit")

            if input_dir_edit:
                profile.paths.input_dir = input_dir_edit.text().strip()
            if output_dir_edit:
                profile.paths.output_dir = output_dir_edit.text().strip()
            if gen_dir_edit:
                profile.paths.generation_output_dir = gen_dir_edit.text().strip()
            if archive_dir_edit:
                archive_val = archive_dir_edit.text().strip()
                profile.paths.archive_dir = archive_val if archive_val else None

            # Watermark
            qr_link_edit = dialog.findChild(QLineEdit, "qr_link_edit")
            if qr_link_edit:
                qr_link = qr_link_edit.text().strip()
                if not qr_link.startswith("http"):
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "QR Link must be a valid URL starting with http:// or https://",
                    )
                    return
                profile.watermark.qr_link = qr_link

            qr_size_spin = dialog.findChild(QSpinBox, "qr_size_spin")
            if qr_size_spin:
                profile.watermark.qr_size = qr_size_spin.value()

            qr_opacity_spin = dialog.findChild(QDoubleSpinBox, "qr_opacity_spin")
            if qr_opacity_spin:
                profile.watermark.qr_opacity = qr_opacity_spin.value()

            qr_padding_spin = dialog.findChild(QSpinBox, "qr_padding_spin")
            if qr_padding_spin:
                profile.watermark.qr_padding = qr_padding_spin.value()

            text_overlay_edit = dialog.findChild(QTextEdit, "text_overlay_edit")
            if text_overlay_edit:
                profile.watermark.text_overlay = text_overlay_edit.toPlainText()

            font_family_combo = dialog.findChild(QFontComboBox, "font_family_combo")
            if font_family_combo:
                profile.watermark.font_family = font_family_combo.currentFont().family()

            font_size_spin = dialog.findChild(QSpinBox, "font_size_spin")
            if font_size_spin:
                profile.watermark.font_size = font_size_spin.value()

            text_padding_spin = dialog.findChild(QSpinBox, "text_padding_spin")
            if text_padding_spin:
                profile.watermark.text_padding = text_padding_spin.value()

            # SEO Naming
            seo_enabled_check = dialog.findChild(QCheckBox, "seo_enabled_check")
            if seo_enabled_check:
                profile.seo_naming.enabled = seo_enabled_check.isChecked()

            slug_prefix_edit = dialog.findChild(QLineEdit, "slug_prefix_edit")
            if slug_prefix_edit:
                profile.seo_naming.slug_prefix = slug_prefix_edit.text().strip()

            slug_location_edit = dialog.findChild(QLineEdit, "slug_location_edit")
            if slug_location_edit:
                profile.seo_naming.slug_location = slug_location_edit.text().strip()

            recursive_check = dialog.findChild(QCheckBox, "recursive_check")
            if recursive_check:
                profile.seo_naming.process_recursive = recursive_check.isChecked()

            collision_combo = dialog.findChild(QComboBox, "collision_combo")
            if collision_combo:
                profile.seo_naming.collision_strategy = collision_combo.currentText()

            max_words_spin = dialog.findChild(QSpinBox, "max_words_spin")
            if max_words_spin:
                profile.seo_naming.slug_max_words = max_words_spin.value()

            min_len_spin = dialog.findChild(QSpinBox, "min_len_spin")
            if min_len_spin:
                profile.seo_naming.slug_min_len = min_len_spin.value()

            # Generation (optional)
            gen_mode_combo = dialog.findChild(QComboBox, "gen_mode_combo")
            if gen_mode_combo:
                profile.generation.mode = gen_mode_combo.currentText()

            gen_count_spin = dialog.findChild(QSpinBox, "gen_count_spin")
            if gen_count_spin:
                profile.generation.count = gen_count_spin.value()

            gen_width_spin = dialog.findChild(QSpinBox, "gen_width_spin")
            if gen_width_spin:
                profile.generation.width = gen_width_spin.value()

            gen_height_spin = dialog.findChild(QSpinBox, "gen_height_spin")
            if gen_height_spin:
                profile.generation.height = gen_height_spin.value()

            # Save profile
            self.config_store.save_profile(profile)

            # If slug changed and we're editing, delete old profile
            if original_slug and original_slug != new_slug:
                self.config_store.delete_profile(original_slug)

            # Close dialog
            dialog.accept()

            # Refresh profile list
            self.refresh_profile_list()

            # Show success message
            QMessageBox.information(
                self,
                "Profile Saved",
                f"Profile '{profile.profile.name}' saved successfully!",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save profile: {str(e)}"
            )
            import traceback

            traceback.print_exc()

    def delete_profile_with_confirmation(self, slug: str) -> None:
        """Delete profile after confirmation"""
        try:
            if not self.config_store:
                self.config_store = ConfigStore()

            # Load profile to get name
            try:
                profile = self.config_store.load_profile(slug)
                profile_name = profile.profile.name
            except Exception:
                profile_name = slug

            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete profile:\n\n{profile_name} ({slug})\n\n"
                "This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Check if this is the active profile
                if hasattr(self, "active_profile") and self.active_profile:
                    if self.active_profile.profile.slug == slug:
                        # Clear active profile
                        self.active_profile = None
                        self.setWindowTitle("Rank Rocket Watermark Wizard v3.0.0")
                        self.update_status_bar(None)

                # Delete profile
                self.config_store.delete_profile(slug)

                # Refresh list
                self.refresh_profile_list()

                QMessageBox.information(
                    self,
                    "Profile Deleted",
                    f"Profile '{profile_name}' has been deleted.",
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Delete Error", f"Failed to delete profile: {str(e)}"
            )
            import traceback

            traceback.print_exc()

    def duplicate_profile(self, slug: str) -> None:
        """Duplicate an existing profile"""
        try:
            from datetime import datetime

            if not self.config_store:
                self.config_store = ConfigStore()

            # Load original profile
            profile = self.config_store.load_profile(slug)

            # Create new slug
            base_slug = f"{slug}-copy"
            new_slug = base_slug
            counter = 1
            while self.config_store.profile_exists(new_slug):
                new_slug = f"{base_slug}-{counter}"
                counter += 1

            # Update metadata
            profile.profile.name = f"{profile.profile.name} (Copy)"
            profile.profile.slug = new_slug
            profile.profile.created = datetime.now().strftime("%Y-%m-%d")
            profile.profile.modified = datetime.now().strftime("%Y-%m-%d")

            # Save duplicate
            self.config_store.save_profile(profile)

            # Refresh list
            self.refresh_profile_list()

            QMessageBox.information(
                self,
                "Profile Duplicated",
                f"Profile duplicated as: {profile.profile.name}\n\nSlug: {new_slug}",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Duplicate Error", f"Failed to duplicate profile: {str(e)}"
            )
            import traceback

            traceback.print_exc()

    def migrate_legacy_settings(self) -> Optional[ClientProfile]:
        """Migrate settings.json to default-client profile"""
        try:
            from datetime import datetime
            from qrmr.config_schema import (
                ClientProfile,
                GenerationConfig,
                PathsConfig,
                ProfileMetadata,
                ProvidersConfig,
                SEONamingConfig,
                UploadConfig,
                WatermarkConfig,
            )

            settings_path = "config/settings.json"
            if not os.path.exists(settings_path):
                print("No settings.json found - skipping migration")
                return None

            # Load legacy settings
            legacy_config = load_config(settings_path)

            print("Migrating legacy settings.json to ClientProfile...")

            # Create default profile from legacy settings
            now = datetime.now().strftime("%Y-%m-%d")

            # Determine generation_output_dir based on input_dir
            input_dir = legacy_config.get("input_dir", "")
            if input_dir:
                # Create sibling directory for AI-generated images
                # E.g., if input_dir is "D:/Clients/ABC/images/original"
                # then generation_output_dir is "D:/Clients/ABC/images/generated"
                parent_dir = os.path.dirname(input_dir)
                generation_output_dir = os.path.join(parent_dir, "generated")
            else:
                # Fallback to local directory
                generation_output_dir = "./generated_images"

            profile = ClientProfile(
                profile=ProfileMetadata(
                    name="Default Client (Migrated)",
                    slug="default-client",
                    client_id="default",
                    created=now,
                    modified=now,
                ),
                paths=PathsConfig(
                    generation_output_dir=generation_output_dir,
                    input_dir=input_dir,
                    output_dir=legacy_config.get("output_dir", ""),
                    archive_dir=None,
                ),
                generation=GenerationConfig(),  # Use defaults
                providers=ProvidersConfig(),  # Use defaults
                watermark=WatermarkConfig(
                    qr_link=legacy_config.get("qr_link", "https://example.com"),
                    qr_size=legacy_config.get("qr_size", 150),  # Default 150px
                    qr_opacity=legacy_config.get("qr_opacity", 0.85),
                    qr_padding=legacy_config.get("qr_padding", 15),  # Default 15px
                    text_overlay=legacy_config.get("text_overlay", ""),
                    text_color=legacy_config.get("text_color", [255, 255, 255]),
                    shadow_color=legacy_config.get("shadow_color", [0, 0, 0, 128]),
                    font_family=legacy_config.get("font_family", "arial"),
                    font_size=legacy_config.get("font_size", 72),  # Default 72pt
                    text_padding=legacy_config.get("text_padding", 40),  # Default 40px
                ),
                seo_naming=SEONamingConfig(
                    enabled=legacy_config.get("seo_rename", False),
                    process_recursive=legacy_config.get("process_recursive", False),
                    collision_strategy=legacy_config.get(
                        "collision_strategy", "counter"
                    ),
                    slug_prefix=legacy_config.get("slug_prefix", ""),
                    slug_location=legacy_config.get("slug_location", ""),
                    slug_max_words=legacy_config.get("slug_max_words", 6),
                    slug_min_len=legacy_config.get("slug_min_len", 3),
                    slug_stopwords=legacy_config.get("slug_stopwords", []),
                    slug_whitelist=legacy_config.get("slug_whitelist", []),
                ),
                upload=UploadConfig(),  # Use defaults
            )

            # Save migrated profile
            if not self.config_store:
                self.config_store = ConfigStore()

            self.config_store.save_profile(profile)

            # Backup original settings.json
            backup_path = f"config/settings.json.backup-{now}"
            import shutil

            shutil.copy(settings_path, backup_path)

            print("Migration complete! Profile saved as 'default-client'")
            print(f"Original settings.json backed up to: {backup_path}")

            return profile

        except Exception as e:
            print(f"Migration error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def check_and_load_default_profile(self) -> None:
        """Check for profiles on startup and load default or migrate"""
        try:
            if not self.config_store:
                self.config_store = ConfigStore()

            # Load app settings
            app_settings = self.config_store.load_app_settings()

            # Check if we have profiles
            profiles = self.config_store.list_profiles()

            if not profiles:
                print("No profiles found - checking for legacy settings.json...")

                # Attempt migration
                migrated_profile = self.migrate_legacy_settings()

                if migrated_profile:
                    # Load migrated profile
                    self.load_profile_into_ui("default-client")

                    QMessageBox.information(
                        self,
                        "Settings Migrated",
                        "Your settings have been migrated to the new profile system!\n\n"
                        "Profile: Default Client (Migrated)\n\n"
                        "You can now create additional profiles for different clients.",
                    )
                else:
                    print("No legacy settings found - starting fresh")

            elif app_settings.last_used_profile:
                # Load last used profile
                if self.config_store.profile_exists(app_settings.last_used_profile):
                    print(
                        f"Loading last used profile: {app_settings.last_used_profile}"
                    )
                    self.load_profile_into_ui(app_settings.last_used_profile)
                else:
                    print(
                        f"Last used profile '{app_settings.last_used_profile}' not found"
                    )

        except Exception as e:
            print(f"Error during startup profile check: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wizard = WatermarkWizard()
    wizard.show()
    sys.exit(app.exec())
