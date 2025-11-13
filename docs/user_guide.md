# User Guide: Musik Archive Viewer

The **Musik Archive Viewer** is a desktop application designed to help you manage, organize, and play your Udio-generated music archives.

## 1. Prerequisites

Before using the application, you need to export your Udio tracks using the provided script.

1.  **Install Tampermonkey/Greasemonkey**: Install a user script manager extension (like Tampermonkey for Chrome/Firefox) in your web browser.
2.  **Install `UdioArchiver.js`**: Install the `UdioArchiver.js` script into your user script manager. This script adds an export button to the Udio interface.
3.  **Export Your Tracks**: Use the script to export your tracks. This will create a directory containing the audio file, metadata JSON, and artwork for each track. **Remember the location of this directory.**

## 2. Installation and Launch

The application is a standalone executable.

1.  **Download**: Download the latest release for your operating system (e.g., Windows Portable Build).
2.  **Launch**: Run the executable file.

The application will automatically create a local database to store your track information.

## 3. Application Interface Overview

The main window is divided into several key areas:

*   **Menu Bar**: Provides access to core functions like File (Scan Directory, Exit), View (Toggle Theme), and Help.
*   **Track List**: The central area, featuring a high-performance, virtualized list of all scanned tracks.
*   **Playback Controls**: Located at the bottom, offering standard controls (Play, Pause, Seek, Volume, Shuffle, Repeat).
*   **Metadata Panel**: A tabbed panel (usually on the right) that displays detailed information about the currently selected track.

## 4. Getting Started: Scanning Your Archive

The first step is to point the application to the directory where you saved your exported Udio tracks.

1.  Go to the **File** menu.
2.  Select **Scan Directory**.
3.  A file dialog will open. Navigate to and select the **root directory** containing your exported Udio tracks.
4.  The application will begin a recursive scan. The `ScanManager` will process all files, group them into `Track` objects, and save the data to the local database.
5.  Once the scan is complete, your tracks will populate the **Track List**.

## 5. Managing and Viewing Tracks

### 5.1. Track List

*   **Selection**: Click on any track in the list to select it. The **Metadata Panel** will update to show its details.
*   **Sorting**: Click on the column headers (e.g., Title, Artist, Duration) to sort the track list.
*   **Search/Filter**: (Future Feature) A search bar will allow you to filter the list by title, artist, or prompt.

### 5.2. Metadata Panel

The Metadata Panel provides a detailed, tabbed view of the selected track's information:

*   **Core Info**: Title, Artist, Duration, Creation Date, and the unique Song ID.
*   **Prompts & Lyrics**: The original generation prompt and the full lyrics.
*   **Technical Details**: File size, file path, and other technical data.
*   **Raw Data**: The complete, raw JSON metadata extracted from the export file.

## 6. Audio Playback

The application features a robust audio player.

1.  **Start Playback**: Double-click a track in the list, or select a track and click the **Play** button in the Playback Controls.
2.  **Controls**: Use the Play/Pause button, the seek bar to jump to a specific time, and the volume slider.
3.  **Playback Modes**: Toggle **Shuffle** and **Repeat** modes for continuous listening.

## 7. Customization

### Dynamic Theming

The application supports instant theme switching.

1.  Go to the **View** menu.
2.  Select **Toggle Theme** (or a specific theme option if available).
3.  The entire user interface will instantly switch between light and dark modes. (Note: This feature is currently planned and may be marked as **-Needs implementing with UI-** in the code.)
