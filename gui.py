import glfw, ctypes
from OpenGL.GL import *
import imgui_ext
from imgui_ext import *

utils_ext = utils
widgets_ext = widgets
del utils, widgets

class GUI:
	def __init__(self, window_title, dpi_scale: float = None):
		self.window_title = window_title
		self.dpi_scale = dpi_scale

	def _init_context(self):
		# GLFW
		glfw.init()
		
		# HiDPI Support
		self.dpi_scale = self.dpi_scale or glfw.get_monitor_content_scale(glfw.get_primary_monitor())[0]

		# OpenGL context version, required for operation on macOS.
		glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
		glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
		glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
		glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
		glfw.window_hint(glfw.VISIBLE, True)

		self.window = glfw.create_window(
			width=int(1280*self.dpi_scale), height=int(720*self.dpi_scale),
			title=self.window_title, monitor=None, share=None
		)
		glfw.make_context_current(self.window)
		glfw.set_key_callback(self.window, self.key_callback)

		glfw.swap_interval(1)

		# ImGUI
		imgui.create_context()
		io = imgui.get_io()
		io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard | imgui.ConfigFlags_.docking_enable
		io.set_ini_filename('.gui.ini')
		imgui.get_style().scale_all_sizes(self.dpi_scale)
		
		# ImPlot
		implot.create_context()
		# scale_all_sizes()
		obj = implot.get_style()
		for attr in dir(obj):
			if not attr.startswith('_'):
				value = getattr(obj, attr)
				if isinstance(value, float):
					setattr(obj, attr, value * self.dpi_scale)
				elif isinstance(value, ImVec2):
					setattr(obj, attr, value * self.dpi_scale)

		# ImGui Backend
		imgui.backends.glfw_init_for_opengl(ctypes.cast(self.window, ctypes.c_void_p).value, True) # Still seeking a perfect language
		imgui.backends.opengl3_init('#version 150')
		
		self.start()

	def _destroy_context(self):
		imgui.backends.glfw_shutdown()
		imgui.backends.opengl3_shutdown()
		implot.destroy_context(None)
		imgui.destroy_context(None)
		glfw.terminate()

	def key_callback(self, window, key, scan_code, action, mods):
		'''GLFW default key callback.'''

	def start(self):
		'''Called after graphics and ImGui context initializes, every time run method is called and the main window opens.'''

	def gui(self):
		'''Main GUI method that runs in a loop. ImGui and OpenGL code here.'''
	
	def close(self):
		'''Called when user closes the window, before the context is destroyed.'''

	def add_font(self, path: str, size=0, merge_with_last=False):
		font_cfg = imgui.ImFontConfig()
		font_cfg.merge_mode = merge_with_last
		font = imgui.get_io().fonts.add_font_from_file_ttf(path, size*self.dpi_scale, font_cfg)
		if not merge_with_last:
			return font

	def run(self):
		'''Every app can only be run once. This method is thread blocking!'''
		self._init_context()
		self.start()

		while not glfw.window_should_close(self.window):
			glfw.poll_events()

			# glClearColor(0, 0, 0, 1)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			imgui.backends.glfw_new_frame()
			imgui.backends.opengl3_new_frame()
			imgui.new_frame()

			self.gui()

			imgui.render()
			imgui.backends.opengl3_render_draw_data(imgui.get_draw_data())

			glfw.swap_buffers(self.window)
		
		self.close()
		self._destroy_context()
