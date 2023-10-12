import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, QFileDialog, QLineEdit 
from PyQt5.QtWidgets import QHBoxLayout, QComboBox
from PyQt5.QtGui import QPixmap, QPen, QPainter, QColor
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import Qt, QSize, QRect

class ImageComparisonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.max_rows = 8
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Image Comparison Tool")
        self.setGeometry(100, 100, 800, 400)
        self.image_folder = None
        self.image_names = []

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.label = QLabel(self)
        self.label.setStyleSheet('background-color: white')
        self.layout.addWidget(self.label)

        self.image_widgets = []  # store all image widgets
        # set dradding on images
        self.dragging = False
        self.box_start, self.box_end = (0, 0), (0, 0)
        self.num_rows, self.num_cols = 1, 1

        self.layout_text = QHBoxLayout()
        self.text_label = QLabel("Number of rows: ", self)
        self.layout_text.addWidget(self.text_label)
        self.row_select = QComboBox(self)
        self.row_select.addItem("1") # at most 10 lines
        self.row_select.currentIndexChanged.connect(self.row_select_action)
        self.layout_text.addWidget(self.row_select)

        self.button = QPushButton("Open Image Folder", self)
        self.layout_text.addWidget(self.button)

        self.layout_font = QHBoxLayout()
        self.font_text = QLabel("Caption font setting: ", self)
        self.layout_font.addWidget(self.font_text)
        self.font_family = QComboBox(self)
        self.font_family.addItems(["Times New Roman", "Calibri", "Palatino Linotype"])
        self.font_family.currentIndexChanged.connect(self.font_family_action)
        self.layout_font.addWidget(self.font_family)
        self.font_size = QComboBox(self)
        self.font_size.addItems([str(item) for item in range(5, 31)])
        self.font_size.setCurrentIndex(6)
        self.font_size.currentIndexChanged.connect(self.font_size_action)
        self.layout_font.addWidget(self.font_size)

        self.layout.addLayout(self.layout_text)
        self.layout.addLayout(self.layout_font)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.button.clicked.connect(self.openImageFolder)
        self.central_widget.setLayout(self.layout)

        if self.label.layout() is None:
            self.row_select.setEnabled(False)
            self.font_size.setEnabled(False)
            self.font_family.setEnabled(False)
        print(self.label.size())

    def openImageFolder(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder", options=options)

        if folder_path:
            self.image_folder = folder_path
            self.readImageNames()
            self.showImages()

    def row_select_action(self):  # change number rows
        if self.label.layout() is not None:
            self.showImages(idx=0)

    def font_family_action(self):  # change caption font family
        if self.label.layout() is not None:
            self.showImages(idx=0)

    def font_size_action(self):  # change caption font size
        if self.label.layout() is not None:
            self.showImages(idx=0)

    def resizeEvent(self, QResizeEvent):
        if self.label.layout() is not None:
            self.showImages(idx=0)

    def readImageNames(self):
        if self.image_folder:
            self.method_names = os.listdir(self.image_folder)
            self.method_names = sorted([item for item in self.method_names if not "DS_Store" in item])
            self.method_dict = dict()
            for method in self.method_names:
                files = os.listdir(os.path.join(self.image_folder, method))
                files = [os.path.join(self.image_folder, method, item) for item in files 
                    if item.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
                self.method_dict[method] = files
        # reset row_select
        self.row_select.clear()
        self.row_select.addItems([str(item) for item in range(1, 1 + len(self.method_names))])

    # Inside the ImageComparisonApp class, add the showImages method
    def showImages(self, idx=0):
        # Get the number of rows (M) from the user input or set to 1 by default
        print(self.label.size())
        M = int(self.row_select.currentIndex() + 1)
        if M <= 0:
            M = 1
        # Get the number of columns (N) based on the total number of images
        total_images = len(self.method_names)
        N = (total_images + M - 1) // M  # Round up to ensure enough columns for all images
        margin = 0
        self.num_rows, self.num_cols = M, N  # rows x cols grid for image display
        self.image_widgets = []

        # Create a grid layout for displaying the images
        if self.label.layout() is None:
            grid_layout = QGridLayout()
            self.label.setLayout(grid_layout)
        else:
            grid_layout = self.label.layout()
            clear_layout(grid_layout)
        grid_layout.setSpacing(3)  # set margin between two adajacent images
        grid_layout.setContentsMargins(0, 0, 0, 0)

        window_h = (self.label.size().height() - M*self.text_label.size().height()) / M - 2 * margin
        window_w = self.label.size().width() / N - 2 * margin

        # Display the same image from each child folder
        for i, method in enumerate(self.method_names):
            cell_widget = QWidget()
            cell_layout = QVBoxLayout()
            label = QLabel(self)
            label.setAlignment(Qt.AlignCenter)
            label.setMouseTracking(True)
            label.installEventFilter(self)

            # Calculate the scaled size for the image based on the current window size
            image = QPixmap(self.method_dict[method][idx])
            image_h, image_w = image.size().height(), image.size().width()
            ratio_h, ratio_w = window_h / image_h, window_w / image_w
            ratio = min(ratio_h, ratio_w)
            scaled_size = QSize(int(ratio*image_w), int(ratio*image_h))
            image = image.scaled(scaled_size)
            # Set the image and label into a layout
            label.setPixmap(image)
            label.setStyleSheet(f"border-width:0;border-style:outset")

            text_label = QLineEdit(self)
            font_family, font_size = self.font_family.currentText(), int(self.font_size.currentText())
            text_label.setStyleSheet(f"background:transparent; border-width:0;border-style:outset; color: black; font: \
                                     {font_size}pt {font_family}")
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setText(f'{method}')
            cell_layout.addWidget(label)
            cell_layout.addWidget(text_label)
            cell_layout.setContentsMargins(margin, margin, margin, margin)
            cell_layout.setSpacing(5)
            cell_widget.setLayout(cell_layout)

            row = i // N
            col = i % N
            grid_layout.addWidget(cell_widget, row, col)
            self.image_widgets.append(cell_widget)
        self.font_size.setEnabled(True)
        self.font_family.setEnabled(True)
        self.row_select.setEnabled(True)

    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress:
            for i in range(len(self.method_names)):
                image_label = self.image_widgets[i].findChild(QLabel)
                if image_label.underMouse():
                    self.selected_image = image_label
                    self.box_start = (event.x(), event.y())
                    self.box_end = (event.x(), event.y())
                    self.dragging = True
                    return True
        elif event.type() == event.MouseMove and self.dragging:
            self.box_end = (event.x(), event.y())
            self.draw_box()

        elif event.type() == event.MouseButtonRelease and self.dragging:
            self.dragging = False
            self.draw_box()
            self.crop_and_resize_images()
        return False

    def draw_box(self):
        if self.selected_image:
            pixmap = self.selected_image.pixmap()
            painter = QPainter(pixmap)
            pen = QPen()
            pen.setColor(QColor(255, 0, 0))  # Red color
            pen.setWidth(2)
            painter.setPen(pen)
            painter.fillRect(0, 0, pixmap.width(), pixmap.height(), Qt.white)
            painter.drawRect(self.box_start[0], self.box_start[1], self.box_end[0] - self.box_start[0],
                             self.box_end[1] - self.box_start[1])
            self.selected_image.setPixmap(pixmap)
            painter.end()

    def crop_and_resize_images(self):
        selected_pixmap = self.selected_image.pixmap()
        selected_rect = QRect(self.box_start[0], self.box_start[1], self.box_end[0] - self.box_start[0],
                              self.box_end[1] - self.box_start[1])
        selected_image = selected_pixmap.toImage().copy(selected_rect)
        selected_pixmap = QPixmap.fromImage(selected_image).scaled(selected_pixmap.size())

        for image_label in self.image_widgets:
            pixmap = image_label.findChild(QLabel).pixmap()
            cropped_pixmap = QPixmap(selected_pixmap)
            cropped_pixmap = cropped_pixmap.scaled(pixmap.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.findChild(QLabel).setPixmap(cropped_pixmap)


def clear_layout(layout: QGridLayout):
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        widget = item.widget()
        if widget is not None:
            layout.removeWidget(widget)
            widget.deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageComparisonApp()
    window.show()
    sys.exit(app.exec_())


