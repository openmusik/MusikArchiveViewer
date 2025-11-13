# udio_media_manager/ui/audio_controller.py - FULLY UPGRADED & CORRECTED

"""
Professional Audio Controller
---------------------------

Manages all audio playback logic, playlist handling, and state, acting as the
brain for the application's audio features. It communicates with the low-level
AudioPlayer service and broadcasts events to the UI layer without being directly
coupled to it.
"""

import threading
import weakref
import random
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict  # <-- CRITICAL FIX: IMPORT ADDED HERE

# Use TYPE_CHECKING to import types for static analysis, breaking circular imports.
if TYPE_CHECKING:
    from .main_window import MainWindow
    from ..domain.models import Track
    from ..services import AudioPlayer

from ..services import PlaybackState
from ..utils.logging import get_logger

logger = get_logger(__name__)

class PlaybackMode(Enum):
    """Defines how the playlist should be traversed."""
    SINGLE, REPEAT_ONE, REPEAT_ALL, SHUFFLE = auto(), auto(), auto(), auto()

@dataclass
class PlaybackSession:
    """Represents the current playback session state."""
    current_track: Optional["Track"] = None
    playlist: List["Track"] = field(default_factory=list)
    shuffled_playlist: List["Track"] = field(default_factory=list)
    current_index: int = -1
    volume: int = 80
    playback_mode: PlaybackMode = PlaybackMode.SINGLE


class AudioController:
    """Manages audio playback, playlists, and communicates state changes via callbacks."""
    
    def __init__(self, audio_player: "AudioPlayer", main_window: "MainWindow"):
        self.audio_player = audio_player
        self.main_window_ref = weakref.ref(main_window)
        self.session = PlaybackSession()
        
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self._progress_timer: Optional[threading.Thread] = None
        self._stop_timer_event = threading.Event()
        
        self.setup_audio_player_callbacks()
        logger.info("Enhanced AudioController initialized")

    @property
    def main_window(self) -> Optional["MainWindow"]:
        """Safely resolves the weak reference to the main window."""
        return self.main_window_ref()

    def setup_audio_player_callbacks(self) -> None:
        """Sets up callbacks to receive events from the low-level AudioPlayer."""
        if not self.audio_player: return
        self.audio_player.register_callback('on_state_change', self._on_playback_state_changed)
        self.audio_player.register_callback('on_complete', self._on_playback_complete)
        self.audio_player.register_callback('on_error', self._handle_playback_error)
        self.audio_player.register_callback('on_progress', self._update_progress_display)

    def register_callback(self, event_type: str, callback: Callable):
        """Allows other components to listen for audio events."""
        self._callbacks[event_type].append(callback)

    def _trigger_callbacks(self, event_type: str, *args, **kwargs):
        """Triggers all registered callbacks for an event on the main UI thread."""
        if (main_win := self.main_window) and main_win.root:
            for callback in self._callbacks.get(event_type, []):
                main_win.root.after(0, lambda c=callback, a=args, kw=kwargs: c(*a, **kw))

    def play_track(self, track: "Track", playlist: Optional[List["Track"]] = None) -> bool:
        """Plays a specific track, optionally setting a new playlist."""
        audio_path = track.audio_path
        if not audio_path or not audio_path.exists():
            self._handle_missing_audio_file(track)
            return False
        
        self.stop()
        self.session.current_track = track
        if playlist is not None:
            self.set_playlist(playlist, start_track=track)
        
        self._update_status(f"Loading: {track.title}", "info")
        
        if self.audio_player.play(audio_path):
            self._trigger_callbacks('playback_started', track)
            self._trigger_callbacks('track_changed', track)
            logger.info(f"Started playback: {track.title}")
            return True
        else:
            self._handle_playback_error(f"AudioPlayer failed to play {track.title}")
            return False

    def toggle_play_pause(self) -> None:
        """Toggles between play and pause states."""
        if not self.audio_player: return
        if self.audio_player.is_playing(): self.audio_player.pause()
        elif self.audio_player.is_paused(): self.audio_player.resume()
        elif self.session.current_track: self.play_track(self.session.current_track, self.session.playlist)

    def stop(self) -> None:
        """Stops audio playback completely."""
        self._stop_progress_timer()
        if self.audio_player: self.audio_player.stop()
        self._trigger_callbacks('playback_stopped')

    def play_next(self) -> None:
        """Plays the next track in the playlist based on the current mode."""
        if not self.session.playlist: return
        next_index = self._get_next_track_index()
        if next_index is not None:
            playlist_to_use = self.session.shuffled_playlist if self.session.playback_mode == PlaybackMode.SHUFFLE else self.session.playlist
            if 0 <= next_index < len(playlist_to_use):
                self.play_track(playlist_to_use[next_index], playlist_to_use)
                return
        self.stop() # Stop if no next track is found

    def play_previous(self) -> None:
        """Plays the previous track, or restarts the current one."""
        if not self.session.playlist or self.session.current_index < 0: return
        if self.audio_player.get_position() > 3:
            self.seek_to_position(0)
        else:
            playlist_to_use = self.session.shuffled_playlist if self.session.playback_mode == PlaybackMode.SHUFFLE else self.session.playlist
            prev_index = max(0, self.session.current_index - 1)
            if 0 <= prev_index < len(playlist_to_use):
                self.play_track(playlist_to_use[prev_index], playlist_to_use)

    def seek_to_position(self, position_seconds: float) -> None:
        """Seeks to a specific position in the current track."""
        if self.audio_player and (self.audio_player.is_playing() or self.audio_player.is_paused()):
            self.audio_player.seek(position_seconds)
            self._update_progress_display(position_seconds, self.audio_player.get_duration())

    def seek_by_percentage(self, percentage: float) -> None:
        """Seeks to a position based on a percentage (0-100) of the track's duration."""
        if self.audio_player and (self.audio_player.is_playing() or self.audio_player.is_paused()):
            duration = self.audio_player.get_duration()
            if duration > 0: self.seek_to_position((percentage / 100.0) * duration)

    def set_volume(self, volume: int) -> None:
        """Sets the playback volume (0-100)."""
        self.session.volume = max(0, min(100, volume))
        if self.audio_player: self.audio_player.set_volume(self.session.volume)
        self._trigger_callbacks('volume_changed', self.session.volume)

    def set_playback_mode(self, mode: PlaybackMode) -> None:
        """Sets playback mode and rebuilds shuffled playlist if needed."""
        if self.session.playback_mode == mode: return
        self.session.playback_mode = mode
        if mode == PlaybackMode.SHUFFLE: self._shuffle_playlist()
        self._trigger_callbacks('playback_mode_changed', mode)
        logger.info(f"Playback mode set to {mode.name}")

    def set_playlist(self, playlist: List["Track"], start_track: Optional["Track"] = None):
        """Sets a new playlist, optionally starting from a specific track."""
        self.session.playlist = list(playlist)
        if self.session.playback_mode == PlaybackMode.SHUFFLE:
            self._shuffle_playlist(new_start_track=start_track)
        else:
            self.session.shuffled_playlist = []
        try:
            playlist_to_use = self.session.shuffled_playlist or self.session.playlist
            self.session.current_index = playlist_to_use.index(start_track) if start_track in playlist_to_use else 0
        except ValueError: self.session.current_index = 0

    def _shuffle_playlist(self, new_start_track: Optional["Track"] = None):
        """Creates and sets a new shuffled playlist, optionally keeping a specific track at the start."""
        start_track = new_start_track or self.session.current_track
        shuffled = list(self.session.playlist)
        random.shuffle(shuffled)
        if start_track and start_track in shuffled:
            shuffled.insert(0, shuffled.pop(shuffled.index(start_track)))
        self.session.shuffled_playlist = shuffled
        self.session.current_index = 0

    def _on_playback_state_changed(self, state: "PlaybackState"):
        is_playing = state == PlaybackState.PLAYING
        self._trigger_callbacks('playback_state_changed', is_playing)
        if is_playing: self._start_progress_timer()
        else: self._stop_progress_timer()

    def _on_playback_complete(self):
        if self.session.current_track: logger.info(f"Track '{self.session.current_track.title}' finished.")
        if self.session.playback_mode == PlaybackMode.REPEAT_ONE and self.session.current_track:
            self.play_track(self.session.current_track, self.session.playlist)
        else:
            self.play_next()

    def _start_progress_timer(self):
        self._stop_progress_timer()
        self._stop_timer_event.clear()
        # The AudioPlayer's on_progress callback is now the primary mechanism.
        # This timer is no longer strictly necessary but can be kept as a fallback.

    def _stop_progress_timer(self):
        self._stop_timer_event.set()
        if self._progress_timer and self._progress_timer.is_alive():
            self._progress_timer.join(timeout=0.5)
        self._progress_timer = None

    def _update_progress_display(self, position: float, duration: float):
        self._trigger_callbacks('progress_update', position, duration)

    def _get_next_track_index(self) -> Optional[int]:
        playlist_to_use = self.session.shuffled_playlist or self.session.playlist
        if not playlist_to_use or self.session.current_index < 0: return None
        next_index = self.session.current_index + 1
        if next_index >= len(playlist_to_use):
            return 0 if self.session.playback_mode == PlaybackMode.REPEAT_ALL else None
        return next_index

    def _update_status(self, message: str, level: str = "info"):
        if main_win := self.main_window:
            main_win.show_notification(message, level)

    def _handle_missing_audio_file(self, track: "Track"):
        error_msg = f"Audio file not found for: {track.title}"
        logger.error(error_msg)
        self._update_status(error_msg, "error")
        self.stop()

    def _handle_playback_error(self, error_message: str):
        logger.error(f"Playback error: {error_message}")
        self._update_status("Playback error", "error")
        self.stop()

    def shutdown(self) -> None:
        """Shuts down the audio controller and cleans up resources."""
        logger.info("Shutting down AudioController...")
        self._stop_progress_timer()
        if self.audio_player: self.audio_player.stop()
        logger.info("AudioController shutdown complete.")