import sys
import time

import cv2
import numpy as np

# from PyQt5.QtMultimedia import QCameraInfo
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtGui import QPixmap
from PyQt5 import QtGui

from graphics.main import Ui_MainWindow


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.cap = None

    def run(self):
        # capture from web cam
        self.cap = cv2.VideoCapture(0,cv2.CAP_V4L2)
        while self._run_flag:
            ret, cv_img = self.cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)

    def stop(self):
        self._run_flag = False

    def adjust_prop(self, prop, value):
        if self.cap is not None:
            self.cap.set(prop, value)

    def get_prop(self, prop):
        if self.cap is not None:
            return self.cap.get(prop)
        return 0


class MainApp(QMainWindow, Ui_MainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        # getting available cameras
        # available_cameras = QCameraInfo.availableCameras()
        # if no camera found
        # if not available_cameras:
            # exit the code
        #    sys.exit()

        self.display_width = 640
        self.display_height = 480
        print("RESOLUTION: {}x{}".format(self.display_width,self.display_height))
        self.img_lbl.resize(self.display_width, self.display_height)
        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()
        time.sleep(3)   # give time to the thread to start

        # set the value according to the current value
        # brightness
        self.bright_hslider.setMaximum(256)
        br_value = int(self.thread.get_prop(cv2.CAP_PROP_BRIGHTNESS))
        self.bright_hslider.valueChanged.connect(self.adjust_brightness)
        self.bright_hslider.setValue(br_value)
        self.bright_lbl_out.setText(self.to_size_three(br_value))

        # saturation
        self.sat_hslider.setMaximum(256)
        sat_value = int(self.thread.get_prop(cv2.CAP_PROP_SATURATION))
        self.sat_hslider.valueChanged.connect(self.adjust_saturation)
        self.sat_hslider.setValue(sat_value)
        self.sat_lbl_out.setText(self.to_size_three(sat_value))

        # gain
        self.gain_hslider.setMaximum(256)
        gain_value = int(self.thread.get_prop(cv2.CAP_PROP_GAIN))
        self.gain_hslider.valueChanged.connect(self.adjust_gain)
        self.gain_hslider.setValue(gain_value)
        self.gain_lbl_out.setText(self.to_size_three(gain_value))

        # contrast
        self.contrast_hslider.setMaximum(256)
        contrast_value = int(self.thread.get_prop(cv2.CAP_PROP_CONTRAST))
        self.contrast_hslider.valueChanged.connect(self.adjust_contrast)
        self.contrast_hslider.setValue(contrast_value)
        self.contrast_lbl_out.setText(self.to_size_three(contrast_value))

        # exposure
        self.exp_hslider.setMaximum(1001)
        auto_exp = int(self.thread.get_prop(cv2.CAP_PROP_AUTO_EXPOSURE)) == 3
        self.exp_hslider.valueChanged.connect(self.adjust_exposure)
        self.auto_exp_cbox.stateChanged.connect(self.auto_exp_changed)
        self.auto_exp_cbox.setChecked(auto_exp)

        self.exp_hslider.setEnabled(not auto_exp)
        if not auto_exp:
            exp_value = int(self.thread.get_prop(cv2.CAP_PROP_EXPOSURE))
            self.exp_hslider.setValue(exp_value)
            self.exp_lbl_out.setText(self.to_size_three(exp_value))


        # defaults
        self.defaul_cbox.stateChanged.connect(self.set_props_default)

    def adjust_brightness(self, value):
        self.thread.adjust_prop(cv2.CAP_PROP_BRIGHTNESS, value)
        self.bright_lbl_out.setText(self.to_size_three(value))

    def adjust_saturation(self, value):
        self.thread.adjust_prop(cv2.CAP_PROP_SATURATION, value)
        self.sat_lbl_out.setText(self.to_size_three(value))

    def adjust_gain(self, value):
        self.thread.adjust_prop(cv2.CAP_PROP_GAIN, value)
        self.gain_lbl_out.setText(self.to_size_three(value))

    def adjust_contrast(self, value):
        self.thread.adjust_prop(cv2.CAP_PROP_CONTRAST, value)
        self.contrast_lbl_out.setText(self.to_size_three(value))

    def adjust_exposure(self, value):
        self.thread.adjust_prop(cv2.CAP_PROP_EXPOSURE, value)
        self.exp_lbl_out.setText(self.to_size_three(value))

    def auto_exp_changed(self, state):
        if state:
            self.exp_hslider.setEnabled(False)
            self.exp_lbl_out.setText('   ')
        else:
            self.exp_hslider.setEnabled(True)
            exp_value = int(self.thread.get_prop(cv2.CAP_PROP_EXPOSURE))
            self.exp_hslider.setValue(exp_value)
            self.exp_lbl_out.setText(self.to_size_three(exp_value))

    def set_props_default(self):
        self.bright_hslider.setValue(0)
        self.sat_hslider.setValue(60)
        self.contrast_hslider.setValue(32)
        self.gain_hslider.setValue(0)
        self.auto_exp_cbox.setChecked(True)

    def closeEvent(self, ev):
        self.thread.stop()
        self.thread.exit()
        super().closeEvent(ev)

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.img_lbl.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    @staticmethod
    def to_size_three(value):
        v = str(value)
        if len(v) < 3:
            v = ' '*(3 - len(v)) + v
        return v


if __name__ == '__main__':
    App = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(App.exec())
