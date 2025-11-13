"""
PROFESSIONAL GRADE Theme Management System for Udio Media Manager
Complete with dynamic theming, a declarative styling engine, and advanced features.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable, Set, Tuple, List
from dataclasses import dataclass, fields
import re
import time

from ...core.singleton import SingletonBase
from ...core.constants import FONTS
from ...domain.enums import ThemeMode
from ...utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ColorScheme:
    """Complete color scheme definition with semantic naming."""
    primary_bg: str
    secondary_bg: str
    tertiary_bg: str
    card_bg: str
    primary_text: str
    secondary_text: str
    tertiary_text: str
    inverted_text: str
    primary_accent: str
    secondary_accent: str
    success: str
    warning: str
    error: str
    info: str
    hover: str
    active: str
    selected: str
    disabled: str
    border: str
    divider: str
    focus_ring: str
    header_bg: str
    sidebar_bg: str
    status_bg: str
    input_bg: str
    scrollbar_track: str
    scrollbar_thumb: str
    scrollbar_thumb_hover: str

@dataclass
class ThemeConfig:
    """Complete theme configuration, including fonts."""
    name: str
    colors: ColorScheme
    fonts: Dict[str, Tuple[str, int, str]]
    spacing: Dict[str, int]

class AdvancedThemeManager(SingletonBase):
    """
    PROFESSIONAL GRADE Theme Manager with a declarative, CSS-like styling engine.
    Features: Dynamic theming, live style reconfiguration, listener notifications, and advanced color utilities.
    """
    
    def __init__(self):
        super().__init__()
        self._root: Optional[tk.Tk] = None
        self._style: Optional[ttk.Style] = None
        self._user_theme_choice: ThemeMode = ThemeMode.SYSTEM
        self._resolved_theme: ThemeMode = ThemeMode.DARK # Default fallback
        self._theme_listeners: Set[Callable[[ThemeMode], None]] = set()
        self._color_cache: Dict[str, str] = {}
        self._is_initialized = False
        self._color_schemes = self._create_color_schemes()
        self._theme_configs = self._create_theme_configs()
        self._style_definitions = self._get_style_definitions()
        logger.info("🚀 Professional ThemeManager initialized")

    def initialize(self, root: tk.Tk) -> None:
        """Initializes the theme manager, configures ttk.Style, and applies the default theme."""
        if self._is_initialized: return
        start_time = time.monotonic()
        self._root = root
        self._style = ttk.Style(root)
        try:
            self._setup_base_theme()
            self.set_theme(self._user_theme_choice) # This will detect system theme and apply styles
            self._is_initialized = True
            init_time = time.monotonic() - start_time
            logger.info(f"🎨 Professional ThemeManager initialized and styles applied in {init_time:.3f}s")
        except Exception as e:
            logger.critical(f"Failed to initialize ThemeManager: {e}", exc_info=True)
            if self._style: self._style.theme_use('default')

    def _create_color_schemes(self) -> Dict[ThemeMode, ColorScheme]:
        """Defines the color palettes for both light and dark modes."""
        return {
            ThemeMode.DARK: ColorScheme(
                primary_bg='#1E1E1E', secondary_bg='#2D2D2D', tertiary_bg='#3C3C3C', card_bg='#252526',
                primary_text='#D4D4D4', secondary_text='#A0A0A0', tertiary_text='#6B6B6B', inverted_text='#FFFFFF',
                primary_accent='#007ACC', secondary_accent='#6A329F', success='#388E3C', warning='#F57C00', error='#D32F2F', info='#0288D1',
                hover='#3A3A3A', active='#3C3C3C', selected='#094771', disabled='#3C3C3C',
                border='#3C3C3C', divider='#3C3C3C', focus_ring='#007ACC',
                header_bg='#2D2D2D', sidebar_bg='#252526', status_bg='#007ACC', input_bg='#3C3C3C',
                scrollbar_track='#2D2D2D', scrollbar_thumb='#555555', scrollbar_thumb_hover='#686868'
            ),
            ThemeMode.LIGHT: ColorScheme(
                primary_bg='#FFFFFF', secondary_bg='#F0F0F0', tertiary_bg='#E1E1E1', card_bg='#FFFFFF',
                primary_text='#1E1E1E', secondary_text='#5B5B5B', tertiary_text='#8C8C8C', inverted_text='#FFFFFF',
                primary_accent='#007ACC', secondary_accent='#6A329F', success='#4CAF50', warning='#FB8C00', error='#F44336', info='#2196F3',
                hover='#E1E1E1', active='#CFCFCF', selected='#CDE8FF', disabled='#CFCFCF',
                border='#CFCFCF', divider='#E1E1E1', focus_ring='#007ACC',
                header_bg='#F0F0F0', sidebar_bg='#F8F8F8', status_bg='#007ACC', input_bg='#FFFFFF',
                scrollbar_track='#F0F0F0', scrollbar_thumb='#C1C1C1', scrollbar_thumb_hover='#A8A8A8'
            )
        }

    def _create_theme_configs(self) -> Dict[ThemeMode, ThemeConfig]:
        """Defines the full theme configuration, including fonts and spacing."""
        configs = {}
        for mode in [ThemeMode.LIGHT, ThemeMode.DARK]:
            configs[mode] = ThemeConfig(
                name=f"UdioManager {'Dark' if mode == ThemeMode.DARK else 'Light'}",
                colors=self._color_schemes[mode],
                fonts={
                    'main': FONTS.get('main', ("Segoe UI", 10, "normal")),
                    'bold': FONTS.get('bold', ("Segoe UI", 10, "bold")),
                    'header': FONTS.get('header', ("Segoe UI", 16, "bold")),
                    'subheader': FONTS.get('subheader', ("Segoe UI", 12, "bold")),
                    'button': FONTS.get('button', ("Segoe UI", 10, "bold")),
                    'small': FONTS.get('small', ("Segoe UI", 9, "normal")),
                },
                spacing={'xs': 2, 'sm': 4, 'md': 8, 'lg': 12, 'xl': 16}
            )
        return configs

    def _get_style_definitions(self) -> Dict[str, Dict[str, Any]]:
        """A declarative, CSS-like dictionary defining all widget styles. This is the core of the fix."""
        return {
            # --- BASE ELEMENT STYLES ---
            'Tk.Root': {'background': 'primary_bg'},
            'TFrame': {'configure': {'background': 'primary_bg'}},
            'TLabel': {'configure': {'background': 'primary_bg', 'foreground': 'primary_text', 'font': 'main'}},
            'TButton': {'configure': {'padding': ('lg', 'md'), 'font': 'button', 'borderwidth': 1}, 'layout': [('Button.padding', {'sticky': 'nswe', 'children': [('Button.label', {'sticky': 'nswe'})]})]},
            'TEntry': {'configure': {'fieldbackground': 'input_bg', 'foreground': 'primary_text', 'borderwidth': 1, 'padding': 'md', 'insertcolor': 'primary_text'}, 'map': {'bordercolor': [('focus', 'focus_ring'), ('!focus', 'border')], 'lightcolor': [('focus', 'focus_ring')]}},
            'Vertical.TScrollbar': {'configure': {'background': 'scrollbar_thumb', 'troughcolor': 'scrollbar_track', 'arrowcolor': 'secondary_text', 'bordercolor': 'border'}, 'map': {'background': [('active', 'scrollbar_thumb_hover'), ('pressed', 'primary_accent')]}},
            'Horizontal.TProgressbar': {'configure': {'background': 'primary_accent', 'troughcolor': 'tertiary_bg'}},
            'TNotebook': {'configure': {'background': 'primary_bg', 'tabmargins': [2, 5, 2, 0]}},
            'TNotebook.Tab': {'configure': {'padding': [10, 5], 'font': 'main'}, 'map': {'background': [('selected', 'secondary_bg'), ('!selected', 'primary_bg')], 'foreground': [('selected', 'primary_text'), ('!selected', 'secondary_text')]}},

            # --- CUSTOM COMPONENT STYLES ---
            'Card.TFrame': {'configure': {'background': 'card_bg'}},
            'Header.TLabel': {'configure': {'font': 'subheader', 'foreground': 'primary_text', 'background': 'card_bg'}},
            'Small.TLabel': {'configure': {'font': 'small', 'foreground': 'secondary_text', 'background': 'card_bg'}},
            'Muted.TLabel': {'configure': {'font': 'small', 'foreground': 'tertiary_text', 'background': 'card_bg'}},
            'Thumbnail.TLabel': {'configure': {'background': 'tertiary_bg'}},
            'Primary.TButton': {'inherit': 'TButton', 'configure': {'background': 'primary_accent', 'foreground': 'inverted_text', 'borderwidth': 0}, 'map': {'background': [('active', 'primary_accent@-0.2'), ('hover', 'primary_accent@-0.1')]}},

            # --- CUSTOM STATES FOR TRACK LIST ---
            'Hover.Card.TFrame': {'configure': {'background': 'hover'}},
            'Hover.Header.TLabel': {'configure': {'background': 'hover', 'foreground': 'primary_text'}},
            'Hover.Muted.TLabel': {'configure': {'background': 'hover', 'foreground': 'secondary_text'}},
            'Hover.Thumbnail.TLabel': {'configure': {'background': 'hover'}},

            'Selected.Card.TFrame': {'configure': {'background': 'selected'}},
            'Selected.Header.TLabel': {'configure': {'background': 'selected', 'foreground': 'inverted_text'}},
            'Selected.Muted.TLabel': {'configure': {'background': 'selected', 'foreground': 'inverted_text'}},
            'Selected.Thumbnail.TLabel': {'configure': {'background': 'selected'}},
        }

    # ... (the rest of the class remains the same) ...

    def _setup_base_theme(self) -> None:
        """Selects the best available base ttk theme for customization."""
        if not self._style: return
        for theme in ['clam', 'alt', 'default']:
            if theme in self._style.theme_names():
                self._style.theme_use(theme)
                logger.debug(f"Using base ttk theme: '{theme}'")
                return

    def apply_theme(self) -> None:
        """Applies the entire declarative style dictionary to the ttk.Style object."""
        if not self._style or not self._root: return
        self._color_cache.clear()
        root_style = self._resolve_style_values(self._style_definitions.get('Tk.Root', {}))
        self._root.configure(**root_style)
        for name, definition in self._style_definitions.items():
            if name.startswith('Tk.'): continue
            full_def = {**self._style_definitions.get(definition.get('inherit', ''), {}), **definition}
            if 'layout' in full_def: self._style.layout(name, full_def['layout'])
            if 'configure' in full_def: self._style.configure(name, **self._resolve_style_values(full_def['configure']))
            if 'map' in full_def:
                resolved_map = {key: [(state, self._resolve_value(value)) for state, value in states] for key, states in full_def['map'].items()}
                self._style.map(name, **resolved_map)

    def _resolve_style_values(self, style_dict: dict) -> dict:
        """Resolves theme variables (e.g., 'primary_bg') into actual values (e.g., '#1E1E1E')."""
        return {key: self._resolve_value(value) for key, value in style_dict.items()}

    def _resolve_value(self, value: Any) -> Any:
        """Resolves a single theme variable, handling colors, fonts, spacing, and brightness modifiers."""
        config = self.current_config
        if isinstance(value, str):
            match = re.match(r"(\w+)(@([+-]?\d*\.?\d+))?$", value)
            if match:
                var_name, _, factor_str = match.groups()
                if hasattr(config.colors, var_name):
                    color = getattr(config.colors, var_name)
                    return self._adjust_color_brightness(color, float(factor_str)) if factor_str else color
            if value in config.spacing: return config.spacing[value]
            if value in config.fonts: return config.fonts[value]
        if isinstance(value, (list, tuple)): return [self._resolve_value(v) for v in value]
        return value

    @property
    def current_theme(self) -> ThemeMode: return self._user_theme_choice
    @property
    def resolved_theme(self) -> ThemeMode: return self._resolved_theme
    @property
    def current_colors(self) -> ColorScheme: return self._theme_configs[self._resolved_theme].colors
    @property
    def current_config(self) -> ThemeConfig: return self._theme_configs[self._resolved_theme]
    @property
    def colors(self) -> Dict[str, str]:
        """Returns the current color scheme as a simple dictionary."""
        scheme = self.current_colors
        return {field.name: getattr(scheme, field.name) for field in fields(scheme)}

    def set_theme(self, theme: ThemeMode) -> None:
        """Sets the application theme, resolving SYSTEM to LIGHT or DARK."""
        if self._is_initialized and theme == self._user_theme_choice: return
        self._user_theme_choice = theme
        new_resolved_theme = self._get_system_theme() if theme == ThemeMode.SYSTEM else theme
        if self._is_initialized and new_resolved_theme == self._resolved_theme: return
        logger.info(f"🎨 Changing theme to: {new_resolved_theme.name} (request was {theme.name})")
        self._resolved_theme = new_resolved_theme
        self.apply_theme()
        self._notify_theme_changed()

    def toggle_theme(self) -> ThemeMode:
        """Toggles between LIGHT and DARK modes."""
        new_theme = ThemeMode.LIGHT if self._resolved_theme == ThemeMode.DARK else ThemeMode.DARK
        self.set_theme(new_theme)
        return new_theme

    def _get_system_theme(self) -> ThemeMode:
        """Detects if the system theme is light or dark."""
        if not self._root or not self._style: return ThemeMode.DARK
        try:
            bg_color = self._style.lookup('TFrame', 'background')
            r, g, b = self._root.winfo_rgb(bg_color)
            brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 65535
            resolved = ThemeMode.LIGHT if brightness > 0.5 else ThemeMode.DARK
            logger.debug(f"System theme detected as: {resolved.name} (Brightness: {brightness:.2f})")
            return resolved
        except Exception as e:
            logger.warning(f"Could not automatically detect system theme: {e}. Defaulting to DARK.")
            return ThemeMode.DARK

    def register_theme_listener(self, listener: Callable[[ThemeMode], None]) -> None:
        self._theme_listeners.add(listener)

    def unregister_theme_listener(self, listener: Callable[[ThemeMode], None]) -> None:
        self._theme_listeners.discard(listener)

    def _notify_theme_changed(self) -> None:
        """Informs all registered listeners that the theme has changed."""
        for listener in list(self._theme_listeners):
            try: listener(self._resolved_theme)
            except Exception as e: logger.error(f"Error in theme listener {listener}: {e}")

    def _adjust_color_brightness(self, color: str, factor: float) -> str:
        """Adjusts a hex color's brightness. Caches results for performance."""
        cache_key = f"{color}_{factor:.2f}"
        if cache_key in self._color_cache: return self._color_cache[cache_key]
        try:
            r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
            if factor > 0: r, g, b = int(r+(255-r)*factor), int(g+(255-g)*factor), int(b+(255-b)*factor)
            else: r, g, b = int(r*(1+factor)), int(g*(1+factor)), int(b*(1+factor))
            result = f'#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}'
            self._color_cache[cache_key] = result
            return result
        except Exception: return color

    def shutdown(self) -> None:
        self._theme_listeners.clear()
        self._color_cache.clear()
        logger.info("🎨 ThemeManager shutdown complete")

# Legacy compatibility alias
ThemeManager = AdvancedThemeManager