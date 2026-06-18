from . import *

ImVec2 = imgui.ImVec2
ImVec2Like = imgui.ImVec2Like
ImVec4 = imgui.ImVec4
ImVec4Like = imgui.ImVec4Like

imgui.INT_MAX = 0x7FFFFFFF
imgui.INT_MIN = -0x80000000

def alpha_mod(col: ImVec4Like, alpha: float):
	return ImVec4(*col) * ImVec4(1, 1, 1, alpha)
ImVec4.alpha_mod = alpha_mod

def _ImVec2_copy(self: ImVec2Like):
	return ImVec2(*self)
ImVec2.copy = _ImVec2_copy
ImVec2.__copy__ = _ImVec2_copy

def _ImVec2_max(self: ImVec2, other: ImVec2Like): return ImVec2(*map(max, self, other))
ImVec2.max = _ImVec2_max

def _ImVec2_min(self: ImVec2, other: ImVec2Like): return ImVec2(*map(min, self, other))
ImVec2.min = _ImVec2_min
