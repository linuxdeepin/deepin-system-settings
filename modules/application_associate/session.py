#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Long Wei
#
# Author:     Long Wei <yilang2007lw@gmail.com>
# Maintainer: Long Wei <yilang2007lw@gmail.com>
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

import dbus
import gobject
import re
import traceback

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default = True)

name_re = re.compile("[0-9a-zA-Z-]*")

session_bus = dbus.SessionBus()

def valid_object_path(object_path):
    if not isinstance(object_path, str):
        return False

    if not object_path.startswith("/"):
        return False

    return all(map(lambda x:name_re.match(x), object_path.split(".")))    

class InvalidPropType(Exception):
    
    def __init__(self, prop_name, need_type, real_type = "string"):
        self.prop_name = prop_name
        self.need_type = need_type
        self.real_type = real_type

    def __str__(self):
        return repr("property %s need type %s ,but given type is :%s",
                    (self.prop_name, self.need_type, self.real_type))

class InvalidObjectPath(Exception):
    
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return repr("InvalidObjectPath:" + self.path)


class BusBase(gobject.GObject):
    
    def __init__(self, path, interface, service = "org.gnome.SessionManager", bus = session_bus):

        if valid_object_path(path):
            self.object_path = path
        else:
            raise InvalidObjectPath(path)

        self.object_interface = interface
        self.service = service
        self.bus = bus

        try:
            self.dbus_proxy = self.bus.get_object(self.service, self.object_path)
            self.dbus_interface = dbus.Interface(self.dbus_proxy, self.object_interface)
        except dbus.exceptions.DBusException:
            traceback.print_exc()

    def init_dbus_properties(self):        
        try:
            self.properties_interface = dbus.Interface(self.dbus_proxy, "org.freedesktop.DBus.Properties" )
        except dbus.exceptions.DBusException:
            traceback.print_exc()

        if self.properties_interface:
            try:
                self.properties = self.properties_interface.GetAll(self.object_interface)
            except:
                print "get properties failed"
                traceback.print_exc()

    def dbus_method(self, method_name, *args, **kwargs):
        try:
            return apply(getattr(self.dbus_interface, method_name), args, kwargs)
        except dbus.exceptions.DBusException:
            print "call dbus method failed:%s\n" % method_name
            traceback.print_exc()

    def call_async(self, method_name, *args, **kwargs):
        try:
            return apply(getattr(self.dbus_interface, method_name), args, kwargs)
        except dbus.exceptions.DBusException:
            print "call dbus method failed:%s\n" % method_name
            traceback.print_exc()

class SessionManager(BusBase):

    def __init__(self):
        BusBase.__init__(self, path = "/org/gnome/SessionManager", interface = "org.gnome.SessionManager")

    ###Methods
    def can_shutdown(self):
        return bool(self.dbus_method("CanShutdown"))

    def get_clients(self):
        if self.dbus_method("GetClients"):
            return map(lambda x:str(x), self.dbus_method("GetClients"))
        else:
            return []

    def get_inhibitors(self):
        if self.dbus_method("GetInhibitors"):
            return map(lambda x:str(x), self.dbus_method("GetInhibitors"))
        else:
            return []

    def inhibit(self, app_id, toplevel_xid, reason, flags):
        return int(self.dbus_method("Inhibit", app_id, toplevel_xid, reason, flags))
        
    def initializationError(self, message, fatal):
        return self.call_async("InitializationError", message, fatal)

    def is_autostart_condition_handled(self, condition):
        return bool(self.dbus_method("IsAutostartConditionHandled", condition))

    def is_inhibited(self, flags):
        return bool(self.dbus_method("IsInhibited", flags))

    def is_session_running(self):
        return bool(self.dbus_method("IsSessionRunning"))

    def logout(self, mode):
        self.call_async("Logout", mode)

    def register_client(self, app_id, client_startup_id):
        return str(self.dbus_method("RegisterClient", app_id, client_startup_id))

    def request_reboot(self):
        self.call_async("RequestReboot")

    def request_shutdown(self):
        self.call_async("RequestShutdown")

    def setenv(self, variable, value):
        self.call_async("Setenv", variable, value)

    def shutdown(self):
        self.call_async("Shutdown")

    def uninhibited(self, inhibited_cookie):
        self.call_async("Unhibited", inhibited_cookie)

    def unregister_client(self, client_id):
        self.call_async("UnRegisterClient", client_id)

    ####Signals
    

class App(BusBase):

    def __init__(self, path):
        BusBase.__init__(self, path, interface = "org.gnome.SessionManager.App")

    def get_app_id(self):
        return str(self.dbus_method("GetAppId"))

    def get_phase(self):
        return int(self.dbus_method("GetPhase"))

    def get_startup_id(self):
        return str(self.dbus_method("GetStartupId"))
    
class Client(BusBase):
    
    def __init__(self, path):
        BusBase.__init__(self, path ,interface = "org.gnome.SessionManager.Client")

    def get_app_id(self):
        return str(self.dbus_method("GetAppId"))

    def get_restart_style_hint(self):
        return int(self.dbus_method("GetRestartStyleHint"))

    def get_startup_id(self):
        return str(self.dbus_method("GetStartupId"))

    def get_status(self):
        return int(self.dbus_method("GetStatus"))

    def get_unix_process_id(self):
        return int(self.dbus_method("GetUnixProcessId"))
    
    def stop(self):
        self.call_async("Stop")

class ClientPrivate(BusBase):
    
    def __init__(self, path):
        BusBase.__init__(self, path, interface = "org.gnome.SessionManager.ClientPrivate")

    def end_session_response(self, is_ok, reason):
        self.dbus_method("EndSessionResponse", is_ok, reason)

    ###Signals    

class Inhibitor(BusBase):
    
    def __init__(self, path):
        BusBase.__init__(path , interface = "org.gnome.SessionManager.Inhibitor")

    def get_app_id(self):
        return str(self.dbus_method("GetAppId"))

    def get_client_id(self):
        return str(self.dbus_method("GetClientId"))

    def get_reason(self):
        return str(self.dbus_method("GetReason"))

    def get_flags(self):
        return int(self.dbus_method("GetFlags"))

    def get_toplevel_xid(self):
        return int(self.dbus_method("GetToplevelXid"))

class Presence(BusBase):
    
    def __init__(self):
        BusBase.__init__(path = "/org/gnome/SessionManager/Presence", interface = "org.gnome.SessionManager.Presence")
        self.init_dbus_properties()

    def set_status(self, status):
        self.call_async("SetStatus", status)

    def set_status_text(self, status_text):
        self.call_async("SetStatusText", status_text)

    def get_status(self):
        return self.properties["Status"]

    def get_status_text(self):
        return self.properties["StatusText"]

    ###Signals



if __name__ == "__main__":
    pass
