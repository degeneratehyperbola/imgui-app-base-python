import json
import sys
from gui import *

class ThirtyThree(GUI):
	def start(self):
		self.font_normal = self.add_font('assets/pp_fraktion_mono.otf', 16)
		self.add_font('assets/fa_solid.otf', 16, True, True)
		self.font_title = self.add_font('assets/kh_interference.ttf', 42)
		self.add_font('assets/fa_solid.otf', 42, True, True)
		self.font_tool = self.add_font('assets/marathon_shapiro.ttf', 16)
		self.add_font('assets/fa_solid.otf', 16, True, True)
		
		self.panel_button = widgets_ext.SlicedFrameButton(
			widgets_ext.SlicedFrame(utils_ext.make_texture('assets/panel_normal.png'), 60, 21, 240-140, 120-98, .5),
			widgets_ext.SlicedFrame(utils_ext.make_texture('assets/panel_hover.png'), 60, 21, 240-140, 120-98, .5),
			widgets_ext.SlicedFrame(utils_ext.make_texture('assets/panel_active.png'), 60, 21, 240-140, 120-98, .5),
			widgets_ext.SlicedFrame(utils_ext.make_texture('assets/panel_disabled.png'), 60, 21, 240-140, 120-98, .5)
		)

		self.icon_filter = ''
		self.settings_filter = ''

	def title(self, text: str):
		with imgui_ctx.push_font(self.font_title, self.font_title.legacy_size):
			imgui.text(text)
	
	def tool_button(self, text: str, icon: str = None):
		with imgui_ctx.push_font(self.font_tool, self.font_tool.legacy_size):
			return imgui.button(f'{icon} {text}' if icon else text)

	def gui(self):
		widgets_ext.main_docking_space()

		with imgui_ctx.begin('Icon Inspector'):
			imgui.set_next_item_width(-imgui.FLT_MIN)
			_, self.icon_filter = imgui.input_text_with_hint('##filter', 'Filter', self.icon_filter)

			flags = imgui.TableFlags_.scroll_y
			flags |= imgui.TableFlags_.borders_inner
			flags |= imgui.TableFlags_.sizing_fixed_fit
			with imgui_ctx.begin_table('Icon Table', 2, flags):
				for name, icon in icons.__dict__.items():
					if not name.startswith('ICON'): continue
					if name in ['ICON_MIN_FA', 'ICON_MAX_FA', 'ICON_MAX_16_FA']: continue
					if not utils_ext.regexp_filter(self.icon_filter, name): continue

					imgui.table_next_column()
					imgui.text(icon)
					imgui.table_next_column()
					imgui.text(name.removeprefix('ICON_FA_'))

		with imgui_ctx.begin('Settings'):
			self.title('Settings')

			imgui.set_next_item_width(-imgui.FLT_MIN)
			_, self.settings_filter = imgui.input_text_with_hint('##filter', 'Filter', self.settings_filter)

			with imgui_ctx.begin_child('Settings List'):
				_, style_ser = widgets_ext.autogui('Style', ser_ext.get_style_serialized(), filter=self.settings_filter)

				file_filters = ['ImGui Style Files', '*.style.json']
				if self.tool_button('Export', icons.ICON_FA_FILE_EXPORT):
					path = pfd.save_file('Save Style Config', filters=file_filters).result()
					try:
						ser_ext.dump_obj(style_ser, path)
					except: pass
				imgui.same_line()
				if self.tool_button('Import', icons.ICON_FA_FILE_IMPORT):
					paths = pfd.open_file('Open Style Config', filters=file_filters).result()
					try:
						style_ser = ser_ext.load_obj(paths[0])
					except: pass
				
				ser_ext.apply_style_serialized(style_ser)

ThirtyThree('ImGui App', 1 if '--nodpi' in sys.argv else None).run()
