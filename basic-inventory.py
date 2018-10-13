#!/usr/bin/env python3
import re
import sys
import json

import netifaces
from psutil import virtual_memory
import requests

from PyQt5.QtWidgets import QApplication, QComboBox, QDialog
from PyQt5.QtWidgets import QDialogButtonBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout
from PyQt5.QtWidgets import QLabel, QLineEdit, QMenu, QMenuBar, QPushButton, QTextEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp

IGNORED_IFACES = ["^lo$", "loopback", "docker", "vboxnet", "virtualBox"]

PC_MODELS = ["Personal", "Desktop Gigabyte", "Desktop Lenovo", "Acer Extensa 2511", "Acer Extensa 2540"]

URL_SUBMIT = "https://api.iesjoandaustria.org/devices/register"

class Dialog(QDialog):

    def __init__(self):
        super(Dialog, self).__init__()
        self.createFormGroupBox()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("IES Joan d'Àstria")



    def createFormGroupBox(self):

        def get_user_field():
            self.user = QLineEdit()
            user_re = QRegExp("^\w+\.\w+$")
            user_validator = QRegExpValidator(user_re, self.user)
            self.user.setValidator(user_validator)
            return self.user

        def get_ram_field():
            self.mem = virtual_memory().total
            mem_line_edit = QLineEdit(str(self.mem))
            mem_line_edit.setReadOnly(True)
            return mem_line_edit

        def xis_not_valid_iface():
            valid = False
            for i_iface in IGNORED_IFACES:
                valid |= iface.lower().startswith(i_iface)
            return valid

        def is_valid_iface(iface):
            for re_iface in IGNORED_IFACES:
                if re.search(re_iface, iface.lower()):
                    return False
            return True

        def get_pc_combobox():
            self.pc_combobox = QComboBox()
            self.pc_combobox.addItems(PC_MODELS)
            self.pc_combobox.setCurrentText(PC_MODELS[0])
            return self.pc_combobox

        self.formGroupBox = QGroupBox("PC Registration")
        layout = QFormLayout()
        layout.addRow(QLabel("JDA User:"), get_user_field())

        self.macs = {}
        for iface in [dev for dev in netifaces.interfaces() if is_valid_iface(dev)]:
            mac = ",".join([l["addr"] for l in netifaces.ifaddresses(iface)[netifaces.AF_LINK]])
            self.macs.update({iface: {"macs": [mac]}})
            mac_line_edit = QLineEdit(mac)
            mac_line_edit.setReadOnly(True)
            layout.addRow(QLabel(f"{iface} MAC:"), mac_line_edit)
            if netifaces.AF_INET in netifaces.ifaddresses(iface):
                ips = ",".join([l["addr"] for l in netifaces.ifaddresses(iface)[netifaces.AF_INET]])
                self.macs[iface]["ips"] = netifaces.ifaddresses(iface)[netifaces.AF_INET]
                ip_line_edit = QLineEdit(ips)
                ip_line_edit.setReadOnly(True)
                layout.addRow(QLabel(f"{iface} IP:"), ip_line_edit)

        layout.addRow(QLabel("RAM size:"), get_ram_field())
        layout.addRow(QLabel("PC name:"), QLineEdit("personal"))
        layout.addRow(QLabel("Country:"), get_pc_combobox())
        self.formGroupBox.setLayout(layout)

    def accept(self, *args, **kwargs):
        data = {"user": self.user.text(),
                "mem": self.mem,
                "macs": self.macs,
                "model": self.pc_combobox.currentText()}
        response = requests.post(URL_SUBMIT, data=json.dumps(data))
        assert response.status_code == 200, f"Error processing {data} to \"{URL_SUBMIT}\""
        super(Dialog, self).accept(*args, **kwargs)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = Dialog()
    dialog.exec_()
