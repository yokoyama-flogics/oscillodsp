"""
Configuration Manager


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

import os
import pathlib

import appdirs
import yaml

debug = False

CONFIGFILE = "configfile"

DEFAULT_CONFIG = {
    "lastdir": str(pathlib.Path.home()),
}


def enable_debug():
    global debug
    debug = True


def diag(s):
    if debug:
        print("confman:", s)


class ConfigManager:
    def __init__(self, appname, appauthor, init_filename="init.yaml"):
        diag("__init__")

        self.confdir = appdirs.user_data_dir(appname, appauthor)
        pathlib.Path(self.confdir).mkdir(parents=True, exist_ok=True)
        self.init_filename = os.path.join(self.confdir, init_filename)
        self.__setup()

    def __setup(self, new=False):
        """
        If new is True, ignore the existing init file
        """
        diag("__setup")
        self.__updated = False

        if new:
            self.init = {}
        elif os.path.exists(self.init_filename):
            self.init = yaml.load(open(self.init_filename), Loader=yaml.Loader)
            if self.init is None:
                self.init = {}
        else:
            self.init = {}

        if CONFIGFILE not in self.init:
            self.init[CONFIGFILE] = None

        if CONFIGFILE in self.init and self.init[CONFIGFILE]:
            self.load(self.init[CONFIGFILE])
        else:
            self.config = DEFAULT_CONFIG

    def new(self):
        diag("new")
        self.__setup(new=True)

    def reset(self):
        diag("reset")
        self.config = {}
        self.__updated = True

    def get(self, name):
        from copy import copy

        diag("get")
        if name in self.config:
            return copy(self.config[name])
        else:
            return None

    def set(self, name, val, save_required=True):
        diag(
            "set (1): {} {} {} {}".format(
                self.config, name, val, save_required
            )
        )
        if name in self.config and self.config[name] == val:
            diag("set: update")
            return

        self.config[name] = val
        if save_required:
            self.__updated = True
        diag(
            "set (2): {} {} {} {}".format(
                self.config, name, val, save_required
            )
        )

    def load(self, filename):
        diag("load")
        if os.path.exists(filename):
            self.config = yaml.load(open(filename), Loader=yaml.Loader)
            if self.config is None:
                self.config = {}
            else:
                self.set_config_filename(filename)
        else:
            self.config = DEFAULT_CONFIG
            self.init[CONFIGFILE] = None
        self.__updated = False

    def save(self, filename=None):
        diag("save")
        if filename is None:
            filename = self.get_config_filename()

        if filename is None:
            raise ValueError("filename is None")

        with open(filename, "w") as f:
            f.write(yaml.dump(self.config))
        self.set_config_filename(filename)
        self.__save_init()
        self.__updated = False

    def updated(self):
        """
        Return True if any items are updated but not saved
        """
        return self.__updated

    def get_config_filename(self):
        return self.init[CONFIGFILE]

    def set_config_filename(self, s):
        self.init[CONFIGFILE] = s

    def get_appdir_path(self, s):
        return os.path.join(self.confdir, s)

    def __save_init(self):
        diag("__save_init")
        with open(self.init_filename, "w") as f:
            f.write(yaml.dump(self.init))
