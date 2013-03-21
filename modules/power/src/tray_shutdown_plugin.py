#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Hailong Qiu
#
# Author:     Hailong Qiu <356752238@qq.com>
# Maintainer: Hailong Qiu <356752238@qq.com>
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


from tray_shutdown_gui import Gui
from tray_dialog import TrayDialog
from deepin_utils.process import run_command
from nls import _
import gtk
import os
import sys
sys.path.append("/usr/share/deepin-system-settings/modules/account/src")
from accounts import User

DBUS_USER_STR = "/org/freedesktop/Accounts/User%s" % (os.getuid())

#RESTART_TOP_TEXT = "现在重启此系统吗？"
RESTART_TOP_TEXT = _("Restart your computer now?")
#RESTART_BOTTOM_TEXT = "系统即将在%s秒后自动重启。"
RESTART_BOTTOM_TEXT = _("The system will restart in \n%s secs.")
#SUSPEND_TOP_TEXT = "现在挂起此系统吗？"
SUSPEND_TOP_TEXT = _("Suspend your computer now?")
#SUSPEND_BOTTOM_TEXT = "系统即将在%s秒后自动挂起。"
SUSPEND_BOTTOM_TEXT = _("The system will suspend in \n%s secs.")
LOGOUT_TOP_TEXT = _("Logout your computer now?")
LOGOUT_BOTTOM_TEXT = _("The system will Logout in \n%s secs.")

RUN_DSS_COMMAND = "deepin-system-settings account"
RUN_SWITCH_TOGREETER = "switchtogreeter"
RUN_LOCK_COMMAND = "dlock"



class TrayShutdownPlugin(object):
    def __init__(self):
        self.gui = Gui()
        self.dbus_user = User(DBUS_USER_STR)
        self.dialog = TrayDialog()
        self.gui.stop_btn.connect("clicked", self.stop_btn_clicked)
        self.gui.restart_btn.connect("clicked", self.restart_btn_clicked)
        self.gui.suspend_btn.connect("clicked", self.suspend_btn_clicked)
        self.gui.logout_btn.connect("clicked", self.logout_btn_clicked)
        self.gui.switch_btn.connect("clicked", self.switch_btn_clicked)
        self.gui.lock_btn.connect("clicked", self.lock_btn_clicked)
        self.gui.user_label_event.connect("button-press-event", self.user_label_clicked)

    def stop_btn_clicked(self, widget):
        self.dialog.show_dialog("deepin_shutdown")
        self.dialog.run_exec = self.gui.cmd_dbus.new_stop
        self.this.hide_menu()
        #self.gui.cmd_dbus.stop()

    def restart_btn_clicked(self, widget):
        self.dialog.show_dialog("deepin_restart",
                                RESTART_TOP_TEXT,
                                RESTART_BOTTOM_TEXT
                                )
        self.dialog.run_exec = self.gui.cmd_dbus.new_restart
        self.this.hide_menu()
        #self.gui.cmd_dbus.stop()

    def suspend_btn_clicked(self, widget): 
        self.dialog.show_dialog("deepin_suspend",
                                SUSPEND_TOP_TEXT,
                                SUSPEND_BOTTOM_TEXT)
        self.dialog.run_exec = self.gui.cmd_dbus.suspend
        self.this.hide_menu()
        #self.gui.cmd_dbus.suspend()

    def logout_btn_clicked(self, widget):
        self.dialog.show_dialog("deepin_hibernate",
                                LOGOUT_TOP_TEXT,
                                LOGOUT_BOTTOM_TEXT)
        self.dialog.run_exec = self.gui.cmd_dbus.logout
        self.dialog.argv = 1
        self.this.hide_menu()

    def user_label_clicked(self, widget, event):
        # run dss command.
        if event.button == 1:
            run_command(RUN_DSS_COMMAND)
            self.this.hide_menu()

    def switch_btn_clicked(self, widget):
        self.this.hide_menu()
        run_command(RUN_SWITCH_TOGREETER)

    def lock_btn_clicked(self, widget):
        self.this.hide_menu()
        run_command(RUN_LOCK_COMMAND)

    def init_values(self, this_list):
        self.this_list = this_list
        self.this = self.this_list[0]
        self.tray_icon = self.this_list[1]
        self.tray_icon.set_icon_theme("user")

    def set_user_icon(self):
        try:
            # set user icon.
            #print self.gui.cmd_dbus.get_user_image_path() 
            #self.gui.user_icon.set_from_file(self.gui.cmd_dbus.get_user_image_path())
            self.gui.user_icon.set_from_file(self.dbus_user.get_icon_file())
            #
            user_pixbuf = self.gui.user_icon.get_pixbuf()
            new_user_pixbuf = user_pixbuf.scale_simple(self.gui.icon_width, 
                                                       self.gui.icon_height, 
                                                       gtk.gdk.INTERP_BILINEAR)
        except Exception, e:
            try:
                user_pixbuf = self.gui.gui_theme.get_pixbuf("account/icon.png").get_pixbuf()
                new_user_pixbuf = user_pixbuf.scale_simple(self.gui.icon_width, 
                                                           self.gui.icon_height, 
                                                           gtk.gdk.INTERP_BILINEAR)
                print "set user icon [error]:", e
            except:
                new_user_pixbuf = self.tray_icon.load_icon("user")

        self.gui.user_icon.set_from_pixbuf(new_user_pixbuf)


    def run(self):
        return True

    def insert(self):
        return 1
        
    def id(self):
        return "tray-shutdown-plugin-hailongqiu"

    def plugin_widget(self):
        return self.gui 

    def show_menu(self):
        self.set_user_icon()
        self.this.set_size_request(160, 210)
        #print "shutdown show menu..."

    def hide_menu(self):
        #print "shutdown hide menu..."
        pass

def return_plugin():
    return TrayShutdownPlugin 


if __name__ == "__main__":
    def ok_btn_clicked(widget):
        #
        if len(sys.argv) >= 2:
            if sys.argv[1] == 'logout':
                gui.cmd_dbus.logout(1)
            elif sys.argv[1] == 'shutdown':
                gui.cmd_dbus.shutdown()
    gui = Gui()
    dialog = TrayDialog()
    dialog.connect("hide", lambda w : gtk.main_quit())
    dialog.connect("destroy", lambda w : gtk.main_quit())
    dialog.argv = 1
    if len(sys.argv) >= 2:
        if sys.argv[1] == 'shutdown':
            dialog.show_dialog("deepin_shutdown")
            #dialog.run_exec = gui.cmd_dbus.shutdown
        elif sys.argv[1] == 'logout':
            dialog.show_dialog("deepin_hibernate",
                                LOGOUT_TOP_TEXT,
                                LOGOUT_BOTTOM_TEXT)
            #dialog.run_exec = gui.cmd_dbus.logout

    dialog.ok_btn.connect("clicked", ok_btn_clicked)
    #
    dialog.set_bg_pixbuf(gtk.gdk.pixbuf_new_from_file('/usr/share/deepin-system-tray/src/image/on_off_dialog/deepin_on_off_bg.png'))
    dialog.show_pixbuf = gtk.gdk.pixbuf_new_from_file('/usr/share/deepin-system-tray/src/image/on_off_dialog/deepin_hibernate.png')
    dialog.show_image.set_from_pixbuf(dialog.show_pixbuf)
    dialog.show_all()
    gtk.main()
