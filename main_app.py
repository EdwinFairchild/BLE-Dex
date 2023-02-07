import faulthandler 
from click import style
from BLE_GUI import Ui_MainWindow
from modules import ButtonCallbacks
from modules import ListCallbacks
from modules import MiscHelpers
from modules import BLE_functions as ble_ctl
from modules import SerialThread as ser_ctl
from modules import Console 
from PyQt5 import Qt as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtCore, QtGui, QtWidgets 
from PyQt5.QtCore import  pyqtSignal
from PyQt5.QtCore import pyqtProperty
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from bleak import *
import asyncio
import platform
import sys
import os
import time
import atexit
import webbrowser
import BLE_UUIDs
import logging


QtWidgets.QApplication.setAttribute(
    QtCore.Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
os.environ["QT_FONT_DPI"] = "96"

class MainInterface(QMainWindow):
    # TODO : cleanup unused
            
    selected_address = None
    advertised_name = None
    connected_address = None
    menuPinned = False
    connected_state = False
    serial_connected_state = False
    # used to keep track of tree widget tree items
    toplevel = None
    child = None
    # side animation configurable limits
    sideBarWidthMax = 210
    sideBarWidthMin = 73
    animationDone = True
    widgets = None
    client = None
    # peristent instance of bleakLoop needs to be kept so the task is not
    # canceled
    bleLoop = None
    serialLoop = None
    UUID_dict = BLE_UUIDs.get_uuid_dict("UUIDs.json")
    user_uuid_dict = BLE_UUIDs.get_uuid_dict("user_UUIDs.json", True)
    # list to manage chars that have notify enabled
    notifyEnabledCharsDict = {}

    def __init__(self):
        QMainWindow.__init__(self)
        # setup gui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.frm_otas.setVisible(False)

        #console_init(self)
        ListCallbacks.register_list_callbacks(self)
        ButtonCallbacks.register_button_callbacks(self)
        MiscHelpers.init_icons(self)
        logTextBox = Console.QTextEditLogger(self)
        logTextBox.logMessage.connect(self.logToTextbox)
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',"%H:%M:%S"))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)
        #logging.getLogger().setLevel(logging.DEBUG)
        logging.info("BLE-Pydex initialized")
        #logging.debug('damn, a bug')
        #logging.warning('that\'s not right')
        #logging.error('foobar')


    def logToTextbox(self,data):
        self.ui.console.append(data)

        

    # ------------------------------------------------------------------------
    # def eventFilter(self, source, event):

    #     if event.type() == QtCore.QEvent.Enter and source == self.ui.sideBar:
    #         self.menuAnimate(self.ui.sideBar, True)
    #     if event.type() == QtCore.QEvent.Leave and source == self.ui.sideBar:
    #         self.menuAnimate(self.ui.sideBar, False)
    #     return super().eventFilter(source, event)
    # ------------------------------------------------------------------------

########################################################################################
def exitFunc():
    global interface
    try:
        interface.bleLoop.disconnect_triggered = True
        while interface.bleLoop.connect==True:
            pass

        # close any on running tasks
        for task in asyncio.all_tasks():
            task.cancel()
    
    except Exception as e:
        print(e)
    # ------------------------------------------------------------------------
if __name__ == '__main__':
    # todo: compile resurces into python files, not sure if its even necessary at this point
    # pyrcc5 image.qrc -o image_rc.py
    # compile gui
    faulthandler.enable()
    os.system("pyuic5 -x BLE_GUI.ui -o BLE_GUI.py")
   # atexit.register(exitFunc)
    app = qtw.QApplication(sys.argv)
    app.setStyle('Fusion')

    interface = MainInterface()
    interface.show()
    MiscHelpers.set_button_icons(interface, interface.ui.btnMenuExplore)
    app.exec_()
