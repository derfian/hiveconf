#!/usr/bin/env python
#
#
# Clarence - programmer's calculator
#
# Copyright (C) 2002-2003 Tomasz M�ka <pasp@ll.pl>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os, sys, getopt
import string, whrandom

#import pygtk
#pygtk.require('1.2')

import gtk, GDK
import hiveconf

from math import *

version = "0.2.2"

gui = {}
gui["fhelp_window"] = gui["disable_menu"] = 0
disable_menu = 0
labels = ("DEC   =>", "HEX   =>", "OCT   =>", "ASCII =>", "BIN   =>")
entries = ("entry_dec", "entry_hex", "entry_oct", "entry_asc", "entry_bin")

flist = (
		"|", "Bitwise OR",
		"^", "Bitwise XOR",
		"&", "Bitwise AND",
		"~x", "Bitwise NOT",
		"<<, >>", "Shifts",
		"+", "Addition",
		"-", "Subtraction",
		"*", "Multiplication",
		"/", "Division",
		"%", "Remainder",
		"**", "Exponentiation",
		"+x, -x", "Positive, negative",
		"acircle(r)", "Return the area of circle.",
		"acos (x)", "Return the arc cosine of x.",
		"and", "Boolean AND",
		"ans ()", "Return last result.",
		'asc ("something")', "Return value for last four ASCII chars.",
		"asin (x)", "Return the arc sine of x.",
		"atan (x)", "Return the arc tangent of x.",
		"atan2 (y, x)", "Return atan(y / x).",
		'bin ("10100010110")', "Return value of binary string.",
		"ceil (x)", "Return the ceiling of x as a real.",
		"cos (x)", "Return the cosine of x.",
		"cosh (x)", "Return the hyperbolic cosine of x.",
		"e", "The mathematical constant e.",
		"exp (x)", "Return e**x.",
		"fabs (x)", "Return the absolute value of the real x.",
		"floor (x)", "Return the floor of x as a real.",
		"fmod (x, y)", "Return x % y.",
		"hypot (x, y)", "Return the Euclidean distance, sqrt(x*x + y*y).",
		"ldexp (x, i)", "Return x * (2**i).",
		"log (x)", "Return the natural logarithm of x.",
		"log10 (x)", "Return the base-10 logarithm of x.",
		"max(x0, x1, ...)", "Return the biggest element.",
		"min(x0, x1, ...)", "Return the smallest element.",
		"not x", "Boolean NOT",
		"or", "Boolean OR",
		"pcircle(r)", "Return the perimeter of circle.",
		"pi", "The mathematical constant pi.",
		"pow (x, y)", "Return x**y.",
		"rnd()", "Return the random number in the range [0.0 ... 1.0).",
		"round(x, n)", "Return the floating point value x rounded to n digits after the decimal point.",
		"sasphere(r)", "Return the surface area of sphere.",
		"sin (x)", "Return the sine of x.",
		"sinh (x)", "Return the hyperbolic sine of x.",
		"sqrt (x)", "Return the square root of x.",
		"tan (x)", "Return the tangent of x.",
		"tanh (x)", "Return the hyperbolic tangent of x.",
		"urnd(a, b)", "Return the random number in the range [a ... b].",
		"vcone(r,h)", "Return the volume of cone.",
		"vcylinder(r,h)", "Return the volume of cylinder.",
		"vl2d(x0,y0,x1,y1)", "Return the length of vector (2D).",
		"vl3d(x0,y0,z0,x1,y1,z1)", "Return the length of vector (3D).",
		"vsphere(r)", "Return the volume of sphere.",
		"bits(x)", "Return the number of set bits.",
		)

default_window_placement = 1
default_ascii_only = 0
default_fixed_font = "fixed"
default_win_height = 400
default_win_width = 240
default_remember_expression = 1
default_binary_separators = 3
default_last_expression = ""

#------------------------------------------------------------

def window_pos_mode(widget):
	placement = hive.get_integer("/window/placement", default_window_placement)
	if placement == 0:
		widget.set_position(gtk.WIN_POS_NONE)
	elif placement == 1:
		widget.set_position(gtk.WIN_POS_CENTER)
	elif placement == 2:
		widget.set_position(gtk.WIN_POS_MOUSE)

def main_menu(action, widget):
	if action == 1:
		gui["main_entry"].set_text("")
	elif action == 2:
		gtk.mainquit()
	elif action == 3:
		prefs_window()

def insert_menu(action, widget):
	if action == 1:
		gui["main_entry"].append_text('bin("")')
		gui["main_entry"].set_position(len(gui["main_entry"].get_text())-2)
	elif action == 2:
		gui["main_entry"].append_text('asc("")')
		gui["main_entry"].set_position(len(gui["main_entry"].get_text())-2)
	elif action == 3:
		gui["main_entry"].append_text('ans()')

def select_menu(action, widget):
	if action < 6:
		gui[entries[action-1]].select_region(0, len(gui[entries[action-1]].get_text()))
	else:
		for i in range(5):
			gui[entries[i]].select_region(0, 0)
		gui["main_entry"].grab_focus()

def help_menu(action, widget):
	if action == 1:
		about_window()

#------------------------------------------------------------

def prefs_window_close(*args):
	gui["prefs_window"].hide()
	gui["main_window"].set_sensitive(gtk.TRUE)
	gui["main_entry"].grab_focus()
	display_binary(int(eval(gui["entry_dec"].get_text())))

def prefs_toggled(widget, option):
	if option == 0:
		hive.set_bool("/ascii_only", widget.active)
	else:
		hive.set_bool("/remember_expression", widget.active)

def prefs_selected_1(widget, option):
	hive.set_integer("/window/placement", option)

def prefs_selected_2(widget, option):
	hive.set_integer("/binary_separators", option)
		
def prefs_window():
	win = gtk.GtkWindow()
	gui["prefs_window"]=win
	win.set_policy(gtk.TRUE, gtk.TRUE, gtk.FALSE)
	win.set_title("Preferences")
	win.connect("delete_event", prefs_window_close)
	win.set_border_width(2)

	window_pos_mode(win)

	frame = gtk.GtkFrame()
	frame.show()
	frame.set_border_width(2)
	win.add(frame)

	vbox = gtk.GtkVBox(spacing=5)
	vbox.show()
	frame.add(vbox)

	gui["cb_ascii"] = gtk.GtkCheckButton("ASCII only")
	vbox.pack_start(gui["cb_ascii"])
	gui["cb_ascii"].connect("toggled", prefs_toggled, 0)
	gui["cb_ascii"].show()

	gui["cb_rexp"] = gtk.GtkCheckButton("Remember last expression")
	vbox.pack_start(gui["cb_rexp"])
	gui["cb_rexp"].connect("toggled", prefs_toggled, 1)
	gui["cb_rexp"].show()

	hbox = gtk.GtkHBox()
	vbox.pack_start(hbox)
	hbox.show()

	label = gtk.GtkLabel(" Window placement: ")
	label.show()
	hbox.pack_start(label)

	menu = gtk.GtkMenu()

	menuitem = gtk.GtkMenuItem("None")
	menuitem.connect("activate", prefs_selected_1, 0)
	menu.append(menuitem)
	menuitem.show()
	menuitem = gtk.GtkMenuItem("Center")
	menuitem.connect("activate", prefs_selected_1, 1)
	menu.append(menuitem)
	menuitem.show()
	menuitem = gtk.GtkMenuItem("Mouse")
	menuitem.connect("activate", prefs_selected_1, 2)
	menu.append(menuitem)
	menuitem.show()

	gui["wp_menu"] = gtk.GtkOptionMenu()
	gui["wp_menu"].set_menu(menu)

	gui["wp_menu"].set_history(
		hive.get_integer("/window/placement", default_window_placement))
	
	hbox.pack_start(gui["wp_menu"])
	gui["wp_menu"].show()

	hbox = gtk.GtkHBox()
	vbox.pack_start(hbox)
	hbox.show()

	label = gtk.GtkLabel(" Binary separators: ")
	label.show()
	hbox.pack_start(label)

	menu = gtk.GtkMenu()

	menuitem = gtk.GtkMenuItem("0")
	menuitem.connect("activate", prefs_selected_2, 0)
	menu.append(menuitem)
	menuitem.show()
	menuitem = gtk.GtkMenuItem("1")
	menuitem.connect("activate", prefs_selected_2, 1)
	menu.append(menuitem)
	menuitem.show()
	menuitem = gtk.GtkMenuItem("3")
	menuitem.connect("activate", prefs_selected_2, 2)
	menu.append(menuitem)
	menuitem.show()
	menuitem = gtk.GtkMenuItem("7")
	menuitem.connect("activate", prefs_selected_2, 3)
	menu.append(menuitem)
	menuitem.show()

	gui["bs_menu"] = gtk.GtkOptionMenu()
	gui["bs_menu"].set_menu(menu)
	gui["bs_menu"].set_history(
		hive.get_integer("/binary_separators", default_binary_separators))
	
	hbox.pack_start(gui["bs_menu"])
	gui["bs_menu"].show()


	if hive.get_bool("/ascii_only", default_ascii_only):
		gui["cb_ascii"].set_active(gtk.TRUE)
	else:
		gui["cb_ascii"].set_active(gtk.FALSE)
	
	if hive.get_bool("/remember_expression", default_remember_expression):
		gui["cb_rexp"].set_active(gtk.TRUE)
	else:
		gui["cb_rexp"].set_active(gtk.FALSE)

	button = gtk.GtkButton("Close")
	button.connect("clicked", prefs_window_close)
	vbox.pack_start(button, expand=gtk.FALSE)
	button.set_flags(gtk.CAN_DEFAULT)
	button.grab_default()
	button.show()

	gui["main_window"].set_sensitive(gtk.FALSE)
	gui["prefs_window"].show()

#------------------------------------------------------------

def about_window_close(*args):
	gui["about_window"].hide()
	gui["main_window"].set_sensitive(gtk.TRUE)
	gui["main_entry"].grab_focus()

def about_window():
	win = gtk.GtkWindow()
	gui["about_window"]=win
	win.set_policy(gtk.TRUE, gtk.TRUE, gtk.FALSE)
	win.set_title("About")
	win.connect("delete_event", about_window_close)
	win.set_border_width(2)

	window_pos_mode(win)

	frame = gtk.GtkFrame()
	frame.show()
	frame.set_border_width(2)
	win.add(frame)

	vbox = gtk.GtkVBox(spacing=5)
	vbox.show()
	frame.add(vbox)

	label = gtk.GtkLabel("\n\n" + "Clarence (programmer's calculator)\n"
						"\nversion " + version +"\n\n"
						"Written by Tomasz Maka <pasp@ll.pl>\n")
	set_font(label)
	label.show()
	vbox.pack_start(label)

	entry = gtk.GtkEntry()
	gui["http_entry"] = entry
	entry.set_editable(gtk.FALSE)
	entry.set_usize(290, -2)
	set_font(entry)
	entry.show()
	vbox.pack_start(entry)

	entry.set_text("http://clay.ll.pl/clarence.html")

	button = gtk.GtkButton("OK")
	button.connect("clicked", about_window_close)
	vbox.pack_start(button, expand=gtk.FALSE)
	button.set_flags(gtk.CAN_DEFAULT)
	button.grab_default()
	button.show()

	gui["main_window"].set_sensitive(gtk.FALSE)
	gui["about_window"].show()


#------------------------------------------------------------

def fhelp_window_close(*args):
	gui["fhelp_window"].hide()
	gui["fhelp_window"] = 0
	gui["main_entry"].grab_focus()

def functions_help_window(*args):
	if gui["fhelp_window"] == 0:
		win = gtk.GtkWindow()
		gui["fhelp_window"]=win
		win.set_policy(gtk.TRUE, gtk.TRUE, gtk.FALSE)
		win.set_title("Available functions and constants")
		win.set_usize(500, 300)
		win.connect("delete_event", fhelp_window_close)
		win.set_border_width(4)

		window_pos_mode(win)

		vbox = gtk.GtkVBox(spacing=5)
		win.add(vbox)
		vbox.show()

	   	scrolled_window = gtk.GtkScrolledWindow()
		vbox.pack_start(scrolled_window, expand=gtk.TRUE)
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled_window.show()
 
		clist = gtk.GtkCList(2)
		clist.set_row_height(18)
		clist.set_column_width(0, 180)
		clist.set_column_width(1, 520)
		clist.set_selection_mode(gtk.SELECTION_BROWSE)
		set_font(clist)
		scrolled_window.add(clist)
		clist.show()

		mlist = map(lambda i: "", range(2))

		clist.freeze()
		for i in range(len(flist)/2):
			mlist[0]=flist[i*2]
			mlist[1]=flist[i*2+1]
			clist.append(mlist)
		clist.thaw()

		button = gtk.GtkButton("Close")
		button.connect("clicked", fhelp_window_close)
		vbox.pack_start(button, expand=gtk.FALSE)
		button.set_flags(gtk.CAN_DEFAULT)
		button.grab_default()
		button.show()

		gui["fhelp_window"].show()
	else:
		gui["fhelp_window"].get_window()._raise()	

#------------------------------------------------------------

def warning_window_close(*args):
	gui["warning_window"].hide()
	gui["main_window"].set_sensitive(gtk.TRUE)
	gui["main_entry"].grab_focus()

def warning_window(title, message):
	win = gtk.GtkWindow()
	gui["warning_window"]=win
	win.set_policy(gtk.TRUE, gtk.TRUE, gtk.FALSE)
	win.set_title(title)
	win.set_usize(300, -2)
	win.connect("delete_event", warning_window_close)
	win.set_border_width(4)

	window_pos_mode(win)

	vbox = gtk.GtkVBox(spacing=5)
	win.add(vbox)
	vbox.show()

	label = gtk.GtkLabel("\n\n" + message + "\n\n")
	set_font(label)
	label.show()
	vbox.pack_start(label)

	button = gtk.GtkButton("Close")
	button.connect("clicked", warning_window_close)
	vbox.pack_start(button, expand=gtk.FALSE)
	button.set_flags(gtk.CAN_DEFAULT)
	button.grab_default()
	button.show()

	gui["main_window"].set_sensitive(gtk.FALSE)
	gui["warning_window"].show()

#------------------------------------------------------------

def create_main_window(*args):
	win = gtk.GtkWindow()
	gui["main_window"]=win

	win.set_policy(gtk.TRUE, gtk.TRUE, gtk.FALSE)
	win.set_title("Clarence " + version)
	win.set_usize(
		hive.get_integer("/window/width", default_win_width),
		hive.get_integer("/window/height", default_win_height))
	
	win.connect("delete_event", gtk.mainquit)

	window_pos_mode(win)

	vbox1 = gtk.GtkVBox(spacing=5)
	win.add(vbox1)
	vbox1.show()

	ag = gtk.GtkAccelGroup()
	itemf = gtk.GtkItemFactory(gtk.GtkMenuBar, "<main>", ag)
	gui["main_window"].add_accel_group(ag)
	itemf.create_items([
		('/_Misc',                      None,               None,           0, '<Branch>'),
		('/_Misc/_Clear',               'Escape',           main_menu,      1, ''),
		('/_Misc/sep1',                 None,               None,           0, '<Separator>'),
		('/_Misc/Pre_ferences',         '<control>P',       main_menu,      3, ''),
		('/_Misc/sep1',                 None,               None,           0, '<Separator>'),
		('/_Misc/E_xit',                '<alt>X',           main_menu,      2, ''),
		('/_Insert',                    None,               None,           0, '<Branch>'),
		('/_Insert/_Bin value',         '<control>comma',   insert_menu,    1, ''),
		('/_Insert/_ASCII chars',       '<control>period',  insert_menu,    2, ''),
		('/_Insert/_Last result',       '<control>slash',   insert_menu,    3, ''),
		('/_Select',                    None,               None,           0, '<Branch>'),
		('/_Select/_Decimal field',     '<control>1',       select_menu,    1, ''),
		('/_Select/_Hexadecimal field', '<control>2',       select_menu,    2, ''),
		('/_Select/_Octal field',       '<control>3',       select_menu,    3, ''),
		('/_Select/_ASCII field',       '<control>4',       select_menu,    4, ''),
		('/_Select/_Binary field',      '<control>5',       select_menu,    5, ''),
		('/_Select/sep1',               None,               None,           0, '<Separator>'),
		('/_Select/_Clear fields',      '<control>0',       select_menu,    6, ''),
		('/_Help',                      None,               None,           0, '<LastBranch>'),
		('/_Help/Functions list',       'F1',   functions_help_window,      1, ''),
		('/_Help/sep1',                 None,               None,           0, '<Separator>'),
		('/_Help/_About',               '<control>I',       help_menu,      1, '')
	])
	menubar = itemf.get_widget('<main>')
	if (gui["disable_menu"] == 0):
		vbox1.pack_start(menubar, expand=gtk.FALSE)
		menubar.show()

	vbox2 = gtk.GtkVBox(spacing=5)
	vbox1.pack_start (vbox2, expand=gtk.TRUE);
	vbox2.show()

	entry = gtk.GtkEntry()
	gui["main_entry"] = entry
	vbox2.pack_start(entry, expand=gtk.FALSE)
	vbox2.set_border_width(4)
	set_font(entry)
	if hive.get_bool("/remember_expression", default_remember_expression):
		entry.set_text(hive.get_string("/last_expression", default_last_expression))
		
	entry.connect("key_press_event", key_function)
	entry.grab_focus()
	gui["main_entry"].show()

	frame = gtk.GtkFrame()
	vbox2.pack_start(frame)
	frame.show()

	vbox3 = gtk.GtkVBox()
	frame.add(vbox3)
	vbox3.show()

	table = gtk.GtkTable(2, 5, gtk.FALSE)
	table.set_row_spacings(5)
	table.set_col_spacings(5)
	table.set_border_width(10)
	vbox3.pack_start(table)
	table.show()

	for y in range(5):
		label = gtk.GtkLabel(labels[y])
		set_font(label)
		label.show()
		table.attach(label, 0,1, y,y+1)
		entry = gtk.GtkEntry()
		gui[entries[y]] = entry
		entry.set_editable(gtk.FALSE)
		entry.set_usize(260, -2)
		set_font(entry)
		entry.show()
		table.attach(entry, 1,2, y,y+1)

	gui["main_window"].show()

	if hive.get_string("/remember_expression", default_remember_expression):
		result(hive.get_string("/last_expression", default_last_expression))
	else:
		result(0)

#------------------------------------------------------------

def getachr(value):
	fld = 255
	if hive.get_bool("/ascii_only", default_ascii_only):
		fld = 127
	if (value>=32) and (value<=fld):
		return value
	else:
		return "."

#------------------------------------------------------------
# functions

def vl2d(x0,y0,x1,y1):
	return sqrt((x1-x0)**2 + (y1-y0)**2)

def vl3d(x0,y0,z0,x1,y1,z1):
	return sqrt((x1-x0)**2 + (y1-y0)**2 + (z1-z0)**2)

def acircle(r):
	return pi*r*r

def pcircle(r):
	return 2.0*pi*r

def vsphere(r):
	return (4.0/3.0)*pi*r*r*r

def sasphere(r):
	return 4.0*pi*r*r

def vcone(r,h):
	return (1.0/3.0)*pi*r*r*h

def vcylinder(r,h):
	return pi*r*r*h

def rnd():
	return whrandom.random()

def urnd(a, b):
	return round(a+(b-a)*whrandom.random())		#uniform()

#------------------------------------------------------------

def bits(value):
	result=0
	for i in range(32):
		k=(value >> i) & 1
		if (k):
			result=result+1	
	return result

#------------------------------------------------------------

def bin(value):
	result=0
	for i in range(len(value)):
		if (value[i]!="0" and value[i]!="1"):
			return 0
	for i in range(len(value)):
		if (i>=32):
			return 0
		result=result+((ord(value[len(value)-1-i])-ord("0")) * 1<<i)
	return result

#------------------------------------------------------------

def asc(value):
	result=0
	for i in range(len(value)):
		if (i<4):
			result=result+(ord(value[len(value)-1-i]) * 256**i)
	return result

#------------------------------------------------------------

def ans():
	return eval(gui["entry_dec"].get_text())

#------------------------------------------------------------

def display_binary(value):
	r_bin=""
	mode = hive.get_integer("/binary_separators", default_binary_separators)
	for i in range(32):
		k = 31 - i
		chrr=chr(ord("0")+((value>>k) & 1))
		r_bin=r_bin+chrr
		if (mode and (k > 0) and (k % (16/(2**(mode-1)))==0)):
			r_bin=r_bin+"."
	gui["entry_bin"].set_text(r_bin)

#------------------------------------------------------------

def result(value):
	if (value):
		try:
			resl=eval(value)
			resli=int(resl)
		except NameError:
			warning_window("Warning", "Function not found!")
			return 0
		except SyntaxError:
			warning_window("Warning", "Wrong syntax!")
			return 0
		except TypeError:
			warning_window("Warning", "Wrong syntax!")
			return 0
		except ZeroDivisionError:
			warning_window("Warning", "Division by zero!")
			return 0
		except OverflowError:
			warning_window("Warning", "Overflow detected!")
			return 0
		except ValueError:
			warning_window("Warning", "Value error!")
			return 0
	else:
		resl=0
		resli=0
	r_dec = str(resl)
	gui["entry_dec"].set_text(r_dec)
	r_hex = str(hex(resli))
	gui["entry_hex"].set_text(r_hex)
	r_oct = str(oct(resli))
	gui["entry_oct"].set_text(r_oct)
	r_asc="%c%c%c%c" % (getachr((resli>>24) & 255),
    getachr((resli>>16) & 255),
    getachr((resli>>8) & 255), getachr(resli & 255))
	gui["entry_asc"].set_text(r_asc)
	display_binary(resli)

#------------------------------------------------------------

def set_font(widget):
	style = widget.get_style().copy()
	style.font = gui["fixed_font"]
	widget.set_style(style)

#------------------------------------------------------------
    
def key_function(entry, event):
	if event.keyval == GDK.Return:
		entry.set_text(string.lower(entry.get_text()))
		result(entry.get_text())

#------------------------------------------------------------

def pcalc_write_config():
	if gui["main_window"].get_window():
		hive.set_integer("/window/width", gui["main_window"].get_window().width)
		hive.set_integer("/window/height", gui["main_window"].get_window().height)
	if hive.get_bool("/remember_expression", default_remember_expression):
		hive.set_string("/last_expression",
				string.replace(gui["main_entry"].get_text(), "ans()", "0"))

#------------------------------------------------------------

def usage():
	sys.stderr.write("usage: clarence [-hvm] [--help] [--version] [--disable-menu]\n")
	sys.exit(2)

def main():

	try:
		opts, args = getopt.getopt(sys.argv[1:], "vhm", ["version", "help", "disable-menu"])
	except getopt.GetoptError:
		usage()

	for o, a in opts:
		if o in ("-v", "--version"):
			print(version)
			sys.exit()
		if o in ("-h", "--help"):
			usage()
		if o in ("-m", "--disable-menu"):
			gui["disable_menu"] = 1
			
	global hive
	hive = hiveconf.open_hive("/usr/local/etc/clarence.hconf")
	gui["fixed_font"] = gtk.load_font(hive.get_string("/fixed_font", default_fixed_font))
	create_main_window()
	gtk.mainloop()
	pcalc_write_config()

if __name__ == '__main__': 
	main()

