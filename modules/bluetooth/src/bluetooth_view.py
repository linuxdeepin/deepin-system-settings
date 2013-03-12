#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Zhai Xiang
# 
# Author:     Zhai Xiang <zhaixiang@linuxdeepin.com>
# Maintainer: Zhai Xiang <zhaixiang@linuxdeepin.com>
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

from theme import app_theme
from dtk.ui.utils import color_hex_to_cairo, get_content_size, cairo_disable_antialias
from dtk.ui.theme import ui_theme
from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.progressbar import ProgressBar
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.menu import Menu
from dtk.ui.iconview import IconView
from dtk.ui.box import ImageBox
from dtk.ui.label import Label
from dtk.ui.line import HSeparator
from dtk.ui.entry import InputEntry
from dtk.ui.combo import ComboBox
from dtk.ui.button import ToggleButton, Button
from dtk.ui.dialog import DialogBox, OpenFileDialog
from dtk.ui.constant import ALIGN_START, ALIGN_MIDDLE, ALIGN_END
import os
import gobject
import gtk
import pango
from constant import *
from nls import _
from bt.device import Device
from bt.utils import bluetooth_class_to_type
from my_bluetooth import MyBluetooth
from ods.OdsManager import OdsManager
import time
import threading as td
import uuid
import re

class ProgressDialog(DialogBox):                                                
    DIALOG_MASK_SINGLE_PAGE = 0                                                 
                                                                                
    def __init__(self, msg, default_width=300, default_height=160, cancel_cb=None):
        DialogBox.__init__(self, "", default_width, default_height, self.DIALOG_MASK_SINGLE_PAGE)

        self.cancel_cb = cancel_cb                                              
        
        self.msg_align = gtk.Alignment()
        self.msg_align.set(0, 0, 0, 0)
        self.msg_align.set_padding(0, 0, 10, 0)
        self.msg_label = Label(msg)
        self.msg_align.add(self.msg_label)
        self.progress_align = gtk.Alignment()                                   
        self.progress_align.set(0, 0, 0, 0)                                     
        self.progress_align.set_padding(20, 0, 10, 10)                         
        self.progress_bar = ProgressBar()                                       
        self.progress_bar.set_size_request(default_width, -1)                   
        self.progress_align.add(self.progress_bar)                              
        self.percentage_align = gtk.Alignment()                                 
        self.percentage_align.set(0, 0, 0, 0)                                   
        self.percentage_align.set_padding(10, 0, 140, 0)                          
        self.percentage_label = Label("0%")          
        self.percentage_label.set_size_request(default_width, -1)               
        self.percentage_align.add(self.percentage_label)                        
        self.cancel_align = gtk.Alignment()                                     
        self.cancel_align.set(0, 0, 0, 0)                                       
        self.cancel_align.set_padding(20, 0, 200, 0)                            
        self.cancel_button = Button(_("Cancel"))                                
        self.cancel_button.set_size_request(70, WIDGET_HEIGHT)
        self.cancel_button.connect("clicked", self.__on_cancel_button_clicked)
        self.cancel_align.add(self.cancel_button)                               
                                        
        self.body_box.pack_start(self.msg_align, False, False)
        self.body_box.pack_start(self.progress_align, False, False)             
        self.body_box.pack_start(self.percentage_align, False, False)           
        self.body_box.pack_start(self.cancel_align)

    def set_progress(self, progress):
        self.progress_bar.progress_buffer.progress = progress
        self.percentage_label.set_text("%d" % progress + "%")

    def __on_cancel_button_clicked(self, widget):
        if self.cancel_cb:
            self.cancel_cb()
            self.destroy()
                                                                                
gobject.type_register(ProgressDialog)

class ReplyDialog(DialogBox):                                                
    DIALOG_MASK_SINGLE_PAGE = 0                                                 
                                                                                
    def __init__(self, msg, default_width=300, default_height=160, is_succeed=True):
        DialogBox.__init__(self, "", default_width, default_height, self.DIALOG_MASK_SINGLE_PAGE)

        self.hbox = gtk.HBox()
        self.image_align = gtk.Alignment()
        self.image_align.set(0, 0, 0, 0)
        self.image_align.set_padding(0, 0, 20, 0)
        self.image_box = ImageBox(app_theme.get_pixbuf("bluetooth/succeed.png"))
        if not is_succeed:
            self.image_box = ImageBox(app_theme.get_pixbuf("bluetooth/failed.png"))
        self.image_align.add(self.image_box)
        self.msg_align = gtk.Alignment()
        self.msg_align.set(0, 0, 0, 0)
        self.msg_align.set_padding(0, 0, 10, 0)
        self.msg_label = Label(msg, wrap_width = 200)
        self.msg_align.add(self.msg_label)
        self.hbox.pack_start(self.image_align)
        self.hbox.pack_start(self.msg_align)
        self.confirm_align = gtk.Alignment()                                     
        self.confirm_align.set(0, 0, 0, 0)                                       
        self.confirm_align.set_padding(20, 0, 200, 0)                            
        self.confirm_button = Button(_("Ok"))                                
        self.confirm_button.set_size_request(70, WIDGET_HEIGHT)
        self.confirm_button.connect("clicked", lambda widget : self.destroy())
        self.confirm_align.add(self.confirm_button)

        self.body_box.pack_start(self.hbox, False, False)
        self.body_box.pack_start(self.confirm_align, False, False)

gobject.type_register(ReplyDialog)

class DeviceIconView(ScrolledWindow):
    def __init__(self, items=None):
        ScrolledWindow.__init__(self, 0, 0)

        self.device_iconview = IconView()
        self.device_iconview.connect("right-click-item", self.__on_right_click_item)
        self.device_iconview.draw_mask = self.draw_mask

        if items:
            self.device_iconview.add_items(items)

        self.device_scrolledwindow = ScrolledWindow()
        self.device_scrolledwindow.add_child(self.device_iconview)

        self.add_child(self.device_scrolledwindow)

    def __do_remove_item(self, item):
        item.do_remove()
        self.device_iconview.delete_items([item])

    def __on_right_click_item(self, widget, item, x, y):
        menu_items = [(None, _("Pair"), lambda : item.do_pair())]
        # TODO: the first item do not show delete                               
        if item.is_paired:                                         
            menu_items = [(None, _("Send File"), lambda : item.do_send_file()), 
                          None,                                                 
                          (None, _("Remove Device"), lambda : self.__do_remove_item(item))]
        Menu(menu_items, True).show((int(x), int(y)))

    def draw_mask(self, cr, x, y, w, h):
        cr.set_source_rgb(*color_hex_to_cairo("#FFFFFF"))
        cr.rectangle(x, y, w, h)
        cr.fill()
        
        cr.set_source_rgb(*color_hex_to_cairo("#AEAEAE"))
        cr.rectangle(x, y, w, h)
        cr.stroke()

    def add_items(self, items, clear=False):
        if clear:
            self.device_iconview.clear()
        
        self.device_iconview.add_items(items)

gobject.type_register(DeviceIconView)

class DeviceItem(gobject.GObject):
    __gsignals__ = {                                                             
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),     
    }
    
    def __init__(self, name, pixbuf, device, adapter, is_paired=False):
        gobject.GObject.__init__(self)

        self.name = name
        self.pixbuf = pixbuf
        self.device = device
        self.adapter = adapter
        self.is_paired = is_paired

        self.pair_pixbuf = app_theme.get_pixbuf("bluetooth/pair.png")
        self.icon_size = 48
        self.is_button_press = False

        self.__const_padding_y = 10

        self.highlight_fill_color = "#7db7f2"                                   
        self.highlight_stroke_color = "#396497"

    def render(self, cr, rect):
        # Draw select background.
        content_width, content_height = get_content_size(self.name)
        if self.is_button_press == True:
            with cairo_disable_antialias(cr):                                      
                cr.set_source_rgb(*color_hex_to_cairo(self.highlight_fill_color))
                cr.rectangle(rect.x + 1,                           
                             rect.y + 1,                           
                             rect.width - 1,                   
                             rect.height - 1)               
                cr.fill_preserve()                                              
                cr.set_line_width(1)                                            
                cr.set_source_rgb(*color_hex_to_cairo(self.highlight_stroke_color))
                cr.stroke()
        
        # Draw device icon.
        draw_pixbuf(cr, self.pixbuf, 
                    rect.x + self.icon_size / 2,
                    rect.y + (rect.height - self.icon_size) / 2,
                    )

        if self.is_paired:
            draw_pixbuf(cr, 
                        self.pair_pixbuf.get_pixbuf(), 
                        rect.x + self.icon_size + self.pair_pixbuf.get_pixbuf().get_width() / 2, 
                        rect.y + self.icon_size + self.pair_pixbuf.get_pixbuf().get_height() / 2)
        
        # Draw device name.
        text_color="#000000"
        if self.is_button_press == True:
            text_color="#FFFFFF"
        draw_text(cr, 
                  self.name, 
                  rect.x,
                  rect.y + self.icon_size + self.__const_padding_y * 2,
                  rect.width - 2, 
                  CONTENT_FONT_SIZE, 
                  CONTENT_FONT_SIZE, 
                  text_color, 
                  alignment=pango.ALIGN_CENTER)
        
    def emit_redraw_request(self):
        '''
        Emit `redraw-request` signal.
        
        This is IconView interface, you should implement it.
        '''
        self.emit("redraw-request")
        
    def get_width(self):
        '''
        Get item width.
        
        This is IconView interface, you should implement it.
        '''
        return self.icon_size * 2
        
    def get_height(self):
        '''
        Get item height.
        
        This is IconView interface, you should implement it.
        '''
        return self.icon_size + CONTENT_FONT_SIZE + self.__const_padding_y * 3
        
    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.
        
        This is IconView interface, you should implement it.
        '''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
    def icon_item_lost_focus(self):
        '''
        Lost focus.
        
        This is IconView interface, you should implement it.
        '''
        self.hover_flag = False
        
        self.emit_redraw_request()
        
    def icon_item_highlight(self):
        '''
        Highlight item.
        
        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()
        
    def icon_item_normal(self):
        '''
        Set item with normal status.
        
        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = False
        self.is_button_press = False
        
        self.emit_redraw_request()
    
    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        
        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True
    
    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.
        
        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True
    
    def icon_item_single_click(self, x, y):
        '''
        Handle single click event.
        
        This is IconView interface, you should implement it.
        '''
        pass

    def __on_session_connected(self, session):
        self.__session = session
        if self.__session and self.__session.Connected:                            
            self.__session.SendFile(self.filename) 
 
    def __on_session_disconnected(self, session):
        if self.__session:
            self.__session.Close()

    def __on_session_error(self, session, name, msg):
        if self.progress_dlg:
            self.progress_dlg.destroy()
        reply_dlg = ReplyDialog(_("Failed!\nerror msg: %s") % msg, is_succeed = False)
        reply_dlg.show_all()

    def __on_cancel(self):                                            
        def reply(*args):                                               
            self.__session.Disconnect()                               
                                                                                
        if self.__session:                                                
            if self.__session.Connected:                              
                self.__session.Cancel(reply_handler=reply, error_handler=reply)
            else:                                                   
                self.__ods_manager.CancelSessionConnect(self.__session.object_path)

    def __on_transfer_started(self, session, filename, path, size):
        self.progress_dlg = ProgressDialog(_("Sending file to %s") % self.device.get_name(), 
                                           cancel_cb = self.__on_cancel)
        self.progress_dlg.show_all()

    def __on_transfer_progress(self, session, progress):
        progress_value = int(float(progress) / float(self.total_bytes) * 100.0)
        if self.progress_dlg:
            self.progress_dlg.set_progress(progress_value)

    def __on_transfer_completed(self, session):
        if self.progress_dlg:
            self.progress_dlg.destroy()

        self.__session.Disconnect()
        self.__session.Close()

        reply_dlg = ReplyDialog(_("Succeed!"))
        reply_dlg.show_all()

    def __on_session_created(self, manager, session):
        self.__session = session
        session.GHandle("connected", self.__on_session_connected)          
        session.GHandle("disconnected", self.__on_session_disconnected)    
        session.GHandle("error-occurred", self.__on_session_error)         
        session.GHandle("transfer-started", self.__on_transfer_started)    
        session.GHandle("transfer-progress", self.__on_transfer_progress) 
        session.GHandle("transfer-completed", self.__on_transfer_completed)

    def __on_session_destroyed(self, manager, path):                          
        if self.__session.object_path == path:                            
            self.__session = None

    def __create_session(self):
        def on_error(msg):
            print "create session error", msg

        props = self.adapter.get_properties()
        self.__ods_manager.create_session(self.device.get_address(), props["Address"], error_handler=on_error)

    def __send_file(self, filename):
        self.filename = filename
        self.total_bytes = os.path.getsize(self.filename)
        self.__ods_manager = OdsManager()
        self.progress_dlg = None
        self.__ods_manager.GHandle("session-created", self.__on_session_created)
        self.__ods_manager.GHandle("session-destroyed", self.__on_session_destroyed)
        self.__create_session()

    def do_send_file(self):
        OpenFileDialog(_("Select File"), None, lambda name : self.__send_file(name), None)

    def __reply_handler_cb(self, device):
        self.is_paired = True
        self.emit_redraw_request()

    def __error_handler_cb(self, error):
        self.is_paired = False
        self.emit_redraw_request()

    def do_remove(self):
        self.adapter.remove_device(self.device.object_path)
    
    def do_pair(self):
        if self.is_paired:                                                      
            return                                                              
                                                                                
        from bt.gui_agent import GuiAgent                                           
        # TODO: wired... it need to use uuid to identify bluez device path         
        path = "/org/bluez/agent/%s" % re.sub('[-]', '_', str(uuid.uuid4()))    
        agent = GuiAgent(path,                                                     
                         _("Please confirm %s pin match as below") % self.name, 
                         _("Yes"),                                              
                         _("No"))                                                   
        agent.set_exit_on_release(False)                                        
        self.device.set_trusted(True)                                           
        if not self.device.get_paired():                                            
            self.adapter.create_paired_device(self.device.get_address(),        
                                              path,                             
                                              "DisplayYesNo",                   
                                              self.__reply_handler_cb,          
                                              self.__error_handler_cb)

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.
        '''
        self.do_pair()
    
    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> del self.pixbuf
        >>> self.pixbuf = None

        This is IconView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        del self.pixbuf
        self.pixbuf = None    
        
        # Return True to tell IconView call gc.collect() to release memory resource.
        return True

gobject.type_register(DeviceItem)

class DiscoveryDeviceThread(td.Thread):
    
    def __init__(self, ThisPtr):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.ThisPtr = ThisPtr
        self.tick = self.ThisPtr.timeout

    def run(self):
        try:
            self.ThisPtr.my_bluetooth.adapter.start_discovery()

            while self.tick:
                self.tick -= 1
                time.sleep(1)

            self.ThisPtr.my_bluetooth.adapter.stop_discovery()
        except Exception, e:
            print "class DiscoveryDeviceThread got error: %s" % e

class BlueToothView(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.VBox.__init__(self)

        self.my_bluetooth = MyBluetooth(self.__on_adapter_removed, 
                                        self.__on_default_adapter_changed, 
                                        self.__device_found)

        self.timeout = 120
        self.timeout_items = [("2 %s" % _("Minutes"), self.timeout)]
        '''
        enable open
        '''
        self.title_align = self.__setup_title_align(
            app_theme.get_pixbuf("bluetooth/enable_open.png"), _("Bluetooth"))
        self.enable_align = self.__setup_align()
        self.enable_box = gtk.HBox(spacing=WIDGET_SPACING)
        self.enable_open_label = self.__setup_label(_("Bluetooth Get Powered"))
        self.enable_open_toggle_align = self.__setup_align(padding_top = 4, padding_left = 158)
        self.enable_open_toggle = self.__setup_toggle()
        if self.my_bluetooth.adapter:
            self.enable_open_toggle.set_active(self.my_bluetooth.adapter.get_powered())
        self.enable_open_toggle.connect("toggled", self.__toggled, "enable_open")
        self.enable_open_toggle_align.add(self.enable_open_toggle)
        self.__widget_pack_start(self.enable_box, 
                                 [self.enable_open_label, 
                                  self.enable_open_toggle_align])
        self.enable_align.add(self.enable_box)
        '''
        display
        '''
        self.display_align = self.__setup_align()
        self.display_box = gtk.HBox(spacing=WIDGET_SPACING)
        self.display_device_label = self.__setup_label(_("Device Shown Name"))
        self.display_device_entry = InputEntry()
        if self.my_bluetooth.adapter:
            self.display_device_entry.set_text(self.my_bluetooth.adapter.get_name())
        self.display_device_entry.set_size(HSCALEBAR_WIDTH, WIDGET_HEIGHT)
        self.display_device_entry.entry.connect("changed", self.__display_device_changed)
        self.__widget_pack_start(self.display_box, 
                                 [self.display_device_label, self.display_device_entry])
        self.display_align.add(self.display_box)
        '''
        enable searchable
        '''
        self.search_align = self.__setup_align()
        self.search_box = gtk.HBox(spacing=WIDGET_SPACING)
        self.search_label = self.__setup_label(_("Be Searchedable"))
        self.search_toggle_align = self.__setup_align(padding_top = 4, padding_left = 158)
        self.search_toggle = self.__setup_toggle()
        if self.my_bluetooth.adapter:
            self.search_toggle.set_active(self.my_bluetooth.adapter.get_discoverable())
        self.search_toggle.connect("toggled", self.__toggled, "search")
        self.search_toggle_align.add(self.search_toggle)
        self.__widget_pack_start(self.search_box, 
                                 [self.search_label, self.search_toggle_align])
        self.search_align.add(self.search_box)
        '''
        device timeout
        '''
        self.timeout_align = self.__setup_align()
        self.timeout_box = gtk.HBox(spacing=WIDGET_SPACING)
        self.timeout_label = self.__setup_label(_("Searching Device Timeout"))
        self.timeout_combo = self.__setup_combo(self.timeout_items)
        self.__widget_pack_start(self.timeout_box, 
                                 [self.timeout_label, self.timeout_combo])
        self.timeout_align.add(self.timeout_box)
        '''
        device iconview
        '''
        self.device_align = self.__setup_align()
        self.device_iconview = DeviceIconView()
        self.device_iconview.set_size_request(690, 190)
        self.device_align.add(self.device_iconview)
        '''
        operation
        '''
        self.oper_align = self.__setup_align()
        self.oper_box = gtk.HBox(spacing = WIDGET_SPACING)
        self.notice_label = Label("", text_x_align = ALIGN_MIDDLE, label_width = 610)
        self.search_button = Button(_("Search"))                                
        self.search_button.connect("clicked", self.__on_search)
        self.__widget_pack_start(self.oper_box, 
                [self.notice_label, 
                 self.search_button, 
                ])
        self.oper_align.add(self.oper_box)
        '''
        this->gtk.VBox pack_start
        '''
        self.__widget_pack_start(self, 
                                 [self.title_align, 
                                  self.enable_align, 
                                  self.display_align, 
                                  self.search_align, 
                                  self.timeout_align, 
                                  self.device_align, 
                                  self.oper_align])

        if self.my_bluetooth.adapter == None:
            self.set_sensitive(False)

        self.connect("expose-event", self.__expose)

        self.__get_devices()

    def __on_adapter_removed(self):                                            
        self.set_sensitive(False)
                                                                                
    def __on_default_adapter_changed(self):                                     
        self.set_sensitive(True)

    def __display_device_changed(self, widget, event):
        self.my_bluetooth.adapter.set_name(widget.get_text())

    def __setup_separator(self):                                                
        hseparator = HSeparator(app_theme.get_shadow_color("hSeparator").get_color_info(), 0, 0)
        hseparator.set_size_request(500, HSEPARATOR_HEIGHT)                                    
        return hseparator                                                       
                                                                                
    def __setup_title_label(self,                                               
                            text="",                                            
                            text_color=app_theme.get_color("globalTitleForeground"),
                            text_size=TITLE_FONT_SIZE,                          
                            text_x_align=ALIGN_START,                           
                            label_width=180):                                   
        return Label(text = text,                                               
                     text_color = text_color,                                   
                     text_size = text_size,                                     
                     text_x_align = text_x_align,                               
                     label_width = label_width, 
                     enable_select = False, 
                     enable_double_click = False)     

    def __setup_title_align(self,                                               
                            pixbuf,                                             
                            text,                                               
                            padding_top=TEXT_WINDOW_TOP_PADDING,                      
                            padding_left=TEXT_WINDOW_LEFT_PADDING):             
        align = self.__setup_align(padding_top = padding_top, padding_left = padding_left)    
        align_box = gtk.VBox(spacing = WIDGET_SPACING)                          
        title_box = gtk.HBox(spacing = WIDGET_SPACING)                          
        image = ImageBox(pixbuf)                                                
        label = self.__setup_title_label(text)                                  
        separator = self.__setup_separator()                                    
        self.__widget_pack_start(title_box, [image, label])                     
        self.__widget_pack_start(align_box, [title_box, separator])             
        align.add(align_box)                                                    
        return align

    def __get_devices(self):
        devices = self.my_bluetooth.get_devices()
        items = []
        i = 0

        while i < len(devices):
            items.append(DeviceItem(devices[i].get_name(),                                
                         app_theme.get_pixbuf("bluetooth/%s.png" % bluetooth_class_to_type(devices[i].get_class())).get_pixbuf(), 
                         devices[i], 
                         self.my_bluetooth.adapter, 
                         True))
            i += 1

        self.device_iconview.add_items(items)

    def __on_search(self, widget):
        DiscoveryDeviceThread(self).start()

    def __device_found(self, adapter, address, values):
        if address not in adapter.get_address_records():
            device = Device(adapter.create_device(address))
            items = []
            
            if not values.has_key("Name"):
                return

            items.append(DeviceItem(values['Name'], 
                         app_theme.get_pixbuf("bluetooth/%s.png" % bluetooth_class_to_type(device.get_class())).get_pixbuf(), device, adapter))
            self.device_iconview.add_items(items)
        else:
            if adapter.get_discovering():
                adapter.stop_discovery()

    def __toggled(self, widget, object):
        if self.adapter == None:
            return

        if object == "enable_open":
            self.adapter.set_powered(widget.get_active())
            return

        if object == "search":
            self.adapter.set_discoverable(widget.get_active())
            return

    def __expose(self, widget, event):                                           
        cr = widget.window.cairo_create()                                        
        rect = widget.allocation                                                 
        
        cr.set_source_rgb(*color_hex_to_cairo(MODULE_BG_COLOR))                  
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)                    
        cr.fill()  
    
    def __combo_item_selected(self, widget, item_text=None, item_value=None, item_index=None, object=None):
        self.timeout = item_value

    def __setup_label(self, text="", width=180, align=ALIGN_END):
        return Label(text, None, TITLE_FONT_SIZE, align, width, False, False, False)

    def __setup_combo(self, items=[], width=HSCALEBAR_WIDTH):
        combo = ComboBox(items, None, 0, width, width)
        combo.set_size_request(width, WIDGET_HEIGHT)
        return combo

    def __setup_toggle(self):
        return ToggleButton(
                app_theme.get_pixbuf("toggle_button/inactive_normal.png"), 
                app_theme.get_pixbuf("toggle_button/active_normal.png"), 
                inactive_disable_dpixbuf = app_theme.get_pixbuf("toggle_button/inactive_normal.png"), 
                active_disable_dpixbuf = app_theme.get_pixbuf("toggle_button/inactive_normal.png"))

    def __setup_align(self, xalign=0, yalign=0, xscale=0, yscale=0, 
                      padding_top=BETWEEN_SPACING, 
                      padding_bottom=0, 
                      padding_left=TEXT_WINDOW_LEFT_PADDING, 
                      padding_right=20):
        align = gtk.Alignment()
        align.set(xalign, yalign, xscale, yscale)
        align.set_padding(padding_top, padding_bottom, padding_left, padding_right)
        return align

    def __widget_pack_start(self, parent_widget, widgets=[], expand=False, fill=False):
        if parent_widget == None:
            return
        for item in widgets:
            parent_widget.pack_start(item, expand, fill)

gobject.type_register(BlueToothView)
