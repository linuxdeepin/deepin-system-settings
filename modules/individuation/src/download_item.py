#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Hou Shaohui
# 
# Author:     Hou Shaohui <houshao55@gmail.com>
# Maintainer: Hou Shaohui <houshao55@gmail.com>
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

import gtk
import pango
from dtk.ui.new_treeview import TreeItem
from dtk.ui.utils import is_in_rect, format_file_size, get_content_size
from dtk.ui.draw import draw_text, draw_pixbuf, draw_shadow
from dtk.ui.button import CheckButtonBuffer
from dtk.ui.progressbar import ProgressBuffer

from download_manager import fetch_service, TaskObject

from pyaxel.report import parse_bytes

from ui_utils import (draw_single_mask)
from theme import app_theme

from cache_manager import cache_manager

BUTTON_NORMAL = 1
BUTTON_HOVER = 2
BUTTON_PRESS = 3

class DownloadItem(TreeItem):
    '''
    class docs
    '''
    
    STATUS_WAIT_DOWNLOAD = 2
    STATUS_IN_DOWNLOAD = 3
    STATUS_STOP = 4
    STATUS_FINISH = 5
    
    def __init__(self, image_object):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        
        
        # Init sizes.
        self.item_height = 50        
        self.info_width = -1
        self.progressbar_width = 100
        self.progressbar_padding_x = 10
        self.progressbar_height = 12
        self.check_button_padding_x = 10
        self.info_padding_x = 5

        self.icon_pixbuf = None
        self.icon_side_pixbuf = None
        self.icon_side_dpixbuf = app_theme.get_pixbuf("individuation/small_side.png")
        self.image_object = image_object        
        self.button_status = BUTTON_NORMAL
        
        # Init status.
        self.status = self.STATUS_WAIT_DOWNLOAD
        self.status_text = "等等下载啊"
        
        # Init buffers. 
        self.progress_buffer = ProgressBuffer()
        self.check_button_buffer = CheckButtonBuffer(True)
        self.check_button_width = self.check_button_buffer.render_width  + self.check_button_padding_x * 2
        
        self.stop_pixbuf = app_theme.get_pixbuf("individuation/stop.png").get_pixbuf()
        self.stop_pixbuf_padding_x = 5
        self.block_width = 50
        self.download_task = TaskObject(image_object.big_url, image_object.get_save_path())
        # self.download_task = TaskObject("http://packages.linuxdeepin.com/deepin/pool/main/d/deepin-emacs/deepin-emacs_1.1-1_all.deb")
        self.download_task.signal.add_callback("update", self.download_update)
        self.download_task.signal.add_callback("finish", self.download_finish)
        
    def start_download(self):    
        fetch_service.add_missions([self.download_task])
        
    def render_check_button(self, cr, rect):
        if self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")

        self.check_button_buffer.render(cr, 
                                        gtk.gdk.Rectangle(rect.x + (rect.width - self.check_button_buffer.render_width) / 2,
                                                          rect.y + (rect.height - self.check_button_buffer.render_height)/ 2,
                                                          rect.width, rect.height))
        
    def render_info(self, cr, rect):
        if self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")
        
        if self.icon_pixbuf is None:
            self.icon_pixbuf = cache_manager.get_small_pixbuf(self.image_object, 37, 38)
            
        icon_width = self.icon_pixbuf.get_width()
        icon_height = self.icon_pixbuf.get_height()
        icon_x = rect.x + self.info_padding_x
        icon_y = rect.y + (rect.height - icon_height) / 2
        
        
        # Draw shadow.
        drop_shadow_padding = 3
        drop_shadow_radious = 3
        draw_shadow(
            cr,
            icon_x,
            icon_y,
            icon_width + drop_shadow_padding,
            icon_height + drop_shadow_padding,
            drop_shadow_radious,
            app_theme.get_shadow_color("window_shadow")
            )

        outside_shadow_padding = 2
        outside_shadow_radious = 3
        draw_shadow(
            cr,
            icon_x - outside_shadow_padding,
            icon_y - outside_shadow_padding,
            icon_width + outside_shadow_padding * 2,
            icon_height + outside_shadow_padding * 2,
            outside_shadow_radious,
            app_theme.get_shadow_color("window_shadow")
            )
        
        # Draw wallpaper.
        draw_pixbuf(cr, self.icon_pixbuf, icon_x, icon_y)
        
            
        rect.x = icon_x + self.icon_pixbuf.get_width() + self.info_padding_x
        rect.width -= self.info_padding_x * 2 - self.icon_pixbuf.get_width()
        _width, _height = get_content_size(self.image_object.get_display_name())
        draw_text(cr, "<b>%s</b>" % self.image_object.get_display_name(), rect.x, icon_y, rect.width, _height,
                  text_size=10)    
        
        rect.y = icon_y + icon_width - _height
        _width, _height = get_content_size(self.status_text)
        draw_text(cr, self.status_text, rect.x, rect.y, rect.width, _height)
        
    def render_progressbar(self, cr, rect):     
        if self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")
       
        self.progress_buffer.render(cr, 
                                    gtk.gdk.Rectangle(rect.x + (rect.width - self.progressbar_width) / 2,
                                                      rect.y + (rect.height - self.progressbar_height)/ 2,
                                                      self.progressbar_width, self.progressbar_height))
        
    def render_stop(self, cr, rect):    
        if self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")
        
        icon_x = rect.x + (rect.width - self.stop_pixbuf.get_width()) / 2
        icon_y = rect.y + (rect.height - self.stop_pixbuf.get_height()) / 2
        draw_pixbuf(cr, self.stop_pixbuf, icon_x, icon_y)
        
    def render_block(self, cr, rect):    
        if self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")
    
    def get_column_widths(self):
        return [self.check_button_width, self.info_width, 
                self.progressbar_width + self.progressbar_padding_x * 2,
                self.stop_pixbuf.get_width() + self.stop_pixbuf_padding_x * 2,
                self.block_width
                ]
    
    
    def get_column_renders(self):
        return [
            self.render_check_button,
            self.render_info,
            self.render_progressbar,
            self.render_stop, 
            self.render_block,
            ]
    
    def get_height(self):
        return self.item_height
    
    def emit_request_redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def unselect(self):
        pass
    
    def select(self):
        pass
    
    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.emit_request_redraw()

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.emit_request_redraw()
    
    def motion_notify(self, column, offset_x, offset_y):
        if column == 0:
            if self.check_button_buffer.motion_button(offset_x, offset_y):
                self.emit_request_redraw()
    
    def button_press(self, column, offset_x, offset_y):
        if column == 0:
            if self.check_button_buffer.press_button(offset_x, offset_y):
                self.emit_request_redraw()
                
    def button_release(self, column, offset_x, offset_y):
        if column == 0 and self.check_button_buffer.release_button(offset_x, offset_y):
            self.emit_request_redraw()
                    
    def single_click(self, column, offset_x, offset_y):
        pass        

    def double_click(self, column, offset_x, offset_y):
        pass        
    
    def download_wait(self):
        self.status = self.STATUS_WAIT_DOWNLOAD
        self.status_text = "等待下载"
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def download_start(self):
        self.status = self.STATUS_IN_DOWNLOAD
        self.status_text = "下载中"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def download_update(self, name, obj, data):
        self.progress_buffer.progress = data.progress
        self.status_text = parse_bytes(data.speed)
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def download_finish(self, name, obj, data):
        print "finish"
        self.progress_buffer.progress = 100
        self.status_text = "下载完成"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def download_stop(self):
        pass
            
    def download_parse_failed(self):
        self.status = self.STATUS_PARSE_DOWNLOAD_FAILED
        self.status_text = "分析依赖失败"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
        # global_event.emit("request-clear-failed-action", self.pkg_name, ACTION_UPGRADE)    
            
    def action_start(self):
        self.status = self.STATUS_IN_UPGRADE
        self.status_text = "升级中"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
                
    def action_update(self, percent):
        self.status = self.STATUS_IN_UPGRADE
        self.status_text = "升级中"
        self.progress_buffer.progress = percent
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def action_finish(self):
        self.status = self.STATUS_UPGRADE_FINISH
        self.progress_buffer.progress = 100
        self.status_text = "升级完成"
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> if self.pixbuf:
        >>>     del self.pixbuf
        >>>     self.pixbuf = None
        >>>
        >>> return True

        This is TreeView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, TreeView will call function gc.collect() to release object to release memory.
        '''
        if self.icon_pixbuf:
            del self.icon_pixbuf
            self.icon_pixbuf = None

        return True    

