from OpenGL.GL import *
import numpy as np
from PIL import Image
import sys
import json
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

def is_disabled():
	return imgui.get_current_context().disabled_stack_size > 0

def render_frame_text(pos: ImVec2, size: ImVec2, text: str = None, text_align: ImVec2Like = ImVec2(0.5, 0.5)):
	if text is None: return
	
	text_size = imgui.calc_text_size(text)
	content_size = size - imgui.get_style().frame_padding
	text_pos = content_size * text_align - text_size * text_align

	dl = imgui.get_window_draw_list()
	dl.push_clip_rect(pos, pos + size, True)
	dl.add_text(pos + text_pos, imgui.get_color_u32(imgui.Col_.text), text)
	dl.pop_clip_rect()

def calc_item_size(size: ImVec2Like, default_w: float = 0, default_h: float = 0) -> ImVec2:
	if size is None: size = [0, 0]
	size = ImVec2(*size)
	
	if size.x == 0: size.x = default_w
	if size.y == 0: size.y = default_h

	if size.x < 0: size.x += imgui.get_content_region_avail().x
	if size.x < 0: size.y += imgui.get_content_region_avail().y
	
	size = size.max([4, 4])
	return size

def format_label(s: str):
	return ' '.join(s.split('_')).title()

_texture_info = {}
def get_texture_size(texture_id) -> ImVec2:
	return ImVec2(*_texture_info[texture_id][0:2])

def make_texture(path: str, filter=GL_LINEAR):
	img = Image.open(path).convert('RGBA')
	width, height = img.size
	img_data = np.array(img, np.uint8)

	texture_id = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, texture_id)

	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filter)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filter)

	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

	glBindTexture(GL_TEXTURE_2D, 0)

	_texture_info[texture_id] = [width, height]
	return texture_id
