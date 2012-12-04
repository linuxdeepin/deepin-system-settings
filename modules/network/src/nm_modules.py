#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Zeng Zhi
# 
# Author:     Zeng Zhi <zengzhilg@gmail.com>
# Maintainer: Zeng Zhi <zengzhilg@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from nmlib.nmclient import NMClient
from nmlib.nm_remote_settings import NMRemoteSettings
from nmlib.nmcache import NMCache, cache
from nmlib.nm_secret_agent import NMSecretAgent
from mm.mmclient import MMClient

from dtk.ui.new_slider import HSlider

class MySlider(HSlider):

    def __init__(self):
        HSlider.__init__(self)

        self.__slider_dict = {}

    def _append_page(self, page, name):
        super(MySlider, self).append_page(page)
        self.__slider_dict[name] = page

    def get_page_by_name(self, name):
        return self.__slider_dict[name]

    def _set_to_page(self, name):
        try:
            page = self.get_page_by_name(name)
            super(MySlider,self).set_to_page(page)
        except :
            print self.__slider_dict

    def _slide_to_page(self, name, direction):
        try:
            page = self.get_page_by_name(name)
            super(MySlider,self).slide_to_page(page, direction)
        except :
            print self.__slider_dict





class NModule(object):

    def __init__(self):
        self.client = cache.getobject("/org/freedesktop/NetworkManager")
        self.setting = cache.getobject("/org/freedesktop/NetworkManager/Settings")
        self.agent = NMSecretAgent()
        self.mclient = MMClient()
        self.hslider = MySlider()

    @property
    def nmclient(self):
        return self.client
    @nmclient.setter
    def nmclient(self, val):
        self.client = val
    @property
    def nm_remote_settings(self):
        return self.setting
    @nm_remote_settings.setter
    def nm_remote_settings(self, val):
        self.setting = val
    @property
    def secret_agent(self):
        return self.agent
    @secret_agent.setter
    def secret_agent(self, val):
        self.agent = NMSecretAgent()
    @property
    def mmclient(self):
        return self.mclient
    @mmclient.setter
    def mmclient(self, val):
        self.mclient = MMClient()
    
    @property
    def slider(self):
        return self.hslider
    
nm_module = NModule()
#wired_device = nmclient.get_wired_devices()[0]
#wireless_device = nmclient.get_wireless_devices()[0]
#if nmclient.get_wireless_devices() != []:
#else:
    #wireless_device = []
##wireless_device = []
