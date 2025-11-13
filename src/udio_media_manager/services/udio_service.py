"""
Professional Udio Service Layer (Upgraded)
"""

import threading
import time
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict

from ..core.exceptions import ScanError, CancellationError
from ..core.singleton import SingletonBase
from ..domain.dto import ScanProgressDTO, ScanRequestDTO, TrackQueryDTO
from ..domain.enums import FileType, ScanStatus
from ..domain.models import ScanResult, Track
from ..utils.logging import get_logger
from .database import Database
from .metadata_parser import MetadataParser

logger = get_logger(__name__)


class UdioService(SingletonBase):
    """Provides high-level methods for managing the audio track library."""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.parser = MetadataParser()
        self._scan_thread: Optional[threading.Thread] = None
        self._cancel_scan_flag = threading.Event()
        self._uuid_pattern = re.compile(r'([a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12})')
        logger.info("🚀 Professional UdioService initialized")

    def scan_directory(
        self,
        request: ScanRequestDTO,
        progress_callback: Callable[[ScanProgressDTO], None],
        completion_callback: Callable[[ScanResult], None],
    ) -> None:
        """Starts a new directory scan in a background thread."""
        if self._scan_thread and self._scan_thread.is_alive():
            logger.warning("Scan is already in progress.")
            completion_callback(ScanResult(scan_path=request.scan_path, status=ScanStatus.ERROR, error_message="Scan already in progress."))
            return

        self._cancel_scan_flag.clear()
        self._scan_thread = threading.Thread(
            target=self._do_scan,
            args=(request, progress_callback, completion_callback),
            name="UdioScanThread",
            daemon=True
        )
        self._scan_thread.start()
        logger.info(f"📁 Started directory scan thread for: {request.scan_path}")

    def _do_scan(
        self,
        request: ScanRequestDTO,
        progress_callback: Callable[[ScanProgressDTO], None],
        completion_callback: Callable[[ScanResult], None],
    ) -> None:
        """The main scanning logic that runs in the background thread."""
        result = ScanResult(scan_path=request.scan_path, status=ScanStatus.RUNNING)
        start_time = time.time()
        try:
            self._report_progress(progress_callback, 0, "Discovering files...")
            file_groups = self._discover_and_group_files(request.scan_path)
            if self._cancel_scan_flag.is_set(): raise CancellationError("Scan cancelled during discovery.")
            self._process_file_groups(file_groups, result, progress_callback)
            result.status = ScanStatus.CANCELLED if self._cancel_scan_flag.is_set() else ScanStatus.COMPLETED
        except CancellationError as e:
            result.status = ScanStatus.CANCELLED
            logger.warning(f"⏹️ Scan was cancelled: {e}")
        except Exception as e:
            result.status = ScanStatus.ERROR
            result.error_message = str(e)
            logger.error(f"💥 Unhandled exception in scan thread: {e}", exc_info=True)
        finally:
            setattr(result, 'duration', time.time() - start_time)
            logger.info(
                f"📊 Scan finished: {result.status.name} "
                f"({result.processed_files} processed, {result.failed_files} failed in {getattr(result, 'duration', 0):.2f}s)"
            )
            completion_callback(result)

    def _discover_and_group_files(self, scan_path: Path) -> Dict[str, List[Path]]:
        """Efficiently discovers and groups related files by a common identifier."""
        logger.info(f"🔍 Starting file discovery in: {scan_path}")
        file_groups: Dict[str, List[Path]] = defaultdict(list)
        supported_extensions = FileType.get_supported_extensions()

        for file_path in scan_path.rglob('*'):
            if self._cancel_scan_flag.is_set(): break
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                match = self._uuid_pattern.search(file_path.name)
                group_key = match.group(1) if match else file_path.stem
                file_groups[group_key].append(file_path)

        logger.info(f"📁 Discovered {sum(len(v) for v in file_groups.values())} files in {len(file_groups)} potential groups.")
        return file_groups

    def _process_file_groups(
        self,
        file_groups: Dict[str, List[Path]],
        result: ScanResult,
        progress_callback: Callable[[ScanProgressDTO], None],
    ) -> None:
        """Processes file groups in batches to create and save Track objects."""
        total_groups = len(file_groups)
        tracks_to_upsert: List[Track] = []

        for i, (group_key, files) in enumerate(file_groups.items()):
            if self._cancel_scan_flag.is_set(): break
            percent = ((i + 1) / total_groups) * 100 if total_groups > 0 else 0
            self._report_progress(progress_callback, percent, f"Processing group {i+1}/{total_groups}")
            
            try:
                track = self._build_track_from_files(group_key, files)
                if track:
                    tracks_to_upsert.append(track)
                    result.processed_files += 1
                else:
                    result.failed_files += 1
            except Exception as e:
                result.failed_files += 1
                result.add_error(str(files[0] if files else group_key), str(e))
                logger.warning(f"❌ Failed to build track for group '{group_key}': {e}")
            
            if len(tracks_to_upsert) >= 50:
                self.db.upsert_tracks(tracks_to_upsert)
                tracks_to_upsert.clear()
        
        if tracks_to_upsert:
            self.db.upsert_tracks(tracks_to_upsert)

    def _build_track_from_files(self, group_key: str, files: List[Path]) -> Optional[Track]:
        """Constructs a single Track object from a group of related files."""
        # UPGRADE: Intelligently find the primary metadata file, ignoring lyric files.
        metadata_path = next((f for f in files if f.suffix.lower() == '.txt' and 'lyrics' not in f.name.lower()), None)
        
        if not metadata_path:
            logger.debug(f"Skipping group '{group_key}': No primary metadata file (.txt) found.")
            return None

        files_by_type = {ft: f for f in files if (ft := FileType.from_filename(f.name)) is not FileType.UNKNOWN}
        
        parsed_data = self.parser.parse_txt_file(metadata_path)
        if not parsed_data.get('song_id'):
            logger.warning(f"Skipping metadata file with no song_id: {metadata_path}")
            return None
            
        parsed_data['file_path'] = metadata_path

        # UPGRADE: Correctly and safely instantiate the Track dataclass.
        track_fields = {f.name for f in Track.__dataclass_fields__.values()}
        valid_data = {k: v for k, v in parsed_data.items() if k in track_fields}
        track = Track(**valid_data)

        track.files = files_by_type
        if art_path := files_by_type.get(FileType.ART) or files_by_type.get(FileType.IMAGE):
            track.artwork_file_path = str(art_path)
        if lrc_path := files_by_type.get(FileType.LYRICS):
            track.lyrics = lrc_path.read_text(encoding='utf-8', errors='ignore')

        return track

    def _report_progress(self, callback: Callable, percent: float, description: str):
        try: callback(ScanProgressDTO(progress=percent, message=description))
        except Exception as e: logger.debug(f"Progress callback failed: {e}")

    def get_tracks(self, query_dto: TrackQueryDTO) -> Tuple[List[Track], int]:
        """Fetches a paginated, sorted, and filtered list of tracks."""
        try:
            tracks = self.db.search_tracks(query_dto)
            total_count = self.db.get_track_count(query=query_dto)
            return tracks, total_count
        except Exception as e:
            logger.error(f"❌ Error fetching tracks: {e}", exc_info=True); return [], 0

    def get_track(self, song_id: str) -> Optional[Track]:
        """Retrieves a single track by its ID."""
        try: return self.db.get_track(song_id)
        except Exception as e: logger.error(f"❌ Error getting track {song_id}: {e}", exc_info=True); return None

    def get_statistics(self) -> Dict[str, Any]:
        """Retrieves library statistics from the database."""
        try: return self.db.get_database_stats()
        except Exception as e: logger.error(f"❌ Error getting statistics: {e}", exc_info=True); return {}

    def cancel_scan(self) -> None:
        """Signals the running scan operation to cancel."""
        if self._scan_thread and self._scan_thread.is_alive():
            logger.info("⏹️ Scan cancellation requested."); self._cancel_scan_flag.set()

    def shutdown(self) -> None:
        """Shuts down the service, cancelling any ongoing scan."""
        logger.info("🛑 Shutting down UdioService...")
        self.cancel_scan()
        if self._scan_thread and self._scan_thread.is_alive(): self._scan_thread.join(timeout=5.0)
        super().shutdown()
        logger.info("✅ UdioService shutdown completed")