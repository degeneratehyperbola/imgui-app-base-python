import numpy as np
from PIL import Image
from gui import *
from dataclasses import dataclass
from enum import Enum, Flag, STRICT
import re

########################
# ImGui Basic Features #
########################

imgui.INT_MAX = 0x7FFFFFFF
imgui.INT_MIN = -0x80000000

def alpha_mod(col: ImVec4Like, alpha: float):
	return ImVec4(*col) * ImVec4(1, 1, 1, alpha)
ImVec4.alpha_mod = alpha_mod

def _ImVec2_copy(self: ImVec2Like):
	return ImVec2(*self)
ImVec2.copy = _ImVec2_copy

def _ImVec2_max(self: ImVec2, other: ImVec2Like): return ImVec2(*map(max, self, other))
ImVec2.max = _ImVec2_max

def _ImVec2_min(self: ImVec2, other: ImVec2Like): return ImVec2(*map(min, self, other))
ImVec2.min = _ImVec2_min

###############
# ImGui Utils #
###############

def render_frame_text(pos: ImVec2, size: ImVec2, text: str = None, text_align: ImVec2Like = ImVec2(0.5, 0.5), text_color=0xFFFFFFFF):
	if text is None: return
	
	text_size = imgui.calc_text_size(text)
	content_size = size - imgui.get_style().frame_padding
	text_pos = content_size * text_align - text_size * text_align

	dl = imgui.get_window_draw_list()
	dl.push_clip_rect(pos, pos + size, True)
	dl.add_text(pos + text_pos, text_color, text)
	dl.pop_clip_rect()

def calc_frame_size(size: ImVec2Like) -> ImVec2:
	if size is None:
		size = [-1, imgui.get_frame_height()]
	size = ImVec2(*size)
	if size.x < 0:
		size.x += imgui.get_content_region_avail().x + 1
	if size.x < 0:
		size.y += imgui.get_content_region_avail().y + 1
	size = size.max([1, 1])
	return size

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

def is_disabled():
	return imgui.get_current_context().disabled_stack_size > 0

#################
# ImGui Widgets #
#################

@dataclass
class SlicedFrame:
	texture_id: any
	cut_left: int = 0
	cut_top: int = 0
	cut_right: int = 0
	cut_bottom: int = 0
	scale: int = 0

	def render(self, pos: ImVec2, size: ImVec2):
		texture = imgui.ImTextureRef(self.texture_id)
		texture_size = get_texture_size(self.texture_id)

		uv_center_min = ImVec2(self.cut_left, self.cut_top) / texture_size
		uv_border_max = ImVec2(self.cut_right, self.cut_bottom) / texture_size
		uv_center_max = ImVec2(1, 1) - uv_border_max
		offset_min = ImVec2(*map(round, uv_center_min * self.scale * texture_size))
		offset_max = ImVec2(*map(round, size - uv_border_max * self.scale * texture_size))

		pointsx = [0, offset_min.x, offset_max.x, size.x]
		pointsy = [0, offset_min.y, offset_max.y, size.y]
		uvx = [0, uv_center_min.x, uv_center_max.x, 1]
		uvy = [0, uv_center_min.y, uv_center_max.y, 1]

		dl = imgui.get_window_draw_list()
		dl.push_clip_rect(pos, pos + size, True)
		for x, px in enumerate(pointsx):
			for y, py in enumerate(pointsy):
				if x == 0 or y == 0: continue

				p1 = ImVec2(pointsx[x-1], pointsy[y-1])
				p2 = ImVec2(px, py)
				uv1 = ImVec2(uvx[x-1], uvy[y-1])
				uv2 = ImVec2(uvx[x], uvy[y])

				dl.add_image(texture, pos + p1, pos + p2, uv1, uv2)
		dl.pop_clip_rect()

@dataclass
class SlicedFrameButton:
	normal: SlicedFrame
	hover: SlicedFrame
	active: SlicedFrame
	disabled: SlicedFrame

	def __call__(self, text='', size: ImVec2Like = None, text_align: ImVec2Like = ImVec2(0.5, 0.5)):
		size = calc_frame_size(size)
		cursor = imgui.get_cursor_screen_pos()
		res = imgui.invisible_button(text, size, imgui.ButtonFlags_.enable_nav)

		state = 0
		if imgui.is_item_hovered():
			state = 1
			if imgui.is_mouse_down(imgui.MouseButton_.left):
				state = 2
		if is_disabled():
			state = 3
		
		text_color = imgui.get_color_u32(imgui.Col_.text)

		match state:
			case 0: self.normal.render(cursor, size)
			case 1: self.hover.render(cursor, size)
			case 2: self.active.render(cursor, size)
			case 3: self.disabled.render(cursor, size)
		render_frame_text(cursor, size, text, text_color=text_color)
		
		return res

class begin_disabled:
	def __init__(self, disabled=True) -> None:
		self._captured = lambda: imgui.begin_disabled(disabled)
	
	def __enter__(self):
		self._captured()
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		imgui.end_disabled()

def main_docking_space():
	vp = imgui.get_main_viewport()
	imgui.set_next_window_pos(vp.work_pos)
	imgui.set_next_window_size(vp.work_size)
	
	flags = imgui.WindowFlags_.no_docking
	flags |= imgui.WindowFlags_.no_background
	flags |= imgui.WindowFlags_.no_title_bar
	flags |= imgui.WindowFlags_.no_move
	flags |= imgui.WindowFlags_.no_resize
	flags |= imgui.WindowFlags_.no_bring_to_front_on_focus
	flags |= imgui.WindowFlags_.no_nav_focus

	imgui.push_style_var(imgui.StyleVar_.window_rounding, 0)
	imgui.push_style_var(imgui.StyleVar_.window_border_size, 0)
	imgui.push_style_var(imgui.StyleVar_.window_padding, [0, 0])
	
	with imgui_ctx.begin('Main Docking Space', flags=flags):
		imgui.pop_style_var(3)
		imgui.dock_space(1, [0, 0], imgui.DockNodeFlags_.passthru_central_node)

snake2label = lambda s: ' '.join(
	word.capitalize() if word.casefold() not in ['of', 'in', 'and', 'or', 'at'] else word.lower() for word in s.split('_')
)

def autogui(label: str, obj, unfolded=False, skip_private=True):
	changed = False
	label_casefold = label.casefold()
	obj_type = type(obj)
	min0 = re.compile('.*(?:scale|rounding|padding|spacing).*').search(label_casefold)
	slider01 = re.compile('.*(?:alpha|transparency|opacity|align).*').search(label_casefold)
	
	if obj_type is dict:
		imgui.set_next_item_open(unfolded, imgui.Cond_.once)
		if imgui.tree_node(label):
			for key in obj:
				if skip_private and key.startswith('_'): continue

				child_changed, obj[key] = autogui(snake2label(key), obj[key], unfolded)
				changed = changed or child_changed
			imgui.tree_pop()
	elif obj_type is list:
		imgui.set_next_item_open(unfolded, imgui.Cond_.once)
		if imgui.tree_node(label):
			with imgui_ctx.begin_child(label, ImVec2(0, -imgui.get_frame_height() - imgui.get_style().item_spacing.y)):
				for i in range(len(obj)):
					child_changed, obj[i] = autogui(f"[{i}]", obj[i], unfolded)
					changed = changed or child_changed

					if len(obj) > 1:
						imgui.same_line()
						if imgui.small_button(f'{icons.ICON_FA_XMARK}##{i}'):
							obj.pop(i)
							changed = True
							break
			imgui.tree_pop()

			if imgui.button(f'Add Element##{label}'):
				if len(obj) > 0:
					# Infer type from first element
					obj.append(type(obj[0])())
					changed = True
	elif isinstance(obj, Enum):
		is_flag = getattr(obj, '_boundary_', None) == STRICT # Some genuine bullshit isn't it
		
		changed = False
		if is_flag:
			if imgui.begin_list_box(label):
				for flag in obj_type:
					sub_changed, selected = imgui.selectable(snake2label(flag.name), bool(obj & flag))
					changed = changed or sub_changed
					if selected: obj = obj | flag
					else: obj = obj & ~flag
				imgui.end_list_box()
		else:
			if imgui.begin_combo(label, snake2label(obj.name)):
				for enum in obj_type:
					sub_changed, selected = imgui.selectable(snake2label(enum.name), obj == enum)
					changed = changed or sub_changed
					if selected: obj = enum
				imgui.end_combo()
	elif obj_type is bool:
		changed, obj = imgui.checkbox(label, obj)
	elif obj_type is str:
		changed, obj = imgui.input_text(label, obj)
	elif obj_type is int:
		is_undefined_flag = re.compile('.*flags.*').search(label_casefold)
		
		if is_undefined_flag:
			if imgui.begin_list_box(label):
				for i in range(31):
					flag = 1 << i
					sub_changed, selected = imgui.selectable(f'1 << {i}', bool(obj & flag))
					changed = changed or sub_changed
					if selected: obj = obj | flag
					else: obj = obj & ~flag
				imgui.end_list_box()
		else:
			changed, obj = imgui.drag_int(label, obj)
			if min0: obj = max(0, obj)
	elif obj_type is float:
		if slider01:
			changed, obj = imgui.slider_float(label, obj, 0, 1)
		else:
			changed, obj = imgui.drag_float(label, obj, 0.01)
			if min0: obj = max(0.0, obj)
	elif obj_type is ImVec2:
		if slider01:
			changed, obj = imgui.slider_float2(label, list(obj), 0, 1)
		else:
			changed, obj = imgui.drag_float2(label, list(obj), 0.01)
		obj = ImVec2(*obj)
		if min0: obj = obj.max([0, 0])
	elif obj_type is ImVec4:
		changed, obj = imgui.color_edit4(label, obj, imgui.ColorEditFlags_.alpha_preview_half)
		obj = ImVec4(*obj)
	elif callable(obj):
		if imgui.button(label):
			obj()
	elif obj is None:
		with begin_disabled():
			imgui.input_text(label, 'None')
	
	return changed, obj
