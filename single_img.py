import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, \
    QColorDialog, QHBoxLayout, QComboBox, QCheckBox, QTextEdit, QMessageBox
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QPalette
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, QSizeF
from PyQt5.QtPrintSupport import QPrinter
import random

class ImageZoomApp(QMainWindow):
    def __init__(self):
        super(ImageZoomApp, self).__init__()

        self.initUI()

        self.dragging = False
        self.start_point = QPoint(0, 0)
        self.end_point = QPoint(0, 0)
        self.border_color = QColor(255, 0, 0)  # current border color
        self.border_colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255)]
        self.boxes = []  # List to store box information (position, size, color)

    def candidate_color(self):
        return QColor(int(255*random.random()), int(255*random.random()), int(255*random.random()))
    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.setGeometry(100, 100, 850, 600)
        self.setWindowTitle("Image Zoom App")
        self.margin = 6  # left, right, top, bottom side margin
        layout = QVBoxLayout()
        layout_other = QHBoxLayout()     # store areas except image regions
        layout_settings = QVBoxLayout()  # store settings area
        layout_other.addLayout(layout_settings)
        layout.setContentsMargins(0, 0, 0, 0)

        layout_image = QHBoxLayout()
        layout_image.setSpacing(self.margin)
        layout_image.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        self.widget_image = QLabel(self)
        self.widget_image.setStyleSheet("background-color:white")
        layout_image.setAlignment(Qt.AlignCenter)
        self.original_image_label = QLabel(self)
        self.original_image_label.setAlignment(Qt.AlignTop)
        self.original_image_label.setMouseTracking(False)
        self.edit_image_label = QLabel(self)
        self.edit_image_label.setAlignment(Qt.AlignTop)
        self.edit_image_label.setMouseTracking(True)
        layout_image.addWidget(self.original_image_label)
        layout_image.addWidget(self.edit_image_label)
        self.layout_image = layout_image
        self.widget_image.setLayout(layout_image)
        layout.addWidget(self.widget_image)

        layout_file = QHBoxLayout()
        layout_file.setAlignment(Qt.AlignLeft)
        self.image_path_label = QLabel("Image path:", self)
        self.image_path_label.setAlignment(Qt.AlignCenter)
        self.open_button = QPushButton("Open image")
        self.open_button.clicked.connect(self.open_image)
        self.save_png_button = QPushButton("Save as png")
        self.save_png_button.clicked.connect(self.save_as_png)
        self.save_pdf_buttion = QPushButton("Save as pdf")
        self.save_pdf_buttion.clicked.connect(self.save_as_pdf)
        layout_file.addWidget(self.image_path_label)
        layout_file.addWidget(self.open_button)
        layout_file.addWidget(self.save_png_button)
        layout_file.addWidget(self.save_pdf_buttion)
        layout_settings.addLayout(layout_file)

        # layout edit
        layout_edit = QHBoxLayout()
        layout_edit.setAlignment(Qt.AlignLeft)
        self.align_text = QLabel("Zoom align:")
        self.align_label = QComboBox(self)
        self.align_label.addItems(["Align below", "Align right"])
        self.align_label.currentIndexChanged.connect(self.align_type_changed)
        layout_edit.addWidget(self.align_text)
        layout_edit.addWidget(self.align_label)

        self.grid_text = QLabel("Row (N):")
        self.grid_label = QComboBox(self)
        self.grid_label.addItems(["1 row", "2 rows", "3 rows", "4 rows"])
        self.grid_label.currentIndexChanged.connect(self.grid_row_changed)
        self.clear_box_button = QPushButton("Clear boxes", self)
        self.clear_box_button.clicked.connect(self.clear_boxes)
        self.margin_text = QLabel("Margin:")  # margin between image and crops
        self.margin_label = QComboBox(self)
        self.margin_label.addItems([str(i) for i in range(0, 21)])
        self.margin_label.currentIndexChanged.connect(self.margin_changed)
        layout_edit.addWidget(self.grid_text)
        layout_edit.addWidget(self.grid_label)
        layout_edit.addWidget(self.clear_box_button)
        layout_edit.addWidget(self.margin_text)
        layout_edit.addWidget(self.margin_label)
        layout_settings.addLayout(layout_edit)

        # draw settings
        layout_draw = QHBoxLayout()
        layout_draw.setAlignment(Qt.AlignLeft)
        self.color_text = QLabel("Line color:")
        self.color_button = QPushButton("Choose box color")
        self.color_button.setEnabled(False)
        self.color_button.clicked.connect(self.choose_color)
        self.color_type = QCheckBox(self)  # use random color | user chosen color
        self.color_type.stateChanged.connect(self.color_mode)
        self.linewidth_text = QLabel("Line width")
        self.linewidth_label = QComboBox(self)
        self.finetune_text = QLabel("Finetune box:")
        self.finetune_label = QCheckBox(self)
        self.finetune_label.stateChanged.connect(self.finetune_mode)
        self.linewidth_label.addItems([str(i) for i in range(1, 9)])
        self.sub_margin_text = QLabel("Sub margin:")  # margin between crops
        self.sub_margin_label = QComboBox(self)
        self.sub_margin_label.addItems([str(i) for i in range(0, 16)])
        self.sub_margin_label.currentIndexChanged.connect(self.sub_margin_changed)
        self.linewidth_label.currentIndexChanged.connect(self.linewidth_changed)
        layout_draw.addWidget(self.color_text)
        layout_draw.addWidget(self.color_type)
        layout_draw.addWidget(self.color_button)
        layout_draw.addWidget(self.linewidth_text)
        layout_draw.addWidget(self.linewidth_label)
        layout_draw.addWidget(self.finetune_text)
        layout_draw.addWidget(self.finetune_label)
        layout_draw.addWidget(self.sub_margin_text)
        layout_draw.addWidget(self.sub_margin_label)
        layout_settings.addLayout(layout_draw)

        # Fine tune boxes
        self.finetune_box = QTextEdit("Fine tune boxes (x, y, w, h): ")
        self.finetune_box.setMaximumHeight(120)
        self.finetune_box.setMaximumWidth(260)
        self.finetune_box.setEnabled(False)
        self.finetune_box.textChanged.connect(self.obtain_box_from_text)
        self.finetune_box.setStyleSheet("background-color: white; border: 0; color: black")
        layout_other.addWidget(self.finetune_box)
        layout.addLayout(layout_other)
        self.num_draws = 0
        self.valid_draw_threshold = 5  # valid drawing box: larger than 5x5 box

        self.central_widget.setLayout(layout)

        self.image = None
        self.aux_image = None  # when cropping images and aligning it, we create a non-visible image to the original image
                               # to make two images have the same size for visualization
        self.selected_image = None
        self.box_image = None  # image with only boxes
        self.cropped_images = []
        self.extra_height = 0  # extra height for placing cropped images
        self.extra_width = 0  # extra width for placing cropped images

    def open_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)", options=options)

        if image_path:
            self.image_path = image_path
            self.image = QPixmap(image_path)
            self.original_image_label.setPixmap(self.image.scaled(self.original_image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.selected_image = self.image.copy()
            self.cropped_images = []  # Reset the cropped images list
            # self.boxes = []  # Reset the boxes
            # If contains box, re-use last boxes
            self.draw_boxes()
            self.zoom_in_boxes()
            self.update_image()

    def update_image(self):
        show_h, show_w = self.widget_image.height(), self.widget_image.width()
        show_w = int((show_w - self.margin * 3) / 2)
        show_h = int((show_h - self.margin * 2))
        if self.image:
            self.edit_image_label.setPixmap(
                self.selected_image.scaled(QSize(show_w, show_h), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            if self.aux_image:
                self.original_image_label.setPixmap(
                    self.aux_image.scaled(QSize(show_w, show_h), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.original_image_label.setPixmap(
                    self.image.scaled(QSize(show_w, show_h), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.image_path_label.setText("Image: " + '/'.join(self.image_path.split("/")[-2:]))

    def save_as_png(self):
        if self.selected_image:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image as PNG", "", "PNG Files (*.png)")
            if file_path:
                self.selected_image.save(file_path, "PNG")

    def save_as_pdf(self):
        if self.selected_image:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image as PDF", "", "PDF Files (*.pdf)")
            if file_path:
                printer = QPrinter()
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)

                # Set page size to match the image size
                image_size = self.selected_image.size()
                printer.setPageSize(QPrinter.Custom)
                printer.setPaperSize(QSizeF(image_size), QPrinter.DevicePixel)
                printer.setFullPage(True)

                painter = QPainter(printer)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.drawPixmap(0, 0, self.selected_image)
                painter.end()

    def resizeEvent(self, QResizeEvent):
        self.update_image()

    # delete latest box
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace and len(self.boxes) > 0:
            self.boxes.pop()
            self.draw_boxes()
            self.zoom_in_boxes()
            self.update_image()
        if len(self.boxes) == 0:  # no cropped boxes
            self.extra_width, self.extra_height = 0, 0
        self.show_box()

    def choose_color(self):
        color = QColorDialog.getColor(self.border_color, self, "Choose Border Color")
        if color.isValid():
            self.border_color = color

    def color_mode(self):
        if self.color_type.isChecked():
            self.color_button.setEnabled(True)
        else:
            self.color_button.setEnabled(False)

    def linewidth_changed(self):
        self.draw_boxes()
        self.zoom_in_boxes()
        self.update_image()

    def clear_boxes(self):
        self.boxes = []
        self.extra_width, self.extra_height = 0, 0
        self.draw_boxes()
        self.zoom_in_boxes()
        self.update_image()

    def align_type_changed(self):
        self.zoom_in_boxes()
        self.update_image()

    def grid_row_changed(self):
        self.zoom_in_boxes()
        self.update_image()

    def margin_changed(self):
        self.zoom_in_boxes()
        self.update_image()

    def sub_margin_changed(self):
        self.zoom_in_boxes()
        self.update_image()

    def finetune_mode(self):
        if self.finetune_label.isChecked():
            self.finetune_box.setEnabled(True)
        else:
            self.finetune_box.setEnabled(False)

    def show_box(self):  # show box (x, y, w, h)
        if self.boxes:
            txt = ""
            for box_start, box_end, _ in self.boxes:
                x1, y1, x2, y2 = box_start.x(), box_start.y(), box_end.x(), box_end.y()
                x, y = min(x1, x2), min(y1, y2)
                w, h = abs(x1 - x2), abs(y1 - y2)
                txt += f"Box, {x}, {y}, {w}, {h}\n"
            self.finetune_box.setText(txt)
        else:
            self.finetune_box.setText("No boxes")

    def obtain_box_from_text(self):  # obtain boxes from user finetune input
        if not self.finetune_label.isChecked():
            return
        txt = self.finetune_box.toPlainText()
        candicate_boxes = txt.split("\n")
        candicate_boxes = [item for item in candicate_boxes if item.startswith("Box")]
        if len(candicate_boxes) != len(self.boxes):
            QMessageBox.warning(self, "warning", "Add / delete box is forbidden")
            return
        for box_idx, box in enumerate(candicate_boxes):
            box_info = box.split(",")[1:]
            print(box_info)
            if not len(box_info) == 4:
                QMessageBox.warning(self, "warning", "Invalid box: "+box)
                return
            x, y, w, h = box_info
            x, y, w, h = x.strip(), y.strip(), w.strip(), h.strip()
            if not x.isdigit() or not y.isdigit() or not w.isdigit() or not h.isdigit():
                QMessageBox.warning(self, "warning", "x, y, w, h should be intergers")
                return
            x, y, w, h = int(x), int(y), int(w), int(h)  # may raise error due to data type
            if not (x + w) <= self.image.width() or not (y+h) <= self.image.height():
                QMessageBox.warning(self, "warning", "size of box should be no larger than image")
            start_point = QPoint(x, y)
            end_point = QPoint(x+w, y+h)
            self.boxes[box_idx] = (start_point, end_point, self.boxes[box_idx][-1])
            self.draw_boxes()
            self.zoom_in_boxes()
            self.update_image()

    def valid_cursor_pos(self, cursor_pos):
        # Four critical details
        # 1. since the image is resized, therefore the computed coordinates should be un-resized. resize (un-resize) makes
        #    coordinates consistent
        # 2. The relative coordinates between cursor and the "image" should be calculated right.
        # 3. The aligned cropped image areas should be excluded with the help of extra_height and extra_width
        # 4. A candidate box is valid, only if its height and width are larger than self.valid_draw_threshold
        resize_h, resize_w = self.edit_image_label.pixmap().size().height(), self.edit_image_label.pixmap().size().width()

        image_h, image_w = self.selected_image.height(), self.selected_image.width()
        # calculate height and width of image label widget
        label_h = int((self.widget_image.height() - 2 * self.margin))  # one margin from the whole layout
        label_w = int((self.widget_image.width() - 3 * self.margin) / 2)  # two margins from the whole layout
        # calibrate the image label coordinates
        image_x = label_w + 2 * self.margin
        image_y = self.margin

        if self.extra_width == 0:
            aspect_ratio = resize_w / image_w
        else:
            aspect_ratio = resize_h / image_h
        # calibrate the (x, y) coordinate of image
        image_x = int(image_x + self.margin / 2)   # because of fixed spacing between two images, the calibrated coordinates is this
        image_y = int(image_y + (label_h - resize_h) / 2)

        # exclude aligned cropped images' regions for cursor
        valid_h = int(resize_h * (1 - self.extra_height / (self.image.height() + self.extra_height)))
        valid_w = int(resize_w * (1 - self.extra_width / (self.image.width() + self.extra_width)))
        if image_x <= cursor_pos.x() <= (image_x + valid_w):
            if image_y <= cursor_pos.y() <= (image_y + valid_h):
                return True, QPoint(int((cursor_pos.x() - image_x) / aspect_ratio),
                                    int((cursor_pos.y() - image_y)/aspect_ratio))
        return False, None

    def mousePressEvent(self, event):
        if self.image:
            if event.button() == Qt.LeftButton:
                valid_cursor, pos = self.valid_cursor_pos(event.pos())
                if valid_cursor:
                    self.dragging = True
                    self.start_point = pos
                    self.end_point = pos

    def mouseMoveEvent(self, event):
        if self.image:
            if self.dragging and event:
                valid_cursor, pos = self.valid_cursor_pos(event.pos())
                if valid_cursor:
                    self.end_point = pos
                    self.draw_boxes(self.start_point, self.end_point)
                    self.zoom_in_boxes()
                    self.update_image()

    def mouseReleaseEvent(self, event):
        if self.image:
            if self.dragging and event:
                self.dragging = False
                valid_cursor, pos = self.valid_cursor_pos(event.pos())
                if valid_cursor:
                    self.end_point = pos
                    if abs(self.start_point.x() - self.end_point.x()) >= self.valid_draw_threshold and abs(
                        self.start_point.y() - self.end_point.y()) >= self.valid_draw_threshold:
                        self.draw_boxes(self.start_point, self.end_point)
                        self.boxes.append((self.start_point, self.end_point, self.border_color))
                        self.show_box()
                        self.zoom_in_boxes()
                        self.update_image()

    def draw_boxes(self, start_point=None, end_point=None):
        # if cursor is moving, then draw extra rect using passed start point and end point
        if self.selected_image:
            self.selected_image = self.image.copy()
            self.aux_image = self.image.copy()  # re-initialize aux_image the same as selected_image
            painter = QPainter(self.selected_image)
            self.num_draws = 0
            for box_start, box_end, color in self.boxes:
                pen = QPen()
                pen.setColor(color)
                pen.setWidth(int(self.linewidth_label.currentText()))
                painter.setPen(pen)
                rect = QRect(box_start, box_end)
                painter.drawRect(rect)
                self.num_draws += 1
            if start_point:
                if not self.color_type.isChecked():
                    if self.num_draws < len(self.border_colors):
                        color = self.border_colors[self.num_draws]
                    else:
                        color = self.candidate_color()
                else:
                    color = self.border_color  # platte chosen color
                pen = QPen()
                pen.setColor(color)
                pen.setWidth(int(self.linewidth_label.currentText()))
                pen.setJoinStyle(Qt.MiterJoin)
                painter.setPen(pen)
                painter.drawRect(QRect(start_point, end_point))  # draw if moving mouse
                self.border_color = color
            painter.end()
            self.box_image = self.selected_image.copy()
            self.update_image()

    def zoom_in_boxes_below(self):
        linewidth = int(self.linewidth_label.currentText())
        self.extra_width = 0  # no extra_width align
        self.extra_height = 0
        self.main_margin = int(self.margin_label.currentText())
        self.sub_margin = int(self.sub_margin_label.currentText())
        if self.boxes:
            number_boxes = len(self.boxes)
            num_rows = int(self.grid_label.currentText().split()[0])
            if number_boxes % num_rows != 0:
                num_rows = 1
            box_num_each_row = number_boxes // num_rows
            selected_image = self.box_image.copy()  # add boxes progressively to selected_image
            aux_image = self.image.copy()  # # add invisible boxes to original image to keep size consistency
            for grp_idx in range(num_rows):
                current_box_grp = self.boxes[grp_idx*box_num_each_row: (grp_idx+1)*box_num_each_row]
                box_colores = []
                self.cropped_images = []
                for box_start, box_end, box_color in current_box_grp:
                    x1, y1 = box_start.x(), box_start.y()
                    x2, y2 = box_end.x(), box_end.y()
                    cropped_image = self.image.copy(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
                    self.cropped_images.append(cropped_image)
                    box_colores.append(box_color)

                # Calculate the aspect ratios for all cropped images
                ratios = sum(image.width() / image.height() for image in self.cropped_images)
                extra_height = int((self.image.width() - linewidth * box_num_each_row * 2
                                    - self.sub_margin * (box_num_each_row - 1)) / ratios)  # extra height for all cropped images below
                # Create a new image for displaying the cropped images
                combined_image = QPixmap(selected_image.width(), selected_image.height() + extra_height
                                         + 2 * linewidth + self.main_margin)
                combined_aux_image = QPixmap(aux_image.width(), aux_image.height() + extra_height
                                             + 2 * linewidth + self.main_margin)
                self.extra_height += extra_height + 2 * linewidth + self.main_margin
                combined_image.fill(Qt.white)
                combined_aux_image.fill(self.original_image_label.palette().color(QPalette.Background))  # fill in with background color
                x_position = 0
                painter = QPainter(combined_image)
                aux_painter = QPainter(combined_aux_image)
                accu_width = 0
                for crop_idx, image in enumerate(self.cropped_images):
                    resize_ratio = extra_height / image.height()
                    if crop_idx == box_num_each_row - 1:
                        # last box
                        image = image.scaled(selected_image.width() - accu_width - 2*box_num_each_row*linewidth
                                             - self.sub_margin * (box_num_each_row - 1), extra_height)
                    else:
                        image = image.scaled(QSize(int(resize_ratio * image.width()), extra_height))
                        accu_width += image.width()
                    painter.drawPixmap(x_position+linewidth, selected_image.height()
                                       + linewidth + self.main_margin, image)
                    # draw boxes
                    pen = QPen()
                    pen.setColor(box_colores[crop_idx])
                    pen.setWidth(linewidth)
                    pen.setJoinStyle(Qt.MiterJoin)
                    painter.setPen(pen)
                    painter.drawRect(int(x_position + linewidth/2), int(selected_image.height()
                                      + linewidth/2 + self.main_margin), image.width() + linewidth, extra_height + linewidth)  # draw if moving mouse
                    x_position += image.width() + 2 * linewidth + self.sub_margin
                painter.drawPixmap(0, 0, selected_image)
                aux_painter.drawPixmap(0, 0, aux_image)
                painter.end()
                aux_painter.end()
                selected_image = combined_image
                aux_image = combined_aux_image
            self.selected_image = selected_image
            self.aux_image = aux_image

    def zoom_in_boxes_right(self):
        linewidth = int(self.linewidth_label.currentText())
        self.extra_width = 0  # no extra_width align
        self.extra_height = 0
        self.main_margin = int(self.margin_label.currentText())
        self.sub_margin = int(self.sub_margin_label.currentText())

        if self.boxes:
            number_boxes = len(self.boxes)
            num_rows = int(self.grid_label.currentText().split()[0])
            if number_boxes % num_rows != 0:
                num_rows = 1
            box_num_each_column = number_boxes // num_rows
            selected_image = self.box_image.copy()  # add boxes progressively to selected_image
            aux_image = self.image.copy()  # # add invisible boxes to original image to keep size consistency
            for grp_idx in range(num_rows):
                current_box_grp = self.boxes[grp_idx * box_num_each_column: (grp_idx + 1) * box_num_each_column]
                box_colores = []
                self.cropped_images = []
                for box_start, box_end, box_color in current_box_grp:
                    x1, y1 = box_start.x(), box_start.y()
                    x2, y2 = box_end.x(), box_end.y()
                    cropped_image = self.image.copy(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
                    self.cropped_images.append(cropped_image)
                    box_colores.append(box_color)

                # Calculate the aspect ratios for all cropped images
                ratios = sum(image.height() / image.width() for image in self.cropped_images)
                extra_width = int((self.image.height() - linewidth * box_num_each_column * 2
                                   - self.sub_margin * (box_num_each_column - 1)) / ratios)  # extra width for all cropped images below
                # Create a new image for displaying the cropped images
                combined_image = QPixmap(selected_image.width()
                                         + extra_width + 2 * linewidth + self.main_margin, selected_image.height())
                combined_aux_image = QPixmap(aux_image.width() + extra_width
                                         + 2 * linewidth + self.main_margin, aux_image.height())
                self.extra_width += extra_width + 2 * linewidth + self.main_margin
                combined_image.fill(Qt.white)
                combined_aux_image.fill(
                    self.original_image_label.palette().color(QPalette.Background))  # fill in with background color
                y_position = 0
                painter = QPainter(combined_image)
                aux_painter = QPainter(combined_aux_image)
                accu_height = 0
                for crop_idx, image in enumerate(self.cropped_images):
                    resize_ratio = extra_width / image.width()
                    if crop_idx == box_num_each_column - 1:
                        # last box
                        image = image.scaled(extra_width, selected_image.height() - accu_height
                                             - 2 * box_num_each_column * linewidth - self.sub_margin * (box_num_each_column - 1))
                    else:
                        image = image.scaled(QSize(extra_width, int(resize_ratio * image.height())))
                        accu_height += image.height()
                    painter.drawPixmap(selected_image.width() + linewidth + self.main_margin,
                                       y_position + linewidth, image)
                    # draw boxes
                    pen = QPen()
                    pen.setColor(box_colores[crop_idx])
                    pen.setWidth(linewidth)
                    pen.setJoinStyle(Qt.MiterJoin)
                    painter.setPen(pen)
                    painter.drawRect(int(selected_image.width() + linewidth / 2 + self.main_margin),
                                     int(y_position + linewidth / 2), extra_width + linewidth, image.height() + linewidth)  # draw if moving mouse
                    y_position += image.height() + 2 * linewidth + self.sub_margin
                painter.drawPixmap(0, 0, selected_image)
                aux_painter.drawPixmap(0, 0, aux_image)
                painter.end()
                aux_painter.end()
                selected_image = combined_image
                aux_image = combined_aux_image
            self.selected_image = selected_image
            self.aux_image = aux_image

    def zoom_in_boxes(self):
        if self.align_label.currentIndex() == 0:
            self.zoom_in_boxes_below()
        else:
            self.zoom_in_boxes_right()

def run_app():
    app = QApplication(sys.argv)
    window = ImageZoomApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_app()
