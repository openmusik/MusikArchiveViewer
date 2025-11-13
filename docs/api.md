# API Reference: Core Data Model

The application's internal "API" is primarily defined by the core data structures used to represent a single media item. The central object is the `Track` dataclass, which encapsulates all metadata and file information for a Udio-generated track.

## `Track` Data Model (`domain/models.py`)

The `Track` class is a comprehensive dataclass designed to hold all possible information extracted from Udio exports, file system scans, and user interactions.

### Fields

| Field Name | Type | Description | Category |
| :--- | :--- | :--- | :--- |
| **`song_id`** | `str` | **REQUIRED**. The unique identifier for the track from the source platform. | Required |
| **`file_path`** | `pathlib.Path` | **REQUIRED**. The primary file path associated with the track (usually the metadata file or the audio file). | Required |
| `title` | `str` | The title of the track. Defaults to "Untitled". | Core Info |
| `artist` | `str` | The artist name. Defaults to "Unknown". | Core Info |
| `duration` | `float` | The length of the track in seconds. | Core Info |
| `created_date` | `datetime` | The date and time the track was created. | Core Info |
| `generation_id` | `str` | A secondary identifier related to the generation process. | Identifiers |
| `user_id` | `str` | The ID of the user who generated the track. | Identifiers |
| `source_url` | `str` | The URL to the track's page on the source platform. | URLs & Media |
| `audio_url` | `str` | The direct URL to the audio file. | URLs & Media |
| `album_art_url` | `str` | The URL to the track's album art image. | URLs & Media |
| `prompt` | `str` | The text prompt used to generate the track. | Content & Metadata |
| `description` | `str` | A description of the track. | Content & Metadata |
| `tags` | `List[str]` | System-generated tags associated with the track. | Content & Metadata |
| `user_tags` | `List[str]` | User-defined tags. | Content & Metadata |
| `lyrics` | `str` | The lyrics of the track. | Content & Metadata |
| `parent_id` | `str` | The ID of the track this one was remixed or continued from. | Relationship |
| `status` | `TrackStatus` | The current status of the track (e.g., DRAFT, FINISHED). | Status |
| `plays` | `int` | The number of times the track has been played in the application. | Engagement |
| `likes` | `int` | The number of likes from the source platform. | Engagement |
| **`artwork_file_path`** | `str` | **NEW**. The local file path to the persistently stored artwork image. | File System |
| `files` | `Dict[FileType, Path]` | A dictionary mapping file types (e.g., AUDIO, METADATA) to their local `Path` objects. | File System |
| `custom_fields` | `Dict[str, Any]` | A catch-all for any non-standard or future metadata fields. | Extended Metadata |
| `audio_metadata` | `Dict[str, Any]` | Raw metadata extracted from the audio file itself (e.g., using `mutagen`). | Extended Metadata |

### Key Properties

The `Track` model exposes several properties for convenient access to derived or calculated information:

*   **`has_audio`**: A boolean indicating if a playable audio file is associated with the track.
*   **`audio_path`**: A property that attempts to resolve the local `pathlib.Path` to the audio file using a multi-step fallback strategy:
    1.  Check the `files` dictionary.
    2.  Check if `file_path` itself is an audio file.
    3.  Look for an audio file with the same base name as `file_path` in the same directory.

## `UdioService` Interface

The `UdioService` (`services/udio_service.py`) acts as the primary interface for managing the track collection.

### Key Methods

| Method | Description |
| :--- | :--- |
| **`scan_directory(path: Path)`** | Initiates a recursive scan of the given directory, identifying Udio exports and creating `Track` objects. |
| **`get_all_tracks() -> List[Track]`** | Retrieves all stored `Track` objects from the database. |
| **`get_track_by_id(song_id: str) -> Optional[Track]`** | Fetches a specific track using its unique `song_id`. |
| **`update_track(track: Track)`** | Persists changes made to a `Track` object back to the database. |
| **`delete_track(song_id: str)`** | Removes a track and its associated files from the database and file system. |
| **`get_track_count() -> int`** | Returns the total number of tracks in the archive. |
