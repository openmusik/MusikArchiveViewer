# database.py - Fully Upgraded with Artwork Path Support and Migration

"""
Advanced database service for track storage and retrieval using SQLite.

This module provides a robust, thread-safe service for all database
interactions, featuring a comprehensive schema, efficient batch operations,
and advanced querying capabilities.

UPGRADE: Now includes artwork_file_path field and automatic schema migration.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from ..core.constants import BATCH_INSERT_SIZE, DATABASE_NAME, DATABASE_TIMEOUT
from ..core.exceptions import DatabaseError
from ..core.singleton import SingletonBase
from ..domain.dto import TrackQueryDTO
from ..domain.enums import SortKey
from ..domain.models import Track
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Database schema version for migration tracking
CURRENT_SCHEMA_VERSION = 2  # Incremented for artwork_file_path addition


class Database(SingletonBase):
    """
    Manages all SQLite database operations with a per-thread connection model.

    This service enables high concurrency and safety by using WAL mode and
    providing a dedicated connection for each thread that interacts with it.
    Its initialization is atomic, making it thread-safe from the moment of creation.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initializes the database service. This constructor is thread-safe and idempotent.
        It immediately configures the database path and ensures the schema exists.
        
        Args:
            db_path (Optional[Path]): Path to the database file. Defaults to a standard
                                       location if not provided.
        """
        super().__init__()
        
        self._init_lock = threading.RLock()

        with self._init_lock:
            if hasattr(self, '_db_path') and self._db_path is not None:
                return  # Already initialized

            self._db_path = db_path if db_path else Path.cwd() / DATABASE_NAME
            self._connection_pool: Dict[int, sqlite3.Connection] = {}
            
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Database service is initializing at: {self._db_path}")
            
            # Check if this is a new database or needs migration
            is_new_db = not self._db_path.exists()
            
            # Create base schema first (without artwork column if migrating)
            self._create_schema(include_artwork=is_new_db)
            
            # Run migrations if needed (adds artwork column to existing DBs)
            if not is_new_db:
                self._run_migrations()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Retrieves or creates a database connection for the current thread.
        Each thread gets its own dedicated connection to ensure thread safety.
        """
        if not self._db_path:
            raise DatabaseError("Database path is not configured.")

        thread_id = threading.get_ident()
        if thread_id in self._connection_pool:
            return self._connection_pool[thread_id]

        try:
            conn = sqlite3.connect(
                self._db_path,
                timeout=DATABASE_TIMEOUT,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA cache_size=-64000;")

            self._connection_pool[thread_id] = conn
            logger.debug(f"Created new database connection for thread {thread_id}")
            return conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database at {self._db_path}", details=str(e)) from e

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Cursor]:
        """
        A context manager for safe, atomic database transactions.
        Automatically commits on success or rolls back on any exception.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN")
            yield cursor
            conn.commit()
        except Exception as e:
            logger.error(f"Transaction failed, rolling back. Error: {e}", exc_info=True)
            conn.rollback()
            raise DatabaseError("Database transaction failed") from e

    def _get_schema_version(self) -> int:
        """Get current schema version from database."""
        try:
            conn = self._get_connection()
            # Check if schema_version table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if not cursor.fetchone():
                return 0  # No version table = version 0
                
            result = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1").fetchone()
            return result[0] if result else 0
        except sqlite3.Error:
            return 0

    def _set_schema_version(self, version: int) -> None:
        """Set schema version in database."""
        try:
            with self._transaction() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute(
                    "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                    (version,)
                )
            logger.info(f"Schema version set to {version}")
        except sqlite3.Error as e:
            logger.error(f"Failed to set schema version: {e}")

    def _run_migrations(self) -> None:
        """Run database migrations to upgrade schema."""
        current_version = self._get_schema_version()
        
        if current_version >= CURRENT_SCHEMA_VERSION:
            logger.info(f"Database schema is up to date (v{current_version})")
            return
            
        logger.info(f"Running database migrations from v{current_version} to v{CURRENT_SCHEMA_VERSION}")
        
        # Migration from v0/v1 to v2: Add artwork_file_path
        if current_version < 2:
            self._migrate_to_v2()
            
        self._set_schema_version(CURRENT_SCHEMA_VERSION)
        logger.info("Database migrations completed successfully")

    def _migrate_to_v2(self) -> None:
        """Migration to v2: Add artwork_file_path field."""
        logger.info("Migrating to schema v2: Adding artwork_file_path field")
        
        try:
            with self._transaction() as cursor:
                # Check if column already exists
                cursor.execute("PRAGMA table_info(tracks)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'artwork_file_path' not in columns:
                    # Add the new column
                    cursor.execute("""
                        ALTER TABLE tracks ADD COLUMN artwork_file_path TEXT
                    """)
                    logger.info("Added artwork_file_path column to tracks table")
                    
                    # Create index for artwork_file_path
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_tracks_artwork_path 
                        ON tracks(artwork_file_path)
                    """)
                    logger.info("Created index for artwork_file_path")
                    
                    # Populate artwork paths from existing file paths
                    self._populate_artwork_paths(cursor)
                else:
                    logger.info("artwork_file_path column already exists")
                    
        except sqlite3.Error as e:
            logger.error(f"Migration to v2 failed: {e}", exc_info=True)
            raise DatabaseError("Failed to migrate database to v2") from e

    def _populate_artwork_paths(self, cursor: sqlite3.Cursor) -> None:
        """Populate artwork_file_path for existing tracks by scanning file system."""
        logger.info("Populating artwork paths for existing tracks...")
        
        try:
            # Get all tracks with file_path
            cursor.execute("SELECT song_id, file_path FROM tracks WHERE file_path IS NOT NULL")
            rows = cursor.fetchall()
            
            updated_count = 0
            for row in rows:
                song_id, file_path_str = row[0], row[1]
                
                if not file_path_str:
                    continue
                    
                try:
                    file_path = Path(file_path_str)
                    
                    # Look for sidecar artwork files
                    artwork_patterns = [
                        f"{file_path.stem} - Artwork.avif",
                        f"{file_path.stem} - Artwork.jpg",
                        f"{file_path.stem} - Artwork.jpeg",
                        f"{file_path.stem} - Artwork.png",
                        f"{file_path.stem}.avif",
                        f"{file_path.stem}.jpg",
                        f"{file_path.stem}.jpeg",
                        f"{file_path.stem}.png",
                    ]
                    
                    for pattern in artwork_patterns:
                        artwork_path = file_path.parent / pattern
                        if artwork_path.exists():
                            cursor.execute(
                                "UPDATE tracks SET artwork_file_path = ? WHERE song_id = ?",
                                (str(artwork_path), song_id)
                            )
                            updated_count += 1
                            logger.debug(f"Found artwork for {song_id}: {artwork_path.name}")
                            break
                            
                except Exception as e:
                    logger.debug(f"Error checking artwork for {song_id}: {e}")
                    continue
                    
            logger.info(f"Populated artwork paths for {updated_count} tracks")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to populate artwork paths: {e}")

    def _create_schema(self, include_artwork: bool = True) -> None:
        """Creates all necessary tables, indices, and triggers for the application.
        
        Args:
            include_artwork: If True, includes artwork_file_path in schema (for new DBs)
        """
        try:
            with self._transaction() as cursor:
                logger.debug("Verifying database schema...")
                
                # Build the CREATE TABLE statement dynamically
                artwork_column = "artwork_file_path TEXT," if include_artwork else ""
                
                # Main tracks table with ALL metadata fields
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS tracks (
                        -- Core identifiers
                        song_id TEXT PRIMARY KEY,
                        generation_id TEXT,
                        user_id TEXT,
                        
                        -- Basic track info
                        title TEXT NOT NULL,
                        artist TEXT,
                        duration REAL DEFAULT 0,
                        created_date TIMESTAMP,
                        
                        -- URLs and media
                        source_url TEXT,
                        audio_url TEXT,
                        album_art_url TEXT,
                        video_url TEXT,
                        artist_image_url TEXT,
                        
                        -- Content and metadata
                        prompt TEXT,
                        description TEXT,
                        tags TEXT,
                        user_tags TEXT,
                        lyrics TEXT,
                        audio_conditioning_type TEXT,
                        capture_method TEXT,
                        
                        -- Relationship info
                        parent_id TEXT,
                        original_song_path TEXT,
                        relationship_type TEXT,
                        relationship_info TEXT,
                        
                        -- Collaboration info
                        collaboration_info TEXT,
                        attribution TEXT,
                        
                        -- Status and engagement
                        plays INTEGER DEFAULT 0,
                        likes INTEGER DEFAULT 0,
                        is_finished BOOLEAN DEFAULT 0,
                        is_publishable BOOLEAN DEFAULT 0,
                        is_disliked BOOLEAN DEFAULT 0,
                        is_liked BOOLEAN DEFAULT 0,
                        is_favorite BOOLEAN DEFAULT 0,
                        status TEXT NOT NULL,
                        
                        -- File system info
                        file_path TEXT NOT NULL,
                        file_size INTEGER DEFAULT 0,
                        file_size_mb REAL DEFAULT 0,
                        file_location TEXT,
                        file_absolute_path TEXT,
                        playlist_context TEXT,
                        {artwork_column}
                        
                        -- Export info
                        exported_date TIMESTAMP,
                        export_tool TEXT,
                        
                        -- Extended metadata
                        custom_fields TEXT,
                        audio_metadata TEXT,
                        export_info TEXT,
                        lyrics_data TEXT,
                        user_data TEXT,
                        
                        -- System timestamps
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """)

                # Create comprehensive indices for performance
                indices = [
                    # Basic search indices
                    "CREATE INDEX IF NOT EXISTS idx_tracks_title ON tracks(title);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_created_date ON tracks(created_date);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status);",
                    
                    # Performance indices
                    "CREATE INDEX IF NOT EXISTS idx_tracks_plays ON tracks(plays);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_likes ON tracks(likes);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_duration ON tracks(duration);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_finished ON tracks(is_finished);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_favorite ON tracks(is_favorite);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_publishable ON tracks(is_publishable);",
                    
                    # URL indices
                    "CREATE INDEX IF NOT EXISTS idx_tracks_audio_url ON tracks(audio_url);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_source_url ON tracks(source_url);",
                    
                    # File path indices
                    "CREATE INDEX IF NOT EXISTS idx_tracks_file_path ON tracks(file_path);",
                    
                    # Relationship indices
                    "CREATE INDEX IF NOT EXISTS idx_tracks_parent_id ON tracks(parent_id);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_relationship_type ON tracks(relationship_type);",
                    
                    # Composite indices
                    "CREATE INDEX IF NOT EXISTS idx_tracks_status_date ON tracks(status, created_date);",
                    "CREATE INDEX IF NOT EXISTS idx_tracks_artist_title ON tracks(artist, title);",
                ]
                
                # Only add artwork index if column exists
                if include_artwork:
                    indices.append("CREATE INDEX IF NOT EXISTS idx_tracks_artwork_path ON tracks(artwork_file_path);")
                
                for index_sql in indices:
                    cursor.execute(index_sql)

                # Update timestamp trigger
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_update_tracks_timestamp
                    AFTER UPDATE ON tracks FOR EACH ROW
                    BEGIN
                        UPDATE tracks SET updated_at = CURRENT_TIMESTAMP WHERE song_id = OLD.song_id;
                    END;
                """)
                
            logger.info("Database schema is up to date with artwork_file_path support.")
        except DatabaseError as e:
            logger.critical("Failed to create database schema", exc_info=True)
            raise

    def upsert_tracks(self, tracks: List[Track]) -> int:
        """Inserts or updates a list of tracks in efficient batches with ALL metadata fields."""
        if not tracks: 
            return 0

        sql = """
            INSERT INTO tracks (
                song_id, generation_id, user_id, title, artist, duration, created_date,
                source_url, audio_url, album_art_url, video_url, artist_image_url,
                prompt, description, tags, user_tags, lyrics, audio_conditioning_type, capture_method,
                parent_id, original_song_path, relationship_type, relationship_info,
                collaboration_info, attribution, plays, likes, is_finished, is_publishable, 
                is_disliked, is_liked, is_favorite, status, file_path, file_size, file_size_mb,
                file_location, file_absolute_path, playlist_context, artwork_file_path,
                exported_date, export_tool, custom_fields, audio_metadata, export_info, 
                lyrics_data, user_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(song_id) DO UPDATE SET
                generation_id=excluded.generation_id,
                user_id=excluded.user_id,
                title=excluded.title,
                artist=excluded.artist,
                duration=excluded.duration,
                created_date=excluded.created_date,
                source_url=excluded.source_url,
                audio_url=excluded.audio_url,
                album_art_url=excluded.album_art_url,
                video_url=excluded.video_url,
                artist_image_url=excluded.artist_image_url,
                prompt=excluded.prompt,
                description=excluded.description,
                tags=excluded.tags,
                user_tags=excluded.user_tags,
                lyrics=excluded.lyrics,
                audio_conditioning_type=excluded.audio_conditioning_type,
                capture_method=excluded.capture_method,
                parent_id=excluded.parent_id,
                original_song_path=excluded.original_song_path,
                relationship_type=excluded.relationship_type,
                relationship_info=excluded.relationship_info,
                collaboration_info=excluded.collaboration_info,
                attribution=excluded.attribution,
                plays=excluded.plays,
                likes=excluded.likes,
                is_finished=excluded.is_finished,
                is_publishable=excluded.is_publishable,
                is_disliked=excluded.is_disliked,
                is_liked=excluded.is_liked,
                is_favorite=excluded.is_favorite,
                status=excluded.status,
                file_path=excluded.file_path,
                file_size=excluded.file_size,
                file_size_mb=excluded.file_size_mb,
                file_location=excluded.file_location,
                file_absolute_path=excluded.file_absolute_path,
                playlist_context=excluded.playlist_context,
                artwork_file_path=excluded.artwork_file_path,
                exported_date=excluded.exported_date,
                export_tool=excluded.export_tool,
                custom_fields=excluded.custom_fields,
                audio_metadata=excluded.audio_metadata,
                export_info=excluded.export_info,
                lyrics_data=excluded.lyrics_data,
                user_data=excluded.user_data;
        """
        
        total_upserted = 0
        try:
            for i in range(0, len(tracks), BATCH_INSERT_SIZE):
                batch = tracks[i : i + BATCH_INSERT_SIZE]
                params = [track.to_row() for track in batch]
                with self._transaction() as cursor:
                    cursor.executemany(sql, params)
                    total_upserted += cursor.rowcount
            logger.info(f"Successfully upserted {total_upserted} of {len(tracks)} tracks with artwork paths.")
            return total_upserted
        except sqlite3.Error as e:
            logger.error(f"Batch upsert failed: {e}")
            return self._upsert_tracks_individually(tracks)

    def _upsert_tracks_individually(self, tracks: List[Track]) -> int:
        """Fallback method to upsert tracks one by one when batch operations fail."""
        total_upserted = 0
        individual_sql = """
            INSERT INTO tracks (
                song_id, generation_id, user_id, title, artist, duration, created_date,
                source_url, audio_url, album_art_url, video_url, artist_image_url,
                prompt, description, tags, user_tags, lyrics, audio_conditioning_type, capture_method,
                parent_id, original_song_path, relationship_type, relationship_info,
                collaboration_info, attribution, plays, likes, is_finished, is_publishable, 
                is_disliked, is_liked, is_favorite, status, file_path, file_size, file_size_mb,
                file_location, file_absolute_path, playlist_context, artwork_file_path,
                exported_date, export_tool, custom_fields, audio_metadata, export_info, 
                lyrics_data, user_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(song_id) DO UPDATE SET
                generation_id=excluded.generation_id,
                user_id=excluded.user_id,
                title=excluded.title,
                artist=excluded.artist,
                duration=excluded.duration,
                created_date=excluded.created_date,
                source_url=excluded.source_url,
                audio_url=excluded.audio_url,
                album_art_url=excluded.album_art_url,
                video_url=excluded.video_url,
                artist_image_url=excluded.artist_image_url,
                prompt=excluded.prompt,
                description=excluded.description,
                tags=excluded.tags,
                user_tags=excluded.user_tags,
                lyrics=excluded.lyrics,
                audio_conditioning_type=excluded.audio_conditioning_type,
                capture_method=excluded.capture_method,
                parent_id=excluded.parent_id,
                original_song_path=excluded.original_song_path,
                relationship_type=excluded.relationship_type,
                relationship_info=excluded.relationship_info,
                collaboration_info=excluded.collaboration_info,
                attribution=excluded.attribution,
                plays=excluded.plays,
                likes=excluded.likes,
                is_finished=excluded.is_finished,
                is_publishable=excluded.is_publishable,
                is_disliked=excluded.is_disliked,
                is_liked=excluded.is_liked,
                is_favorite=excluded.is_favorite,
                status=excluded.status,
                file_path=excluded.file_path,
                file_size=excluded.file_size,
                file_size_mb=excluded.file_size_mb,
                file_location=excluded.file_location,
                file_absolute_path=excluded.file_absolute_path,
                playlist_context=excluded.playlist_context,
                artwork_file_path=excluded.artwork_file_path,
                exported_date=excluded.exported_date,
                export_tool=excluded.export_tool,
                custom_fields=excluded.custom_fields,
                audio_metadata=excluded.audio_metadata,
                export_info=excluded.export_info,
                lyrics_data=excluded.lyrics_data,
                user_data=excluded.user_data;
        """
        
        for track in tracks:
            try:
                with self._transaction() as cursor:
                    cursor.execute(individual_sql, track.to_row())
                    if cursor.rowcount > 0:
                        total_upserted += 1
            except sqlite3.IntegrityError as e:
                logger.warning(f"Failed to upsert track {track.song_id}: {e}")
            except Exception as e:
                logger.error(f"Failed to upsert track {track.song_id}: {e}")
        
        logger.info(f"Individual upsert completed: {total_upserted} of {len(tracks)} tracks processed.")
        return total_upserted

    def get_track_by_file_path(self, file_path: Path) -> Optional[Track]:
        """Retrieve a track by its file path."""
        sql = "SELECT * FROM tracks WHERE file_path = ?;"
        try:
            conn = self._get_connection()
            row = conn.execute(sql, (str(file_path),)).fetchone()
            return Track.from_row(row) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get track by file_path {file_path}", sql=sql, params=(str(file_path),)) from e

    def get_track(self, song_id: str) -> Optional[Track]:
        """Retrieves a single track by its unique ID."""
        sql = "SELECT * FROM tracks WHERE song_id = ?;"
        try:
            conn = self._get_connection()
            row = conn.execute(sql, (song_id,)).fetchone()
            return Track.from_row(row) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get track {song_id}", sql=sql, params=(song_id,)) from e

    def get_all_tracks(self) -> List[Track]:
        """Retrieves all tracks, ordered by the most recently created."""
        return self.search_tracks(TrackQueryDTO(sort_by=SortKey.DATE, sort_descending=True))

    def search_tracks(self, query: TrackQueryDTO, limit: Optional[int] = None) -> List[Track]:
        """Searches for tracks based on text and sorting criteria with optional limit."""
        base_sql = "SELECT * FROM tracks"
        where_clauses, params = [], []

        if query.search_text:
            where_clauses.append("(title LIKE ? OR artist LIKE ? OR tags LIKE ? OR prompt LIKE ? OR lyrics LIKE ?)")
            search_param = f"%{query.search_text}%"
            params.extend([search_param] * 5)
            
        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)
        
        sort_column = query.sort_by.value
        sort_direction = "DESC" if query.sort_descending else "ASC"
        base_sql += f" ORDER BY {sort_column} {sort_direction}"
        
        # ADD LIMIT for performance
        if limit:
            base_sql += f" LIMIT {limit}"
        
        base_sql += ";"
        
        try:
            conn = self._get_connection()
            rows = conn.execute(base_sql, params).fetchall()
            tracks = [Track.from_row(row) for row in rows]
            logger.info(f"Search with query '{query.search_text}' returned {len(tracks)} tracks.")
            return tracks
        except sqlite3.Error as e:
            raise DatabaseError("Failed to search tracks", sql=base_sql, params=tuple(params)) from e

    def get_track_count(self) -> int:
        """Returns the total number of tracks in the database."""
        sql = "SELECT COUNT(song_id) FROM tracks;"
        try:
            conn = self._get_connection()
            return conn.execute(sql).fetchone()[0] or 0
        except sqlite3.Error as e:
            raise DatabaseError("Failed to get track count", sql=sql) from e

    def delete_track(self, song_id: str) -> bool:
        """Deletes a track from the database by its ID."""
        sql = "DELETE FROM tracks WHERE song_id = ?;"
        try:
            with self._transaction() as cursor:
                cursor.execute(sql, (song_id,))
                deleted = cursor.rowcount > 0
            if deleted: 
                logger.info(f"Deleted track: {song_id}")
            return deleted
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete track {song_id}", sql=sql, params=(song_id,)) from e

    def get_database_stats(self) -> Dict[str, Any]:
        """Retrieves a dictionary of key statistics about the database."""
        queries = {
            "total_tracks": "SELECT COUNT(*) FROM tracks",
            "total_plays": "SELECT SUM(plays) FROM tracks",
            "total_likes": "SELECT SUM(likes) FROM tracks",
            "total_favorites": "SELECT COUNT(*) FROM tracks WHERE is_favorite = 1",
            "total_finished": "SELECT COUNT(*) FROM tracks WHERE is_finished = 1",
            "total_publishable": "SELECT COUNT(*) FROM tracks WHERE is_publishable = 1",
            "total_duration_sec": "SELECT SUM(duration) FROM tracks",
            "total_file_size_mb": "SELECT SUM(file_size) / (1024.0 * 1024.0) FROM tracks",
            "tracks_with_video": "SELECT COUNT(*) FROM tracks WHERE video_url IS NOT NULL AND video_url != ''",
            "tracks_with_lyrics": "SELECT COUNT(*) FROM tracks WHERE lyrics IS NOT NULL AND lyrics != ''",
            "tracks_with_artwork": "SELECT COUNT(*) FROM tracks WHERE artwork_file_path IS NOT NULL AND artwork_file_path != ''",
            "unique_artists": "SELECT COUNT(DISTINCT artist) FROM tracks WHERE artist IS NOT NULL",
        }
        stats = {}
        try:
            conn = self._get_connection()
            for key, sql in queries.items():
                result = conn.execute(sql).fetchone()[0]
                stats[key] = result if result is not None else 0
            return stats
        except sqlite3.Error as e:
            raise DatabaseError("Failed to retrieve database stats") from e

    def get_tracks_by_artist(self, artist: str) -> List[Track]:
        """Retrieves all tracks by a specific artist."""
        sql = "SELECT * FROM tracks WHERE artist = ? ORDER BY created_date DESC;"
        try:
            conn = self._get_connection()
            rows = conn.execute(sql, (artist,)).fetchall()
            return [Track.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get tracks by artist {artist}", sql=sql, params=(artist,)) from e

    def get_favorite_tracks(self) -> List[Track]:
        """Retrieves all favorite tracks."""
        sql = "SELECT * FROM tracks WHERE is_favorite = 1 ORDER BY created_date DESC;"
        try:
            conn = self._get_connection()
            rows = conn.execute(sql).fetchall()
            return [Track.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError("Failed to get favorite tracks", sql=sql) from e
        
    def get_track_count(self, query: Optional[TrackQueryDTO] = None) -> int:
        """Get the total number of tracks matching the query."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if query and query.search_text:
                    # Count with search
                    search_pattern = f"%{query.search_text}%"
                    cursor.execute("""
                        SELECT COUNT(*) FROM tracks 
                        WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
                    """, (search_pattern, search_pattern, search_pattern))
                else:
                    # Count all
                    cursor.execute("SELECT COUNT(*) FROM tracks")
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting track count: {e}")
            return 0

    def shutdown(self) -> None:
        """Closes all active database connections managed by this service."""
        with self._init_lock:
            logger.info("Shutting down all database connections...")
            for thread_id, conn in self._connection_pool.items():
                try:
                    conn.close()
                    logger.debug(f"Closed connection for thread {thread_id}")
                except sqlite3.Error as e:
                    logger.error(f"Error closing DB connection for thread {thread_id}: {e}")
            self._connection_pool.clear()
        super().shutdown()