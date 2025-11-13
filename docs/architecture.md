# Architecture

The **Musik Archive Viewer** is built with a strong emphasis on **modularity**, **extensibility**, and **separation of concerns**, following a clean, layered architecture. This design ensures the application is maintainable, testable, and easy to extend with new features.

## 1. Core Architectural Principles

| Principle | Description | Implementation in Code |
| :--- | :--- | :--- |
| **Modularity** | The application is divided into distinct, independent modules (Domain, Services, UI, Utils) with well-defined interfaces. | The `src/udio_media_manager` package is split into sub-packages: `core`, `domain`, `services`, `ui`, and `utils`. |
| **Separation of Concerns** | Each module is responsible for a single, specific aspect of the application, preventing tight coupling. | Business logic (Domain) is isolated from data access (Services) and presentation (UI). |
| **Single-Instance** | The application ensures only one instance can run at a time to prevent database corruption and resource conflicts. | Implemented using `filelock.FileLock` in `core/app.py` to acquire a lock file upon startup. |
| **Deterministic Shutdown** | A robust shutdown sequence is implemented to ensure all resources (database connections, threads, UI) are cleanly closed. | The `Application` class in `core/app.py` handles the `WM_DELETE_WINDOW` protocol to initiate a controlled shutdown. |

## 2. Component Breakdown

The application is structured around the following key components:

### 2.1. `domain`

This package contains the **business logic** and **data models** of the application. It is the core layer, independent of any specific service or UI implementation.

*   **`models.py`**: Defines the central data structure, the `Track` dataclass, which encapsulates all Udio-related metadata, file paths, and status information.
*   **`enums.py`**: Contains enumerations for various states, such as `TrackStatus` and `FileType`.
*   **`dto.py`**: Contains Data Transfer Objects (DTOs) used for transferring data between service layers, ensuring type safety and clear data contracts.

### 2.2. `services`

The services layer handles all external interactions, data persistence, and complex business operations.

*   **`UdioService`**: The primary service for managing the track collection. It handles track scanning, database interaction, and business logic related to the `Track` models.
*   **`database.py`**: Manages the SQLite database connection and provides CRUD (Create, Read, Update, Delete) operations for persisting `Track` data.
*   **`metadata_parser.py`**: Responsible for reading and extracting metadata from Udio-exported files (JSON, text, audio tags).
*   **`audio_player.py`**: Encapsulates the audio playback logic (using `pygame` or other backends).
*   **`image_loader.py`**: Handles asynchronous loading and caching of artwork and thumbnails to keep the UI responsive.

### 2.3. `ui`

This package contains all components related to the graphical user interface, built using the `tkinter` framework.

*   **`main_window.py`**: The main application window, which assembles all UI components.
*   **`components`**: A sub-package containing reusable UI elements, notably the `virtual_list` implementation for high-performance display of large track collections.
*   **`event_handlers.py`**: Acts as a controller, receiving user input from the UI and translating it into calls to the `services` layer. This decouples the UI from the business logic.
*   **`themes`**: Manages the application's theming (e.g., light/dark mode).

### 2.4. `core`

This package contains fundamental, cross-cutting concerns for the application.

*   **`app.py`**: The main entry point and application lifecycle manager. It handles initialization, component assembly, and shutdown.
*   **`singleton.py`**: Provides a base class for implementing the Singleton pattern, used for core services that should only have one instance (e.g., the main application instance).
*   **`constants.py`**: Stores application-wide configuration values and magic strings.

### 2.5. `utils`

A collection of utility functions and helper classes used across the application.

*   **`logging.py`**: Configures and manages the application's logging system.
*   **`file_utils.py`**: Contains helpers for file system operations.
*   **`validation.py`**: Provides data validation logic.

## 3. Data Flow and Interaction

1.  **Startup**: `core/app.py` initializes all `services` (e.g., `UdioService`, `AudioPlayer`) and the `MainWindow`.
2.  **Scanning**: The `ScanManager` (in `ui`) calls the `UdioService` (in `services`) to initiate a scan. The service uses `metadata_parser.py` to create `Track` objects (in `domain`) and persists them using `database.py`.
3.  **Display**: The `MainWindow` requests the list of `Track` objects from the `UdioService`. The UI components, especially the `virtual_list`, render the data.
4.  **User Interaction**: User actions (e.g., clicking "Play") are captured by `event_handlers.py`, which calls the appropriate method on the `AudioController` (in `ui`), which in turn interacts with the `AudioPlayer` (in `services`).
5.  **Artwork**: The UI requests artwork from the `ImageLoader` (in `services`), which handles asynchronous loading and caching, delivering the image back to the UI without blocking the main thread.
