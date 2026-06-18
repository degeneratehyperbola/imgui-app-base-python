'''`ImGui and enum data types serialization helper module.'''

import sys
import json
from pathlib import Path
from . import *

class JSONEncoder(json.JSONEncoder):
	def default(self, obj):
		match obj:
			case ImVec2():
				return {'x': obj.x, 'y': obj.y}
			case ImVec4():
				return {'x': obj.x, 'y': obj.y, 'z': obj.z, 'w': obj.w}
			case Enum():
				return obj.value

class JSONDecoder(json.JSONDecoder):
	def __init__(self, *args, **kwargs):
		kwargs['object_hook'] = self._object_hook # In parent class it's a property, hence we can't simply override
		super().__init__(*args, **kwargs)

	def _object_hook(self, d: dict):
		match d:
			case {'x': x, 'y': y, 'z': z, 'w': w}:
				return ImVec4(x, y, z, w)
			case {'x': x, 'y': y}:
				return ImVec2(x, y)
		
		return d

def dump_obj(obj, path: str):
	Path(path).write_text(json.dumps(obj, indent='\t', cls=JSONEncoder))

def load_obj(path: str):
	return json.loads(Path(path).read_text(), cls=JSONDecoder)

def enum_subset(
	name: str,
	T: type[Enum],
	include: list[Enum] = None,
	exclude: list[Enum] = None,
	flag=False
) -> type[Enum]:
	'''A type factory that makes an Enum with limited possible values. Use statically!'''

	subset = include or list(T)
	negative_subset = exclude or []
	mapping = {e.name: e.value for e in subset if e not in negative_subset}

	if flag:
		cls = Flag(name, mapping)
	else:
		cls = Enum(name, mapping)
	
	setattr(sys.modules[__name__], name, cls)

def flag_subset(
	name: str,
	T: type[Enum],
	include: list[Enum] = None,
	exclude: list[Enum] = None
) -> type[Flag]:
	'''`enum_subset` but for flags. Use statically!'''

	return enum_subset(name, T, include, exclude, True)

enum_subset('TreeLines', imgui.TreeNodeFlags_, include=[
	imgui.TreeNodeFlags_.draw_lines_full,
	imgui.TreeNodeFlags_.draw_lines_to_nodes,
	imgui.TreeNodeFlags_.draw_lines_none,
])
enum_subset('WindowMenuButtonPosition', imgui.Dir, include=[
	imgui.Dir.none,
	imgui.Dir.left,
	imgui.Dir.right,
])
enum_subset('ColorButtonPosition', imgui.Dir, include=[
	imgui.Dir.left,
	imgui.Dir.right,
])

def get_style_serialized():
	style = imgui.get_style()
	serialized = {
		'colors': {}
	}

	for attr_name in dir(style):
		val = getattr(style, attr_name)

		if callable(val): continue
		if attr_name.startswith('_'): continue
		
		match attr_name:
			case 'tree_lines_flags':
				val = TreeLines(val)
			case 'hover_flags_for_tooltip_mouse' | 'hover_flags_for_tooltip_nav':
				val = imgui.HoveredFlags_(val)
			case 'window_menu_button_position':
				val = WindowMenuButtonPosition(val)
			case 'color_button_position':
				val = ColorButtonPosition(val)
		
		serialized[attr_name] = val

	for col in imgui.Col_:
		if 'count' in col.name.casefold(): continue

		serialized['colors'][col.name] = style.color_(col.value)

	return serialized

def apply_style_serialized(serialized: dict):
	style = imgui.get_style()

	for attr_name, val in serialized.items():
		if attr_name == 'colors': continue

		setattr(style, attr_name, getattr(val, 'value', val))
	
	for col_name, val in serialized['colors'].items():
		style.set_color_(getattr(imgui.Col_, col_name), val)
