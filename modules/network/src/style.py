#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
from dtk.ui.utils import get_parent_dir, cairo_disable_antialias, color_hex_to_cairo
from dtk.ui.draw import draw_line
from dtk.ui.line import HSeparator
sys.path.append(os.path.join(get_parent_dir(__file__, 4), "dss"))
from constants import *
import gtk

MYHSEPARATOR_COLOR = [
		(0,		("#ffffff", 0)),
		(0.5,	("#777777", 0.8)),
		(1,		("#ffffff", 0))
	 ]

def add_separator(container):
        h_separator = HSeparator(MYHSEPARATOR_COLOR, 0, 0)
        h_separator.set_size_request(-1, 10)
        h_separator.set(0, 0.5, 1, 0)
        container.pack_start(h_separator, False, False)

# Setting UI styles
def set_frame_box_align(box):
    #box.set_spacing(BETWEEN_SPACING)
    align = gtk.Alignment(0, 0, 0, 0)
    align.set_padding(FRAME_TOP_PADDING, STATUS_HEIGHT, FRAME_LEFT_PADDING, 0)
    align.add(box)

    return align

def set_box_with_align(box, types):
    if types is "text":
        align = gtk.Alignment(0, 0, 0, 0)
        align.set_padding(TEXT_WINDOW_TOP_PADDING, 0, TEXT_WINDOW_LEFT_PADDING, 0)
        align.add(box)
        return align
    else:
        align = gtk.Alignment(0, 0, 0, 0)
        align.set_padding(FRAME_TOP_PADDING, STATUS_HEIGHT, FRAME_LEFT_PADDING, FRAME_LEFT_PADDING)
        align.add(box)
        return align

def set_align_text_box(align):
    align.set_padding(TEXT_WINDOW_TOP_PADDING, 0, TEXT_WINDOW_LEFT_PADDING, 0)

def set_main_window(align, has_right=False):
    align.set_padding(FRAME_TOP_PADDING, 1, [0, FRAME_LEFT_PADDING][has_right is True], [0, FRAME_LEFT_PADDING][has_right is True])

def set_table(table):
    #table.set_row_spacings(8)
    table.set_col_spacings(BETWEEN_SPACING)

def wrap_with_align(widget, align="right", width=-1):
    if align is "left":
        align = gtk.Alignment(0, 0.5, 1, 0)
    elif align is "right":
        align = gtk.Alignment(1, 0.5, 0, 0)
        align.set_padding(0,0, 1, 0)
    align.set_size_request(width, CONTAINNER_HEIGHT)
    align.add(widget)
    return align


def set_table_items(table, item_name):
    children = table.get_children()
    for child in children:
        if item_name is "entry":
            from dtk.ui.new_entry import InputEntry, PasswordEntry
            if type(child) is gtk.Alignment:
                c = child.get_children()[0]
                if type(c).__name__ == type(InputEntry()).__name__ or \
                    type(c).__name__ == type(PasswordEntry()).__name__:
                    c.set_size(222, WIDGET_HEIGHT)

def draw_separator(widget, direction):

    def draw_lines(w, event):
        cr = w.window.cairo_create()
        rect = w.allocation
        BORDER_COLOR = color_hex_to_cairo("#d2d2d2")
        cr.set_source_rgb(*BORDER_COLOR)
        cr.set_line_width(1)

        if direction is 0: # Top
            draw_line(cr, rect.x, rect.y, rect.x + rect.width, rect.y)

        elif direction is 1: #Bottom
            draw_line(cr, rect.x, rect.y + rect.height + 1, rect.x + rect.width, rect.y + rect.height +1)
        elif direction is 2: #left
            draw_line(cr, rect.x , rect.y , rect.x, rect.y + rect.height)
        else:
            draw_line(cr, rect.x + rect.width , rect.y + 29, rect.x + rect.width , rect.y + rect.height)

    widget.connect("expose-event", draw_lines)


def draw_out_line(cr, rect, exclude=[]):
    with cairo_disable_antialias(cr):
        BORDER_COLOR = color_hex_to_cairo("#d2d2d2")
        cr.set_source_rgb(*BORDER_COLOR)
        cr.set_line_width(1)
        
        # Top
        if "top" not in exclude:
            draw_line(cr, rect.x, rect.y, rect.x + rect.width, rect.y)
        # bottom
        if "bot" not in exclude:
            draw_line(cr, rect.x, rect.y + rect.height + 1, rect.x + rect.width, rect.y + rect.height +1)
        # left
        if "left" not in exclude:
            draw_line(cr, rect.x , rect.y , rect.x, rect.y + rect.height)
        # right
        if "right" not in exclude:
            draw_line(cr, rect.x + rect.width , rect.y + 29, rect.x + rect.width , rect.y + rect.height)

def draw_background_color(widget):
    def expose_background(w, event):
        cr = w.window.cairo_create()
        rect = w.allocation
        cr.set_source_rgb( 1, 1, 1) 
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
    widget.connect("expose-event", expose_background)
