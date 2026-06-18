from OpenGL.GL import *
import numpy as np
from PIL import Image
import re
from . import *

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

def regexp_filter(pattern: str, s: str):
	if pattern == '' or s == '': return True
	
	try:
		return re.search(pattern, s, re.IGNORECASE)
	except:
		return False

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
