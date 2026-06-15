from typing import Callable
from gui import *
import imgui_utils
import sys

class ThirtyThree(GUI):
	def start(self):
		self.font_normal = self.add_font('assets/pp_fraktion_mono.otf', 16)
		self.add_font('assets/fa_solid.otf', 16, True)
		self.font_title = self.add_font('assets/kh_interference.ttf', 32)
		self.add_font('assets/fa_solid.otf', 32, True)
		
		self.panel_button = imgui_utils.SlicedFrameButton(
			imgui_utils.SlicedFrame(imgui_utils.make_texture('assets/panel_normal.png'), 60, 21, 240-140, 120-98, .5),
			imgui_utils.SlicedFrame(imgui_utils.make_texture('assets/panel_hover.png'), 60, 21, 240-140, 120-98, .5),
			imgui_utils.SlicedFrame(imgui_utils.make_texture('assets/panel_active.png'), 60, 21, 240-140, 120-98, .5),
			imgui_utils.SlicedFrame(imgui_utils.make_texture('assets/panel_disabled.png'), 60, 21, 240-140, 120-98, .5)
		)

		self.icon_filter = ''
		self.dummy_flag = lambda: print('fart')

	def gui(self):
		imgui_utils.main_docking_space()

		with imgui_ctx.begin('Icon Inspector'):
			imgui.set_next_item_width(-.01)
			_, self.icon_filter = imgui.input_text_with_hint('##filter', 'Filter', self.icon_filter)

			column_width = imgui.get_content_region_avail().x - 20
			imgui.columns(2, borders=False)
			imgui.set_column_width(-1, width=column_width)

			for name, utf in icons.__dict__.items():
				if not name.startswith('ICON'): continue
				if name in ['ICON_MIN_FA', 'ICON_MAX_FA', 'ICON_MAX_16_FA']: continue
				if not self.icon_filter.casefold() in name.casefold(): continue

				imgui.text(name)
				imgui.next_column()
				imgui.text(str(utf))
				imgui.next_column()

		with imgui_ctx.begin('ImGui Custom Demo'):
			self.panel_button('Panel Button')

			style = imgui.get_style()
			style_props = {key: getattr(style, key) for key in style.__dir__() if key[0] != '_' and not isinstance(getattr(style, key), Callable)}
			style_colors = {key: style.color_(val) for key, val in imgui.Col_.__dict__.items() if key[0] != '_' and 'count' not in key}
			
			_, style_props = imgui_utils.autogui('Style', style_props, True)
			_, style_colors = imgui_utils.autogui('Colors', style_colors, True)

			for key, val in style_props.items():
				setattr(style, key, val)
			for key, val in style_colors.items():
				style.set_color_(imgui.Col_.__dict__[key], val)

			_, self.dummy_flag = imgui_utils.autogui('rounding', self.dummy_flag)

ThirtyThree('ImGui App', 1 if '--nodpi' in sys.argv else None).run()
