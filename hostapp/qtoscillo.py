# pylint: disable=too-many-lines

"""
Copyright (c) 2020-2021, Chubu University and Firmlogics

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
import math
import os
import sys
import threading
import time

import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import EngFormatter
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QStyleFactory,
    QVBoxLayout,
)

from colorman import ColorManager
from confman import ConfigManager
from oscillodsp import dsp
from oscillodsp.oscillodsp_pb2 import (  # pylint: disable=no-name-in-module
    TriggerMode,
    TriggerType,
)
from oscillodsp.utils import Blinker, get_filename, modified_ylim, run_pcsim

# Various definitions
WIN_STYLE = "Fusion"
DEFAULT_SAMPLE_QUANTIZE_BITS = 16
TSCALE_SLIDER_INIT = 4
TSCALE_SLIDER_DIV = 3
FTEXT_TRIGLEVEL_INIT_VAL = 0.0
SLIDER_MAG_INIT_VAL = 10
SLIDER_YPOS_INIT_VAL = 0
VSLIDER_SPACER_PXL = 65  # needs fine adjustment
FTDI_PRODUCT_IDS = {0xA6D0}  # For TI XDS560-USB
QPLAIN_TEXT_EDIT_WIDTH = 80  # in letters
LOGVIEW_UPDATE_INTERVAL_SEC = 0.5
VISIB_BUTTON_HEIGHT = 20
VISIB_BUTTON_HEIGHT_MARGIN = 6  # XXX  more sophisticated way?
LOGGING_DISABLE = logging.CRITICAL + 1
MIN_UPDATE_INTERVAL = 30  # milliseconds
DEBUG_PCSIM = False


def find_in_listdict(listdict, search_key, val, return_key):
    """
    For a given listdict (list of dictionary), if dict[search_key] is equal
    to val, return dict[return_key].  Return None if no match is found.
    """
    search_key_exists = False

    for _ in listdict:
        if search_key in _:
            search_key_exists = True
            if _[search_key] == val:
                if return_key in _:
                    return _[return_key]
                raise ValueError("return_key doesn't exist")
    if search_key_exists:
        return None
    raise ValueError("search_key doesn't exist")


def trig_status_txt(s):
    """
    Generates an HTML-formatted trigger status string.
    """
    return "<b>Trigger Status</b>: " + s


def slider_tscale_to_actual_tscale(slider_val, max_timescale):
    """
    Convert a slider_tscale internal value to the actual exponential time
    scale value
    """
    return max_timescale / math.pow(10, slider_val / TSCALE_SLIDER_DIV)


def com_ports():
    """
    Make a list contains serial ports and FTDI URLs, and return it.
    In the POSIX case, also add 'pcsim'.
    """
    # The reason for importing here is that it may be required for PyInstaller.
    # This needs to be re-checked.
    from pyftdi.ftdi import Ftdi  # pylint: disable=import-outside-toplevel
    from serial.tools import (  # pylint: disable=import-outside-toplevel
        list_ports,
    )

    # Add custom USB product IDs to Ftdi
    for pid in FTDI_PRODUCT_IDS:
        try:
            Ftdi.add_custom_product(Ftdi.DEFAULT_VENDOR, pid)
        except ValueError:
            pass

    items = []

    # First, add generic serial ports
    for p in list_ports.comports():
        items.append({"name": p.device, "desc": None})

    # Next, add FTDI devices
    try:
        for d, num_interfaces in Ftdi.list_devices():
            for i in range(num_interfaces):
                url = f"ftdi://ftdi:0x{d.pid:x}:{d.sn}/{i + 1:d}"
                desc = d.description
                items.append({"name": url, "desc": desc})
    except ValueError as err:
        if "No backend available" in str(err):
            # This occurs if libusb is not installed.
            # Refer https://eblot.github.io/pyftdi/troubleshooting.html
            pass
        else:
            raise

    if os.name == "posix":
        items.append({"name": "pcsim", "desc": None})

    return items


def create_visibility_button(channel, label=None, colorman=None):
    """
    Create a channel visibility button widget and return it
    """
    if colorman is None:
        raise ValueError("colorman is not specified")

    if label is None:
        label = str(channel)

    btn = QtWidgets.QPushButton(label)
    btn.setFixedWidth(50)
    btn.setFixedHeight(VISIB_BUTTON_HEIGHT)
    btn.setStyleSheet(
        f"color: white; background-color: {colorman.color(channel)}"
    )
    return btn


def load_loglevels(confman):
    """
    Ask configuration manager the loglevels.  If None was returned, set the
    loglevels to the default.  Finally return the loglevels.
    """
    loglevels = confman.get("loglevels")
    if loglevels is None:
        loglevels = OscilloWidget.LOGS_FROM
    return loglevels


def show_msgbox_timeout(parent):
    """
    Display an error message box regarding interface timeout.
    """
    QMessageBox.critical(
        parent, "Timeout Error", "No response from the interface."
    )


class PlotCanvas(FigureCanvasQTAgg):
    """
    Create a plotting canvas for Matplotlib
    """

    def __init__(self, parent=None, width=8, height=4.5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.set_tight_layout(True)

        self.ax = self.fig.add_subplot(111)
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

        super().__init__(self.fig)
        self.setParent(parent)

    def set_visible(self, b):
        self.ax.get_xaxis().set_visible(b)
        self.ax.get_yaxis().set_visible(b)


class SuppressFractionSpinBox(QtWidgets.QDoubleSpinBox):
    """
    Child (or inherited) class of QDoubleSpinBox which always show the
    natural floating value string in the text frame
    """

    def textFromValue(self, val):
        return str(val)


class ComPortDialog(QtWidgets.QDialog):
    """
    Com-port (serial/ftdi interface) selection dialog
    """

    DEFAULT_BAUDRATE = 9600

    def __init__(  # pylint: disable=too-many-locals,too-many-statements
        self, parent=None, logger=None, confman=None
    ):
        super().__init__(parent)

        self.logger = logger
        self.confman = confman
        items = com_ports()

        #
        # Create a com-port selection menu (or combo-box)
        #

        m = QComboBox(self)
        self.menu_comport = m

        found_ftdi = False
        idx = 0
        for port in items:
            if idx > 0:
                if not found_ftdi and port["name"][:4] == "ftdi":
                    found_ftdi = True
                    m.insertSeparator(idx)
                    # a separator is also included in the number of items
                    idx += 1
                if port["name"] == "pcsim":
                    m.insertSeparator(idx)
                    idx += 1

            if port["name"] == "pcsim":
                m.addItem("PC Simulator (pcsim)", "pcsim")
            elif port["desc"]:
                m.addItem(
                    f'{port["name"]} ({port["desc"]})',
                    port["name"],
                )
            else:
                m.addItem(f"{port['name']}", port["name"])
            idx += 1

        # Pre-select COM port, specified in the settings, in the combo box
        comport = self.confman.get("comport")
        if comport:
            index = m.findData(comport)
            self.logger.debug(f"comport: index={index:d}")
            if index >= 0:
                m.setCurrentIndex(index)

        m.currentIndexChanged.connect(self.menu_changed)

        #
        # Create a line-edit to set baudrate
        #

        eb = QLineEdit()
        self.edit_baudrate = eb
        eb.setValidator(QtGui.QIntValidator())

        baudrate = self.confman.get("baudrate")
        if baudrate is None:
            baudrate = self.DEFAULT_BAUDRATE
        eb.setText(str(baudrate))

        # This must come AFTER the self.edit_baudrate assignment above
        self.menu_changed(self.menu_comport.currentIndex())

        bb = QHBoxLayout()
        box_baudrate = bb
        bb.addWidget(QLabel("<b>Baud rate (bps):</b>"))
        bb.addWidget(self.edit_baudrate)

        #
        # Create dialog buttons
        #

        dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        dialog_buttons.accepted.connect(self.button_ok_clicked)
        dialog_buttons.rejected.connect(self.reject)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("<b>Select interface:</b>"))
        vbox.addWidget(self.menu_comport)
        vbox.addLayout(box_baudrate)
        vbox.addWidget(dialog_buttons)

        self.setLayout(vbox)

    def menu_changed(self, index):
        _ = index  # Index is required by Qt, even if unused

        if self.menu_comport.currentData() == "pcsim":
            self.edit_baudrate.setEnabled(False)
        else:
            self.edit_baudrate.setEnabled(True)

    def button_ok_clicked(self):
        # The reason for importing here is that it may be required for
        # PyInstaller. This needs to be re-checked.
        import serial  # pylint: disable=import-outside-toplevel

        com_port = self.menu_comport.currentData()
        baudrate = int(self.edit_baudrate.text())
        self.logger.debug(f"button_ok_clicked: {com_port} {baudrate:d}")

        # Test if the com_port can accept the baudrate
        try:
            if com_port != "pcsim":
                dsp.open_interface(com_port, baudrate).close()
            self.confman.set("comport", com_port)
            self.confman.set("baudrate", baudrate)
            self.accept()
        except serial.SerialException:
            QMessageBox.critical(
                self,
                "Error",
                f"The baudrate {baudrate:d} isn't available on the interface",
            )


class ChannelColorsDialog(QtWidgets.QDialog):
    """
    Channel colors selection dialog
    """

    def __init__(
        self, parent=None, logger=None, colorman=None, cur_buttons=None
    ):
        super().__init__(parent)

        self.logger = logger
        self.colorman = colorman
        self.cur_buttons = cur_buttons

        hbox = QHBoxLayout()

        buttons_ch = []
        for ch in range(len(self.colorman.all_colors())):
            b = create_visibility_button(ch, colorman=self.colorman)
            b.clicked.connect(self.buttons_ch_changed)
            buttons_ch.append(b)
            hbox.addWidget(b)

        hbox.addStretch(1)

        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        dialog_buttons.accepted.connect(self.accept)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("<b>Click channel button to change color:</b>"))
        vbox.addLayout(hbox)
        vbox.addWidget(dialog_buttons)

        self.setLayout(vbox)

    def buttons_ch_changed(self):
        btn = self.sender()
        id_ = int(btn.text())
        self.logger.debug(f"buttons_ch: changed ({id_:d})")

        color = QtWidgets.QColorDialog.getColor(self.colorman.color(id_))
        self.logger.debug(f"returned color: {color.name()}")
        if not color.isValid():
            self.logger.debug("returned color: not isValid()")
            return

        self.colorman.set_color(id_, color.name())

        style_txt = f"color: white; background-color: {color.name()}"

        btn.setStyleSheet(style_txt)

        if self.cur_buttons and id_ < len(self.cur_buttons):
            self.cur_buttons[id_].setStyleSheet(style_txt)


class LogTextView(QtWidgets.QPlainTextEdit):
    """
    Modified version of QPlainTextEdit which can set sizeHint
    """

    def __init__(self):
        super().__init__()
        self.__width = super().width()
        self.__height = super().height()

    def set_size_hint(self, width, height):
        if width:
            self.__width = width
        if height:
            self.__height = height

    def size_hint(self):
        return QSize(self.__width, self.__height)


class LogViewerDialog(  # pylint: disable=too-many-instance-attributes
    QtWidgets.QDialog
):
    """
    Log viewer and control which levels of messages should be shown
    """

    signal = Signal()

    LOGGING_LEVELS = [
        (LOGGING_DISABLE, "Disabled"),
        (logging.CRITICAL, "Critical"),
        (logging.ERROR, "Error"),
        (logging.WARNING, "Warning"),
        (logging.INFO, "Info"),
        (logging.DEBUG, "Debug"),
    ]

    def __init__(  # pylint: disable=too-many-arguments,
        # pylint: disable=too-many-positional-arguments,
        # pylint: disable=too-many-locals,
        # pylint: disable=too-many-statements
        self,
        parent=None,
        app_logger=None,
        get_dsp_logger=None,  # call-back function
        loglevels=None,
        set_loglevels=None,  # call-back function
        log_filename=None,
        action_view_log=None,
        confman=None,
    ):
        super().__init__(parent)

        self.app_logger = app_logger
        self.get_dsp_logger = get_dsp_logger
        self.loglevels = loglevels
        self.set_loglevels = set_loglevels
        self.action_view_log = action_view_log
        self.confman = confman
        self.running = False

        # Open the file and make sure to close it in __delete() to manage
        # resources manually
        self.fd = open(  # pylint: disable=consider-using-with
            log_filename, encoding="utf-8"
        )
        self.signal.connect(self.update)
        self.str_pushback = ""
        self.autoscroll = True

        font = QtGui.QFont("Fixedsys", 10)
        font.setStyleHint(QtGui.QFont.Monospace)
        fm = QtGui.QFontMetrics(font)
        text_width = fm.boundingRect("W" * QPLAIN_TEXT_EDIT_WIDTH).width()

        self.viewer = LogTextView()
        self.viewer.setReadOnly(True)
        self.viewer.setFont(font)

        m = self.viewer.contentsMargins()
        d = self.viewer.document()
        """
        Refer
        https://stackoverflow.com/questions/5258665/how-to-set-number-of-lines-for-an-qtextedit
        """
        total_width = text_width + m.left() + m.right()
        total_width += (d.documentMargin() + self.viewer.frameWidth()) * 2
        total_width += self.viewer.verticalScrollBar().size_hint().width()
        self.viewer.set_size_hint(total_width, None)

        boxes_loglevel = []
        for idx, _ in enumerate(loglevels):
            m = QComboBox()

            for level in self.LOGGING_LEVELS:
                m.addItem(level[1], [idx, level[0]])

            index = m.findData([idx, _["level"]])
            if index >= 0:
                m.setCurrentIndex(index)

            # This must be called after the m.setCurrentIndex() above
            m.currentIndexChanged.connect(self.menu_changed)

            vbox = QVBoxLayout()
            vbox.addWidget(QLabel(f"<b>{_['desc']} Log Level</b>"))
            vbox.addWidget(m)
            boxes_loglevel.append(vbox)

        hbox_loglevels = QHBoxLayout()
        for _ in boxes_loglevel:
            hbox_loglevels.addLayout(_)

        cb1 = QCheckBox("&Autoscroll")
        self.checkbox_autoscroll = cb1
        cb1.setChecked(True)
        cb1.stateChanged.connect(self.checkbox_autoscroll_changed)

        cb2 = QCheckBox(
            "&Set the Log Levels as the default (You need to save your "
            "settings later.)"
        )
        self.checkbox_setdefault = cb2

        vbox = QVBoxLayout()
        vbox.addWidget(self.viewer)
        vbox.addWidget(self.checkbox_autoscroll)
        vbox.addWidget(self.checkbox_setdefault)
        vbox.addLayout(hbox_loglevels)

        self.setLayout(vbox)

        # This doesn't work.  Can't we resize QPlainTextEdit?
        # self.viewer.resize(total_width, self.viewer.height())

        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def checkbox_autoscroll_changed(self):
        if self.checkbox_autoscroll.isChecked():
            self.autoscroll = True
        else:
            self.autoscroll = False

    def menu_changed(self, index):
        _ = index  # Index is required by Qt, even if unused

        log_from, loglevel = self.sender().currentData()
        self.app_logger.debug(
            "LogViewerDialog.menu_changed: "
            f"from={log_from} loglevel={loglevel}"
        )

        from_ = self.loglevels[log_from]["from"]
        if from_ == "app":
            self.app_logger.setLevel(loglevel)
        elif from_ == "dsp":
            dsp_logger = self.get_dsp_logger()
            if dsp_logger:
                dsp_logger.setLevel(loglevel)

        self.loglevels[log_from]["level"] = loglevel
        self.set_loglevels(self.loglevels)

    def update(self):
        s = self.str_pushback + self.fd.read()
        if len(s) > 0 and s[-1] == "\n":
            self.str_pushback = s[-1]
            s = s[:-1]

        if s:
            self.viewer.insertPlainText(s)
            if self.autoscroll:
                sb = self.viewer.verticalScrollBar()
                sb = sb.setValue(sb.maximum())

    def run(self):
        self.running = True

        self.signal.emit()

        while True:
            time.sleep(LOGVIEW_UPDATE_INTERVAL_SEC)
            self.signal.emit()
            if not self.running:
                break

    def closeEvent(self, event):
        self.__delete()
        super().closeEvent(event)

    def __delete(self):
        if self.checkbox_setdefault.isChecked():
            self.confman.set("loglevels", self.loglevels)
        self.running = False
        self.thread.join()
        if self.action_view_log:
            self.action_view_log.setEnabled(True)

        # Close the file to free resources
        if self.fd:
            self.fd.close()


class OscilloWidget(  # pylint: disable=too-many-instance-attributes,
    # pylint: disable=too-many-public-methods
    QtWidgets.QMainWindow
):
    """
    Oscilloscope main window
    """

    LAST_DIR = "lastdir"
    LOGS_FROM = [
        {"from": "app", "level": LOGGING_DISABLE, "desc": "Application"},
        {"from": "dsp", "level": LOGGING_DISABLE, "desc": "DSP Driver"},
    ]

    def __init__(  # pylint: disable=too-many-arguments,
        # pylint: disable=too-many-positional-arguments,
        # pylint: disable=too-many-statements
        self,
        oscillo_app,
        logger,
        confman,
        appname,
        log_filename,
    ):
        super().__init__()

        # Defining attributes here to avoid pylint warnings (W0201: Attribute
        # defined outside __init__).
        # These attributes are initialized elsewhere in the code, but pylint
        # expects them to be defined in __init__.
        self.ani = None
        self.blinker = None
        self.ch_active = None
        self.ch_trig = None
        self.ch_trig_new = None
        self.clear_trig = None
        self.last_reply = None
        self.last_ylim = None
        self.lines = None
        self.mag10 = None
        self.max_timescale = None
        self.old_status = None
        self.req_save_csv_filename = None
        self.triggered = None
        self.triglevel = None
        self.triglevel_new = None
        self.trigmode = None
        self.trigmode_new = None
        self.trigtype = None
        self.trigtype_new = None
        self.tscale = None
        self.tscale_new = None
        self.waves = None
        self.ypos10 = None

        self.oscillo_app = oscillo_app
        self.logger = logger
        self.confman = confman
        self.appname = appname
        self.log_filename = log_filename

        # Initialize member variables
        self.running = False
        self.sub_ax = []
        self.buttons_visibility = []
        self.log_viewer_dialog = None
        self.colorman = ColorManager(self.confman)
        self.view_enabled_ch = []
        self.dsp_logger = None
        self.save_loglevels = False

        # Initialize loglevels
        loglevels = load_loglevels(self.confman)
        self.loglevels = loglevels

        # Set style
        self.set_style()

        #
        # Create a HBox contains canvas and sliders
        #

        self.canvas = PlotCanvas(self)
        vbox_slider_mag, self.slider_mag = self.create_slider_mag_layout()
        vbox_slider_ypos, self.slider_ypos = self.create_slider_ypos_layout()

        _ = QtWidgets.QHBoxLayout()
        hbox_canvas_and_vslider = _
        _.addWidget(self.canvas)
        _.addLayout(vbox_slider_mag)
        _.addLayout(vbox_slider_ypos)
        _.setStretch(0, 1)
        _.setStretch(1, 0)
        _.setStretch(2, 0)

        #
        # Create channel visibility buttons layout
        #

        self.visible_ch_layout = self.create_visible_ch_layout()

        _ = QtWidgets.QVBoxLayout()
        vbox_canvas_and_btn = _
        _.addLayout(hbox_canvas_and_vslider)
        _.addLayout(self.visible_ch_layout)

        #
        # Create rightmost control panel
        #

        vbox_control = self.create_controller_layout()

        #
        # Put all layouts and widgets in an HBox (box_main)
        #

        box_main = QtWidgets.QHBoxLayout()
        box_main.addLayout(vbox_canvas_and_btn)
        box_main.addLayout(vbox_control)
        box_main.setStretch(0, 1)
        box_main.setStretch(1, 0)

        # Create menu bars and menu items (actions)
        self.create_menus()

        #
        # Finally put widgets in the QMainWindow
        #

        _ = QtWidgets.QWidget()
        _.setLayout(box_main)
        self.setCentralWidget(_)

        #
        # Finishing the window
        #

        self.button_stop.setFocus()
        self.update_window_title()

    def set_style(self):
        styles = QStyleFactory.keys()
        if WIN_STYLE in styles:
            QApplication.setStyle(QStyleFactory.create(WIN_STYLE))
            QApplication.setPalette(QApplication.style().standardPalette())

    def create_controller_layout(self):  # pylint: disable=too-many-statements
        """
        Create controller panel layout which contains carious buttons and menus
        and return the layout to the caller
        """
        _ = QComboBox(self)
        self.menu_act_ch = _
        _.activated.connect(self.menu_act_ch_changed)
        menu_act_ch_label = QLabel("<b>Active Channel</b>")

        _ = QComboBox(self)
        self.menu_trig_ch = _
        _.activated.connect(self.menu_trig_ch_changed)
        menu_trig_ch_label = QLabel("<b>Trigger Channel</b>")

        _ = QComboBox(self)
        self.menu_trigtype = _
        _.activated.connect(self.menu_trigtype_changed)
        _.addItem("Rising Edge", TriggerType.RisingEdge)
        _.addItem("Falling Edge", TriggerType.FallingEdge)
        menu_trigtype_label = QLabel("<b>Trigger Type</b>")

        _ = QComboBox(self)
        self.menu_trigmode = _
        _.activated.connect(self.menu_trigmode_changed)
        _.addItem("Auto", TriggerMode.Auto)
        _.addItem("Normal", TriggerMode.Normal)
        _.addItem("Single", TriggerMode.Single)
        menu_trigmode_label = QLabel("<b>Trigger Mode</b>")

        _ = QPushButton("Reset")
        self.button_single = _
        _.setEnabled(False)
        _.clicked.connect(self.button_single_clicked)

        self.text_trig_status = QLabel(trig_status_txt("Triggered"))

        _ = SuppressFractionSpinBox()
        self.ftext_triglevel = _
        _.setValue(FTEXT_TRIGLEVEL_INIT_VAL)
        _.setSingleStep(0.5)
        _.setDecimals(6)
        _.setMinimum(float("-inf"))
        _.setMaximum(float("inf"))
        _.valueChanged.connect(self.ftext_triglevel_changed)
        ftext_triglevel_label = QLabel("<b>Trigger Level</b>")

        _ = QSlider(Qt.Horizontal)
        self.slider_tscale = _
        _.setMinimum(0)
        _.setMaximum(9 * TSCALE_SLIDER_DIV)
        _.setSingleStep(1)
        _.setPageStep(1)
        _.setValue(TSCALE_SLIDER_INIT)
        _.valueChanged.connect(self.slider_tscale_changed)
        slider_tscale_label = QLabel("<b>Horizontal Scale</b>")

        _ = QPushButton("Run")
        self.button_stop = _
        _.setStyleSheet("font-weight: bold")
        _.setCheckable(True)
        _.clicked.connect(self.button_stop_changed)

        button_save_image = QPushButton("Save as Image File")
        button_save_image.clicked.connect(self.button_save_image_clicked)

        _ = QPushButton("Save as CSV File")
        self.button_save_csv = _
        _.setEnabled(False)
        _.clicked.connect(self.button_save_csv_clicked)

        vbox = QVBoxLayout()
        vbox.addWidget(menu_act_ch_label)
        vbox.addWidget(self.menu_act_ch)
        vbox.addWidget(menu_trig_ch_label)
        vbox.addWidget(self.menu_trig_ch)
        vbox.addWidget(menu_trigtype_label)
        vbox.addWidget(self.menu_trigtype)
        vbox.addWidget(menu_trigmode_label)
        vbox.addWidget(self.menu_trigmode)
        vbox.addWidget(self.button_single)
        vbox.addWidget(self.text_trig_status)
        vbox.addWidget(ftext_triglevel_label)
        vbox.addWidget(self.ftext_triglevel)
        vbox.addWidget(slider_tscale_label)
        vbox.addWidget(self.slider_tscale)
        vbox.addItem(
            QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        vbox.addWidget(self.button_stop)
        vbox.addWidget(button_save_image)
        vbox.addWidget(self.button_save_csv)
        return vbox

    def create_slider_mag_layout(self):
        """
        Create y-axis magnification slider layout and return the layout
        and generated slider widget to the caller

        NOTE: This slider holds 10 times the actual value because QSlider can't
        treat floating values.
        """
        _ = QSlider(Qt.Vertical)
        slider_mag = _
        _.setMinimum(1)
        _.setMaximum(19)
        _.setSingleStep(1)
        _.setPageStep(1)
        _.setValue(SLIDER_MAG_INIT_VAL)
        _.valueChanged.connect(self.slider_mag_changed)
        slider_mag_label = QLabel("Scale")

        vbox = QVBoxLayout()
        vbox.addWidget(slider_mag_label)
        vbox.addWidget(slider_mag, alignment=Qt.AlignHCenter)
        vbox.addItem(
            QSpacerItem(
                0, VSLIDER_SPACER_PXL, QSizePolicy.Fixed, QSizePolicy.Fixed
            )
        )

        return vbox, slider_mag

    def create_slider_ypos_layout(self):
        """
        Create y-axis position slider layout and return the layout
        and generated slider widget to the caller

        NOTE: This slider holds 10 times the actual value because QSlider can't
        treat floating values.
        """
        _ = QSlider(Qt.Vertical)
        slider_ypos = _
        _.setMinimum(-10)
        _.setMaximum(10)
        _.setSingleStep(1)
        _.setPageStep(1)
        _.setValue(SLIDER_YPOS_INIT_VAL)
        _.valueChanged.connect(self.slider_ypos_changed)
        slider_ypos_label = QLabel("Pos")

        vbox = QVBoxLayout()
        vbox.addWidget(slider_ypos_label)
        vbox.addWidget(slider_ypos, alignment=Qt.AlignHCenter)
        vbox.addItem(
            QSpacerItem(
                0, VSLIDER_SPACER_PXL, QSizePolicy.Fixed, QSizePolicy.Fixed
            )
        )

        return vbox, slider_ypos

    def create_visible_ch_layout(self):
        """
        Create a layout to hold Visible Channel buttons
        """
        hbox = QHBoxLayout()
        hbox.addItem(
            QSpacerItem(
                0,
                VISIB_BUTTON_HEIGHT + VISIB_BUTTON_HEIGHT_MARGIN,
                QSizePolicy.Minimum,
                QSizePolicy.Expanding,
            )
        )
        hbox.addStretch(1)
        return hbox

    def create_menus(self):
        # Menu Bar
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)  # for macOS

        # File Menu
        menu_file = self.menubar.addMenu("&File")

        action_quit = QAction(f"&Quit {self.appname}", self)
        action_quit.setShortcut("Ctrl+Q")
        action_quit.triggered.connect(self.quit)
        menu_file.addAction(action_quit)

        # Settings Menu
        menu_settings = self.menubar.addMenu("&Settings")

        self.action_new = QAction("&New", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self.action_new_triggered)
        menu_settings.addAction(self.action_new)

        self.action_load = QAction("&Load...", self)
        self.action_load.setShortcut("Ctrl+L")
        self.action_load.triggered.connect(self.action_load_triggered)
        menu_settings.addAction(self.action_load)

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self.action_save_triggered)
        menu_settings.addAction(self.action_save)

        action_save_as = QAction("Save As...", self)
        action_save_as.setShortcut("Shift+Ctrl+S")
        action_save_as.triggered.connect(self.action_save_as_triggered)
        menu_settings.addAction(action_save_as)

        menu_settings.addSeparator()

        _ = QAction("&Interface...", self)
        _.triggered.connect(self.action_com_port_triggered)
        menu_settings.addAction(_)
        self.action_com_port = _

        action_ch_color = QAction("&Channel Colors...", self)
        action_ch_color.triggered.connect(self.action_ch_color_triggered)
        menu_settings.addAction(action_ch_color)

        # Logging Menu
        menu_logging = self.menubar.addMenu("&Logging")

        self.action_view_log = QAction("&View log...", self)
        self.action_view_log.triggered.connect(self.action_view_log_triggered)
        menu_logging.addAction(self.action_view_log)

    def alter_and_fix_width(self):
        """
        Notice: we need call this after 'self.widget.show()'
        """
        width = self.text_trig_status.width()
        self.text_trig_status.setText(trig_status_txt("Waiting"))
        self.text_trig_status.setFixedWidth(width)

    def reset(self):
        """
        Reset widgets setting to the initial state
        """
        self.menu_act_ch.clear()
        self.menu_trig_ch.clear()
        self.menu_trigmode.setCurrentIndex(TriggerMode.Auto)
        self.button_single.setEnabled(False)
        self.text_trig_status.setText(trig_status_txt("Waiting"))
        self.ftext_triglevel.setValue(FTEXT_TRIGLEVEL_INIT_VAL)
        self.slider_tscale.setValue(TSCALE_SLIDER_INIT)
        self.button_stop.setText("Run")
        self.slider_mag.setValue(SLIDER_MAG_INIT_VAL)
        self.slider_ypos.setValue(SLIDER_YPOS_INIT_VAL)

    def update_window_title(self):
        filename = self.confman.get_config_filename()
        self.logger.debug(f"update_window_title(): filename={filename}")
        if filename is None:
            filename = "Untitled"
        else:
            filename = os.path.basename(filename)
            filename = os.path.splitext(filename)[0]
        title = f"{filename} | {self.appname}"
        self.logger.debug(f"update_window_title(): title={title}")
        self.setWindowTitle(title)

    def menu_act_ch_changed(self, index):
        self.logger.debug(f"menu_act_ch_changed: {index:d}")
        self.ch_active = index
        self.slider_mag.setValue(self.mag10[self.ch_active])
        self.slider_ypos.setValue(self.ypos10[self.ch_active])

    def menu_trig_ch_changed(self, index):
        self.logger.debug(f"menu_trig_ch_changed: {index:d}")
        self.ch_trig_new = index

    def menu_trigtype_changed(self, index):
        self.logger.debug(f"menu_trigtype_changed: {index:d}")
        self.trigtype_new = index

    def menu_trigmode_changed(self, index):
        self.logger.debug(f"menu_trigmode_changed: {index:d}")
        self.trigmode_new = index

    def slider_tscale_changed(self, value):
        if hasattr(self, "max_timescale"):
            self.tscale_new = slider_tscale_to_actual_tscale(
                value, self.max_timescale
            )
            self.logger.debug(f"tscale_changed: {self.tscale_new:e}")

    def button_single_clicked(self):
        self.logger.debug("button_single: clicked")
        self.clear_trig = True

    def ftext_triglevel_changed(self, value):
        self.logger.debug("ftext_triglevel: changed")
        self.triglevel_new = value

    def button_save_image_clicked(self):
        self.logger.debug("button_save_image: clicked")
        lastdir = self.confman.get(self.LAST_DIR)
        candidate_filename = os.path.join(lastdir, get_filename(".png"))
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save image file", candidate_filename, "PNG (*.png)"
        )
        if filename[0]:
            self.canvas.fig.savefig(filename[0])
            self.confman.set(self.LAST_DIR, os.path.dirname(filename[0]))

    def button_save_csv_clicked(self):
        self.logger.debug("button_save_csv: clicked")
        lastdir = self.confman.get(self.LAST_DIR)
        candidate_filename = os.path.join(lastdir, get_filename(".csv"))
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save CSV file", candidate_filename, "CSV (*.csv)"
        )
        if filename[0]:
            self.req_save_csv_filename = filename[0]
            self.confman.set(self.LAST_DIR, os.path.dirname(filename[0]))

    def slider_mag_changed(self, value):
        if hasattr(self, "mag10"):
            self.mag10[self.ch_active] = value
            self.logger.debug("slider_mag: changed")

    def slider_ypos_changed(self, value):
        if hasattr(self, "ypos10"):
            self.ypos10[self.ch_active] = value
            self.logger.debug("slider_ypos: changed")

    def action_new_triggered(self):
        self.logger.debug("action_new: triggered")
        self.confman.new()
        self.button_stop.setEnabled(False)
        self.update_window_title()
        result = ComPortDialog(logger=self.logger, confman=self.confman).exec()
        if result:
            self.button_stop.setEnabled(True)

    def action_load_triggered(self):
        self.logger.debug("action_load: triggered")
        lastdir = self.confman.get(self.LAST_DIR)
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load settings file", lastdir, "YAML (*.yaml)"
        )
        if filename[0]:
            self.confman.load(filename[0])
            self.confman.set(self.LAST_DIR, os.path.dirname(filename[0]))
            self.update_window_title()

    def action_save_triggered(self):
        self.logger.debug("action_save: triggered")
        filename = self.confman.get_config_filename()
        if filename:
            self.confman.save()
        else:
            self.action_save_as_triggered()

    def action_save_as_triggered(self):
        self.logger.debug("action_save_as: triggered")
        lastdir = self.confman.get(self.LAST_DIR)
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save settings file", lastdir, "YAML (*.yaml)"
        )
        if filename[0]:
            self.confman.set(self.LAST_DIR, os.path.dirname(filename[0]))
            self.confman.save(filename[0])
            self.update_window_title()

    def action_com_port_triggered(self):
        self.logger.debug("action_com_port: triggered")
        w = ComPortDialog(logger=self.logger, confman=self.confman)
        result = w.exec()
        self.logger.debug(f"action_com_port: result={result:d}")
        if result:
            self.button_stop.setEnabled(True)

    def action_ch_color_triggered(self):
        self.logger.debug("action_ch_color: triggered")
        w = ChannelColorsDialog(
            logger=self.logger,
            colorman=self.colorman,
            cur_buttons=self.buttons_visibility,
        )
        w.exec()

    def get_dsp_logger(self):
        """
        Call-back function which is called from LogViewerDialog()
        """
        return self.dsp_logger

    def set_loglevels(self, _):
        """
        Call-back function which is called from LogViewerDialog()
        """
        self.loglevels = _

    def action_view_log_triggered(self):
        self.logger.debug("action_view_log: triggered")
        self.action_view_log.setEnabled(False)
        self.log_viewer_dialog = LogViewerDialog(
            app_logger=self.logger,
            get_dsp_logger=self.get_dsp_logger,
            loglevels=self.loglevels,
            set_loglevels=self.set_loglevels,
            log_filename=self.log_filename,
            action_view_log=self.action_view_log,
            confman=self.confman,
        )
        self.log_viewer_dialog.show()  # This makes a dialog modeless

    def buttons_visibility_changed(self):
        """
        Event handler which should be called when user clicked channel
        visibility buttons
        """
        b = self.sender()
        id_ = int(b.text())
        self.logger.debug(f"buttons_visibility: changed ({id_:d})")
        if b.isChecked():
            self.view_enabled_ch[id_] = False
        else:
            self.view_enabled_ch[id_] = True

    def closeEvent(self, event):
        if self.cleanup_before_closing():
            self.logger.debug("closeEvent(): cleanup() is True")
            super().closeEvent(event)
        else:
            self.logger.debug("closeEvent(): cleanup() is False")
            event.ignore()

    def resizeEvent(self, event):
        self.logger.debug("resizeEvent()")
        super().resizeEvent(event)

    def cleanup_before_closing(self):
        """
        'Clean-up procedures' before closing widget

        Ask user if settings haven't been saved yet.  Settings are saved if
        user clicked OK.  Return False if closing was cancelled by user.
        Otherwise return True.
        """
        if self.save_loglevels:
            self.confman.set("loglevels", self.loglevels)

        if self.confman.updated():
            mbox = QMessageBox()
            mbox.setText("There are changed settings.")
            mbox.setInformativeText("Do you want to save your settings?")
            mbox.setStandardButtons(
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            mbox.setDefaultButton(QMessageBox.Save)
            ret = mbox.exec()

            self.logger.debug(f"save before quit: {ret:d}")

            if ret == QMessageBox.Save:
                filename = self.confman.get_config_filename()
                if filename:
                    self.confman.save()
                else:
                    self.action_save_as_triggered()
            elif ret == QMessageBox.Discard:
                pass
            elif ret == QMessageBox.Cancel:
                return False

        self.stop_animation()
        if self.log_viewer_dialog:
            self.logger.debug("OscilloWidget().cleanup()")
            self.log_viewer_dialog.close()

        return True

    def update_plot(self, _):  # pylint: disable=too-many-locals,
        # pylint: disable=too-many-branches,
        # pylint: disable=too-many-statements
        """
        Main function to update the plot.  Should be called by Matplotlib
        FuncAnimation()
        """
        app = self.oscillo_app

        # When requested by UI, clear triggered flag synchronously
        if self.clear_trig:
            self.triggered = False
            self.clear_trig = False  # Reset the request

        # Communication with DSP may fail by time-out, so surround them by
        # try and except clause.
        try:
            # When requested by UI, clear triggered flag synchronously
            if (
                self.trigmode_new != self.trigmode
                or self.trigtype_new != self.trigtype
                or self.ch_trig_new != self.ch_trig
                or self.tscale_new != self.tscale
                or self.triglevel_new != self.triglevel
            ):
                self.trigmode = self.trigmode_new
                self.trigtype = self.trigtype_new
                self.ch_trig = self.ch_trig_new
                self.tscale = self.tscale_new
                self.triglevel = self.triglevel_new
                self.triggered = False
                self.button_single.setEnabled(
                    (self.trigmode == TriggerMode.Single)
                )

                self.logger.debug("app.target.config()")
                config_reply = app.target.config(
                    resolution=app.quantize_bits,
                    trigmode=self.trigmode,
                    trigtype=self.trigtype,
                    ch_trig=self.ch_trig,
                    triglevel=self.triglevel,
                    timescale=self.tscale,
                )

                self.last_reply = config_reply

            # Once triggered for single-shot mode, re-use wave data
            if self.trigmode != TriggerMode.Single or not self.triggered:
                start_get_wave = time.time()

                self.waves = app.target.get_waves()  # Trying update wave data
                if len(self.waves.wave) > 0:
                    self.triggered = self.waves.triggered

                update_interval = (time.time() - start_get_wave) * 1000
                update_interval = max(update_interval, MIN_UPDATE_INTERVAL)
                self.ani.event_source.interval = update_interval

        except Exception as err:  # pylint: disable=broad-exception-caught
            if "Timeout" in str(err) or "timeout" in str(err):
                show_msgbox_timeout(self)
                self.stop()
                return
            raise

        # Determine if plotting is required
        need_plot = len(self.waves.wave) > 0
        blank_screen = False

        # Update trigger status message
        if self.trigmode == TriggerMode.Auto:
            if self.triggered:
                new_status = "Triggered"
            else:
                new_status = "Auto"
        elif self.trigmode == TriggerMode.Normal:
            if need_plot:
                new_status = "Triggered"
            else:
                new_status = "Waiting"
        else:
            if self.triggered:
                new_status = "Stopped"
            else:
                new_status = "Waiting"
                blank_screen = True

        # Blinking trigger status message
        if new_status != self.old_status:
            self.blinker.reset()
        if new_status in ["Waiting", "Auto"] and not self.blinker.active():
            msg_status = ""
        else:
            msg_status = new_status
        self.text_trig_status.setText(trig_status_txt(msg_status))
        self.old_status = new_status

        if need_plot:
            # Generate CSV file header if required
            csv_samples = []
            if self.req_save_csv_filename:
                csv_printer = open(  # pylint: disable=consider-using-with
                    self.req_save_csv_filename, "w", encoding="utf-8"
                )
                csv_printer.write("time [sec]")
                for ch in self.last_reply.chconfig:
                    csv_printer.write(f",{ch.name} [{ch.unit}]")
                csv_printer.write("\n")

            # Now we can determine samples in a wave
            n_xsamples = len(self.waves.wave[0].samples)
            xlim = (-self.tscale / 2, self.tscale / 2)

            chconfig_active = self.last_reply.chconfig[self.ch_active]

            if blank_screen:
                self.canvas.ax.clear()
                for ax in self.sub_ax:
                    ax.clear()
                    # ax.set_axis_off() isn't required anymore because of
                    # set_visible(False) in create_sub_ax()

                self.canvas.ax.set_xlim(xlim)

                if self.last_ylim is not None:
                    self.canvas.ax.set_ylim(self.last_ylim)
            else:
                # [NOTICE} This self.lines must be a class member variable.
                # Otherwise, Single-shot triggering will fail.
                self.lines = []

                # xser is common among multiple channels, so assign here
                xser = np.linspace(xlim[0], xlim[1], n_xsamples)

                ct_sub_ax = 0
                for idx, wave in enumerate(self.waves.wave):
                    chconfig_idx = self.last_reply.chconfig[idx]

                    if idx == self.ch_active:
                        cur_ax = self.canvas.ax
                    else:
                        cur_ax = self.sub_ax[ct_sub_ax]
                        ct_sub_ax += 1

                    cur_ax.clear()

                    # ax.set_axis_off() isn't required anymore because of
                    # set_visible(False) in create_sub_ax()

                    # Convert wave samples to original float values
                    ylim = (chconfig_idx.min, chconfig_idx.max)
                    yser = np.asarray(wave.samples, dtype=np.float32)
                    yser /= (1 << app.quantize_bits) / (ylim[1] - ylim[0])
                    yser += (ylim[0] + ylim[1]) / 2

                    # Keep yser samples for CSV output
                    if self.req_save_csv_filename:
                        csv_samples.append(yser)

                    # Use a special ylim which taking account of mag and
                    # ypos, and set_ylim()
                    self.last_ylim = modified_ylim(
                        ylim, self.mag10[idx] / 10, self.ypos10[idx] / 10
                    )  # save for blank_screen
                    cur_ax.set_ylim(self.last_ylim)

                    # Generating label for line plot
                    label = chconfig_idx.name
                    if idx == self.ch_active:
                        label += " (active)"

                    # Finally plot line of a channel
                    if self.view_enabled_ch[idx]:
                        (line,) = cur_ax.plot(
                            xser, yser, self.colorman.color(idx), label=label
                        )

                        # Append the line to lines[] to show legend on the
                        # screen.
                        # Note that this is required ONLY for legend purpose.
                        # Even without this "lines", plottings themselves are
                        # accomplished.
                        self.lines.append(line)

            # xlim is common among channels, so process here
            self.canvas.ax.set_xlim(xlim)
            self.canvas.ax.xaxis.set_major_formatter(EngFormatter())
            self.canvas.ax.set_xlabel("[sec]")

            # ylim is configured for currently active channel
            self.canvas.ax.yaxis.set_major_formatter(EngFormatter())
            self.canvas.ax.set_ylabel(
                f"{chconfig_active.name} [{chconfig_active.unit}]"
            )

            # Show legend here
            if len(self.lines) > 0:
                self.canvas.ax.legend(
                    self.lines,
                    [_.get_label() for _ in self.lines],
                    loc="upper left",
                    # labelcolor='white',
                    facecolor="lightgray",
                    # edgecolor='white'
                )

            # Show grid and finally draw everything
            self.canvas.ax.grid(True)

            self.canvas.set_visible(True)  # XXX Is here okay?

            # Finally save sample data to CSV file
            if self.req_save_csv_filename:
                for i in range(n_xsamples):
                    csv_printer.write(f"{i:e}")
                    for ch_id in range(len(self.last_reply.chconfig)):
                        csv_printer.write(f",{csv_samples[ch_id][i]:e}")
                    csv_printer.write("\n")
                csv_printer.close()
                self.req_save_csv_filename = None
                csv_printer.close()

    def button_stop_changed(self):
        """
        When Run/Stop button is clicked, this function (event handler)
        should be called.
        """
        if self.button_stop.isChecked():
            # Initialize member variables
            self.blinker = Blinker()
            self.ch_active = 0
            self.ch_trig = 0
            self.clear_trig = False
            self.last_reply = None
            self.last_ylim = None
            self.mag10 = None
            self.max_timescale = 0.0
            self.old_status = ""
            self.req_save_csv_filename = None
            self.triggered = False
            self.triglevel = None
            self.trigmode = None
            self.trigtype = None
            self.tscale = None

            self.reset()

            # Set Trigger Mode according to the menu selection
            self.trigmode_new = self.menu_trigmode.currentData()
            self.trigtype_new = self.menu_trigtype.currentData()
            self.triglevel_new = self.ftext_triglevel.value()
            self.ch_trig_new = self.ch_trig

            config = self.oscillo_app.connect_target(
                self.trigmode_new,
                self.trigtype_new,
                self.ch_trig,
                self.triglevel_new,
            )

            if config is None:
                # An error should have been occurred
                self.logger.debug("failed to connect_dsp()")
                self.button_stop.setChecked(False)
                return

            self.action_new.setEnabled(False)
            self.action_load.setEnabled(False)
            self.action_com_port.setEnabled(False)
            self.button_save_csv.setEnabled(True)

            self.button_stop.setText("Stop")
            # XXX  self.button_stop.update() doesn't work

            self.mag10 = config["mag10"]
            self.ypos10 = config["ypos10"]
            self.max_timescale = config["max_timescale"]
            self.dsp_logger = config["logger"]

            for item in config["ch_items"]:
                self.menu_act_ch.addItem(item[0], item[1])
                self.menu_trig_ch.addItem(item[0], item[1])

            self.tscale = slider_tscale_to_actual_tscale(
                self.slider_tscale.value(), self.max_timescale
            )
            self.tscale_new = self.tscale

            self.ani = FuncAnimation(
                self.canvas.figure,
                self.update_plot,
                blit=False,
                cache_frame_data=False,
                interval=MIN_UPDATE_INTERVAL,
            )
            self.canvas.draw()  # In the blit=False case, this is required

            self.running = True
        else:
            self.stop()

    def quit(self):
        if self.cleanup_before_closing():
            QtWidgets.QApplication.quit()

    def stop_animation(self):
        """
        Stop Matplotlib FuncAnimation()
        """
        self.logger.debug("stop_animation()")
        if self.running:
            self.logger.debug("stop_animation(): self.running is True")
            self.ani._stop()  # pylint: disable=protected-access
            self.running = False

    def stop(self):
        """
        Stop oscilloscope.
        The following items are which should be done when "Stop" button is
        pressed.
        """
        self.logger.debug("OscilloWidget.stop()")
        self.action_new.setEnabled(True)
        self.action_load.setEnabled(True)
        self.action_com_port.setEnabled(True)
        self.button_stop.setChecked(False)
        self.button_stop.setText("Run")
        self.button_save_csv.setEnabled(False)
        self.oscillo_app.disconnect_target()
        self.stop_animation()

    def create_sub_ax(self, n):
        # First need to remove all sub_ax entities from the Figure
        for ax in self.sub_ax:
            ax.remove()

        self.sub_ax = []
        for _ in range(n):
            new_sub_ax = self.canvas.ax.twinx()
            new_sub_ax.get_xaxis().set_visible(False)
            new_sub_ax.get_yaxis().set_visible(False)
            self.sub_ax.append(new_sub_ax)

    def create_buttons_visibility(self, n):
        # First, remove QSpacerItem as a space holder
        self.visible_ch_layout.removeItem(self.visible_ch_layout.itemAt(0))

        # Next, need to remove all buttons
        for b in self.buttons_visibility:
            self.visible_ch_layout.removeWidget(b)

        self.buttons_visibility = []
        self.view_enabled_ch = []

        for i in range(n):
            b = create_visibility_button(i, colorman=self.colorman)
            b.setCheckable(True)
            b.clicked.connect(self.buttons_visibility_changed)
            self.visible_ch_layout.insertWidget(i, b)
            self.buttons_visibility.append(b)
            self.view_enabled_ch.append(True)


class QtOscillo:  # pylint: disable=too-many-instance-attributes
    """
    QtOscillo application main class
    """

    APPNAME = "QtOscillo"
    ORGNAME = "Firmlogics"
    DOMAINNAME = "flogics.com"
    REVERSE_DOMAINNAME = "com.flogics"
    PCSIM_BAUDRATE = 115200

    def __init__(self, quantize_bits=DEFAULT_SAMPLE_QUANTIZE_BITS):
        self.quantize_bits = quantize_bits
        self.confman = ConfigManager(
            appname=self.APPNAME, appauthor=self.REVERSE_DOMAINNAME
        )

        # Defining attributes here to avoid pylint warnings (W0201: Attribute
        # defined outside __init__).
        # These attributes are initialized elsewhere in the code, but pylint
        # expects them to be defined in __init__.
        self.dsp_bitrate = None
        self.dsp_tty = None
        self.target = None

        log_filename = self.confman.get_appdir_path("log.txt")

        #
        # Set-up logger for debugging
        #

        logger = logging.getLogger("oscillo")
        app_loglevel = find_in_listdict(
            load_loglevels(self.confman), "from", "app", "level"
        )
        logger.setLevel(app_loglevel)
        console_handler = logging.StreamHandler()
        self.file_handler = logging.FileHandler(log_filename, "w")
        console_handler.setFormatter(
            logging.Formatter("oscillo.py: %(message)s")
        )
        # XXX  should add logger name (dsp.py etc.) in the below format
        self.file_handler.setFormatter(
            logging.Formatter("%(asctime)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(console_handler)
        logger.addHandler(self.file_handler)
        self.logger = logger

        # Create QApplication
        qt_app = QtWidgets.QApplication(sys.argv)
        qt_app.setApplicationName(self.APPNAME)
        qt_app.setOrganizationName(self.ORGNAME)
        qt_app.setOrganizationDomain(self.DOMAINNAME)

        # Create main window
        self.widget = OscilloWidget(
            oscillo_app=self,
            logger=self.logger,
            confman=self.confman,
            appname=self.APPNAME,
            log_filename=log_filename,
        )

        self.widget.show()
        self.widget.alter_and_fix_width()

        # If the current comport is not available, disable the Run button
        curr_comport = self.confman.get("comport")
        for item in com_ports():
            if item["name"] == curr_comport:
                break
        else:
            self.widget.button_stop.setEnabled(False)
            result = ComPortDialog(
                logger=self.logger, confman=self.confman
            ).exec()
            if result:
                self.widget.button_stop.setEnabled(True)

        # Finally run the QApplication() and enter the GUI event handler loop
        sys.exit(qt_app.exec())

    def connect_target(  # pylint: disable=too-many-locals
        self, trigmode, trigtype, ch_trig, triglevel
    ):
        """
        Connect to the target processor (MCU, DSP, etc.)
        """
        comport = self.confman.get("comport")
        if comport == "pcsim":
            if DEBUG_PCSIM:
                # In the DEBUG case, manually run 'pcsim' by hand, and read
                # the file ptyname.txt
                with open("../pcsim/ptyname.txt", encoding="ascii") as f:
                    self.dsp_tty = f.read()
            else:
                self.dsp_tty = run_pcsim("../pcsim/pcsim")

            self.dsp_bitrate = self.PCSIM_BAUDRATE
        else:
            self.dsp_tty = comport
            self.logger.debug("dsp_tty: %s", self.dsp_tty)
            self.dsp_bitrate = self.confman.get("baudrate")

        self.target = dsp.DSP(
            self.dsp_tty,
            self.dsp_bitrate,
            loglevel=find_in_listdict(
                self.widget.loglevels, "from", "dsp", "level"
            ),
            console_handler=logging.StreamHandler(),
            file_handler=self.file_handler,
        )

        # Once configure the target to obtain various information need to
        # set-up variables
        try:
            config_reply = self.target.config(
                resolution=self.quantize_bits,
                trigmode=trigmode,
                trigtype=trigtype,
                ch_trig=ch_trig,
                triglevel=triglevel,
                timescale=0.0,
            )  # timescale as '0.0' means "Don't update timescale"
        except Exception as err:  # pylint: disable=broad-exception-caught
            if "Timeout" in str(err) or "timeout" in str(err):
                show_msgbox_timeout(self.widget)
                del self.target
                return None
            raise

        # Set-up mag10 and ypos10
        mag10 = []  # mag10 holds 10 times the actual magnification value
        ypos10 = []
        for ch in config_reply.chconfig:
            mag10.append(10)
            center = (ch.min + ch.max) / 2
            width = ch.max - ch.min
            ypos10.append(int(math.floor(-2.0 * center / width + 0.5)) * 10)

        self.widget.create_sub_ax(len(config_reply.chconfig) - 1)

        self.widget.create_buttons_visibility(len(config_reply.chconfig))

        # Gather all the information the caller requires and put it in a
        # dictionary
        ch_items = []
        for idx, ch in enumerate(config_reply.chconfig):
            ch_items.append((f"{idx:d}: {ch.name}", idx))

        return {
            "mag10": mag10,
            "ypos10": ypos10,
            "ch_items": ch_items,
            "max_timescale": config_reply.max_timescale,
            "logger": self.target.get_logger(),
        }

    def disconnect_target(self):
        """
        Disconnect from the target processor (MCU, DSP, etc.)
        """
        del self.target
        if self.confman.get("comport") == "pcsim":
            os.system("killall pcsim")


def main():
    QtOscillo()


if __name__ == "__main__":
    main()
