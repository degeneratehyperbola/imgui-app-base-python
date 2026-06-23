from collections.abc import Callable
from dataclasses import dataclass
import re
from . import *

class begin_disabled:
	def __init__(self, disabled=True) -> None:
		self._captured = lambda: imgui.begin_disabled(disabled)
	
	def __enter__(self):
		self._captured()
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		imgui.end_disabled()

class style_compact:
	def __enter__(self):
		imgui.push_style_var(imgui.StyleVar_.frame_padding, [0, 0])
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		imgui.pop_style_var()

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

		uv_border_topleft = ImVec2(self.cut_left, self.cut_top) / texture_size
		uv_border_bottomright = ImVec2(self.cut_right, self.cut_bottom) / texture_size
		uv_center_min = uv_border_topleft
		uv_center_max = ImVec2(1, 1) - uv_border_bottomright
		offset_min = ImVec2(*map(round, uv_border_topleft * self.scale * texture_size))
		offset_max = ImVec2(*map(round, size - uv_border_bottomright * self.scale * texture_size))

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

				dl.add_image(texture, pos + p1, pos + p2, uv1, uv2, imgui.get_color_u32([1, 1, 1, 1]))
		dl.pop_clip_rect()

@dataclass
class SlicedFrameButton:
	normal: SlicedFrame
	hover: SlicedFrame
	active: SlicedFrame
	disabled: SlicedFrame

	def __call__(self, text='', size: ImVec2Like = None, text_align: ImVec2Like = ImVec2(0.5, 0.5)):
		default_size = imgui.calc_text_size(text) + imgui.get_style().frame_padding*2
		size = calc_item_size(size, *default_size)
		cursor = imgui.get_cursor_screen_pos()

		clicked = imgui.invisible_button(text, size, imgui.ButtonFlags_.enable_nav)

		state = 0
		if imgui.is_item_hovered():
			state = 1
			if imgui.is_mouse_down(imgui.MouseButton_.left):
				state = 2
		if is_disabled():
			state = 3

		match state:
			case 0: self.normal.render(cursor, size)
			case 1: self.hover.render(cursor, size)
			case 2: self.active.render(cursor, size)
			case 3: self.disabled.render(cursor, size)
		render_frame_text(cursor, size, text)
		
		return clicked

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

def autogui(label: str, obj_serialized, unfolded=True, filter='', skip_private=True):
	changed = False
	
	if not isinstance(obj_serialized, dict) and utils.regexp_filter(filter, label) is None:
		return changed, obj_serialized
	if skip_private and label.startswith('_'):
		return changed, obj_serialized

	label = utils.format_label(label)
		
	min0 = re.search('scale|rounding|padding|spacing|delay', label, re.IGNORECASE) is not None
	slider01 = re.search('alpha|transparency|opacity|align', label, re.IGNORECASE) is not None
	is_undefined_flag = re.search('flags', label, re.IGNORECASE) is not None

	match obj_serialized:
		case dict():
			flags = imgui.TreeNodeFlags_.span_full_width
			if unfolded: flags |= imgui.TreeNodeFlags_.default_open
			if imgui.tree_node_ex(label, flags):
				for key in obj_serialized:
					child_changed, obj_serialized[key] = autogui(key, obj_serialized[key], unfolded, filter, skip_private)
					changed = changed or child_changed
				imgui.tree_pop()
		case list():
			with begin_disabled(len(obj_serialized) == 0):
				with imgui_ctx.begin_list_box(label):
					for i, item in enumerate(obj_serialized):
						child_changed, obj_serialized[i] = autogui(f"[{i}]", item)
						changed = changed or child_changed

						if len(obj_serialized) > 1:
							imgui.same_line()
							if imgui.button(f'{icons.ICON_FA_XMARK}##{i}'):
								obj_serialized.pop(i)
								changed = True
								break
					
					if imgui.button(f'{icons.ICON_FA_SQUARE_PLUS} Add Item', [-imgui.FLT_MIN, 0]):
						obj_serialized.append(type(obj_serialized[0])()) # Infer type from first element
						changed = True
		case Flag():
			if imgui.begin_list_box(label):
				T = type(obj_serialized)
				with style_compact():
					for flag in T:
						sub_changed, obj_serialized = imgui.checkbox_flags(utils.format_label(flag.name), obj_serialized.value, flag.value)
						obj_serialized = T(obj_serialized)
						changed = changed or sub_changed
				imgui.end_list_box()
		case Enum():
			if imgui.begin_combo(label, utils.format_label(obj_serialized.name)):
				for enum in type(obj_serialized):
					sub_changed, selected = imgui.selectable(utils.format_label(enum.name), obj_serialized == enum)
					changed = changed or sub_changed
					if selected: obj_serialized = enum
				imgui.end_combo()
		case bool():
			changed, obj_serialized = imgui.checkbox(label, obj_serialized)
		case str():
			changed, obj_serialized = imgui.input_text(label, obj_serialized)
		case int():
			if is_undefined_flag:
				if imgui.begin_list_box(label):
					for i in range(31):
						flag = 1 << i
						sub_changed, selected = imgui.selectable(f'1 << {i}', bool(obj_serialized & flag))
						changed = changed or sub_changed
						if selected: obj_serialized = obj_serialized | flag
						else: obj_serialized = obj_serialized & ~flag
					imgui.end_list_box()
			else:
				changed, obj_serialized = imgui.drag_int(label, obj_serialized, v_max=imgui.INT_MAX if min0 else 0)
		case float():
			if slider01:
				changed, obj_serialized = imgui.slider_float(label, obj_serialized, 0, 1)
			else:
				changed, obj_serialized = imgui.drag_float(label, obj_serialized, 0.01, v_max=imgui.INT_MAX if min0 else 0)
		case ImVec2():
			if slider01:
				changed, obj_serialized = imgui.slider_float2(label, list(obj_serialized), 0, 1)
			else:
				changed, obj_serialized = imgui.drag_float2(label, list(obj_serialized), 0.01, v_max=imgui.INT_MAX if min0 else 0)
			obj_serialized = ImVec2(*obj_serialized)
			if min0: obj_serialized = obj_serialized.max([0, 0])
		case ImVec4():
			flags = imgui.ColorEditFlags_.alpha_preview_half | imgui.ColorEditFlags_.alpha_bar
			changed, obj_serialized = imgui.color_edit4(label, obj_serialized, flags)
			obj_serialized = ImVec4(*obj_serialized)
		case Callable():
			if imgui.button(label):
				obj_serialized()
		case None:
			with begin_disabled():
				imgui.input_text(label, 'None')
		case _:
			with begin_disabled():
				imgui.input_text(label, 'Unknown')
	
	return changed, obj_serialized
