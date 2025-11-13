"""
PROFESSIONAL Metadata View Component - VISUALLY ENHANCED
Clean, modern, and user-friendly metadata display with improved aesthetics.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import pyperclip
import subprocess
import platform
from pathlib import Path

from ...domain.models import Track
from ...utils.logging import get_logger
from ...utils.helpers import format_duration, format_file_size
from ..themes.theme_manager import ThemeManager

logger = get_logger(__name__)


def _reveal_in_folder(path: Path) -> None:
    """Cross-platform helper to open OS file manager with file selected."""
    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(["explorer", "/select,", str(path)], check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", "-R", str(path)], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(path.parent)], check=True)
    except Exception as e:
        logger.warning("Could not open file manager: %s", e)


class ClickableLabel(ttk.Label):
    """An enhanced clickable label with better visual feedback."""
    
    def __init__(self, parent, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self._bind_events()
        
    def _bind_events(self):
        """Bind click events with better visual feedback."""
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
    def _on_click(self, event):
        """Handle click event with visual feedback."""
        if self.command:
            self.command()
            
    def _on_enter(self, event):
        """Handle mouse enter - change cursor."""
        self.configure(cursor="hand2")
        
    def _on_leave(self, event):
        """Handle mouse leave - reset cursor."""
        self.configure(cursor="")


class MetadataView(ttk.Frame):
    """VISUALLY ENHANCED VERSION: Beautiful, modern metadata display."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_track: Optional[Track] = None
        self.value_labels: Dict[str, ClickableLabel] = {}
        self.text_widgets: Dict[str, scrolledtext.ScrolledText] = {}
        
        # Track update calls for debugging
        self.update_count = 0
        
        self._build_ui()
        logger.info("🎨 MetadataView initialized - VISUAL MODE")

    def _build_ui(self) -> None:
        """Constructs the modern tabbed interface."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=8, pady=8)

        self._build_overview_tab()
        self._build_content_tab()
        self._build_technical_tab()
        self._build_raw_tab()

    def _build_overview_tab(self) -> None:
        """Builds the 'Overview' tab with clean card layout."""
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="📋 Overview")

        # Debug info section (minimized but available)
        debug_frame = ttk.LabelFrame(frame, text="🔧 Debug", padding=8)
        debug_frame.pack(fill='x', pady=(0, 8))
        
        self.debug_label = ttk.Label(debug_frame, text="No track selected", 
                                   wraplength=500, font=('TkDefaultFont', 8))
        self.debug_label.pack(fill='x')

        # Core information card - prominent display
        core_frame = ttk.LabelFrame(frame, text="🎵 Core Information", padding=12)
        core_frame.pack(fill='x', pady=5)
        
        core_fields = [
            ('title', 'Title', '📝'), 
            ('artist', 'Artist', '👤'),
            ('album', 'Album', '💿'),
            ('duration', 'Duration', '⏱️'),
            ('file_path', 'File Path', '📁')
        ]
        
        for field, label_text, icon in core_fields:
            row_frame = ttk.Frame(core_frame)
            row_frame.pack(fill='x', pady=3)
            
            # Icon + label
            label_frame = ttk.Frame(row_frame)
            label_frame.pack(side='left', padx=(0, 8))
            ttk.Label(label_frame, text=icon, font=('TkDefaultFont', 9)).pack(side='left')
            ttk.Label(label_frame, text=label_text, width=12, anchor='w', 
                     font=('TkDefaultFont', 9, 'bold')).pack(side='left', padx=(2, 0))
            
            # Value with enhanced clickable area
            value_label = ClickableLabel(
                row_frame, 
                text="-", 
                anchor='w',
                command=lambda f=field: self._copy_field_value(f)
            )
            value_label.pack(side='left', fill='x', expand=True)
            
            self.value_labels[field] = value_label

    def _build_content_tab(self) -> None:
        """Builds the 'Content' tab with better text presentation."""
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text="📝 Content")
        
        # Prompt section with copy icon in title
        self.prompt_frame = ttk.LabelFrame(frame, text="💡 Prompt  📋", padding=8)
        self.prompt_frame.pack(fill='both', expand=True, pady=(0, 8))
        
        # Make the prompt frame title clickable
        def copy_prompt_from_title(event):
            self._copy_text_content('prompt', 'Prompt')
        
        # Apply clickable behavior to the label frame
        self.prompt_frame.bind('<Button-1>', copy_prompt_from_title)
        self.prompt_frame.configure(cursor="hand2")
        
        self.prompt_text = self._create_enhanced_scrolled_text(self.prompt_frame, height=6)
        self.prompt_text.pack(fill='both', expand=True, pady=(4, 0))
        self.text_widgets['prompt'] = self.prompt_text

        # Lyrics section with copy icon in title
        self.lyrics_frame = ttk.LabelFrame(frame, text="🎤 Lyrics  📋", padding=8)
        self.lyrics_frame.pack(fill='both', expand=True, pady=(0, 8))
        
        def copy_lyrics_from_title(event):
            self._copy_text_content('lyrics', 'Lyrics')
        
        self.lyrics_frame.bind('<Button-1>', copy_lyrics_from_title)
        self.lyrics_frame.configure(cursor="hand2")
        
        self.lyrics_text = self._create_enhanced_scrolled_text(self.lyrics_frame, height=6)
        self.lyrics_text.pack(fill='both', expand=True, pady=(4, 0))
        self.text_widgets['lyrics'] = self.lyrics_text

        # Tags section with copy icon in title
        self.tags_frame = ttk.LabelFrame(frame, text="🏷️ Tags  📋", padding=8)
        self.tags_frame.pack(fill='both', expand=True, pady=0)
        
        def copy_tags_from_title(event):
            self._copy_text_content('tags', 'Tags')
        
        self.tags_frame.bind('<Button-1>', copy_tags_from_title)
        self.tags_frame.configure(cursor="hand2")
        
        self.tags_text = self._create_enhanced_scrolled_text(self.tags_frame, height=4)
        self.tags_text.pack(fill='both', expand=True, pady=(4, 0))
        self.text_widgets['tags'] = self.tags_text

    def _build_technical_tab(self) -> None:
        """Builds the 'Technical' tab with organized sections."""
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text="⚙️ Technical")
        
        # Two-column layout for technical data
        columns = ttk.Frame(frame)
        columns.pack(fill='both', expand=True)
        
        # Left column - File information
        left_column = ttk.Frame(columns)
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        file_frame = ttk.LabelFrame(left_column, text="📁 File Info", padding=8)
        file_frame.pack(fill='both', expand=True, pady=5)
        
        file_fields = [
            ('file_size', 'File Size', '📊'),
            ('file_size_mb', 'Size (MB)', '💾'),
            ('created_date', 'Created', '📅'),
            ('song_id', 'Song ID', '🆔'),
            ('generation_id', 'Gen ID', '🔧'),
            ('user_id', 'User ID', '👤'),
            ('status', 'Status', '🟢')
        ]
        
        for field, label_text, icon in file_fields:
            self._create_technical_row(file_frame, field, label_text, icon)

        # Right column - Statistics & URLs
        right_column = ttk.Frame(columns)
        right_column.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        stats_frame = ttk.LabelFrame(right_column, text="📊 Stats", padding=8)
        stats_frame.pack(fill='both', expand=True, pady=5)
        
        stats_fields = [
            ('plays', 'Plays', '▶️'),
            ('likes', 'Likes', '❤️'),
            ('is_favorite', 'Favorite', '⭐'),
            ('is_finished', 'Finished', '✅'),
            ('is_publishable', 'Publishable', '📤')
        ]
        
        for field, label_text, icon in stats_fields:
            self._create_technical_row(stats_frame, field, label_text, icon)

        # URLs section
        urls_frame = ttk.LabelFrame(frame, text="🌐 URLs", padding=8)
        urls_frame.pack(fill='x', pady=5)
        
        url_fields = [
            ('source_url', 'Source', '🔗'),
            ('audio_url', 'Audio', '🎵'),
            ('video_url', 'Video', '🎥'),
            ('album_art_url', 'Artwork', '🖼️')
        ]
        
        for field, label_text, icon in url_fields:
            self._create_technical_row(urls_frame, field, label_text, icon)

    def _create_technical_row(self, parent, field: str, label_text: str, icon: str):
        """Helper to create consistent technical info rows."""
        row_frame = ttk.Frame(parent, padding=1)
        row_frame.pack(fill='x', pady=2)
        
        # Icon + label
        label_frame = ttk.Frame(row_frame)
        label_frame.pack(side='left', padx=(0, 8))
        ttk.Label(label_frame, text=icon, font=('TkDefaultFont', 9)).pack(side='left')
        ttk.Label(label_frame, text=label_text, width=12, anchor='w', 
                 font=('TkDefaultFont', 9)).pack(side='left', padx=(2, 0))
        
        value_label = ClickableLabel(
            row_frame, 
            text="-", 
            anchor='w',
            command=lambda f=field: self._copy_field_value(f)
        )
        value_label.pack(side='left', fill='x', expand=True)
        
        self.value_labels[field] = value_label

    def _build_raw_tab(self) -> None:
        """Builds the 'Raw Data' tab with modern presentation."""
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text="📊 Raw Data")
        
        # Header with enhanced buttons
        header = ttk.Frame(frame)
        header.pack(fill='x', pady=(0, 8))
        
        ttk.Label(header, text="Complete Track Data (JSON)", 
                 font=('TkDefaultFont', 10, 'bold')).pack(side='left')
        
        button_frame = ttk.Frame(header)
        button_frame.pack(side='right')
        
        ttk.Button(button_frame, text="📋", 
                  command=self._copy_raw_json, width=3).pack(side='left', padx=(2, 0))
        ttk.Button(button_frame, text="🔄", 
                  command=self._format_raw_json, width=3).pack(side='left', padx=(2, 0))

        # Enhanced text area with better styling
        self.raw_text = self._create_enhanced_scrolled_text(frame, font_size=9, height=10)
        self.raw_text.pack(fill='both', expand=True)
        self.text_widgets['raw'] = self.raw_text

    def _create_enhanced_scrolled_text(self, parent: ttk.Frame, font_size: int = 10, height: int = 8) -> scrolledtext.ScrolledText:
        """Helper to create a modern ScrolledText widget."""
        st = scrolledtext.ScrolledText(
            parent, 
            height=height, 
            wrap=tk.WORD, 
            relief='flat', 
            padx=8, 
            pady=8,
            font=('Consolas', font_size),
            background='#fafafa',
            foreground='#2c3e50',
            insertbackground='#3498db',
            selectbackground='#3498db',
            borderwidth=1,
            highlightthickness=1,
            highlightcolor='#bdc3c7',
            highlightbackground='#bdc3c7'
        )
        st.config(state='disabled')
        return st

    def update(self, track: Optional[Track]) -> None:
        """Enhanced update with better visual feedback."""
        self.update_count += 1
        logger.info(f"🔄 MetadataView.update() CALLED #{self.update_count}")
        
        if track is None:
            logger.warning("🚫 update() received None track")
            self._clear_all_fields()
            return
            
        logger.info(f"✅ update() received track: {track.title if hasattr(track, 'title') else 'NO TITLE'}")
        
        self.current_track = track
        
        try:
            self._update_debug_info(track)
            self._update_field_labels(track)
            self._update_text_areas(track)
            self._update_raw_data(track)
            logger.info("✅ MetadataView.update() completed successfully")
        except Exception as e:
            logger.error(f"❌ Error in update(): {e}", exc_info=True)

    def _update_debug_info(self, track: Track) -> None:
        """Update debug information with cleaner presentation."""
        debug_text = [
            f"Track: {getattr(track, 'title', 'NO TITLE')}",
            f"Artist: {getattr(track, 'artist', 'NO ARTIST')}",
            f"Update #{self.update_count}",
            f"ID: {id(track)}"
        ]
        
        self.debug_label.config(text=" • ".join(debug_text))

    def _update_field_labels(self, track: Track) -> None:
        """Update all field labels with better formatting."""
        for field, label in self.value_labels.items():
            try:
                value = None
                
                if hasattr(track, field):
                    value = getattr(track, field)
                    
                # Format the value for display
                display_value = self._format_value(field, value)
                label.config(text=display_value)
                
            except Exception as e:
                logger.error(f"❌ Error updating field '{field}': {e}")
                label.config(text=f"Error: {e}")

    def _update_text_areas(self, track: Track) -> None:
        """Update the large text areas."""
        try:
            # Update prompt
            prompt_content = getattr(track, 'prompt', None)
            self._set_enhanced_text(self.prompt_text, prompt_content)
            
            # Update lyrics
            lyrics_content = getattr(track, 'lyrics', None)
            self._set_enhanced_text(self.lyrics_text, lyrics_content)
            
            # Update tags
            tags_content = getattr(track, 'tags', None)
            if tags_content and isinstance(tags_content, list):
                tags_text = ", ".join(tags_content)
                self._set_enhanced_text(self.tags_text, tags_text)
            else:
                self._set_enhanced_text(self.tags_text, "-")
            
        except Exception as e:
            logger.error(f"❌ Error updating text areas: {e}")

    def _update_raw_data(self, track: Track) -> None:
        """Update raw data tab with pretty JSON."""
        try:
            if hasattr(track, 'to_dict'):
                track_dict = track.to_dict()
                formatted_json = json.dumps(track_dict, indent=2, default=str)
                self._set_enhanced_text(self.raw_text, formatted_json)
            elif hasattr(track, '__dict__'):
                formatted_json = json.dumps(track.__dict__, indent=2, default=str)
                self._set_enhanced_text(self.raw_text, formatted_json)
            else:
                self._set_enhanced_text(self.raw_text, "No serializable data available")
                
        except Exception as e:
            error_msg = f"Error serializing track data: {e}"
            self._set_enhanced_text(self.raw_text, error_msg)

    def _set_enhanced_text(self, widget: scrolledtext.ScrolledText, content: Optional[str]) -> None:
        """Safely update text widget."""
        try:
            widget.config(state='normal')
            widget.delete('1.0', tk.END)
            
            if content:
                widget.insert('1.0', content)
            else:
                widget.insert('1.0', '-')
                
            widget.config(state='disabled')
        except Exception as e:
            logger.error(f"❌ Error setting enhanced text content: {e}")

    def _format_value(self, field: str, value: Any) -> str:
        """Enhanced value formatting with better presentation."""
        if value is None:
            return "-"
            
        if isinstance(value, str) and not value.strip():
            return "-"
            
        # Special formatting for specific fields
        if field == 'duration':
            # Handle both timedelta and numeric duration
            if hasattr(value, 'total_seconds'):
                # It's a timedelta object
                seconds = value.total_seconds()
            elif isinstance(value, (int, float)):
                # It's numeric seconds
                seconds = value
            else:
                return str(value)
                
            # Format as MM:SS
            minutes = int(seconds // 60)
            seconds_remainder = int(seconds % 60)
            return f"⏱️ {minutes:02d}:{seconds_remainder:02d}"
            
        elif field == 'file_size' and isinstance(value, (int, float)):
            return f"📊 {format_file_size(value)}"
        elif field == 'file_size_mb' and isinstance(value, (int, float)):
            return f"💾 {value:.2f} MB"
        elif field == 'file_path' and isinstance(value, Path):
            return f"📁 {value.name}"
        elif isinstance(value, datetime):
            return f"📅 {value.strftime('%Y-%m-%d %H:%M')}"
        elif isinstance(value, bool):
            return "✅ Yes" if value else "❌ No"
        elif field == 'is_favorite':
            return "⭐ Yes" if value else "☆ No"
        elif field in ['is_finished', 'is_publishable']:
            return "✅ Yes" if value else "❌ No"
        elif isinstance(value, list):
            if field == 'tags':
                return f"🏷️ {len(value)} tags"
            return " • ".join(str(item) for item in value) if value else "-"
        elif field in ['source_url', 'audio_url', 'video_url', 'album_art_url']:
            # Truncate long URLs for display
            if value and len(value) > 40:
                return f"🔗 {value[:40]}..."
            return f"🔗 {value}" if value else "-"
        else:
            return str(value)

    def _clear_all_fields(self) -> None:
        """Clear all fields with better visual state."""
        for label in self.value_labels.values():
            label.config(text="-")
            
        for text_widget in self.text_widgets.values():
            self._set_enhanced_text(text_widget, "-")
            
        self.debug_label.config(text="No track selected")

    def _copy_field_value(self, field: str) -> None:
        """Copy field value with visual confirmation."""
        if self.current_track:
            try:
                value = getattr(self.current_track, field, None)
                if value:
                    pyperclip.copy(str(value))
                    logger.debug(f"📋 Copied field '{field}': {value}")
                    
                    # Visual feedback
                    label = self.value_labels[field]
                    original_text = label.cget('text')
                    label.config(text="✅ Copied!")
                    label.after(1000, lambda: label.config(text=original_text))
                    
            except Exception as e:
                logger.error(f"❌ Error copying field '{field}': {e}")

    def _copy_prompt(self) -> None:
        """Copy prompt text."""
        self._copy_text_content('prompt', 'Prompt')

    def _copy_lyrics(self) -> None:
        """Copy lyrics text."""
        self._copy_text_content('lyrics', 'Lyrics')

    def _copy_tags(self) -> None:
        """Copy tags text."""
        self._copy_text_content('tags', 'Tags')

    def _copy_text_content(self, content_type: str, display_name: str) -> None:
        """Generic method to copy text content with feedback."""
        try:
            text_widget = self.text_widgets[content_type]
            content = text_widget.get('1.0', tk.END).strip()
            if content and content != '-':
                pyperclip.copy(content)
                logger.debug(f"📋 Copied {display_name} to clipboard")
        except Exception as e:
            logger.error(f"❌ Error copying {display_name}: {e}")

    def _copy_raw_json(self) -> None:
        """Copy raw JSON data with visual feedback."""
        try:
            text = self.raw_text.get('1.0', tk.END).strip()
            if text and text != "-":
                pyperclip.copy(text)
                logger.debug("📋 Copied raw JSON to clipboard")
        except Exception as e:
            logger.error(f"❌ Error copying raw JSON: {e}")

    def _format_raw_json(self) -> None:
        """Re-format the raw JSON for better readability."""
        try:
            content = self.raw_text.get('1.0', tk.END).strip()
            if content and content != "-":
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                self._set_enhanced_text(self.raw_text, formatted)
        except Exception as e:
            logger.error(f"❌ Error formatting JSON: {e}")

    def shutdown(self) -> None:
        """Cleanup."""
        logger.info(f"🛑 MetadataView shutdown after {self.update_count} updates")