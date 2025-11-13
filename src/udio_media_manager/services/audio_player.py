"""
PROFESSIONAL & RESILIENT Audio Playback Service for Udio Media Manager

This fully upgraded version includes:
- A robust, multi-listener callback system (register/unregister).
- Centralized, atomic state management to ensure consistent UI updates.
- Clearer separation of events (e.g., on_state_change vs. on_complete).
- Support for more audio formats and better error recovery.
- Enhanced VLC integration and Pygame fallback handling.
- Audio analysis capabilities and waveform data generation.
"""

import threading
import time
import wave
import struct
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Callable, List, Tuple, Dict, Any
from collections import defaultdict
import math

from ..core.singleton import SingletonBase
from ..utils.logging import get_logger

# Optional dependencies are imported defensively
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import vlc
    VLC_AVAILABLE = True
except (ImportError, OSError):
    VLC_AVAILABLE = False

try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

logger = get_logger(__name__)

class PlaybackState(Enum):
    """Enhanced playback states with more granular control."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    BUFFERING = auto()
    SEEKING = auto()
    DISABLED = auto()
    ERROR = auto()

    def is_playing(self) -> bool:
        """Helper to check if in a playing state."""
        return self == PlaybackState.PLAYING

class AudioFormat(Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    AAC = "aac"
    WMA = "wma"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, extension: str) -> 'AudioFormat':
        """Get audio format from file extension."""
        ext_map = {
            '.mp3': cls.MP3, '.wav': cls.WAV, '.flac': cls.FLAC, '.ogg': cls.OGG,
            '.m4a': cls.M4A, '.aac': cls.AAC, '.wma': cls.WMA,
        }
        return ext_map.get(extension.lower(), cls.UNKNOWN)

class AudioPlayer(SingletonBase):
    """
    PROFESSIONAL thread-safe, resilient audio player with advanced features.
    Orchestrates playback via VLC or Pygame backends and emits consistent events.
    """

    def __init__(self):
        super().__init__()
        self._state: PlaybackState = PlaybackState.STOPPED
        self._current_file: Optional[Path] = None
        self._volume: int = 80
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._vlc_instance: Optional[vlc.Instance] = None
        self._vlc_player: Optional[vlc.MediaPlayer] = None
        self._current_backend: Optional[str] = None
        self._duration: float = 0.0
        self._last_position: float = 0.0
        
        # UPGRADE: Switched to a multi-listener callback system.
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        self._audio_metadata: Dict[str, Any] = {}
        
        self._initialize_backends()
        logger.info("Professional AudioPlayer initialized")

    # UPGRADE: New state management method for consistency and event emission.
    def _set_state(self, new_state: PlaybackState):
        """Atomically sets the player state and triggers the on_state_change event."""
        with self._lock:
            if self._state == new_state:
                return
            self._state = new_state
            logger.debug(f"AudioPlayer state changed to {new_state.name}")
            self._trigger_callback('on_state_change', new_state)

    # UPGRADE: New flexible multi-listener callback registration.
    def register_callback(self, event_name: str, callback: Callable):
        """Allows multiple components to listen for a specific event."""
        with self._lock:
            if callback not in self.callbacks[event_name]:
                self.callbacks[event_name].append(callback)
                logger.debug(f"Registered callback for '{event_name}'")

    # UPGRADE: New callback unregistration for clean shutdown.
    def unregister_callback(self, event_name: str, callback: Callable):
        """Removes a specific callback from an event's listener list."""
        with self._lock:
            if event_name in self.callbacks and callback in self.callbacks[event_name]:
                self.callbacks[event_name].remove(callback)
                logger.debug(f"Unregistered callback for '{event_name}'")

    def _trigger_callback(self, name: str, *args, **kwargs) -> None:
        """Safely triggers all registered callbacks for an event."""
        with self._lock:
            # Iterate over a copy in case a callback modifies the list
            listeners = list(self.callbacks.get(name, []))
        
        for callback in listeners:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback for '{name}' failed: {e}", exc_info=True)

    def _initialize_backends(self):
        """Enhanced backend initialization with better error handling."""
        backends_tried = []
        if VLC_AVAILABLE:
            try:
                vlc_options = ["--no-xlib", "--quiet", "--audio-resampler=soxr"]
                self._vlc_instance = vlc.Instance(" ".join(vlc_options))
                self._vlc_player = self._vlc_instance.media_player_new()
                self._current_backend = "vlc"
                backends_tried.append("VLC")
                logger.info("VLC audio backend initialized.")
            except Exception as e:
                logger.error(f"VLC backend failed: {e}")
                backends_tried.append(f"VLC(failed)")
        if not self._current_backend and PYGAME_AVAILABLE:
            try:
                pygame.init()
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                self._current_backend = "pygame"
                backends_tried.append("Pygame")
                logger.info("Pygame audio backend initialized as fallback.")
            except Exception as e:
                logger.error(f"Pygame backend failed: {e}")
                backends_tried.append(f"Pygame(failed)")
        if not self._current_backend:
            self._set_state(PlaybackState.DISABLED)
            logger.critical(f"No audio backends available. Tried: {', '.join(backends_tried)}")
        else:
            logger.info(f"Audio backend selected: {self._current_backend}")
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available - audio metadata will be limited.")

    def play(self, file_path: Path) -> bool:
        """Enhanced audio playback with comprehensive validation."""
        with self._lock:
            if self._state == PlaybackState.DISABLED:
                self._trigger_callback('on_error', "Audio system not available")
                return False

            is_valid, validation_msg = self._validate_audio_file(file_path)
            if not is_valid:
                self._trigger_callback('on_error', f"Invalid file: {validation_msg}")
                self._set_state(PlaybackState.ERROR)
                return False

            self.stop()

            self._current_file = file_path
            self._stop_event.clear()
            self._duration = self._get_enhanced_duration(file_path)
            self._audio_metadata = self._analyze_audio_metadata(file_path)
            
            logger.info(f"Playing {file_path.name} (Duration: {self._duration:.2f}s)")

            success = False
            if self._current_backend == "vlc":
                success = self._play_with_vlc()
            elif self._current_backend == "pygame":
                success = self._play_with_pygame()

            if success:
                self._start_monitor_thread()
                
            return success

    def _play_with_vlc(self) -> bool:
        """Enhanced VLC playback with better event handling."""
        try:
            if not self._vlc_instance or not self._vlc_player:
                raise RuntimeError("VLC not properly initialized")
                
            media = self._vlc_instance.media_new(str(self._current_file))
            self._vlc_player.set_media(media)
            self._vlc_player.audio_set_volume(self._volume)
            
            event_manager = self._vlc_player.event_manager()
            event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._handle_vlc_finished)
            event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._handle_vlc_error)
            event_manager.event_attach(vlc.EventType.MediaPlayerBuffering, self._handle_vlc_buffering)
            
            if self._vlc_player.play() == -1:
                raise RuntimeError("VLC play command failed")
                
            self._set_state(PlaybackState.PLAYING)
            return True
        except Exception as e:
            logger.error(f"VLC playback failed: {e}", exc_info=True)
            self._set_state(PlaybackState.ERROR)
            self._trigger_callback('on_error', str(e))
            return False

    def _play_with_pygame(self) -> bool:
        """Enhanced Pygame playback with better error handling."""
        try:
            pygame.mixer.music.load(str(self._current_file))
            pygame.mixer.music.set_volume(self._volume / 100.0)
            pygame.mixer.music.play()
            self._set_state(PlaybackState.PLAYING)
            return True
        except Exception as e:
            logger.error(f"Pygame playback failed: {e}", exc_info=True)
            self._set_state(PlaybackState.ERROR)
            self._trigger_callback('on_error', f"Pygame error: {e}")
            return False

    def pause(self) -> bool:
        """Enhanced pause with state validation."""
        with self._lock:
            if not self.is_playing(): return False
            try:
                if self._current_backend == "vlc": self._vlc_player.pause()
                elif self._current_backend == "pygame": pygame.mixer.music.pause()
                self._set_state(PlaybackState.PAUSED)
                return True
            except Exception as e:
                logger.error(f"Pause failed: {e}")
                return False

    def resume(self) -> bool:
        """Enhanced resume with state validation."""
        with self._lock:
            if not self.is_paused(): return False
            try:
                if self._current_backend == "vlc": self._vlc_player.pause() # VLC uses pause to toggle
                elif self._current_backend == "pygame": pygame.mixer.music.unpause()
                self._set_state(PlaybackState.PLAYING)
                return True
            except Exception as e:
                logger.error(f"Resume failed: {e}")
                return False

    def stop(self) -> bool:
        """Enhanced stop with comprehensive cleanup."""
        with self._lock:
            if self._state in (PlaybackState.STOPPED, PlaybackState.DISABLED):
                return True
            self._stop_event.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=1.0)
            try:
                if self._current_backend == "vlc" and self._vlc_player and self._vlc_player.is_playing():
                    self._vlc_player.stop()
                elif self._current_backend == "pygame":
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
            except Exception as e:
                logger.error(f"Error during backend stop: {e}")
            self._last_position = 0.0
            self._set_state(PlaybackState.STOPPED)
            return True

    def seek(self, position: float) -> bool:
        """Seek to specific position in audio track."""
        with self._lock:
            if self._state not in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                return False
            if not (0 <= position <= self._duration):
                return False
            try:
                if self._current_backend == "vlc" and self._vlc_player:
                    self._vlc_player.set_time(int(position * 1000))  # VLC uses milliseconds
                    self._trigger_callback('on_seek', position)
                    return True
                elif self._current_backend == "pygame":
                    logger.warning("Seeking not supported with Pygame backend")
                    return False
            except Exception as e:
                logger.error(f"Seek failed: {e}")
                return False
        return False

    def set_volume(self, volume: int) -> None:
        """Set volume with validation."""
        with self._lock:
            if self._state == PlaybackState.DISABLED: return
            self._volume = max(0, min(100, volume))
            try:
                if self._current_backend == "vlc" and self._vlc_player:
                    self._vlc_player.audio_set_volume(self._volume)
                elif self._current_backend == "pygame":
                    pygame.mixer.music.set_volume(self._volume / 100.0)
            except Exception as e:
                logger.error(f"Volume set failed: {e}")

    def get_position(self) -> float:
        """Get current playback position with error handling."""
        with self._lock:
            if self._state in (PlaybackState.STOPPED, PlaybackState.DISABLED):
                return 0.0
            try:
                if self._current_backend == "vlc" and self._vlc_player:
                    return self._vlc_player.get_time() / 1000.0  # Convert to seconds
                elif self._current_backend == "pygame":
                    return pygame.mixer.music.get_pos() / 1000.0  # Convert to seconds
            except Exception as e:
                logger.debug(f"Position get failed: {e}")
            return self._last_position

    def get_volume(self) -> int: return self._volume
    def get_state(self) -> PlaybackState: return self._state
    def is_playing(self) -> bool: return self._state == PlaybackState.PLAYING
    def is_paused(self) -> bool: return self._state == PlaybackState.PAUSED
    def get_duration(self) -> float: return self._duration
    def get_current_file(self) -> Optional[Path]: return self._current_file
    def get_audio_metadata(self) -> Dict[str, Any]: return self._audio_metadata.copy()

    def _start_monitor_thread(self):
        """Start enhanced playback monitoring thread."""
        self._monitor_thread = threading.Thread(
            target=self._monitor_playback_progress,
            daemon=True,
            name="AudioMonitor"
        )
        self._monitor_thread.start()

    def _monitor_playback_progress(self):
        """Enhanced playback monitoring with better state management."""
        logger.debug("Playback monitor thread started")
        while not self._stop_event.is_set():
            with self._lock:
                if self._state == PlaybackState.PLAYING:
                    current_position = self.get_position()
                    self._last_position = current_position
                    self._trigger_callback('on_progress', current_position, self._duration)
                    if self._current_backend == "pygame" and not pygame.mixer.music.get_busy():
                        self._trigger_callback('on_complete')
                        self.stop() # This will change state and stop the loop
                        break
                elif self._state in [PlaybackState.STOPPED, PlaybackState.ERROR, PlaybackState.DISABLED]:
                    break
            time.sleep(0.25)  # Responsive polling
        logger.debug("Playback monitor thread finished")

    def _handle_vlc_finished(self, event):
        """Handle VLC playback finished event."""
        with self._lock:
            if self._state != PlaybackState.STOPPED:
                logger.debug("VLC playback naturally finished")
                self._trigger_callback('on_complete')
                self.stop()

    def _handle_vlc_error(self, event):
        """Handle VLC error event."""
        with self._lock:
            logger.error("VLC encountered a playback error")
            self._set_state(PlaybackState.ERROR)
            self._trigger_callback('on_error', "VLC playback error")

    def _handle_vlc_buffering(self, event):
        """Handle VLC buffering events."""
        buffering = event.u.new_cache
        if buffering < 100:
            self._set_state(PlaybackState.BUFFERING)
            self._trigger_callback('on_buffering', buffering)
        else:
            if self._state == PlaybackState.BUFFERING:
                self._set_state(PlaybackState.PLAYING)

    def _detect_audio_format(self, file_path: Path) -> AudioFormat:
        """Enhanced audio format detection."""
        if not file_path.exists(): return AudioFormat.UNKNOWN
        format_from_ext = AudioFormat.from_extension(file_path.suffix)
        if format_from_ext != AudioFormat.UNKNOWN: return format_from_ext
        if MUTAGEN_AVAILABLE:
            try:
                audio_file = MutagenFile(file_path)
                if audio_file:
                    file_type = type(audio_file).__name__.lower()
                    if 'mp3' in file_type: return AudioFormat.MP3
                    elif 'wave' in file_type: return AudioFormat.WAV
                    elif 'flac' in file_type: return AudioFormat.FLAC
                    elif 'ogg' in file_type: return AudioFormat.OGG
            except Exception: pass
        return AudioFormat.UNKNOWN

    def _validate_audio_file(self, file_path: Path) -> Tuple[bool, str]:
        """Comprehensive audio file validation."""
        if not file_path.exists(): return False, "File does not exist"
        if not file_path.is_file(): return False, "Path is not a file"
        try:
            if file_path.stat().st_size == 0: return False, "File is empty"
        except OSError as e: return False, f"Cannot access file: {e}"
        if self._detect_audio_format(file_path) == AudioFormat.UNKNOWN: return False, "Unsupported audio format"
        return True, "Valid"

    def _get_enhanced_duration(self, file_path: Path) -> float:
        """Enhanced duration detection with multiple fallbacks."""
        if MUTAGEN_AVAILABLE:
            try:
                audio_file = MutagenFile(file_path)
                if audio_file and hasattr(audio_file.info, 'length'): return audio_file.info.length
            except Exception: pass
        if file_path.suffix.lower() == '.wav':
            try:
                with wave.open(str(file_path), 'rb') as wav_file:
                    return wav_file.getnframes() / float(wav_file.getframerate())
            except Exception: pass
        if self._current_backend == "vlc" and self._vlc_instance:
            try:
                media = self._vlc_instance.media_new(str(file_path))
                media.parse()
                return media.get_duration() / 1000.0
            except Exception: pass
        return 0.0

    def _analyze_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Analyze audio file for technical metadata."""
        metadata = {'format': self._detect_audio_format(file_path).value, 'duration': self._duration}
        try: metadata['file_size'] = file_path.stat().st_size
        except OSError: metadata['file_size'] = 0
        if MUTAGEN_AVAILABLE:
            try:
                audio_file = MutagenFile(file_path)
                if audio_file:
                    info = audio_file.info
                    metadata['bitrate'] = getattr(info, 'bitrate', 0) // 1000
                    metadata['sample_rate'] = getattr(info, 'sample_rate', 0)
                    metadata['channels'] = getattr(info, 'channels', 0)
            except Exception: pass
        return metadata

    def generate_waveform_data(self, file_path: Path, num_points: int = 200) -> Optional[List[float]]:
        """Generate simplified waveform data for visualization."""
        if not file_path.exists() or file_path.suffix.lower() != '.wav': return None
        try:
            with wave.open(str(file_path), 'rb') as wav_file:
                n_frames, sample_width = wav_file.getnframes(), wav_file.getsampwidth()
                frames = wav_file.readframes(n_frames)
                if sample_width == 2: samples = struct.unpack(f'<{n_frames}h', frames)
                elif sample_width == 1: samples = [s - 128 for s in struct.unpack(f'<{n_frames}B', frames)]
                else: return None
                step = max(1, len(samples) // num_points)
                waveform = [math.sqrt(sum(s*s for s in samples[i:i+step]) / len(samples[i:i+step])) for i in range(0, len(samples), step) if samples[i:i+step]]
                max_val = max(waveform) if waveform else 0
                return [w / max_val for w in waveform] if max_val > 0 else []
        except Exception as e:
            logger.debug(f"Waveform generation failed: {e}")
            return None

    def shutdown(self):
        """Enhanced shutdown with comprehensive cleanup."""
        logger.info("Shutting down Professional AudioPlayer")
        with self._lock:
            self.stop()
            if self._vlc_player:
                try: self._vlc_player.release()
                except Exception: pass
            if self._vlc_instance:
                try: self._vlc_instance.release()
                except Exception: pass
            if PYGAME_AVAILABLE:
                try: pygame.mixer.quit(); pygame.quit()
                except Exception: pass
            self._set_state(PlaybackState.DISABLED)
            self.callbacks.clear()
        super().shutdown()
        logger.info("Professional AudioPlayer shutdown complete")