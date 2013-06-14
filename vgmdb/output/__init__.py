import sys
from vgmdb.accept import parse_accept_header
from vgmdb.config import AUTO_RELOAD

# import submodules
import html
import json
import yaml
import turtle
import rdfxml

# As output modules are loaded the name_outputters and
# add_name_handler will be populated
name_outputters = {}	# store a list of outputter objects
name_modules = {}	# store a list of outputter modules
mime_names = {}		# map mimetypes to names

def add_mime_name(mime, name):
	mime_names[mime] = name
def add_name_handler(name, outputter):
	name_outputters[name] = outputter
def add_name_module(name, module):
	name_modules[name] = module
def unload_module(name):
	global mime_names
	new_mime_names = {k:mime_names[k] for k in mime_names.keys() if mime_names[k] != name}
	mime_names = new_mime_names
	del name_outputters[name]
	del name_modules[name]
def load_module(module):
	name = module.name
	# try to create the outputter
	# Skip the plugin if any errors happen
	outputter = module.outputter()
	for type in module.mimetypes:
		add_mime_name(type, name)
	add_name_handler(name, outputter)
	add_name_module(name, module)
def reload_module(name):
	global mime_names
	global name_outputters
	global name_modules
	old_mime_names = dict(mime_names)
	old_name_outputters = dict(name_outputters)
	old_name_modules = dict(name_modules)
	try:
		module = name_modules[name]
		unload_module(name)
		reload(module)
		load_module(module)
	except:
		sys.stderr.write("Couldn't create outputter %s: %s\n"%(name, sys.exc_info()[1]))
		mime_names = old_mime_names
		name_outputters = old_name_outputters
		name_modules = old_name_modules

def load_plugins():
	from types import ModuleType
	for module in globals().values():
		if isinstance(module, ModuleType) and \
		   hasattr(module, 'name') and \
		   hasattr(module, 'mimetypes') and \
		   hasattr(module, 'outputter'):
			try:
				load_module(module)
			except:
				# couldn't load plugin
				sys.stderr.write("Couldn't create outputter %s: %s\n"%(module.name, sys.exc_info()[1]))

def decide_format(forced, accept):
	format = "json"
	all_accepts = parse_accept_header(accept) or []
	for accepts in all_accepts:
		if accepts[0] in mime_names.keys():
			format = mime_names[accepts[0]]
			break
	if forced in mime_names.values():
		format = forced
	return format

def get_outputter(forced, accept):
	format = decide_format(forced, accept)
	if AUTO_RELOAD:
		reload_module(format)
	return name_outputters[format]

load_plugins()