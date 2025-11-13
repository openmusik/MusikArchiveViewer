// ==UserScript==
// @name         Udio Downloader (v36.0)
// @namespace    http://tampermonkey.net/
// @version      36.0
// @description  Udio Downloader with MP4, Album Art & Comprehensive Metadata
// @author       YourName
// @match        https://www.udio.com/*
// @grant        GM_download
// @grant        GM_addStyle
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_addValueChangeListener
// @grant        GM_xmlhttpRequest
// @connect      udio.com
// @connect      storage.googleapis.com
// @connect      imagedelivery.net
// @run-at       document-start
// ==/UserScript==

(function() {
        'use strict';

        // ====================================================================================
        // --- ENHANCED INITIALIZATION GUARD WITH PROPER CLEANUP ---
        // ====================================================================================

        // 1. SINGLE INITIALIZATION GUARD - Consolidated and fixed
        if (window.udioDownloaderInitialized) {
            console.log('[UDIO-DL] Injection Guard: Script already initialized, preventing duplicate execution.');
            return;
        }

        // 2. ENHANCED CLEANUP - Perform cleanup but ALLOW re-initialization
        if (window.UdioDownloaderDebug) {
            console.log('[UDIO-DL] Injection Guard: Previous instance detected. Performing cleanup...');
            performComprehensiveCleanup();
            // CRITICAL FIX: Don't return here - allow fresh initialization after cleanup
        }

        // 3. SET INITIALIZATION FLAG
        window.udioDownloaderInitialized = true;
        console.log('[UDIO-DL] Injection Guard: Fresh initialization approved.');

        // 4. SINGLE UNLOAD HANDLER - Consolidated
        window.addEventListener('beforeunload', () => {
            console.log('[UDIO-DL] Injection Guard: Page unloading, resetting initialization flag.');
            window.udioDownloaderInitialized = false;
        });

        // ====================================================================================
        // --- DEDUPLICATED CLEANUP FUNCTION ---
        // ====================================================================================

        function performComprehensiveCleanup() {
            let cleanupSuccessful = false;

            try {
                // Attempt graceful cleanup through UI component
                if (window.UdioDownloaderDebug && window.UdioDownloaderDebug.UI &&
                    typeof window.UdioDownloaderDebug.UI.destroy === 'function') {
                    window.UdioDownloaderDebug.UI.destroy();
                    console.log('[UDIO-DL] Injection Guard: UI component destroyed gracefully.');
                    cleanupSuccessful = true;
                }
            } catch (e) {
                console.error('[UDIO-DL] Injection Guard: Error during graceful cleanup:', e);
            }

            // Fallback: Manual DOM cleanup
            if (!cleanupSuccessful) {
                console.log('[UDIO-DL] Injection Guard: Performing manual DOM cleanup...');
                const elementsToRemove = [
                    'udio-downloader-ui',
                    'udio-downloader-toggle',
                    'udio-context-menu'
                ];

                elementsToRemove.forEach(id => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.remove();
                        console.log(`[UDIO-DL] Injection Guard: Removed element #${id}`);
                    }
                });

                // Remove any leftover event listeners
                document.querySelectorAll('[data-udio-dl-processed]').forEach(el => {
                    el.removeAttribute('data-udio-dl-processed');
                });
            }

            // Global cleanup
            const globalsToDelete = [
                'UdioDownloaderDebug',
                'UdioDownloaderUI',
                'udioDownloaderInitialized',
                'udioDlStartTime'
            ];

            globalsToDelete.forEach(global => {
                try {
                    if (window[global]) {
                        delete window[global];
                        console.log(`[UDIO-DL] Injection Guard: Deleted global ${global}`);
                    }
                } catch (e) {
                    console.warn(`[UDIO-DL] Injection Guard: Could not delete global ${global}:`, e);
                }
            });

            // Force garbage collection hint
            if (window.gc) {
                try {
                    window.gc();
                    console.log('[UDIO-DL] Injection Guard: Garbage collection triggered.');
                } catch (e) {
                    // gc() might not be available
                }
            }

            console.log('[UDIO-DL] Injection Guard: Previous instance cleanup completed.');

            // Small delay to ensure cleanup propagates
            setTimeout(() => {
                console.log('[UDIO-DL] Injection Guard: Ready for fresh initialization.');
            }, 50);
        }

        // ====================================================================================
        // --- COMPATIBILITY POLYFILLS (Deduplicated) ---
        // ====================================================================================

        // Polyfill for Array.prototype.includes
        if (!Array.prototype.includes) {
            Object.defineProperty(Array.prototype, 'includes', {
                value: function(searchElement, fromIndex) {
                    if (this == null) throw new TypeError('"this" is null or not defined');
                    var o = Object(this);
                    var len = o.length >>> 0;
                    if (len === 0) return false;
                    var n = fromIndex | 0;
                    var k = Math.max(n >= 0 ? n : len - Math.abs(n), 0);
                    while (k < len) {
                        if (o[k] === searchElement) return true;
                        k++;
                    }
                    return false;
                }
            });
        }

        // Polyfill for String.prototype.includes
        if (!String.prototype.includes) {
            String.prototype.includes = function(search, start) {
                'use strict';
                if (typeof start !== 'number') start = 0;
                if (start + search.length > this.length) return false;
                return this.indexOf(search, start) !== -1;
            };
        }

        // Polyfill for Object.entries
        if (!Object.entries) {
            Object.entries = function(obj) {
                var ownProps = Object.keys(obj);
                var resArray = new Array(ownProps.length);
                for (var i = 0; i < ownProps.length; i++) {
                    resArray[i] = [ownProps[i], obj[ownProps[i]]];
                }
                return resArray;
            };
        }

        // Polyfill for Object.values
        if (!Object.values) {
            Object.values = function(obj) {
                var vals = [];
                for (var key in obj) {
                    if (Object.prototype.hasOwnProperty.call(obj, key)) {
                        vals.push(obj[key]);
                    }
                }
                return vals;
            };
        }

        // Polyfill for Element.prototype.remove()
        if (!('remove' in Element.prototype)) {
            Element.prototype.remove = function() {
                if (this.parentNode) this.parentNode.removeChild(this);
            };
        }

        // ====================================================================================
        // --- CONFIGURATION & CONSTANTS ---
        // ====================================================================================

        var CONFIG = {
            CONCURRENT_REQUESTS: 8,
            MAX_RETRIES: 2,
            REQUEST_DELAY: 50,
            SCAN_DEBOUNCE_MS: 200,
            API_TIMEOUT: 5000,
            PRECHECK_TIMEOUT: 1000,
            INITIAL_SCAN_DELAY: 500,
            PRECHECK_BATCH_SIZE: 12,
            AGGRESSIVE_SCAN: true,
            SCAN_INTERVAL: 3000,
            FORCE_SCAN_INTERVAL: 15000
        };

        const LOGGING_CONFIG = {
            ENABLED: true,
            PERFORMANCE: false,
            METADATA_SAMPLES: false,
            API_RESPONSES: false,
            RELATIONSHIPS: false,
            SCANNER: true,
            QUEUE: true,
            CONTEXT: false,
            TAB_COORDINATION: false
        };

        // ====================================================================================
        // --- DOWNLOAD OPTIONS CONFIGURATION ---
        // ====================================================================================

        var DOWNLOAD_OPTIONS = {
            DOWNLOAD_METADATA_FILE: GM_getValue('downloadMetadataFile', true),
            DOWNLOAD_LYRICS: GM_getValue('downloadLyrics', true),
            DOWNLOAD_VIDEO: GM_getValue('downloadVideo', true),
            DOWNLOAD_ART: GM_getValue('downloadArt', true),
            DOWNLOAD_AUDIO: GM_getValue('downloadAudio', true),
            OMIT_ARTIST_NAME: GM_getValue('omitArtistName', false)
        };

        // UDIO-SPECIFIC SELECTORS - WE KNOW EXACTLY WHAT TO SCAN
        var UDIO_SELECTORS = {
            // PRIMARY TARGETS - EXACT UDIO ELEMENTS
            SONG_LINKS: [
                'a[href^="/songs/"]',
                'a[href*="/songs/"]'
            ],

            // SONG CARDS & CONTAINERS
            SONG_CONTAINERS: [
                '[class*="song"]',
                '[class*="track"]',
                '[class*="audio"]',
                '.flex.items-center', // Common Udio flex container
                'div > button[aria-label*="Play"]', // Play buttons
                '[data-testid*="song"]',
                '[data-testid*="track"]'
            ],

            // DATA ATTRIBUTES
            DATA_SELECTORS: [
                '[data-song-id]',
                '[data-track-id]',
                '[data-href*="/songs/"]',
                '[data-url*="/songs/"]'
            ],

            // ALTERNATIVE SELECTORS
            FALLBACK_SELECTORS: [
                'a[href*="udio.com/songs/"]',
                '[href*="/songs/"]'
            ]
        };

        var LOG_PREFIX = '[UDIO-DL]';

        // ====================================================================================
        // --- 2. STATE MANAGEMENT - PROFESSIONAL GRADE WITH MEMORY MANAGEMENT ---
        // ====================================================================================

        class State {
            constructor() {
                this.capturedTracks = new Map();
                this.processedGenerationIds = new Set();
                this.isAutoCapturing = false;
                this.listObserver = null;
                this.activeRequests = 0;
                this.isProcessingQueue = false;
                this.isAddingToQueue = false;
                this.isClearing = false;
                this.bearerToken = null;
                this.scanTimeout = null;
                this.performanceMetrics = {
                    scansCompleted: 0,
                    tracksCaptured: 0,
                    apiCalls: 0,
                    lastScanTime: 0,
                    totalDownloadSize: 0,
                    startupTime: 0
                };
                this.trackVersion = 0; // Performance: Used to track data changes for efficient UI updates
                this.saveDebounceTimeout = null; // Performance: Timeout for debouncing storage writes
                this.sessionStartTime = Date.now();
            }

            async initialize() {
                // Minimal initialization logging - only show in debug mode
                if (GM_getValue('debugMode', false)) {
                    this.log('🚀 Initializing enhanced state management...');
                }

                this.bearerToken = this.extractBearerToken();

                // Load persisted data with validation (silent operation)
                this.capturedTracks = this.loadCapturedTracks();
                this.processedGenerationIds = this.loadProcessedIds();
                this.isAutoCapturing = GM_getValue('isAutoCapturing', false);

                // NEW: Migrate old context data to fix ALL incorrect folder contexts
                const migratedCount = this.migrateAllTrackContexts();
                if (migratedCount > 0 && GM_getValue('debugMode', false)) {
                    this.log(`🔄 Migrated ${migratedCount} tracks to fix incorrect folder contexts`);
                }

                // Initialize performance metrics (silent)
                this.performanceMetrics.startupTime = Date.now();

                // Single consolidated status log instead of multiple logs
                const statusSummary = `State: ${this.capturedTracks.size} tracks, ${this.processedGenerationIds.size} processed IDs | Auto-Capture: ${this.isAutoCapturing ? 'ON' : 'OFF'}`;

                // Only log if we have tracks or in debug mode
                if (this.capturedTracks.size > 0 || GM_getValue('debugMode', false)) {
                    this.log(`✅ ${statusSummary}`);
                }

                // Initial memory optimization (silent)
                this.optimizeMemory();
            }

            /**
             * NEW: Remove only undefined or invalid folder contexts from existing tracks
             */
            migrateAllTrackContexts() {
                let migratedCount = 0;

                for (let [url, track] of this.capturedTracks.entries()) {
                    // Only remove undefined, null, or empty folder contexts
                    // Keep valid folder contexts that were properly captured
                    if (track.folderContext === undefined ||
                        track.folderContext === null ||
                        track.folderContext === '' ||
                        track.folderContext === 'undefined') {

                        // Remove the invalid context
                        delete track.folderContext;
                        this.capturedTracks.set(url, track);
                        migratedCount++;
                        this.log(`[Migration] Removed invalid context "${track.folderContext}" from track: "${track.title}"`);
                    }
                }

                if (migratedCount > 0) {
                    this.saveTracks();
                    this.log(`[Migration] COMPLETE: Removed ${migratedCount} invalid folder contexts`);
                }

                return migratedCount;
            }

            loadCapturedTracks() {
                try {
                    var stored = GM_getValue('capturedTracks', '[]');
                    var parsed = this.safeJSONParse(stored, []);
                    var tracksMap = new Map(parsed);

                    // Validate track data integrity
                    var validCount = 0;
                    var invalidCount = 0;

                    for (var [url, track] of tracksMap) {
                        if (url && track && track.title) {
                            validCount++;
                        } else {
                            tracksMap.delete(url);
                            invalidCount++;
                        }
                    }

                    if (invalidCount > 0) {
                        this.log(`🧹 Cleaned ${invalidCount} invalid tracks, ${validCount} remain`);
                        GM_setValue('capturedTracks', JSON.stringify(Array.from(tracksMap.entries())));
                    }

                    return tracksMap;
                } catch (error) {
                    this.error('Failed to load captured tracks:', error);
                    return new Map();
                }
            }

            loadProcessedIds() {
                try {
                    var stored = GM_getValue('processedGenerationIds', '[]');
                    var parsed = this.safeJSONParse(stored, []);
                    return new Set(parsed);
                } catch (error) {
                    this.error('Failed to load processed IDs:', error);
                    return new Set();
                }
            }

            saveTracks() {
                if (this.isClearing) return;

                // --- 1. IMMEDIATE ACTIONS ---
                // Increment version to signal a change to the UI. This is cheap and fast.
                this.trackVersion++;
                this.performanceMetrics.tracksCaptured = this.capturedTracks.size;

                // Notify the UI immediately that data has changed so it can schedule an efficient update.
                if (typeof window !== 'undefined') {
                    window.dispatchEvent(new CustomEvent('udio-dl-state-change'));
                }

                // --- 2. DEBOUNCED (DELAYED) ACTIONS ---
                // Clear any previously scheduled save to reset the timer.
                if (this.saveDebounceTimeout) {
                    clearTimeout(this.saveDebounceTimeout);
                }

                // Schedule the actual, expensive save operation to run after 1.5 seconds of inactivity.
                this.saveDebounceTimeout = setTimeout(() => {
                    try {
                        // This is the only place we write to GM storage for tracks.
                        GM_setValue('capturedTracks', JSON.stringify(Array.from(this.capturedTracks.entries())));
                        this.log(`💾 Debounced save complete. Stored ${this.capturedTracks.size} tracks.`);
                    } catch (error) {
                        this.error('Failed to save tracks during debounced operation:', error);
                    }
                }, 1500); // 1.5-second delay
            }

            saveProcessedIds() {
                if (this.isClearing) return;

                try {
                    var idCount = this.processedGenerationIds.size;
                    GM_setValue('processedGenerationIds', JSON.stringify([...this.processedGenerationIds]));

                    // TRIGGER UI UPDATE
                    if (typeof window !== 'undefined') {
                        window.dispatchEvent(new CustomEvent('udio-dl-state-change'));
                    }

                    if (idCount > 0 && idCount % 50 === 0) {
                        this.log(`📝 Saved ${idCount} processed generation IDs`);
                    }
                } catch (error) {
                    this.error('Failed to save processed IDs:', error);
                }
            }

            optimizeMemory() {
                var oneHourAgo = Date.now() - (60 * 60 * 1000);

                // Clear old processed URLs to prevent memory bloat
                var processedUrls = new Set(this.safeJSONParse(GM_getValue('processedUrls', '[]'), []));
                var urlsArray = Array.from(processedUrls);

                if (urlsArray.length > 1000) {
                    var trimmedUrls = urlsArray.slice(-500); // Keep last 500
                    GM_setValue('processedUrls', JSON.stringify(trimmedUrls));
                    this.log(`🧹 Memory: Trimmed processed URLs from ${urlsArray.length} to 500`);
                }

                // Warn about large collections but don't auto-delete user data
                if (this.capturedTracks.size > 200) {
                    this.log(`📊 Memory: Large track collection (${this.capturedTracks.size} tracks)`);
                }

                if (this.processedGenerationIds.size > 1000) {
                    this.log(`📊 Memory: Large processed ID set (${this.processedGenerationIds.size} IDs)`);
                }

                // Clean up any orphaned data
                this.cleanOrphanedData();
            }

            cleanOrphanedData() {
                try {
                    // Check for inconsistencies between tracks and processed IDs
                    var queue = this.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                    var failed = this.safeJSONParse(GM_getValue('failedUrls', '[]'), []);

                    var orphanedQueueItems = 0;
                    var orphanedFailedItems = 0;

                    // Basic validation of queue items
                    var validQueue = queue.filter(item => {
                        var isValid = item && item.url && getSongIdFromUrl(item.url);
                        if (!isValid) orphanedQueueItems++;
                        return isValid;
                    });

                    // Basic validation of failed items
                    var validFailed = failed.filter(item => {
                        var isValid = item && item.url && getSongIdFromUrl(item.url);
                        if (!isValid) orphanedFailedItems++;
                        return isValid;
                    });

                    if (orphanedQueueItems > 0 || orphanedFailedItems > 0) {
                        GM_setValue('urlQueue', JSON.stringify(validQueue));
                        GM_setValue('failedUrls', JSON.stringify(validFailed));
                        this.log(`🧹 Cleaned ${orphanedQueueItems} orphaned queue items and ${orphanedFailedItems} orphaned failed items`);
                    }
                } catch (error) {
                    this.error('Error cleaning orphaned data:', error);
                }
            }

            clearAllData() {
                this.log('🗑️ Clear All triggered. Halting operations and wiping data...');
                this.isClearing = true;

                // NEW: Stop ALL active operations immediately
                this.haltAllOperations();

                // Clear memory state
                this.capturedTracks.clear();
                this.processedGenerationIds.clear();
                this.activeRequests = 0;
                this.isProcessingQueue = false;
                this.isAddingToQueue = false;

                // NEW: Clear all manual selections
                if (window.UdioDownloaderUI) {
                    window.UdioDownloaderUI.manualSelectionsInProgress.clear();
                }

                // Clear persisted data - EXPANDED list
                var keysToClear = [
                    'isAutoCapturing', 'capturedTracks', 'urlQueue',
                    'failedUrls', 'processedUrls', 'processedGenerationIds',
                    'pendingManualSelections', 'lastQueueCelebration' // NEW
                ];

                keysToClear.forEach(key => {
                    GM_setValue(key, key === 'isAutoCapturing' ? false : '[]');
                });

                // Clear any DOM markers
                document.querySelectorAll('[data-udio-dl-processed]').forEach(el => {
                    el.removeAttribute('data-udio-dl-processed');
                });

                // NEW: Reset all UI states
                this.resetUIState();

                // Reset performance metrics (keep session time)
                var sessionDuration = this.getSessionDuration();
                this.performanceMetrics = {
                    scansCompleted: 0,
                    tracksCaptured: 0,
                    apiCalls: 0,
                    lastScanTime: 0,
                    totalDownloadSize: 0,
                    startupTime: Date.now()
                };

                this.log(`✅ All data cleared successfully. Previous session: ${sessionDuration}`);

                // NEW: Force immediate UI update
                setTimeout(() => {
                    this.log('🔄 Resuming normal operations.');
                    this.isClearing = false;

                    // Trigger comprehensive UI refresh
                    if (window.UdioDownloaderUI) {
                        window.UdioDownloaderUI.forceUIRefresh();
                        window.UdioDownloaderUI.showToast('All data cleared successfully', 'success', 3000);
                    }
                }, 500);
            }

            haltAllOperations() {
                // Stop all timeouts and intervals
                clearTimeout(this.scanTimeout);

                // Stop observer - FIX: Only call if method exists and observer is active
                if (typeof this.stopListObserver === 'function') {
                    this.stopListObserver();
                }

                // Stop auto-capture
                this.isAutoCapturing = false;
                GM_setValue('isAutoCapturing', false);

                // NEW: Stop scanner with proper error handling
                if (this.scanner && typeof this.scanner.stop === 'function') {
                    try {
                        this.scanner.stop();
                        this.log('🛑 Scanner stopped during halt operations');
                    } catch (error) {
                        this.error('Error stopping scanner:', error);
                    }
                } else {
                    this.debug('Scanner not available or stop method not found');
                }

                // NEW: Stop queue processing
                this.isProcessingQueue = false;
                this.isAddingToQueue = false;
                this.activeRequests = 0;

                // NEW: Stop tab coordinator if available
                if (this.tabCoordinator && typeof this.tabCoordinator.cleanup === 'function') {
                    try {
                        this.tabCoordinator.cleanup();
                        this.log('🛑 Tab coordinator cleaned up');
                    } catch (error) {
                        this.error('Error cleaning up tab coordinator:', error);
                    }
                }

                // NEW: Stop player observer if available
                if (this.playerObserver && typeof this.playerObserver.cleanup === 'function') {
                    try {
                        this.playerObserver.cleanup();
                        this.log('🛑 Player observer cleaned up');
                    } catch (error) {
                        this.error('Error cleaning up player observer:', error);
                    }
                }

                // NEW: Clear API handler caches if available
                if (this.apiHandler && typeof this.apiHandler.cleanup === 'function') {
                    try {
                        this.apiHandler.cleanup();
                        this.log('🛑 API handler caches cleared');
                    } catch (error) {
                        this.error('Error cleaning up API handler:', error);
                    }
                }

                // NEW: Clear UI intervals with comprehensive cleanup
                if (window.UdioDownloaderUI) {
                    // Clear render interval
                    if (window.UdioDownloaderUI.renderInterval) {
                        clearInterval(window.UdioDownloaderUI.renderInterval);
                        window.UdioDownloaderUI.renderInterval = null;
                    }

                    // Clear debounce timeouts
                    if (window.UdioDownloaderUI.renderDebounce) {
                        clearTimeout(window.UdioDownloaderUI.renderDebounce);
                        window.UdioDownloaderUI.renderDebounce = null;
                    }

                    // Clear scheduled refresh
                    if (window.UdioDownloaderUI._scheduledRefresh) {
                        clearTimeout(window.UdioDownloaderUI._scheduledRefresh);
                        window.UdioDownloaderUI._scheduledRefresh = null;
                    }

                    // Clear queued refresh
                    if (window.UdioDownloaderUI._queuedRefresh) {
                        clearTimeout(window.UdioDownloaderUI._queuedRefresh);
                        window.UdioDownloaderUI._queuedRefresh = null;
                    }

                    // Clear manual selections
                    if (window.UdioDownloaderUI.manualSelectionsInProgress) {
                        window.UdioDownloaderUI.manualSelectionsInProgress.clear();
                    }

                    // Clear event listeners
                    if (window.UdioDownloaderUI.eventListeners) {
                        window.UdioDownloaderUI.eventListeners.forEach(({ element, event, handler }) => {
                            try {
                                element.removeEventListener(event, handler);
                            } catch (e) {
                                // Silent fail for event listener removal
                            }
                        });
                        window.UdioDownloaderUI.eventListeners.clear();
                    }

                    this.log('🛑 UI components cleaned up');
                }

                // NEW: Clear any remaining timeouts in queue manager
                if (this.queueManager) {
                    // Stop any active queue processing
                    this.queueManager.clearQueue && this.queueManager.clearQueue();
                    this.log('🛑 Queue processing halted');
                }

                // NEW: Reset performance metrics
                this.performanceMetrics.activeRequests = 0;
                this.performanceMetrics.lastScanTime = 0;

                // NEW: Clear any DOM markers
                try {
                    document.querySelectorAll('[data-udio-dl-processed]').forEach(el => {
                        el.removeAttribute('data-udio-dl-processed');
                    });
                } catch (error) {
                    this.debug('Error clearing DOM markers:', error);
                }

                this.log('✅ All operations halted successfully');
            }

        /**
             * NEW: Reset UI state completely using the new optimized render calls.
             */
            resetUIState() {
                // Reset track version to force UI refresh
                this.trackVersion = 0;

                // --- START THE FIX ---
                // CRITICAL FIX: Instead of calling internal UI methods directly from the State class,
                // call the public, safe forceUIRefresh() method on the UI object. This prevents
                // TypeErrors if the UI's internal functions change and ensures a complete refresh.
                if (window.UdioDownloaderUI && window.UdioDownloaderUI.forceUIRefresh) {
                    window.UdioDownloaderUI.lastTrackVersion = -1; // Force a full list rebuild
                    window.UdioDownloaderUI.forceUIRefresh();
                }
                // --- END THE FIX ---
            }

            getSessionDuration() {
                var duration = Date.now() - this.sessionStartTime;
                var minutes = Math.floor(duration / 60000);
                var seconds = Math.floor((duration % 60000) / 1000);
                return `${minutes}m ${seconds}s`;
            }

            formatBytes(bytes) {
                if (bytes === 0) return '0 Bytes';
                var k = 1024;
                var sizes = ['Bytes', 'KB', 'MB', 'GB'];
                var i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }

            getTimestamp() {
                return new Date().toLocaleTimeString();
            }

            log(...args) {
                console.log(`${LOG_PREFIX} [${this.getTimestamp()}]`, ...args);
            }

            warn(...args) {
                console.warn(`${LOG_PREFIX} [${this.getTimestamp()}] ⚠️`, ...args);
            }

            error(...args) {
                console.error(`${LOG_PREFIX} [${this.getTimestamp()}] 🚨`, ...args);
            }

            debug(...args) {
                if (GM_getValue('debugMode', false)) {
                    console.debug(`${LOG_PREFIX} [${this.getTimestamp()}] 🔍`, ...args);
                }
            }

            safeJSONParse(jsonString, defaultValue) {
                try {
                    return JSON.parse(jsonString);
                } catch (error) {
                    this.debug('JSON parse error, using default:', error.message);
                    return defaultValue;
                }
            }

            extractBearerToken() {
                this.log('🔐 Extracting bearer token...');
                try {
                    var cookiePrefix = 'sb-ssr-production-auth-token.';
                    var cookies = document.cookie.split('; ').filter(row => row.trim().startsWith(cookiePrefix));

                    if (cookies.length === 0) {
                        this.warn('Authentication cookie not found');
                        return null;
                    }

                    // Sort cookies by their numeric part to ensure correct order
                    var fullEncodedToken = cookies
                    .sort((a, b) => {
                        var aNum = parseInt(a.split('.')[1]) || 0;
                        var bNum = parseInt(b.split('.')[1]) || 0;
                        return aNum - bNum;
                    })
                    .map(part => part.split('=')[1])
                    .join('');

                    if (!fullEncodedToken) {
                        this.warn('Empty authentication token');
                        return null;
                    }

                    // Handle base64 encoding variations
                    var cleanToken = fullEncodedToken.replace('base64-', '');
                    var tokenData = JSON.parse(atob(cleanToken));

                    if (tokenData?.access_token) {
                        this.log('✅ Successfully extracted authentication token');
                        return tokenData.access_token;
                    } else {
                        this.warn('Invalid token data structure');
                        return null;
                    }
                } catch (error) {
                    this.error('Failed to extract bearer token:', error);
                    return null;
                }
            }

            stopListObserver() {
                if (this.listObserver) {
                    this.log('👁️ Stopping page mutation observer...');
                    this.listObserver.disconnect();
                    this.listObserver = null;
                }
            }

            // Performance tracking methods
            trackScan(startTime) {
                const duration = performance.now() - startTime;
                this.performanceMetrics.scansCompleted++;
                this.performanceMetrics.lastScanTime = duration;

                // Only log every 50 scans instead of 20
                if (this.performanceMetrics.scansCompleted % 50 === 0) {
                    this.log(`📊 Performance: ${this.performanceMetrics.scansCompleted} scans, avg ${this.performanceMetrics.lastScanTime.toFixed(2)}ms`);
                }
            }

            trackApiCall() {
                this.performanceMetrics.apiCalls++;

                // Only log every 100 API calls instead of 50
                if (this.performanceMetrics.apiCalls % 100 === 0) {
                    this.log(`📊 Performance: ${this.performanceMetrics.apiCalls} API calls completed`);
                }
            }

            getPerformanceReport() {
                var sessionDuration = this.getSessionDuration();
                return {
                    sessionDuration,
                    tracksCaptured: this.performanceMetrics.tracksCaptured,
                    scansCompleted: this.performanceMetrics.scansCompleted,
                    apiCalls: this.performanceMetrics.apiCalls,
                    avgScanTime: this.performanceMetrics.lastScanTime.toFixed(2) + 'ms',
                    estimatedDownloadSize: this.formatBytes(this.performanceMetrics.totalDownloadSize),
                    activeRequests: this.activeRequests,
                    autoCaptureEnabled: this.isAutoCapturing
                };
            }

            // Utility method to check if we're in a good state
            isHealthy() {
                return !this.isClearing &&
                    this.activeRequests >= 0 &&
                    this.activeRequests < 100; // Sanity check
            }

            // Method to gracefully handle token expiration
            handleTokenExpiration() {
                this.log('🔄 Handling possible token expiration...');
                this.bearerToken = this.extractBearerToken();

                if (!this.bearerToken) {
                    this.warn('❌ Token refresh failed, disabling auto-capture');
                    this.isAutoCapturing = false;
                    GM_setValue('isAutoCapturing', false);
                    return false;
                }

                this.log('✅ Token refreshed successfully');
                return true;
            }

            /**
             * Remove "by Artist" suffix from playlist names
             */
            _removeByArtist(text) {
                if (!text || typeof text !== 'string') return text;

                // Remove "by ArtistName" pattern (case insensitive)
                const byArtistRegex = /\s+by\s+[A-Za-z0-9\s]+$/i;
                const cleaned = text.replace(byArtistRegex, '').trim();

                // Only return if we actually removed something and result is still valid
                if (cleaned !== text && cleaned.length >= 2) {
                    this.log(`[Context Clean] Removed "by Artist": "${text}" -> "${cleaned}"`);
                    return cleaned;
                }

                return text; // Return original if no change or result is too short
            }

            /**
             * Check if text is a valid playlist context
             */
            _isValidPlaylistContext(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 100) return false;

                // Exclude invalid values
                const invalidPatterns = [
                    'undefined', 'null', '...', '›', '>',
                    'My Library > My Library' // Specific spam case
                ];

                if (invalidPatterns.some(pattern => trimmed.includes(pattern))) {
                    return false;
                }

                // Must contain meaningful content
                const meaningfulText = trimmed.replace(/[-›>]/g, '').trim();
                if (meaningfulText.length < 2) return false;

                return true;
            }

            /**
             * Check if folder is a generic root that should be filtered out
             */
            _isGenericRootFolder(text) {
                if (!text || typeof text !== 'string') return false;

                const lowerText = text.toLowerCase().trim();

                const genericRoots = [
                    'my library', 'library', 'home', 'dashboard',
                    'main', 'root', 'udio', 'all songs', 'all tracks',
                    'back to library'
                ];

                return genericRoots.some(root => lowerText === root || lowerText.includes(root));
            }

            /**
             * Check if breadcrumb item is valid
             */
            _isValidBreadcrumbItem(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 50) return false;

                const lowerText = trimmed.toLowerCase();

                // Exclude UI elements and navigation items
                const excludePatterns = [
                    'toggle sidebar', 'chevron', 'arrow', 'back', 'home',
                    'menu', 'navigation', '...', 'more', '›', '>', '·',
                    'search', 'filter', 'open folder sidebar', 'open search', 'open filters'
                ];

                if (excludePatterns.some(pattern => lowerText.includes(pattern))) {
                    return false;
                }

                // Must contain meaningful characters
                if (!/[a-zA-Z0-9]/.test(trimmed)) {
                    return false;
                }

                return true;
            }
        }

        // ====================================================================================
        // --- NEW: TAB COORDINATION & BUFFER QUEUE SYSTEM ---
        // ====================================================================================

        class TabCoordinator {
            constructor(state) {
                this.state = state;
                this.tabId = this.generateTabId();
                this.isMaster = false;
                this.syncInterval = null;
                this.bufferQueue = [];
                this.lastLoggedContext = null;
                this.lastSignificantContext = null;
            }

            generateTabId() {
                return 'tab_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            }

            initialize() {
                this.state.log(`[TabCoordinator] Initializing tab ${this.tabId}`);
                this.claimMasterStatus();
                this.startSyncInterval();
                this.setupCrossTabListeners();
            }

            claimMasterStatus() {
                try {
                    const currentMaster = GM_getValue('queueMasterTab', null);
                    const masterTimestamp = GM_getValue('queueMasterTimestamp', 0);
                    const fifteenSecondsAgo = Date.now() - 15000; // Aggressive 15-second takeover

                    if (!currentMaster || masterTimestamp < fifteenSecondsAgo) {
                        GM_setValue('queueMasterTab', this.tabId);
                        GM_setValue('queueMasterTimestamp', Date.now());
                        this.isMaster = true;
                        this.state.log(`[TabCoordinator] 🎯 Claimed MASTER status for tab ${this.tabId}`);
                    } else if (currentMaster === this.tabId) {
                        GM_setValue('queueMasterTimestamp', Date.now());
                        this.isMaster = true;
                        this.state.log(`[TabCoordinator] 🔄 Renewed MASTER status for tab ${this.tabId}`);
                    } else {
                        this.isMaster = false;
                        this.state.log(`[TabCoordinator] 📡 Operating as SLAVE. Master is: ${currentMaster}`);
                    }
                } catch (error) {
                    this.state.error('[TabCoordinator] Error claiming master status:', error);
                    this.isMaster = false;
                }
            }

            startSyncInterval() {
                this.syncInterval = setInterval(() => {
                    this.maintainMasterStatus();
                    this.cleanupBufferQueue();
                }, 5000);
            }

            maintainMasterStatus() {
                if (this.isMaster) {
                    GM_setValue('queueMasterTimestamp', Date.now());
                } else {
                    const masterTimestamp = GM_getValue('queueMasterTimestamp', 0);
                    const thirtySecondsAgo = Date.now() - 30000;
                    if (masterTimestamp < thirtySecondsAgo) {
                        this.state.log('[TabCoordinator] Master appears stale, attempting to claim...');
                        this.claimMasterStatus();
                    }
                }
            }

            setupCrossTabListeners() {
                GM_addValueChangeListener('queueMasterTab', (key, oldVal, newVal, remote) => {
                    if (remote && newVal !== this.tabId) {
                        this.isMaster = false;
                        this.state.log(`[TabCoordinator] 📡 Now SLAVE to new master tab: ${newVal}`);
                    }
                });

                GM_addValueChangeListener('bufferQueue', (key, oldVal, newVal, remote) => {
                    if (remote) {
                        this.state.debug('[TabCoordinator] Buffer queue updated by another tab.');
                        if (this.isMaster) {
                            this.state.log('[TabCoordinator] Waking up to process buffer...');
                            setTimeout(() => this.state.queueManager.processQueue(), 250);
                        }
                    }
                });
            }

            /**
             * ENHANCED: Asynchronously adds an array of song URLs to a shared, cross-tab buffer queue.
             */
            async addToBufferQueue(urlsToAdd, isManualSelection, folderContext) {
                if (this.state.isClearing || !Array.isArray(urlsToAdd) || urlsToAdd.length === 0) return;

                let finalContext = folderContext;

                if (finalContext) {
                    finalContext = this._removeByArtist(finalContext);
                    this.state.log(`[TabCoordinator] Cleaned provided context: "${folderContext}" -> "${finalContext}"`);
                }

                if (!finalContext) {
                    finalContext = this.detectCurrentPageContext();
                    if (finalContext) {
                        finalContext = this._removeByArtist(finalContext);
                        this.state.log(`[TabCoordinator] Cleaned detected context: "${finalContext}"`);
                    }
                }

                if (finalContext === 'My Library') {
                    this.state.log(`[TabCoordinator] Capturing ${urlsToAdd.length} tracks from base library (no folder context)`);
                    finalContext = null;
                }

                if (finalContext && finalContext !== this.lastLoggedContext) {
                    const source = folderContext ? 'provided' : 'detected';
                    this.state.log(`[TabCoordinator] ${source} context: "${finalContext}" for ${urlsToAdd.length} items`);
                    this.lastLoggedContext = finalContext;
                } else if (!finalContext) {
                    this.state.debug(`[TabCoordinator] No context available for ${urlsToAdd.length} items`);
                }

                const itemsToAdd = urlsToAdd.map(url => ({
                    url: normalizeUrl(url),
                    isManual: isManualSelection,
                    folderContext: finalContext
                }));

                const existingBuffer = this.state.safeJSONParse(GM_getValue('bufferQueue', '[]'), []);
                const existingUrls = new Set(existingBuffer.map(item => item.url));
                const newUniqueItems = itemsToAdd.filter(item => !existingUrls.has(item.url));

                if (newUniqueItems.length === 0) return;

                const updatedBuffer = [...existingBuffer, ...newUniqueItems];
                GM_setValue('bufferQueue', JSON.stringify(updatedBuffer));

                if (newUniqueItems.length > 0) {
                    const contextInfo = finalContext ? ` with context "${finalContext}"` : ' without context';
                    if (newUniqueItems.length > 3) {
                        this.state.log(`[TabCoordinator] Added ${newUniqueItems.length} items${contextInfo}`);
                    } else {
                        this.state.debug(`[TabCoordinator] Added ${newUniqueItems.length} items${contextInfo}`);
                    }
                }

                if (this.isMaster) {
                    this.state.debug('[TabCoordinator] Triggering queue processing for new items');
                    setTimeout(() => {
                        if (this.state.queueManager && !this.state.isProcessingQueue) {
                            this.state.queueManager.processQueue();
                        }
                    }, 100);
                }
            }

            /**
             * Remove "by Artist" part from playlist names
             */
            _removeByArtist(text) {
                if (!text || typeof text !== 'string') return text;

                const byArtistRegex = /\s+by\s+[A-Za-z0-9\s]+$/i;
                const cleaned = text.replace(byArtistRegex, '').trim();

                if (cleaned !== text && cleaned.length >= 2) {
                    this.state.log(`[Context Clean] Removed "by Artist": "${text}" -> "${cleaned}"`);
                    return cleaned;
                }

                return text;
            }

            /**
             * Get playlist page context with proper detection
             */
            _getPlaylistPageContext() {
                try {
                    const titleSelectors = [
                        'h1.text-4xl', 'h1.text-2xl', 'h2.text-2xl',
                        '[data-testid="playlist-title"]', '[class*="playlist-title"]',
                        'img[alt*="playlist"]', 'div.flex.flex-col h4',
                        'div.mb-\\[50px\\] h4', 'div.flex.w-full.flex-col h4'
                    ];

                    for (const selector of titleSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            let text = '';

                            if (element.tagName === 'IMG' && element.alt) {
                                text = element.alt.trim();
                            } else if (element.textContent) {
                                text = element.textContent.trim();
                            }

                            if (text && this._isValidPlaylistContext(text)) {
                                this.state.log(`[Playlist Context] Found via "${selector}": "${text}"`);
                                return text;
                            }
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Playlist] Error:', error);
                    return null;
                }
            }

            /**
             * Direct breadcrumb context detection for TabCoordinator
             */
            _getBreadcrumbContextDirect() {
                try {
                    const breadcrumb = document.querySelector('div.-ml-4.flex.items-center');
                    if (breadcrumb) {
                        const buttons = Array.from(breadcrumb.querySelectorAll('button'));

                        if (buttons.length >= 3) {
                            const textElements = buttons.map(button => {
                                const text = button.textContent?.trim();
                                return text && text.length > 0 && this._isValidBreadcrumbItem(text) ? text : null;
                            }).filter(Boolean);

                            this.state.log(`[TabCoordinator Breadcrumb] Found buttons: ${JSON.stringify(textElements)}`);

                            if (textElements.length >= 2) {
                                const filteredElements = textElements.filter(text =>
                                    !this._isGenericRootFolder(text)
                                );

                                if (filteredElements.length >= 1) {
                                    const fullPath = filteredElements.join(' - ');
                                    this.state.log(`[TabCoordinator Breadcrumb] Full path: "${textElements.join(' > ')}" -> Cleaned: "${fullPath}"`);
                                    return fullPath;
                                } else if (textElements.length > 0) {
                                    const currentFolder = textElements[textElements.length - 1];
                                    this.state.log(`[TabCoordinator Breadcrumb] Using current folder only: "${currentFolder}"`);
                                    return currentFolder;
                                }
                            }
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[TabCoordinator Breadcrumb] Error:', error);
                    return null;
                }
            }

            /**
             * Detect context from current page when not provided
             */
            detectCurrentPageContext() {
                try {
                    const url = window.location.href;
                    const path = window.location.pathname;

                    if (path === '/library' && window.location.search) {
                        const urlParams = new URLSearchParams(window.location.search);
                        const filter = urlParams.get('filter');

                        if (filter) {
                            if (filter.startsWith('show.[') && filter.endsWith(']')) {
                                const contextType = filter.replace('show.[', '').replace(']', '');
                                const contextMap = {
                                    'liked': 'Liked Songs', 'recent': 'Recently Played',
                                    'created': 'My Creations', 'saved': 'Saved Songs',
                                    'playlists': 'My Playlists'
                                };

                                const context = contextMap[contextType] ||
                                            contextType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                                if (context && context.length > 1) {
                                    this.state.debug(`[TabCoordinator] Detected library context from filter: "${context}"`);
                                    return context;
                                }
                            }

                            if (filter.includes('liked')) return 'Liked Songs';
                            if (filter.includes('created')) return 'My Creations';
                            if (filter.includes('saved')) return 'Saved Songs';
                            if (filter.includes('recent')) return 'Recently Played';
                        }

                        const breadcrumb = document.querySelector('[class*="breadcrumb"], nav[aria-label*="breadcrumb"]');
                        if (breadcrumb) {
                            const buttons = breadcrumb.querySelectorAll('button, a');
                            if (buttons.length > 1) {
                                const currentFolder = buttons[buttons.length - 1].textContent?.trim();
                                if (currentFolder && this._isValidPlaylistContext(currentFolder)) {
                                    this.state.debug(`[TabCoordinator] Detected library folder from breadcrumb: "${currentFolder}"`);
                                    return currentFolder;
                                }
                            }
                        }
                    }

                    if (path.startsWith('/playlists/') || path.includes('/playlist/')) {
                        if (window.UdioDownloaderUI && window.UdioDownloaderUI.getPlaylistContext) {
                            const uiContext = window.UdioDownloaderUI.getPlaylistContext();
                            if (uiContext && this._isValidPlaylistContext(uiContext)) {
                                this.state.debug(`[TabCoordinator] Detected context from UI: "${uiContext}"`);
                                return uiContext;
                            }
                        }
                    }

                    const pageTitle = document.title;
                    if (pageTitle && pageTitle.includes('|')) {
                        const titleParts = pageTitle.split('|');
                        if (titleParts.length > 1) {
                            const possibleContext = titleParts[0].trim();
                            if (this._isValidPlaylistContext(possibleContext) && !possibleContext.includes('Udio')) {
                                this.state.debug(`[TabCoordinator] Detected context from page title: "${possibleContext}"`);
                                return possibleContext;
                            }
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[TabCoordinator] Error detecting page context:', error);
                    return null;
                }
            }

            /**
             * Check if text is a valid playlist context
             */
            _isValidPlaylistContext(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 100) return false;

                const invalidPatterns = [
                    'undefined', 'null', '...', '›', '>',
                    'My Library > My Library'
                ];

                if (invalidPatterns.some(pattern => trimmed.includes(pattern))) {
                    return false;
                }

                const meaningfulText = trimmed.replace(/[-›>]/g, '').trim();
                if (meaningfulText.length < 2) return false;

                return true;
            }

            /**
             * Check if folder is a generic root that should be filtered out
             */
            _isGenericRootFolder(text) {
                if (!text || typeof text !== 'string') return false;

                const lowerText = text.toLowerCase().trim();

                const genericRoots = [
                    'my library', 'library', 'home', 'dashboard',
                    'main', 'root', 'udio', 'all songs', 'all tracks',
                    'back to library'
                ];

                return genericRoots.some(root => lowerText === root || lowerText.includes(root));
            }

            /**
             * Check if breadcrumb item is valid
             */
            _isValidBreadcrumbItem(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 50) return false;

                const lowerText = trimmed.toLowerCase();

                const excludePatterns = [
                    'toggle sidebar', 'chevron', 'arrow', 'back', 'home',
                    'menu', 'navigation', '...', 'more', '›', '>', '·',
                    'search', 'filter', 'open folder sidebar', 'open search', 'open filters'
                ];

                if (excludePatterns.some(pattern => lowerText.includes(pattern))) {
                    return false;
                }

                if (!/[a-zA-Z0-9]/.test(trimmed)) {
                    return false;
                }

                return true;
            }

            /**
             * Check if text is likely a track title rather than a folder name
             */
            _isLikelyTrackTitle(text) {
                if (!text || typeof text !== 'string') return false;

                const lowerText = text.toLowerCase();

                const trackIndicators = [
                    'by ', 'feat.', 'ft.', 'vs.', ' - ', '–', '—',
                    'official', 'video', 'lyrics', 'remix', 'edit',
                    'mix', 'version', 'extended', 'radio'
                ];

                if (trackIndicators.some(indicator => lowerText.includes(indicator))) {
                    return true;
                }

                if (text.includes(' - ') || text.includes('–') || text.includes('—')) {
                    return true;
                }

                return false;
            }

            /**
             * NEW: Improved breadcrumb detection that handles nested folders and prevents log spam.
             */
            _getEnhancedBreadcrumbContext() {
                try {
                    // Strategy 1: Try multiple breadcrumb selectors
                    const breadcrumbContainers = [
                        ...document.querySelectorAll('div.-ml-4.flex.items-center'),
                        ...document.querySelectorAll('[class*="breadcrumb"]'),
                        ...document.querySelectorAll('nav[aria-label*="breadcrumb"]'),
                        ...document.querySelectorAll('.flex.items-center.space-x-2'),
                        ...document.querySelectorAll('div.flex.items-center')
                    ];

                    for (const breadcrumb of breadcrumbContainers) {
                        const pathElements = this._extractBreadcrumbPath(breadcrumb);
                        if (pathElements.length >= 2) {
                            const cleanedPath = this._cleanBreadcrumbPath(pathElements);
                            if (cleanedPath && this._isValidFolderContext(cleanedPath)) {
                                // --- START OF FIX ---
                                // Use the smart logger to only log when the context changes.
                                this._logContextDetection('breadcrumb (enhanced)', cleanedPath);
                                // --- END OF FIX ---
                                return cleanedPath;
                            }
                        }
                    }

                    // Strategy 2: Look for current folder context in page structure
                    const currentFolder = this._findCurrentFolderContext();
                    if (currentFolder && this._isValidFolderContext(currentFolder)) {
                        // --- START OF FIX ---
                        // Use the smart logger here as well to prevent spam.
                        this._logContextDetection('breadcrumb (current folder)', currentFolder);
                        // --- END OF FIX ---
                        return currentFolder;
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Enhanced Breadcrumb] Error:', error);
                    return null;
                }
            }

            /**
             * Extract meaningful path from breadcrumb
             */
            _extractBreadcrumbPath(breadcrumb) {
                const elements = Array.from(breadcrumb.querySelectorAll('button, a, [class*="button"], span'));
                const pathElements = [];

                for (const el of elements) {
                    const text = el.textContent?.trim();
                    if (text && text.length > 0 && this._isValidBreadcrumbItem(text)) {
                        pathElements.push(text);
                    }
                }

                return pathElements;
            }

            /**
             * Clean breadcrumb path by removing generic roots and building hierarchy
             */
            _cleanBreadcrumbPath(pathElements) {
                if (pathElements.length === 0) return null;

                const filteredElements = pathElements.filter(text =>
                    !this._isGenericRootFolder(text)
                );

                if (filteredElements.length === 0) {
                    return pathElements[pathElements.length - 1];
                }

                return filteredElements.join(' - ');
            }

            /**
             * Find current folder context from page structure
             */
            _findCurrentFolderContext() {
                try {
                    const folderIndicators = [
                        'h1', 'h2', 'h3', 'h4',
                        '[class*="current"]', '[class*="selected"]', '[class*="active"]',
                        '.flex.flex-col h4', 'div.mb-\\[50px\\] h4', 'div.flex.w-full.flex-col h4'
                    ];

                    for (const selector of folderIndicators) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            const text = el.textContent?.trim();
                            if (text && this._isValidPlaylistContext(text) && !this._isGenericRootFolder(text)) {
                                const cleanedText = this._removeByArtist(text);
                                if (cleanedText && cleanedText.length >= 2) {
                                    return cleanedText;
                                }
                            }
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Current Folder] Error:', error);
                    return null;
                }
            }

            /**
             * Check if folder context is valid
             */
            _isValidFolderContext(context) {
                if (!context || typeof context !== 'string') return false;

                const trimmed = context.trim();
                if (trimmed.length < 2 || trimmed.length > 80) return false;

                const invalidContexts = [
                    'My Library', 'My Library > My Library', 'Library',
                    'Home', 'undefined', 'null', '...', '›', '>'
                ];

                if (invalidContexts.includes(trimmed) || invalidContexts.some(invalid => trimmed.includes(invalid))) {
                    return false;
                }

                const meaningfulText = trimmed.replace(/[-›>]/g, '').trim();
                if (meaningfulText.length < 2) return false;

                if (this._isLikelyTrackTitle(trimmed)) {
                    return false;
                }

                return true;
            }

            /**
             * Clean breadcrumb cache periodically
             */
            _cleanBreadcrumbCache() {
                if (this._breadcrumbCache) {
                    this._breadcrumbCache.detectionCount = 0;
                    this.state.debug('[Breadcrumb] Cache cleaned');
                }
            }

                        /**
             * SIMPLE: Fallback breadcrumb detection with spam prevention.
             */
            _getSimpleBreadcrumbContext() {
                try {
                    const breadcrumbSelectors = [
                        'div.-ml-4.flex.items-center',
                        '[class*="breadcrumb"]',
                        'nav[aria-label*="breadcrumb"]'
                    ];

                    for (const selector of breadcrumbSelectors) {
                        const breadcrumb = document.querySelector(selector);
                        if (breadcrumb) {
                            const elements = Array.from(breadcrumb.querySelectorAll('button, a, span'));
                            const validElements = elements.map(el => el.textContent?.trim())
                                .filter(text => text && text.length > 0 && this._isValidBreadcrumbItem(text));

                            if (validElements.length >= 2) {
                                // Remove generic roots and get the meaningful path
                                const filtered = validElements.filter(text => !this._isGenericRootFolder(text));
                                if (filtered.length > 0) {
                                    const path = filtered.join(' - ');
                                    // Use the smart, anti-spam logger
                                    this._logContextDetection('breadcrumb (simple)', path);
                                    return path;
                                } else if (validElements.length > 0) {
                                    // Use last element if everything else was filtered
                                    const lastElement = validElements[validElements.length - 1];
                                    this._logContextDetection('breadcrumb (simple)', lastElement);
                                    return lastElement;
                                }
                            }
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Simple Breadcrumb] Error:', error);
                    return null;
                }
            }


            cleanupBufferQueue() {
                if (!this.isMaster) return;
                const buffer = this.state.safeJSONParse(GM_getValue('bufferQueue', '[]'), []);
                if (buffer.length === 0) return;

                const processedUrls = new Set(this.state.safeJSONParse(GM_getValue('processedUrls', '[]'), []));
                const mainQueueUrls = new Set(this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []).map(item => normalizeUrl(item.url)));

                const itemsToKeep = buffer.filter(item => {
                    const normalizedUrl = normalizeUrl(item.url);
                    return !processedUrls.has(normalizedUrl) && !mainQueueUrls.has(normalizedUrl);
                });

                if (itemsToKeep.length < buffer.length) {
                    this.state.log(`[TabCoordinator] Cleaned ${buffer.length - itemsToKeep.length} processed items from buffer.`);
                    GM_setValue('bufferQueue', JSON.stringify(itemsToKeep));
                }
            }

            cleanup() {
                if (this.syncInterval) clearInterval(this.syncInterval);
                if (this.isMaster && GM_getValue('queueMasterTab') === this.tabId) {
                    GM_setValue('queueMasterTab', null);
                    this.state.log(`[TabCoordinator] Released MASTER status.`);
                }
            }
        }

        // ====================================================================================
        // --- 3. UTILITY FUNCTIONS ---
        // ====================================================================================
        function sanitizeForWindows(name) {
            if (!name) {
                return 'Unknown';
            }
            // Replace all invalid characters with an underscore.
            // Condense multiple spaces to one, and trim whitespace.
            // Remove leading/trailing dots which are invalid in Windows.
            return name.replace(/[<>:"/\\|?*]/g, '_')
                    .replace(/\s+/g, ' ')
                    .trim()
                    .replace(/^\.+|\.+$/g, '');
        }

        function normalizeUrl(url) {
            try { var urlObj = new URL(url); return urlObj.origin + urlObj.pathname.replace(/\/+$/, ''); }
            catch { return url; }
        }

        function getSongIdFromUrl(url) {
            try { var match = url.match(/\/songs\/([a-zA-Z0-9]+)/); return match ? match[1] : null; }
            catch { return null; }
        }

        function camelToUpperSnake(str) {
            if (!str) return '';
            return str.replace(/([A-Z])/g, '_$1').toUpperCase();
        }

        /**
         * Asynchronously finds the playlist context by polling the DOM.
         * This is more resilient to dynamic page loading than a single, immediate check.
         * @param {number} timeout - The maximum time to wait in milliseconds.
         * @returns {Promise<string|null>} A promise that resolves with the playlist name or null.
         */
        function findPlaylistContextAsync(timeout = 4000) {
            return new Promise(resolve => {
                const startTime = Date.now();
                const interval = setInterval(() => {
                    const context = UI.getPlaylistContext ? UI.getPlaylistContext() : null;
                    if (context) {
                        clearInterval(interval);
                        resolve(context);
                    } else if (Date.now() - startTime > timeout) {
                        clearInterval(interval);
                        resolve(null); // Resolve with null if not found after the timeout
                    }
                }, 250); // Check every 250ms
            });
        }

        function promisifiedGmDownload(options) {
            return new Promise((resolve, reject) => {
                GM_download({
                    ...options,
                    onload: () => resolve(),
                    onerror: (error) => reject(new Error(`Download failed: ${error.details || error}`)),
                    ontimeout: () => reject(new Error('Download timed out'))
                });
            });
        }

        function getSongIdFromTrack(track) {
            if (!track) return null;
            return track.id || getSongIdFromUrl(track.songPageUrl) || track.generationId;
        }

        // ====================================================================================
        // --- 4. API HANDLING - SILENT & EFFICIENT ---
        // ====================================================================================

        class ApiHandler {
            constructor(state) {
                this.state = state;
                this.albumArtCache = new Map();
                this.videoUrlCache = new Map();
                this.apiResponseCache = new Map();
                this.rateLimitTracker = {
                    requests: 0,
                    windowStart: Date.now(),
                    lastRetry: 0
                };
                this.consecutiveFailures = 0;
                this.maxConsecutiveFailures = 5;
                this.processedCount = 0;
                this.lastLogCount = 0;
                this.metadataSamplesLogged = new Set(); // Track which songs we've logged samples for

                // 🆕 NEW DEBUGGING COUNTERS
                this.completeLogCount = 0;
                this.relationshipLogCount = 0;
                this.completenessLogCount = 0;
            }

            async fetchSongData(songId, retryCount = 0) {
                // Enhanced rate limiting and failure tracking
                if (this.shouldRateLimit()) {
                    await this.delay(1000);
                }

                // Check cache first with enhanced validation
                var cachedResponse = this.getCachedResponse(songId);
                if (cachedResponse) {
                    return cachedResponse;
                }

                return new Promise((resolve, reject) => {
                    if (!this.state.bearerToken) {
                        var error = new Error('No authentication token available');
                        reject(error);
                        return;
                    }

                    this.trackRateLimit();

                    GM_xmlhttpRequest({
                        method: 'GET',
                        url: `https://www.udio.com/api/songs?songIds=${songId}`,
                        headers: {
                            'Authorization': `Bearer ${this.state.bearerToken}`,
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        },
                        responseType: 'json',
                        timeout: CONFIG.API_TIMEOUT,
                        onload: (response) => {
                            this.state.trackApiCall();
                            this.handleApiResponse(response, songId, resolve, reject, retryCount);
                        },
                        onerror: (response) => {
                            this.handleApiError(response, songId, reject, retryCount);
                        },
                        ontimeout: () => {
                            this.handleApiTimeout(songId, reject, retryCount);
                        }
                    });
                });
            }

            shouldRateLimit() {
                var now = Date.now();
                var windowMs = 60000; // 1 minute window

                // Reset counter if window expired
                if (now - this.rateLimitTracker.windowStart > windowMs) {
                    this.rateLimitTracker.requests = 0;
                    this.rateLimitTracker.windowStart = now;
                }

                // Enhanced rate limiting: max 30 requests per minute
                if (this.rateLimitTracker.requests >= 30) {
                    return true;
                }

                // Consecutive failure backoff
                if (this.consecutiveFailures > 0) {
                    var backoffDelay = Math.min(1000 * Math.pow(2, this.consecutiveFailures), 30000);
                    if (now - this.rateLimitTracker.lastRetry < backoffDelay) {
                        return true;
                    }
                }

                return false;
            }

            trackRateLimit() {
                this.rateLimitTracker.requests++;
            }

            getCachedResponse(songId) {
                var cached = this.apiResponseCache.get(songId);
                if (cached && Date.now() - cached.timestamp < 300000) { // 5 minute cache
                    return cached.data;
                }
                return null;
            }

            cacheResponse(songId, data) {
                this.apiResponseCache.set(songId, {
                    data: data,
                    timestamp: Date.now()
                });

                // Clean old cache entries
                if (this.apiResponseCache.size > 100) {
                    var oldestKey = Array.from(this.apiResponseCache.entries())
                    .reduce((oldest, [key, value]) =>
                            value.timestamp < oldest.timestamp ? {key, ...value} : oldest
                        );
                    this.apiResponseCache.delete(oldestKey.key);
                }
            }

            cleanup() {
                // Clear old cache entries
                const now = Date.now();
                const maxAge = 30 * 60 * 1000; // 30 minutes

                for (const [key, value] of this.apiResponseCache.entries()) {
                    if (now - value.timestamp > maxAge) {
                        this.apiResponseCache.delete(key);
                    }
                }

                // Limit cache sizes
                if (this.albumArtCache.size > 50) {
                    const entries = Array.from(this.albumArtCache.entries());
                    this.albumArtCache = new Map(entries.slice(-50));
                }

                if (this.videoUrlCache.size > 50) {
                    const entries = Array.from(this.videoUrlCache.entries());
                    this.videoUrlCache = new Map(entries.slice(-50));
                }

                // Clean up metadata samples log
                if (this.metadataSamplesLogged.size > 1000) {
                    const samplesArray = Array.from(this.metadataSamplesLogged);
                    this.metadataSamplesLogged = new Set(samplesArray.slice(-500));
                }

                this.state.log('[ApiHandler] Cache cleanup completed');
            }

            /**
             * ENHANCED: Handle API response with complete debugging
             */
            handleApiResponse(response, songId, resolve, reject, retryCount) {
                if (response.status === 401) {
                    this.handleTokenExpiration(songId, resolve, reject, retryCount);
                    return;
                }

                if (response.status === 429) {
                    this.handleRateLimit(songId, resolve, reject, retryCount);
                    return;
                }

                if (response.status >= 200 && response.status < 300) {
                    this.consecutiveFailures = 0; // Reset failure counter on success

                    if (response.response) {
                        // 🆕 LOG COMPLETE API RESPONSE FOR DEBUGGING
                        this.logCompleteApiResponse(response.response, songId);

                        this.cacheResponse(songId, response.response);
                        resolve(response.response);
                    } else {
                        reject(new Error('Empty API response'));
                    }
                } else {
                    this.consecutiveFailures++;
                    reject(new Error(`HTTP ${response.status}: ${response.statusText}`));
                }
            }

            /**
             * OPTIMIZED: Log essential API response data - minimal debugging
             */
            logCompleteApiResponse(responseJson, songId) {
                // Only log for the VERY first song to avoid console spam
                if (this.completeLogCount < 1) {
                    this.completeLogCount++;

                    console.groupCollapsed(`%c[UDIO-DL] 🧩 API RESPONSE for ${songId}`, 'color: #FF6B6B; font-weight: bold; font-size: 14px');

                    if (responseJson && responseJson.songs && responseJson.songs.length > 0) {
                        const song = responseJson.songs.find(s => s.id === songId) || responseJson.songs[0];

                        // Log only essential properties
                        console.log('🔍 ESSENTIAL PROPERTIES:');
                        const essentialFields = [
                            'title', 'artist', 'id', 'generation_id',
                            'song_path', 'video_path', 'image_path',
                            'lyrics', 'prompt', 'created_at'
                        ];

                        essentialFields.forEach(field => {
                            if (song[field]) {
                                const value = field === 'lyrics' || field === 'prompt' ?
                                    `${song[field].substring(0, 80)}...` : song[field];
                                console.log(`  ${field}:`, value);
                            }
                        });

                        // Quick relationship check
                        console.log('🔗 RELATIONSHIPS:');
                        if (song.parent_id) console.log('  Parent:', song.parent_id);
                        if (song.child_songs) console.log('  Children:', song.child_songs.length);
                        if (song.style_source_song_id) console.log('  Style Source:', song.style_source_song_id);

                        // Media availability
                        console.log('🎵 MEDIA:');
                        console.log('  Audio:', !!song.song_path);
                        console.log('  Video:', !!song.video_path);
                        console.log('  Artwork:', !!song.image_path);

                        // Quick stats
                        console.log('📊 STATS:');
                        if (song.plays !== undefined) console.log('  Plays:', song.plays);
                        if (song.likes !== undefined) console.log('  Likes:', song.likes);

                    } else {
                        console.warn('❌ No song data found in API response');
                    }

                    console.groupEnd();

                    // Log one-time message about reduced debugging
                    if (this.completeLogCount === 1) {
                        console.log('%c[UDIO-DL] 🔕 Debug logging reduced. Future API responses will be processed silently.', 'color: #888; font-style: italic;');
                    }
                }
            }

            handleTokenExpiration(songId, resolve, reject, retryCount) {
                if (retryCount >= 2) {
                    reject(new Error('Token refresh failed after retries'));
                    return;
                }

                if (this.state.handleTokenExpiration()) {
                    setTimeout(() => {
                        this.fetchSongData(songId, retryCount + 1)
                            .then(resolve)
                            .catch(reject);
                    }, 1000);
                } else {
                    reject(new Error('Authentication token refresh failed'));
                }
            }

            handleRateLimit(songId, resolve, reject, retryCount) {
                if (retryCount >= 3) {
                    reject(new Error('Rate limit exceeded after retries'));
                    return;
                }

                var backoffTime = Math.min(1000 * Math.pow(2, retryCount), 30000);

                setTimeout(() => {
                    this.fetchSongData(songId, retryCount + 1)
                        .then(resolve)
                        .catch(reject);
                }, backoffTime);
            }

            handleApiError(response, songId, reject, retryCount) {
                this.consecutiveFailures++;
                this.rateLimitTracker.lastRetry = Date.now();

                if (retryCount < CONFIG.MAX_RETRIES) {
                    setTimeout(() => {
                        this.fetchSongData(songId, retryCount + 1)
                            .catch(reject);
                    }, 500 * Math.pow(2, retryCount));
                } else {
                    reject(new Error(`Request error: ${response.statusText}`));
                }
            }

            handleApiTimeout(songId, reject, retryCount) {
                this.consecutiveFailures++;
                this.rateLimitTracker.lastRetry = Date.now();

                if (retryCount < CONFIG.MAX_RETRIES) {
                    setTimeout(() => {
                        this.fetchSongData(songId, retryCount + 1)
                            .catch(reject);
                    }, 500 * Math.pow(2, retryCount));
                } else {
                    reject(new Error('Request timeout'));
                }
            }

            delay(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }

            parseAndValidateSong(responseJson, requestedSongId) {
                if (!responseJson || !responseJson.songs || responseJson.songs.length === 0) {
                    return null;
                }

                // Enhanced song matching with fallbacks
                var song = responseJson.songs.find(s => s.id === requestedSongId) || responseJson.songs[0];

                if (!song) {
                    return null;
                }

                return this.validateSongData(song);
            }

            validateSongData(song) {
                // Enhanced validation with detailed error reporting
                if (!song.song_path || !song.generation_id) {
                    return null;
                }

                // SILENT metadata extraction
                var fullInfo = this.extractCompleteMetadata(song);

                return {
                    audioUrl: song.song_path,
                    videoUrl: this.extractVideoUrl(song),
                    generationId: song.generation_id,
                    fullInfo: fullInfo
                };
            }

            extractCompleteMetadata(song) {
                // Safe extraction with comprehensive field coverage
                var safeGet = (obj, path, defaultValue = null) => {
                    return path.split('.').reduce((acc, part) => acc && acc[part], obj) || defaultValue;
                };

                // Extract tags with enhanced processing
                var tags = this.extractTags(song);

                // Core metadata with enhanced validation
                var metadata = {
                    // Core identification
                    id: song.id,
                    title: safeGet(song, 'title', 'Untitled'),
                    artist: safeGet(song, 'artist', 'Unknown Artist'),
                    creationDate: this.formatCreationDate(safeGet(song, 'created_at')),
                    songPageUrl: `https://www.udio.com/songs/${song.id}`,

                    // Media assets - USE THE ALBUM ART WE EXTRACTED
                    albumArt: this.extractAlbumArt(song),
                    videoUrl: this.extractVideoUrl(song),
                    audioUrl: song.song_path,

                    // Content information
                    lyrics: safeGet(song, 'lyrics'),
                    prompt: safeGet(song, 'prompt'),
                    tags: tags,

                    // Statistics
                    plays: safeGet(song, 'plays', 0),
                    likes: safeGet(song, 'likes', 0),
                };

                // Enhanced conditional field inclusion with categorization
                this.addConditionalFields(metadata, song);

                // Add technical metadata
                this.addTechnicalMetadata(metadata, song);

                // Add user and social data
                this.addUserMetadata(metadata, song);

                // ==================================================================
                // --- ENHANCED: CAPTURE PARENT/CHILD RELATIONSHIPS AND CHAINS ---
                // ==================================================================
                this.addRelationshipMetadata(metadata, song);

                // ==================================================================
                // --- ENHANCED: LOG RELATIONSHIP METADATA FOR DEBUGGING ---
                // ==================================================================
                this.logRelationshipMetadata(metadata, song);

                // ==================================================================
                // --- NEW: LOG SAMPLE OF CAPTURED METADATA FOR VERIFICATION ---
                // ==================================================================
                this.logMetadataSample(metadata, song.id);

                // ==================================================================
                // --- NEW: Catch-all for any remaining metadata to prevent loss ---
                // ==================================================================
                this.addRemainingMetadata(metadata, song);

                // ==================================================================
                // --- ENHANCED: LOG METADATA COMPLETENESS ---
                // ==================================================================
                this.logMetadataCompleteness(metadata, song);

                return metadata;
            }

            /**
             * NEW: Capture parent/child relationships and derivation chains
             */
            addRelationshipMetadata(metadata, song) {
                // Parent relationship (if this is a remix/derivative)
                if (song.parent_id) {
                    metadata.parentId = song.parent_id;
                    metadata.relationshipType = 'child';

                    // Try to get parent song details if available in the response
                    if (song.parent_song) {
                        metadata.parentSong = {
                            id: song.parent_song.id,
                            title: song.parent_song.title,
                            artist: song.parent_song.artist,
                            url: `https://www.udio.com/songs/${song.parent_song.id}`
                        };
                    }
                }

                // Child relationships (if this song has remixes/derivatives)
                if (song.child_songs && Array.isArray(song.child_songs) && song.child_songs.length > 0) {
                    metadata.childSongs = song.child_songs.map(child => ({
                        id: child.id,
                        title: child.title,
                        artist: child.artist,
                        url: `https://www.udio.com/songs/${child.id}`
                    }));
                    metadata.relationshipType = metadata.relationshipType ? 'both' : 'parent';
                }

                // Style/source relationships
                if (song.style_source_song_id) {
                    metadata.styleSourceSongId = song.style_source_song_id;
                    metadata.styleSourceType = song.style_source_type;

                    // If style source song data is included
                    if (song.style_source_song) {
                        metadata.styleSourceSong = {
                            id: song.style_source_song.id,
                            title: song.style_source_song.title,
                            artist: song.style_source_song.artist
                        };
                    }
                }

                // Generation chain (for extended/reworked tracks)
                if (song.generation_chain) {
                    metadata.generationChain = song.generation_chain;
                }

                // Variants and alternative versions
                if (song.variants && Array.isArray(song.variants)) {
                    metadata.variants = song.variants.map(variant => ({
                        id: variant.id,
                        type: variant.variant_type,
                        audioUrl: variant.song_path,
                        videoUrl: variant.video_path,
                        duration: variant.duration
                    }));
                }

                // Collaboration information
                if (song.collaborators && Array.isArray(song.collaborators)) {
                    metadata.collaborators = song.collaborators.map(collab => ({
                        userId: collab.user_id,
                        displayName: collab.user_display_name,
                        role: collab.role
                    }));
                }

                // Collection/album context
                if (song.collection_id) {
                    metadata.collectionId = song.collection_id;
                    metadata.collectionPosition = song.collection_position;
                }

                // Session context (for multi-part generations)
                if (song.session_id) {
                    metadata.sessionId = song.session_id;
                }

                // Additional relationship metadata that might be present
                if (song.original_song_id) {
                    metadata.originalSongId = song.original_song_id;
                }

                if (song.derivative_works && Array.isArray(song.derivative_works)) {
                    metadata.derivativeWorks = song.derivative_works.map(work => ({
                        id: work.id,
                        title: work.title,
                        type: work.work_type
                    }));
                }
            }

            /**
             * OPTIMIZED: Log relationship metadata - minimal debugging
             */
            logRelationshipMetadata(metadata, song) {
                const hasRelationships = metadata.parentId || metadata.childSongs || metadata.styleSourceSongId;

                // Only log for the first 1 song total
                if (hasRelationships && this.relationshipLogCount < 1) {
                    this.relationshipLogCount++;

                    console.groupCollapsed(`%c[UDIO-DL] 🔗 Relationships for ${song.id}`, 'color: #4ECDC4; font-weight: bold;');

                    if (metadata.parentId) {
                        console.log('👨‍👦 Parent:', metadata.parentId);
                    }

                    if (metadata.childSongs) {
                        console.log('👶 Children:', metadata.childSongs.length);
                    }

                    if (metadata.styleSourceSongId) {
                        console.log('🎨 Style Source:', metadata.styleSourceSongId);
                    }

                    console.groupEnd();

                    // Log one-time message
                    if (this.relationshipLogCount === 1) {
                        console.log('%c[UDIO-DL] 🔕 Relationship logging reduced. Future relationships will be processed silently.', 'color: #888; font-style: italic;');
                    }
                }
            }

            /**
             * OPTIMIZED: Log essential metadata sample - minimal debugging
             */
            logMetadataSample(metadata, songId) {
                // Only log for the first 2 songs total, then stop completely
                if (this.metadataSamplesLogged.size < 2 && !this.metadataSamplesLogged.has(songId)) {
                    this.metadataSamplesLogged.add(songId);

                    console.groupCollapsed(`%c[UDIO-DL] Metadata for ${songId}`, 'color: #4CAF50; font-weight: bold');

                    // Essential metadata only
                    console.log('📝 Core:', {
                        title: metadata.title,
                        artist: metadata.artist,
                        id: metadata.id
                    });

                    // Quick media status
                    console.log('🎵 Media:', {
                        audio: !!metadata.audioUrl,
                        video: !!metadata.videoUrl,
                        artwork: !!metadata.albumArt,
                        lyrics: !!metadata.lyrics,
                        prompt: !!metadata.prompt
                    });

                    // Quick relationship summary
                    const hasRelationships = metadata.parentId || metadata.childSongs || metadata.styleSourceSongId;
                    if (hasRelationships) {
                        console.log('🔗 Relationships:', {
                            parent: !!metadata.parentId,
                            children: metadata.childSongs ? metadata.childSongs.length : 0,
                            styleSource: !!metadata.styleSourceSongId
                        });
                    }

                    // Basic completeness
                    const completeness = this.trackMetadataCompleteness(metadata);
                    console.log(`📊 ${Math.round(completeness * 100)}% complete`);

                    console.groupEnd();

                    // Log one-time message about reduced samples
                    if (this.metadataSamplesLogged.size === 2) {
                        console.log('%c[UDIO-DL] 🔕 Metadata samples reduced. Future tracks will be processed silently.', 'color: #888; font-style: italic;');
                    }
                }
            }

            /**
             * ENHANCED: Log metadata completeness with field analysis
             */
            logMetadataCompleteness(metadata, song) {
                const fieldAnalysis = {
                    'Core Identification': ['id', 'title', 'artist', 'creationDate', 'songPageUrl'],
                    'Media Assets': ['audioUrl', 'albumArt', 'videoUrl'],
                    'Content': ['lyrics', 'prompt', 'tags'],
                    'Statistics': ['plays', 'likes'],
                    'Relationships': ['parentId', 'childSongs', 'styleSourceSongId'],
                    'Technical': ['generationId', 'duration', 'bpm']
                };

                let completenessReport = {};
                let totalFields = 0;
                let capturedFields = 0;

                Object.entries(fieldAnalysis).forEach(([category, fields]) => {
                    const categoryFields = fields.filter(field => metadata[field] !== undefined && metadata[field] !== null);
                    completenessReport[category] = {
                        captured: categoryFields.length,
                        total: fields.length,
                        percentage: Math.round((categoryFields.length / fields.length) * 100)
                    };
                    totalFields += fields.length;
                    capturedFields += categoryFields.length;
                });

                const overallPercentage = Math.round((capturedFields / totalFields) * 100);

                if (this.completenessLogCount < 2) {
                    this.completenessLogCount++;

                    console.groupCollapsed(`%c[UDIO-DL] 📊 METADATA COMPLETENESS: ${overallPercentage}% for ${song.id}`, 'color: #FFD93D; font-weight: bold;');
                    console.log('Overall:', `${capturedFields}/${totalFields} fields captured (${overallPercentage}%)`);

                    Object.entries(completenessReport).forEach(([category, stats]) => {
                        const icon = stats.percentage >= 80 ? '✅' : stats.percentage >= 50 ? '⚠️' : '❌';
                        console.log(`${icon} ${category}: ${stats.captured}/${stats.total} (${stats.percentage}%)`);
                    });

                    // Log missing important fields
                    const importantMissing = [];
                    if (!metadata.parentId && song.parent_id) importantMissing.push('parent_id');
                    if (!metadata.childSongs && song.child_songs) importantMissing.push('child_songs');
                    if (!metadata.styleSourceSongId && song.style_source_song_id) importantMissing.push('style_source_song_id');

                    if (importantMissing.length > 0) {
                        console.warn('🚨 IMPORTANT RELATIONSHIPS MISSING:', importantMissing);
                    }

                    console.groupEnd();
                }

                return overallPercentage;
            }

            /**
             * NEW: Track metadata completeness for quality assurance
             */
            trackMetadataCompleteness(metadata) {
                const checks = {
                    hasBasic: !!(metadata.title && metadata.artist && metadata.id),
                    hasTechnical: !!(metadata.generationId || metadata.duration),
                    hasMedia: !!(metadata.audioUrl || metadata.albumArt),
                    hasContent: !!(metadata.prompt || metadata.lyrics || metadata.tags),
                    hasRelationships: !!(metadata.parentId || metadata.childSongs || metadata.styleSourceSongId || metadata.sessionId)
                };

                const completeness = Object.values(checks).filter(Boolean).length / Object.values(checks).length;

                if (completeness < 0.6) {
                    this.state.warn(`Low metadata completeness (${Math.round(completeness * 100)}%) for: "${metadata.title}"`);
                    console.log('Missing field categories:', Object.entries(checks).filter(([_, has]) => !has).map(([cat, _]) => cat));
                }

                return completeness;
            }

            /**
             * NEW METHOD: Ensures no metadata is discarded
             */
            addRemainingMetadata(metadata, song) {
                const explicitlyHandled = new Set([
                    'id', 'title', 'artist', 'created_at', 'song_path', 'image_path',
                    'video_path', 'lyrics', 'prompt', 'tags', 'plays', 'likes',
                    'parent_id', 'parent_song', 'child_songs', 'style_source_song_id',
                    'style_source_type', 'style_source_song', 'generation_chain',
                    'variants', 'collaborators', 'collection_id', 'collection_position',
                    'session_id', 'generation_id', 'duration', 'bpm', 'key', 'genre',
                    'mood', 'tempo', 'energy', 'danceability', 'valence',
                    'audio_conditioning_type', 'style_id', 'style_source_type', 'user_id',
                    'user_display_name', 'finished', 'publishable', 'disliked', 'published_at',
                    'description', 'attribution', 'user_tags', 'replaced_tags', 'instruments',
                    'audio_features', 'error_code', 'error_detail', 'error_type',
                    'original_song_id', 'derivative_works', 'original_song_path',
                    'cover_image', 'album_art', 'artist_image'
                ]);

                for (var key in song) {
                    if (Object.prototype.hasOwnProperty.call(song, key) &&
                        !explicitlyHandled.has(key) &&
                        !Object.prototype.hasOwnProperty.call(metadata, key)) {

                        var value = song[key];

                        // Only add meaningful values (not null, undefined, empty arrays/objects)
                        if (value !== null && value !== undefined && value !== '') {
                            if (Array.isArray(value) && value.length > 0) {
                                metadata[key] = value;
                            } else if (typeof value === 'object' && value !== null && Object.keys(value).length > 0) {
                                metadata[key] = value;
                            } else if (typeof value !== 'object') {
                                metadata[key] = value;
                            }
                        }
                    }
                }

                // Special handling for nested objects that might contain additional metadata
                if (song.metadata && typeof song.metadata === 'object') {
                    for (var metaKey in song.metadata) {
                        if (!metadata[metaKey] && song.metadata[metaKey] !== undefined) {
                            metadata[metaKey] = song.metadata[metaKey];
                        }
                    }
                }

                // Handle additional_info if present
                if (song.additional_info && typeof song.additional_info === 'object') {
                    for (var infoKey in song.additional_info) {
                        if (!metadata[infoKey] && song.additional_info[infoKey] !== undefined) {
                            metadata[infoKey] = song.additional_info[infoKey];
                        }
                    }
                }
            }

            formatCreationDate(dateString) {
                if (!dateString) return 'Unknown';

                try {
                    var date = new Date(dateString);
                    return date.toLocaleString();
                } catch (error) {
                    return dateString || 'Unknown';
                }
            }

            addConditionalFields(metadata, song) {
                var conditionalFields = {
                    // Attribution and description
                    attribution: 'attribution',
                    description: 'description',

                    // Audio properties
                    duration: 'duration',
                    bpm: 'bpm',
                    key: 'key',
                    genre: 'genre',
                    mood: 'mood',
                    tempo: 'tempo',
                    energy: 'energy',
                    danceability: 'danceability',
                    valence: 'valence',

                    // Additional content
                    originalSongPath: 'original_song_path',
                    parentId: 'parent_id',
                    publishedAt: 'published_at',
                    replacedTags: 'replaced_tags',
                    userTags: 'user_tags',

                    // Collections
                    instruments: 'instruments',
                    audioFeatures: 'audio_features',

                    // Artist information
                    artistImage: 'artist_image'
                };

                for (var [field, source] of Object.entries(conditionalFields)) {
                    var value = song[source];
                    if (value !== undefined && value !== null && value !== '') {
                        if (Array.isArray(value) && value.length > 0) {
                            metadata[field] = value;
                        } else if (!Array.isArray(value)) {
                            metadata[field] = value;
                        }
                    }
                }
            }

            addTechnicalMetadata(metadata, song) {
                var technicalFields = {
                    generationId: 'generation_id',
                    audioConditioningType: 'audio_conditioning_type',
                    styleId: 'style_id',
                    styleSourceType: 'style_source_type',
                    styleSourceSongId: 'style_source_song_id',
                    userId: 'user_id',
                    userDisplayName: 'user_display_name'
                };

                for (var [field, source] of Object.entries(technicalFields)) {
                    var value = song[source];
                    if (value !== undefined && value !== null) {
                        metadata[field] = value;
                    }
                }

                // Boolean fields with explicit checks
                var booleanFields = {
                    disliked: 'disliked',
                    finished: 'finished',
                    publishable: 'publishable'
                };

                for (var [field, source] of Object.entries(booleanFields)) {
                    if (source in song) {
                        metadata[field] = song[source];
                    }
                }
            }

            addUserMetadata(metadata, song) {
                // Error information
                if (song.error_code || song.error_detail || song.error_type) {
                    metadata.errorInfo = {
                        code: song.error_code,
                        detail: song.error_detail,
                        type: song.error_type
                    };
                }

                // User engagement metrics
                if (song.user_id) {
                    metadata.userInfo = {
                        id: song.user_id,
                        displayName: song.user_display_name
                    };
                }

                // Additional user context if available
                if (song.user_context) {
                    metadata.userContext = song.user_context;
                }
            }

            extractTags(song) {
                if (!song.tags) return [];

                try {
                    return song.tags
                        .map(tag => {
                        if (typeof tag === 'object' && tag.tag) {
                            return String(tag.tag).trim();
                        }
                        return String(tag).trim();
                    })
                        .filter(tag => tag && tag !== '' && tag !== 'undefined' && tag !== 'null')
                        .slice(0, 50); // Limit to prevent excessive data
                } catch (error) {
                    return [];
                }
            }

            // PERFECTED ALBUM ART EXTRACTION - SIMPLE AND RELIABLE
            extractAlbumArt(song) {
                // PRIORITY 1: Direct image_path from API (primary album art)
                if (song.image_path && this.isValidImageUrl(song.image_path)) {
                    return this.ensureOptimalFormat(song.image_path);
                }

                // PRIORITY 2: Cover image fallback
                if (song.cover_image && this.isValidImageUrl(song.cover_image)) {
                    return this.ensureOptimalFormat(song.cover_image);
                }

                // PRIORITY 3: Album art fallback
                if (song.album_art && this.isValidImageUrl(song.album_art)) {
                    return this.ensureOptimalFormat(song.album_art);
                }

                // PRIORITY 4: Artist image as last resort
                if (song.artist_image && this.isValidImageUrl(song.artist_image)) {
                    return this.ensureOptimalFormat(song.artist_image);
                }

                return null;
            }

            // SIMPLIFIED URL VALIDATION - FOCUSED ON UDIO URLS
            isValidImageUrl(url) {
                if (!url || typeof url !== 'string') return false;

                // Basic validation
                if (url.trim() === '') return false;
                if (!url.startsWith('http')) return false;

                // For Udio URLs, always return true - this is the key fix!
                if (url.includes('imagedelivery.net') || url.includes('storage.googleapis.com')) {
                    return true;
                }

                return false;
            }

            // OPTIMAL FORMAT OPTIMIZATION - CLEAN AND RELIABLE
            ensureOptimalFormat(url) {
                if (!url) return url;

                // Only optimize Udio image delivery URLs
                if (url.includes('imagedelivery.net')) {
                    try {
                        var urlObj = new URL(url);

                        // Add AVIF format if not present
                        if (!urlObj.searchParams.has('format')) {
                            urlObj.searchParams.set('format', 'avif');
                        }

                        // Add quality parameter for optimal compression
                        if (!urlObj.searchParams.has('quality')) {
                            urlObj.searchParams.set('quality', '80');
                        }

                        return urlObj.toString();
                    } catch (error) {
                        return url; // Return original if URL parsing fails
                    }
                }

                return url;
            }

            extractVideoUrl(song) {
                // Direct video path from API
                if (song.video_path) {
                    return song.video_path;
                }

                // Check variants array
                if (song.variants && Array.isArray(song.variants)) {
                    for (var variant of song.variants) {
                        if (variant.video_path) {
                            return variant.video_path;
                        }
                    }
                }

                return null;
            }

            async downloadAlbumArt(albumArtUrl, filenameBase) {
                if (!albumArtUrl) {
                    return; // Return directly instead of null for cleaner async flow
                }

                // Check cache first
                if (this.albumArtCache.has(albumArtUrl)) {
                    // If it's cached, we still need to simulate the download to keep the progress bar consistent
                    // but we can skip the actual network request.
                    return;
                }

                try {
                    var extension = this.getImageExtension(albumArtUrl);
                    var artFilename = `${filenameBase} - Artwork.${extension}`;

                    // --- START THE FIX ---
                    // Use the new promisified helper function to ensure we can await its completion.
                    await promisifiedGmDownload({
                        url: albumArtUrl,
                        name: artFilename,
                        saveAs: false
                    });
                    // --- END THE FIX ---

                    this.albumArtCache.set(albumArtUrl, artFilename);
                    // No need to return the filename as we are just confirming completion.

                } catch (error) {
                    this.state.error(`[Download Error] Failed to download album art for "${filenameBase}":`, error);
                    throw error; // Re-throw the error so the main downloadAllTracks loop can catch it.
                }
            }

            getImageExtension(url) {
                if (url.includes('.avif') || url.includes('format=avif')) return 'avif';
                if (url.includes('.png')) return 'png';
                if (url.includes('.webp')) return 'webp';
                if (url.includes('.gif')) return 'gif';
                return 'jpg'; // Default
            }

            async downloadVideo(videoUrl, filenameBase) {
                if (!videoUrl) {
                    return;
                }

                if (this.videoUrlCache.has(videoUrl)) {
                    return;
                }

                try {
                    var videoFilename = `${filenameBase}.mp4`;

                    // --- START THE FIX ---
                    await promisifiedGmDownload({
                        url: videoUrl,
                        name: videoFilename,
                        saveAs: false
                    });
                    // --- END THE FIX ---

                    this.videoUrlCache.set(videoUrl, videoFilename);

                } catch (error) {
                    this.state.error(`[Download Error] Failed to download video for "${filenameBase}":`, error);
                    throw error; // Re-throw the error
                }
            }

            async processApiRequest(item) {
                var songId = getSongIdFromUrl(item.url);

                if (!songId) {
                    return { success: false, shouldRetry: false, error: 'Invalid URL' };
                }

                // Enhanced pre-check data handling
                if (item.preCheckData) {
                    var parsedData = this.parseAndValidateSong({ songs: [item.preCheckData] }, songId);

                    if (parsedData) {
                        return this.handleSuccessfulProcessing(parsedData, item);
                    }
                }

                // Regular API call with enhanced error handling
                try {
                    var responseData = await this.fetchSongData(songId);
                    var parsedData = this.parseAndValidateSong(responseData, songId);

                    if (parsedData) {
                        return this.handleSuccessfulProcessing(parsedData, item);
                    } else {
                        return { success: false, shouldRetry: false, error: 'Parse failed' };
                    }
                } catch (error) {
                    // Enhanced retry logic based on error type
                    var shouldRetry = this.shouldRetryRequest(error, item.retries || 0);
                    return {
                        success: false,
                        shouldRetry: shouldRetry,
                        error: error.message,
                        retryAfter: shouldRetry ? this.getRetryDelay(item.retries || 0) : 0
                    };
                }
            }

            handleSuccessfulProcessing(parsedData, item) {
                var { audioUrl, generationId, fullInfo } = parsedData;
                var isDuplicateGenId = this.state.processedGenerationIds.has(generationId);

                // SILENT PROGRESS LOGGING
                this.processedCount++;
                if (this.processedCount - this.lastLogCount >= 5 || this.processedCount % 10 === 0) {
                    this.state.log(`[API] Processed ${this.processedCount} songs, captured: "${fullInfo.title}"`);
                    this.lastLogCount = this.processedCount;
                }

                if (!isDuplicateGenId) {
                    this.state.processedGenerationIds.add(generationId);
                    this.state.saveProcessedIds();

                    this.state.capturedTracks.set(audioUrl, fullInfo);
                    this.state.saveTracks();

                    // Mark URL as processed
                    var processedUrls = new Set(this.state.safeJSONParse(GM_getValue('processedUrls', '[]'), []));
                    processedUrls.add(normalizeUrl(item.url));
                    GM_setValue('processedUrls', JSON.stringify([...processedUrls]));
                } else {
                    // --- THIS IS THE FIX ---
                    // Add this else block to log when a duplicate is found and skipped.
                    this.state.log(`[Duplicate] Skipping track "${fullInfo.title}" (ID: ${generationId}). Already captured.`);
                    // --------------------------
                }

                return { success: true };
            }

            shouldRetryRequest(error, retryCount) {
                if (retryCount >= CONFIG.MAX_RETRIES) {
                    return false;
                }

                // Retry on network errors, timeouts, and rate limits
                var retryableErrors = [
                    'timeout',
                    'Network Error',
                    'Failed to fetch',
                    '429',
                    '503',
                    '504'
                ];

                return retryableErrors.some(retryableError =>
                                            error.message.includes(retryableError)
                                        );
            }

            getRetryDelay(retryCount) {
                return Math.min(1000 * Math.pow(2, retryCount), 30000); // Exponential backoff with max 30s
            }

            // Cleanup method for memory management
            cleanup() {
                // Clear old cache entries
                var now = Date.now();
                var maxAge = 30 * 60 * 1000; // 30 minutes

                for (var [key, value] of this.apiResponseCache.entries()) {
                    if (now - value.timestamp > maxAge) {
                        this.apiResponseCache.delete(key);
                    }
                }

                // Limit cache sizes
                if (this.albumArtCache.size > 50) {
                    var entries = Array.from(this.albumArtCache.entries());
                    this.albumArtCache = new Map(entries.slice(-50));
                }

                if (this.videoUrlCache.size > 50) {
                    var entries = Array.from(this.videoUrlCache.entries());
                    this.videoUrlCache = new Map(entries.slice(-50));
                }

                // Clean up metadata samples log to prevent memory bloat
                if (this.metadataSamplesLogged.size > 1000) {
                    var samplesArray = Array.from(this.metadataSamplesLogged);
                    this.metadataSamplesLogged = new Set(samplesArray.slice(-500));
                }
            }
        }

        // ====================================================================================
        // --- 5. QUEUE MANAGEMENT - HIGH-PERFORMANCE, CONTINUOUS FLOW ---
        // ====================================================================================

        class QueueManager {
            constructor(state, apiHandler, tabCoordinator) {
                this.state = state;
                this.apiHandler = apiHandler;
                this.tabCoordinator = tabCoordinator;
            }

            async validateAndCleanQueue() {
                try {
                    const queue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                    const failedUrls = this.state.safeJSONParse(GM_getValue('failedUrls', '[]'), []);
                    const validQueue = queue.filter(item => item?.url && getSongIdFromUrl(item.url));
                    const validFailed = failedUrls.filter(item => item?.url && getSongIdFromUrl(item.url));
                    const queueCleaned = queue.length - validQueue.length;
                    const failedCleaned = failedUrls.length - validFailed.length;

                    if (queueCleaned > 0 || failedCleaned > 0) {
                        GM_setValue('urlQueue', JSON.stringify(validQueue));
                        GM_setValue('failedUrls', JSON.stringify(validFailed));
                        this.state.log(`[Queue] Cleaned ${queueCleaned} invalid queue items and ${failedCleaned} invalid failed items.`);
                    }
                    return { queueCleaned, failedCleaned };
                } catch (error) {
                    this.state.error('[Queue] Error validating queue:', error);
                    return { queueCleaned: 0, failedCleaned: 0 };
                }
            }

            async addToQueue(urlsToAdd, isManualSelection = false, folderContext = null) { // Add folderContext parameter
                if (this.state.isClearing || !Array.isArray(urlsToAdd) || urlsToAdd.length === 0) return;

                // If the context isn't provided by the scanner, try to detect it now.
                // This handles manual captures and player captures.
                const finalContext = folderContext || (UI.getPlaylistContext ? UI.getPlaylistContext() : null);

                // Delegate to TabCoordinator with the final context.
                await this.tabCoordinator.addToBufferQueue(urlsToAdd, isManualSelection, finalContext);
            }

            async processQueue() {
                // FIXED: Allow queue processing even when auto-capture is disabled
                // Only the MASTER tab can process the queue, and only one process at a time
                if (!this.tabCoordinator.isMaster || this.state.isProcessingQueue || this.state.isClearing) {
                    return;
                }
                this.state.isProcessingQueue = true;

                // Initialize queue logging cache if needed
                if (!this._queueLogCache) {
                    this._queueLogCache = {
                        lastBatchLog: 0,
                        lastCompletionLog: 0,
                        lastSyncLog: 0,
                        suppressedLogs: 0
                    };
                }
                const cache = this._queueLogCache;
                const now = Date.now();

                try {
                    // Step 1: Sync new items from the shared buffer into this tab's main queue.
                    const buffer = this.state.safeJSONParse(GM_getValue('bufferQueue', '[]'), []);
                    if (buffer.length > 0) {
                        const mainQueue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                        const mainQueueUrls = new Set(mainQueue.map(item => normalizeUrl(item.url)));
                        const uniqueNewItems = buffer.filter(item => !mainQueueUrls.has(normalizeUrl(item.url)));

                        if (uniqueNewItems.length > 0) {
                            GM_setValue('urlQueue', JSON.stringify([...mainQueue, ...uniqueNewItems]));
                            GM_setValue('bufferQueue', '[]'); // Clear the buffer now that we've synced it.

                            // OPTIMIZED: Only log significant syncs or first sync after quiet period
                            if (uniqueNewItems.length > 10 || (uniqueNewItems.length > 0 && (now - cache.lastSyncLog > 30000))) {
                                this.state.log(`[Queue] Synced ${uniqueNewItems.length} new items`);
                                cache.lastSyncLog = now;
                            } else if (uniqueNewItems.length > 0 && GM_getValue('debugMode', false)) {
                                this.state.debug(`[Queue] Synced ${uniqueNewItems.length} items`);
                            }
                        }
                    }

                    // Step 2: Process a batch from the main queue.
                    const queue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                    if (queue.length === 0) {
                        // If the queue is empty, check if there are any previously failed items to retry.
                        await this.checkAndRetryFailed();
                        return; // Nothing to do, the finally block will schedule the next check.
                    }

                    const batchSize = Math.min(queue.length, CONFIG.CONCURRENT_REQUESTS);

                    // OPTIMIZED: Much stricter batch logging with anti-spam
                    if (batchSize > 0) {
                        const shouldLogBatch =
                            batchSize > 15 ||
                            queue.length > 30 ||
                            (batchSize > 5 && (now - cache.lastBatchLog > 30000)) || // Only log every 30s for medium batches
                            cache.suppressedLogs > 10; // Log if we've suppressed many logs

                        if (shouldLogBatch) {
                            this.state.log(`[Queue] Processing ${batchSize} items (${queue.length} total)`);
                            cache.lastBatchLog = now;
                            cache.suppressedLogs = 0;
                        } else {
                            cache.suppressedLogs++;
                            // Only debug log small batches in debug mode
                            if (GM_getValue('debugMode', false)) {
                                this.state.debug(`[Queue] Processing ${batchSize} items`);
                            }
                        }
                    }

                    const batch = queue.splice(0, batchSize);
                    GM_setValue('urlQueue', JSON.stringify(queue)); // Save the shortened queue.

                    this.state.activeRequests += batch.length;
                    const processingPromises = batch.map(item => this._processItem(item));
                    await Promise.allSettled(processingPromises);
                    this.state.activeRequests -= batch.length;

                    // OPTIMIZED: Completion logging - only for significant milestones
                    if (batchSize > 0) {
                        const remaining = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []).length;

                        // Only log completion milestones, not every batch
                        const shouldLogCompletion =
                            remaining === 0 ||
                            (remaining < 5 && batchSize >= 10) ||
                            (remaining === 0 && (now - cache.lastCompletionLog > 60000)); // Don't spam "all done"

                        if (shouldLogCompletion) {
                            if (remaining === 0) {
                                this.state.log(`[Queue] ✅ All ${batchSize} items processed successfully`);
                                cache.lastCompletionLog = now;
                            } else if (remaining < 10) {
                                this.state.debug(`[Queue] ${remaining} items remaining`);
                            }
                        }
                    }

                } catch (error) {
                    this.state.error('[Queue] Critical error during batch processing:', error);
                } finally {
                    this.state.isProcessingQueue = false;

                    // FIXED: Continuous loop with optimized delay - ALWAYS continue processing
                    // regardless of auto-capture state
                    const currentQueue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                    const bufferQueue = this.state.safeJSONParse(GM_getValue('bufferQueue', '[]'), []);

                    // Dynamic delay: faster when there's work, slower when idle
                    let nextDelay;
                    if (currentQueue.length > 0 || bufferQueue.length > 0) {
                        // Active work - check quickly (100-300ms)
                        nextDelay = Math.max(100, CONFIG.REQUEST_DELAY * 2);
                        // OPTIMIZED: Only debug log scheduling in debug mode
                        if (GM_getValue('debugMode', false)) {
                            this.state.debug(`[Queue] Next batch in ${nextDelay}ms (${currentQueue.length} in queue)`);
                        }
                    } else {
                        // Idle - check less frequently (1-2 seconds)
                        nextDelay = 1000 + Math.random() * 1000;
                    }

                    setTimeout(() => {
                        if (this.tabCoordinator.isMaster && !this.state.isClearing) {
                            this.processQueue();
                        }
                    }, nextDelay);
                }
            }

            async _processItem(item) {
                const songId = getSongIdFromUrl(item.url);
                if (!songId) return this._markAsFailed(item, 'Invalid URL');

                try {
                    const responseData = await this.apiHandler.fetchSongData(songId);
                    const parsedData = this.apiHandler.parseAndValidateSong(responseData, songId);
                    if (parsedData) {
                        await this._handleSuccessfulProcessing(parsedData, item);
                    } else {
                        this._markAsFailed(item, 'API response parsing failed');
                    }
                } catch (error) {
                    if (this.apiHandler.shouldRetryRequest(error, item.retries || 0)) {
                        item.retries = (item.retries || 0) + 1;
                        this.state.warn(`[Queue] Item failed, re-queueing for another attempt (${item.retries}/${CONFIG.MAX_RETRIES}): ${item.url}`);
                        const currentQueue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                        GM_setValue('urlQueue', JSON.stringify([...currentQueue, item]));
                    } else {
                        this._markAsFailed(item, `Failed after max retries: ${error.message}`);
                    }
                }
            }

            async _handleSuccessfulProcessing(parsedData, item) {
                const { audioUrl, generationId, fullInfo } = parsedData;

                // --- START OF FIX ---
                // This new logic correctly handles duplicates by checking for new, valuable information
                // like a different folder context or a metadata upgrade, instead of bluntly skipping.

                const existingTrack = this.state.capturedTracks.get(audioUrl);
                const newContext = item.folderContext;

                if (existingTrack) {
                    const hasNewContext = newContext && newContext !== existingTrack.folderContext;
                    const isMetadataUpgrade = !this.hasCompleteMetadata(existingTrack) && this.hasCompleteMetadata(fullInfo);

                    // Skip ONLY if the track already exists AND there's no new context AND it's not a metadata upgrade.
                    if (!hasNewContext && !isMetadataUpgrade) {
                        this.state.log(`[Queue] Skipping duplicate: "${fullInfo.title}" (already captured, no new info).`);

                        // Mark this specific URL as processed to prevent the scanner from re-adding it.
                        const processedUrls = new Set(this.state.safeJSONParse(GM_getValue('processedUrls', '[]'), []));
                        processedUrls.add(normalizeUrl(item.url));
                        GM_setValue('processedUrls', JSON.stringify([...processedUrls]));
                        return; // Safely skip this item.
                    }
                    // If we don't skip, it's because we want to update the existing track.
                    this.state.log(`[Queue] Updating track: "${fullInfo.title}" with new context or metadata.`);
                }
                // --- END OF FIX ---


                // Add to processed IDs to prevent re-processing from other potential URLs in the same batch
                this.state.processedGenerationIds.add(generationId);
                this.state.saveProcessedIds();

                // ENHANCED: Smart data merging - preserve existing data while adding new information
                // CRITICAL FIX: Preserve the folder context from the queue item
                const enhancedInfo = this.mergeTrackData(existingTrack, fullInfo, item, generationId);

                // Store the track
                this.state.capturedTracks.set(audioUrl, enhancedInfo);
                this.state.saveTracks();

                // DEBUG: Check what was stored
                if (window.UdioDownloaderUI && window.UdioDownloaderUI.debugTrackData) {
                    setTimeout(() => {
                        window.UdioDownloaderUI.debugTrackData();
                    }, 1000);
                }

                // Trigger manual selection completion event if needed
                if (item.isManual) {
                    window.dispatchEvent(new CustomEvent('udio-dl-manual-selection-complete', {
                        detail: {
                            url: item.url,
                            track: enhancedInfo,
                            wasUpgrade: !!existingTrack // Indicate if this was an metadata upgrade
                        }
                    }));
                }

                // Log appropriate message based on whether this was new or an upgrade
                if (existingTrack) {
                    this.state.log(`[Queue] ✅ Metadata upgraded for "${enhancedInfo.title}"`);

                    // Show upgrade notification to user
                    if (window.UdioDownloaderUI) {
                        window.UdioDownloaderUI.showToast(
                            `📊 Enhanced metadata for "${enhancedInfo.title}"`,
                            'success',
                            3000
                        );
                    }
                } else {
                    this.state.log(`[Queue] ✅ New track captured: "${enhancedInfo.title}" by ${enhancedInfo.artist}`);

                    // Show new capture notification
                    if (window.UdioDownloaderUI && !item.isManual) {
                        window.UdioDownloaderUI.showToast(
                            `🎵 Captured: "${enhancedInfo.title}"`,
                            'success',
                            3000
                        );
                    }
                }

                // Mark URL as processed
                const processedUrls = new Set(this.state.safeJSONParse(GM_getValue('processedUrls', '[]'), []));
                processedUrls.add(normalizeUrl(item.url));
                GM_setValue('processedUrls', JSON.stringify([...processedUrls]));
            }

        /**
             * NEW: Smart track data merging to preserve existing information
             */
            mergeTrackData(existingTrack, newData, item, generationId) {
                // If no existing track, create new one with all the data including folder context
                if (!existingTrack) {
                    return {
                        ...newData,
                        generationId: generationId,
                        captureMethod: item.isManual ? 'manual' : 'auto',
                        captureTime: new Date().toISOString(),
                        // CRITICAL: Always use the folder context from the queue item when creating new track
                        folderContext: item.folderContext || newData.folderContext
                    };
                }

                // Merge strategy: Preserve existing data, but allow new data to fill gaps
                const mergedData = {
                    // Start with existing data (this preserves any manually added info)
                    ...existingTrack,

                    // Override with new API data where it provides better information
                    ...newData,

                    // Preserve critical existing fields that shouldn't be overwritten
                    captureMethod: existingTrack.captureMethod || (item.isManual ? 'manual' : 'auto'),
                    captureTime: existingTrack.captureTime || new Date().toISOString(),

                    // ENHANCED FOLDER CONTEXT MERGING:
                    // - If the queue item has a folder context, use it (this is the capture context)
                    // - Otherwise, preserve the existing folder context
                    // - Never overwrite a valid context with undefined/null
                    folderContext: item.folderContext || existingTrack.folderContext || newData.folderContext,

                    // Ensure generation ID is updated
                    generationId: generationId,

                    // Preserve any custom user-added fields that might exist
                    ...this.preserveCustomFields(existingTrack, newData)
                };

                return mergedData;
            }

            /**
             * NEW: Preserve custom fields from existing track that aren't in API response
             */
            preserveCustomFields(existingTrack, newData) {
                const preservedFields = {};
                const apiFieldNames = new Set(Object.keys(newData));

                // List of fields that might contain user customizations
                const potentialCustomFields = [
                    'userNotes', 'customTags', 'rating', 'playCount',
                    'lastPlayed', 'downloadPath', 'fileSize', 'localModifications'
                ];

                potentialCustomFields.forEach(field => {
                    if (existingTrack[field] !== undefined && !apiFieldNames.has(field)) {
                        preservedFields[field] = existingTrack[field];
                    }
                });

                return preservedFields;
            }

            /**
             * NEW: Check if track has complete metadata
             */
            hasCompleteMetadata(track) {
                if (!track) return false;

                // Define what constitutes "complete" metadata
                const requiredFields = [
                    'title',
                    'artist',
                    'creationDate',
                    'songPageUrl',
                    'audioUrl'
                ];

                const desirableFields = [
                    'prompt',
                    'albumArt',
                    'lyrics',
                    'duration'
                ];

                // Check required fields
                const hasRequiredFields = requiredFields.every(field =>
                    track[field] && track[field] !== 'Unknown' && track[field] !== 'Unknown Artist'
                );

                if (!hasRequiredFields) return false;

                // Check if we have most desirable fields (at least 50%)
                const hasDesirableFields = desirableFields.filter(field =>
                    track[field] && track[field] !== ''
                ).length >= Math.floor(desirableFields.length / 2);

                return hasDesirableFields;
            }

            async checkAndRetryFailed() {
                const failedUrls = this.state.safeJSONParse(GM_getValue('failedUrls', '[]'), []);
                if (failedUrls.length > 0) {
                    // Logic to decide when to retry (e.g., after a certain time) could go here.
                    // For now, we don't auto-retry to avoid infinite loops on permanently broken links.
                }
            }

            retryFailedUrls() {
                const failures = this.state.safeJSONParse(GM_getValue('failedUrls', '[]'), []);
                if (failures.length > 0) {
                    const retriedItems = failures.map(f => ({ ...f, retries: 0 }));
                    const existingQueue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                    GM_setValue('urlQueue', JSON.stringify([...existingQueue, ...retriedItems]));
                    GM_setValue('failedUrls', '[]');
                    this.state.log(`[Queue] 🔄 Moved ${failures.length} failed URLs back to the main queue.`);
                    this.processQueue(); // Manually trigger processing for the retried items.
                }
            }

            _markAsFailed(item, error) {
                const failures = this.state.safeJSONParse(GM_getValue('failedUrls', '[]'), []);
                if (!failures.some(f => f.url === item.url)) {
                    failures.push({ ...item, error, failedAt: Date.now() });
                    GM_setValue('failedUrls', JSON.stringify(failures));
                }
            }

            clearQueue() {
                GM_setValue('urlQueue', '[]');
                GM_setValue('failedUrls', '[]');
                GM_setValue('bufferQueue', '[]');
                this.inMemoryQueue = [];
            }
        }

        // ====================================================================================
        // --- 6. SCANNER & OBSERVER - RELIABLE CONTEXT-AWARE CAPTURE ---
        // ====================================================================================

        class Scanner {
            constructor(state, queueManager) {
                this.state = state;
                this.queueManager = queueManager;
                this.observer = null;
                this.pollingInterval = null;
                this.processedUrls = new Set(state.safeJSONParse(GM_getValue('processedUrls', '[]'), []));
                this.lastKnownContext = null; // Memoization for context
                this.scanDebounceTimeout = null; // Prevent rapid-fire scans
            }

            start() {
                this.stop();
                this.state.log('[Scanner] Starting aggressive scanner...');

                // Existing observers
                this.observer = new MutationObserver(() => this.scheduleScan());
                this.observer.observe(document.body, { childList: true, subtree: true });

                this.pollingInterval = setInterval(() => this.scheduleScan(), 2500);

                // ADD MISSING AGGRESSIVE SCANNING
                if (CONFIG.AGGRESSIVE_SCAN) {
                    this.aggressiveScanInterval = setInterval(() => {
                        this.scanPageForSongs();
                    }, CONFIG.SCAN_INTERVAL);

                    this.forceScanInterval = setInterval(() => {
                        this.state.log('[Scanner] Force scan triggered');
                        this.scanPageForSongs();
                    }, CONFIG.FORCE_SCAN_INTERVAL);
                }

                this.scheduleScan();
            }

            stop() {
                if (this.observer) {
                    this.observer.disconnect();
                    this.observer = null;
                }
                if (this.pollingInterval) {
                    clearInterval(this.pollingInterval);
                    this.pollingInterval = null;
                }
                if (this.aggressiveScanInterval) {
                    clearInterval(this.aggressiveScanInterval);
                    this.aggressiveScanInterval = null;
                }
                if (this.forceScanInterval) {
                    clearInterval(this.forceScanInterval);
                    this.forceScanInterval = null;
                }
                clearTimeout(this.scanDebounceTimeout);
                this.state.log('[Scanner] Scanner stopped.');
            }

            /**
             * Schedules a debounced scan to prevent the scanner from running hundreds of times
             * during a complex page load.
             */
            scheduleScan() {
                // Clear any existing timeout to prevent stacking
                clearTimeout(this.scanDebounceTimeout);

                // Execute immediately for better responsiveness
                this.scanDebounceTimeout = setTimeout(() => {
                    this.scanPageForSongs();
                }, 50); // Reduced from 350ms to 50ms for near-instant capture
            }

            scanPageForSongs() {
                if (this.state.isClearing || !this.state.isAutoCapturing) return;

                const songLinks = document.querySelectorAll('a[href*="/songs/"]');
                if (songLinks.length === 0) return;

                const currentContext = (UI.getPlaylistContext ? UI.getPlaylistContext() : null) || this.lastKnownContext;

                // ADD: Anti-spam for context logging
                if (currentContext && currentContext !== this.lastContextLogged) {
                    this.state.debug(`[Scanner] Context: "${currentContext}"`);
                    this.lastContextLogged = currentContext;
                }

                const newUrls = [];
                songLinks.forEach(link => {
                    const url = link.href;
                    if (url && !url.includes('/create')) {
                        const normalizedUrl = normalizeUrl(url);
                        if (!this.processedUrls.has(normalizedUrl)) {
                            newUrls.push(normalizedUrl);
                            this.processedUrls.add(normalizedUrl);
                        }
                    }
                });

                if (newUrls.length > 0) {
                    // REDUCE: Only log significant finds (5+ songs or context changes)
                    if (newUrls.length > 5 || currentContext !== this.lastSignificantContext) {
                        this.state.log(`[Scanner] Found ${newUrls.length} songs${currentContext ? ` in "${currentContext}"` : ''}`);
                        this.lastSignificantContext = currentContext;
                    } else if (GM_getValue('debugMode', false)) {
                        this.state.debug(`[Scanner] Found ${newUrls.length} songs`); // Debug only
                    }

                    this.queueManager.addToQueue(newUrls, false, currentContext);

                    if (currentContext) {
                        this.lastKnownContext = currentContext;
                    }
                }
            }
        }

// ====================================================================================
// --- 7. PLAYER OBSERVER - FIXED TRACK CHANGE DETECTION ---
// ====================================================================================

class PlayerObserver {
    constructor(state, apiHandler) {
        this.state = state;
        this.apiHandler = apiHandler;
        this.currentlyFetching = new Set();
        this.lastMediaUrl = null;
        this.lastSongId = null;
        this.lastProcessedTime = 0;
        this.observer = null;

        // Enhanced state tracking
        this.currentTrackState = {
            songId: null,
            title: null,
            artist: null,
            mediaUrl: null,
            lastSeen: 0,
            isProcessed: false // NEW: Track if we've already processed this track
        };

        this.SAME_TRACK_COOLDOWN = 10000; // 10 seconds for same track
        this.DIFFERENT_TRACK_COOLDOWN = 2000; // 2 seconds for different track

        // Breadcrumb cache
        this._breadcrumbCache = { detectionCount: 0 };
    }

    /**
     * ENHANCED: Initialize with better player detection
     */
    observe() {
        if (GM_getValue('debugMode', false)) {
            this.state.log('[PlayerObserver] Starting enhanced player observation...');
        }

        if (this.observer) {
            this.observer.disconnect();
        }

        const findPlayerWithRetry = (attempts = 0) => {
            if (attempts > 10) {
                if (GM_getValue('debugMode', false)) {
                    this.state.log('[PlayerObserver] Player not found after max attempts');
                }
                return;
            }

            const player = this.findPlayerElement();
            if (player) {
                if (GM_getValue('debugMode', false)) {
                    this.state.log('[PlayerObserver] Player found, setting up observers');
                }
                this.setupPlayerObservers(player);
                setTimeout(() => this.throttledCapture(), 500);
            } else {
                if (GM_getValue('debugMode', false)) {
                    this.state.debug(`[PlayerObserver] Player not found, retrying... (${attempts + 1}/10)`);
                }
                setTimeout(() => findPlayerWithRetry(attempts + 1), 1000);
            }
        };

        findPlayerWithRetry();
    }

    /**
     * NEW: Enhanced playlist name detection with specific selectors
     */
    getSpecificPlaylistContext() {
        try {
            const specificSelectors = [
                'h1.text-2xl',
                'h4.text-2xl',
                '[class*="playlist-title"]',
                '[class*="playlist-name"]',
                'img[alt*="playlist"]',
                'img[alt*="album"]'
            ];

            for (const selector of specificSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    let text = '';
                    if (element.tagName === 'IMG' && element.alt) {
                        text = element.alt.trim();
                    } else if (element.textContent) {
                        text = element.textContent.trim();
                    }

                    if (text && this.isValidPlaylistName(text) && !this.isLikelyTrackTitle(text)) {
                        this.state.log(`[UI Context] Found playlist via specific selector "${selector}": "${text}"`);
                        return text;
                    }
                }
            }

            return null;
        } catch (error) {
            this.state.debug('[UI Context] Error in specific playlist detection:', error);
            return null;
        }
    }

    /**
     * ENHANCED: Get current track state from player
     */
    getCurrentTrackState() {
        try {
            const player = this.findPlayerElement() || document.body;
            const songInfo = this.extractCurrentSongInfo(player);
            const mediaDetection = this.detectMediaElements();

            if (!songInfo.songId) {
                return {
                    songId: null,
                    title: null,
                    artist: null,
                    mediaUrl: null,
                    lastSeen: this.currentTrackState.lastSeen,
                    isProcessed: false
                };
            }

            return {
                songId: songInfo.songId,
                title: songInfo.title,
                artist: songInfo.artist,
                mediaUrl: mediaDetection.found ? mediaDetection.mediaUrl : null,
                lastSeen: Date.now(),
                isProcessed: this.currentTrackState.songId === songInfo.songId ?
                    this.currentTrackState.isProcessed : false
            };
        } catch (error) {
            this.state.error('[PlayerObserver] Error getting current track state:', error);
            return {
                songId: null,
                title: null,
                artist: null,
                mediaUrl: null,
                lastSeen: this.currentTrackState.lastSeen,
                isProcessed: false
            };
        }
    }

    /**
     * NEW: Setup multiple observation strategies
     */
    setupPlayerObservers(player) {
        this.observer = new MutationObserver((mutations) => {
            let shouldCheck = false;
            mutations.forEach(mutation => {
                if (mutation.type === 'attributes' &&
                    (mutation.attributeName === 'src' ||
                     mutation.attributeName === 'href' ||
                     mutation.attributeName === 'class')) {
                    shouldCheck = true;
                }
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    shouldCheck = true;
                }
            });

            if (shouldCheck) {
                this.throttledCapture();
            }
        });

        this.observer.observe(player, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['src', 'href', 'class', 'style', 'title']
        });

        this.setupMediaEventListeners();

        this.periodicCheckInterval = setInterval(() => {
            this.throttledCapture();
        }, 3000);
    }

    setupMediaEventListeners() {
        const mediaObserver = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        if (node.tagName === 'AUDIO' || node.tagName === 'VIDEO') {
                            this.attachMediaListeners(node);
                        }
                        node.querySelectorAll('audio, video').forEach(media => {
                            this.attachMediaListeners(media);
                        });
                    }
                });
            });
        });

        mediaObserver.observe(document.body, { childList: true, subtree: true });
        document.querySelectorAll('audio, video').forEach(media => {
            this.attachMediaListeners(media);
        });
    }

    attachMediaListeners(mediaElement) {
        const events = ['play', 'playing', 'timeupdate', 'loadedmetadata'];
        events.forEach(event => {
            mediaElement.addEventListener(event, () => {
                this.throttledCapture();
            }, { passive: true });
        });
    }

    throttledCapture() {
        if (this.state.isClearing || !this.state.isHealthy()) return;

        const now = Date.now();
        const currentTrack = this.getCurrentTrackState();

        if (!currentTrack.songId) return;

        const existingTrack = this.findExistingTrack(currentTrack.songId);
        if (existingTrack && this.hasCompleteMetadata(existingTrack)) {
            this.state.debug(`[PlayerObserver] Track "${currentTrack.title}" already captured with complete metadata`);
            this.currentTrackState.isProcessed = true;
            return;
        }

        const isSameTrack = currentTrack.songId === this.currentTrackState.songId;
        const timeSinceLastProcess = now - this.currentTrackState.lastSeen;

        if (isSameTrack && timeSinceLastProcess < this.SAME_TRACK_COOLDOWN) return;
        if (!isSameTrack && timeSinceLastProcess < this.DIFFERENT_TRACK_COOLDOWN) return;

        this.currentTrackState = { ...currentTrack, lastSeen: now, isProcessed: false };
        this.captureTrackData();
    }

    findExistingTrack(songId) {
        for (const track of this.state.capturedTracks.values()) {
            const trackSongId = getSongIdFromTrack(track);
            if (trackSongId === songId) return track;
        }
        return null;
    }

    hasCompleteMetadata(track) {
        return track && track.title && track.artist && track.prompt && track.creationDate;
    }

    async captureTrackData() {
        if (this.state.isClearing || !this.state.isHealthy()) return;

        const mediaDetection = this.detectMediaElements();
        if (!mediaDetection.found) return;

        const { mediaUrl } = mediaDetection;
        const player = this.findPlayerElement() || document.body;
        const songInfo = this.extractCurrentSongInfo(player);

        if (!songInfo.songId) {
            this.state.debug('[PlayerObserver] Song info not available yet');
            return;
        }

        const existingTrack = this.findExistingTrack(songInfo.songId);
        if (existingTrack && this.hasCompleteMetadata(existingTrack)) {
            this.state.debug(`[PlayerObserver] Track "${songInfo.title}" already captured with complete data`);
            this.currentTrackState.isProcessed = true;
            return;
        }

        if (mediaUrl === this.lastMediaUrl && Date.now() - this.lastProcessedTime < 2500) return;

        this.lastMediaUrl = mediaUrl;
        this.lastSongId = songInfo.songId;
        this.lastProcessedTime = Date.now();

        await this.queueTrackForProcessing(songInfo.songId, mediaUrl, mediaDetection.mediaType, existingTrack);
    }

    // ===== CONTEXT DETECTION HELPERS (MOVED INSIDE CLASS) =====

    _isValidFolderContext(context) {
        if (!context || typeof context !== 'string') return false;
        const trimmed = context.trim();
        if (trimmed.length < 2 || trimmed.length > 80) return false;

        const invalidContexts = ['My Library', 'My Library > My Library', 'Library', 'Home', 'undefined', 'null', '...', '>', '›'];
        if (invalidContexts.includes(trimmed) || invalidContexts.some(inv => trimmed.includes(inv))) return false;

        const meaningfulText = trimmed.replace(/[-›>]/g, '').trim();
        if (meaningfulText.length < 2) return false;

        if (this._isLikelyTrackTitle(trimmed)) return false;

        return true;
    }

    _cleanBreadcrumbCache() {
        if (this._breadcrumbCache) {
            this._breadcrumbCache.detectionCount = 0;
            this.state.debug('[Breadcrumb] Cache cleaned');
        }
    }

    _isValidBreadcrumbItem(text) {
        if (!text || typeof text !== 'string') return false;
        const trimmed = text.trim();
        if (trimmed.length < 2 || trimmed.length > 50) return false;

        const lowerText = trimmed.toLowerCase();
        const excludePatterns = [
            'toggle sidebar', 'chevron', 'arrow', 'back', 'home', 'menu', 'navigation',
            '...', 'more', '›', '>', '·', 'search', 'filter', 'open folder sidebar',
            'open search', 'open filters'
        ];

        if (excludePatterns.some(p => lowerText.includes(p))) return false;
        if (!/[a-zA-Z0-9]/.test(trimmed)) return false;

        return true;
    }

    _isGenericRootFolder(text) {
        const rootFolders = ['My Library', 'Library', 'Home'];
        return rootFolders.includes(text.trim());
    }

    _isLikelyTrackTitle(text) {
        return /^\s*.+\s+[-–—]\s+.+$/.test(text.trim());
    }

    isValidPlaylistName(name) {
        return name && name.length > 1 && !this._isLikelyTrackTitle(name);
    }

    isLikelyTrackTitle(text) {
        return this._isLikelyTrackTitle(text);
    }

    // You must implement these if used:
    _getBreadcrumbContextDirect() { return null; }
    _extractBreadcrumbPath(el) { return []; }
    _cleanBreadcrumbPath(path) { return path.join(' - '); }
    _findCurrentFolderContext() { return null; }

    // ===== END CONTEXT HELPERS =====

    async queueTrackForProcessing(songId, mediaUrl, mediaType, existingTrack) {
        const songUrl = `https://www.udio.com/songs/${songId}`;
        const currentQueue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
        const isAlreadyQueued = currentQueue.some(item => getSongIdFromUrl(item.url) === songId);

        if (isAlreadyQueued) {
            this.state.debug(`[PlayerObserver] Track ${songId} already in queue`);
            return;
        }

        let playlistContext = null;

        playlistContext = this._getBreadcrumbContextDirect();
        // The following line was removed because the function does not exist:
        // if (!playlistContext) playlistContext = this._detectContextFromPageStructure();
        if (!playlistContext && window.location.pathname.startsWith('/library')) {
            playlistContext = this.extractContextFromLibraryPage();
        }
        if (!playlistContext && window.UdioDownloaderUI?.getPlaylistContext) {
            const uiCtx = window.UdioDownloaderUI.getPlaylistContext();
            playlistContext = (uiCtx && uiCtx !== 'null') ? uiCtx : null;
        }

        if (playlistContext && ['null', 'undefined'].includes(playlistContext)) {
            playlistContext = null;
        }

        if (playlistContext) {
            this.state.log(`[PlayerObserver] Context detected: "${playlistContext}"`);
        } else {
            this.state.debug('[PlayerObserver] No context detected for player track');
        }

        this.state.log(`[PlayerObserver] Queuing track from player: "${songId}"`);

        await this.state.tabCoordinator.addToBufferQueue([songUrl], false, playlistContext);

        if (this.state.tabCoordinator.isMaster) {
            setTimeout(() => {
                if (this.state.queueManager && !this.state.isProcessingQueue) {
                    this.state.queueManager.processQueue();
                }
            }, 100);
        }

        const player = this.findPlayerElement() || document.body;
        const songInfo = this.extractCurrentSongInfo(player);
        if (songInfo.title && songInfo.artist) {
            this.state.log(`[PlayerObserver] Queued: "${songInfo.title}" by ${songInfo.artist}`);
            window.UdioDownloaderUI?.showToast(`Captured: "${songInfo.title}"`, 'success', 3000);
        }
    }

    extractContextFromLibraryPage() {
        try {
            if (!window.location.pathname.startsWith('/library')) return null;
            const params = new URLSearchParams(window.location.search);
            const filter = params.get('filter');
            if (!filter) return null;

            const contextMap = {
                'liked': 'Liked Songs',
                'recent': 'Recently Played',
                'created': 'My Creations',
                'saved': 'Saved Songs'
            };

            if (filter.startsWith('show.[') && filter.endsWith(']')) {
                const key = filter.slice(6, -1);
                return contextMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            }

            for (const [k, v] of Object.entries(contextMap)) {
                if (filter.includes(k)) return v;
            }

            return null;
        } catch (e) {
            this.state.debug('[PlayerObserver] Error extracting library context:', e);
            return null;
        }
    }

    detectMediaElements() {
        const allMedia = [
            ...document.querySelectorAll('audio[src*="storage.googleapis.com"]'),
            ...document.querySelectorAll('video[src*="storage.googleapis.com"]'),
            ...document.querySelectorAll('audio source[src*="storage.googleapis.com"]'),
            ...document.querySelectorAll('video source[src*="storage.googleapis.com"]')
        ];

        const activeMedia = allMedia.filter(m => {
            const el = m.tagName === 'SOURCE' ? m.parentElement : m;
            return el && !el.paused && el.duration > 0;
        });

        if (activeMedia.length > 0) {
            const m = activeMedia[0];
            const el = m.tagName === 'SOURCE' ? m.parentElement : m;
            return { found: true, mediaElement: el, mediaType: el.tagName.toLowerCase(), mediaUrl: m.src || el.src };
        }

        const withSrc = allMedia.find(m => m.src);
        if (withSrc) {
            const el = withSrc.tagName === 'SOURCE' ? withSrc.parentElement : withSrc;
            return { found: true, mediaElement: el, mediaType: el.tagName.toLowerCase(), mediaUrl: withSrc.src };
        }

        return { found: false };
    }

    extractCurrentSongInfo(player) {
        const strategies = [
            () => {
                const link = player.querySelector('a[href*="/songs/"]');
                if (!link) return null;
                const title = link.querySelector('h1, h2, h3, [class*="title"]')?.textContent?.trim() || 'Unknown Title';
                const artistLink = player.querySelector('a[href*="/creators/"]');
                const artist = artistLink?.querySelector('p, span, div')?.textContent?.trim() || 'Unknown Artist';
                return { title, artist, songPageUrl: link.href, songId: getSongIdFromUrl(link.href) };
            },
            () => {
                const el = player.querySelector('[data-song-id], [data-track-id]');
                if (!el) return null;
                const songId = el.getAttribute('data-song-id') || el.getAttribute('data-track-id');
                const title = el.querySelector('[data-title], [class*="title"]')?.textContent?.trim() || el.getAttribute('data-title') || 'Unknown Title';
                const artist = el.querySelector('[data-artist], [class*="artist"]')?.textContent?.trim() || el.getAttribute('data-artist') || 'Unknown Artist';
                return { title, artist, songPageUrl: `https://www.udio.com/songs/${songId}`, songId };
            },
            () => {
                const text = player.textContent;
                const songId = text.match(/"songId":"([a-zA-Z0-9]+)"/)?.[1];
                if (!songId) return null;
                const title = text.match(/"title":"([^"]+)"/)?.[1] || 'Unknown Title';
                const artist = text.match(/"artist":"([^"]+)"/)?.[1] || 'Unknown Artist';
                return { title, artist, songPageUrl: `https://www.udio.com/songs/${songId}`, songId };
            }
        ];

        for (const s of strategies) {
            const res = s();
            if (res?.songId) {
                this.state.debug(`[PlayerObserver] Extracted: "${res.title}" by ${res.artist}`);
                return res;
            }
        }

        return { title: 'Unknown', artist: 'Unknown', songPageUrl: null, songId: null };
    }

    findPlayerElement() {
        const selectors = [
            '#player', '[data-testid="player"]', 'div[class*="player-container"]',
            'div[class*="player_"]', 'div[style*="position: fixed"][style*="bottom: 0"]',
            'div[class*="audio-player"]', 'div[class*="now-playing"]', 'audio', 'video', '.player'
        ];

        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) return el;
        }

        const media = document.querySelector('audio, video');
        return media?.closest('div') || document.body;
    }

    cleanup() {
        if (this.observer) this.observer.disconnect();
        if (this.periodicCheckInterval) clearInterval(this.periodicCheckInterval);
        this.currentlyFetching.clear();
        this.observer = null;
        this.periodicCheckInterval = null;
    }

}

        // ====================================================================================
        // --- 8. UI MANAGEMENT - FIXED QUEUE UPDATE & MANUAL SELECTION SUPPORT ---
        // ====================================================================================

        /**
         * Check if element contains specific text (case insensitive)
         */
        function elementContainsText(element, text) {
            if (!element || !element.textContent) return false;
            return element.textContent.toLowerCase().includes(text.toLowerCase());
        }

        /**
         * Find elements that contain specific text
         */
        function findElementsWithText(selector, text) {
            var elements = document.querySelectorAll(selector);
            var matches = [];
            for (var i = 0; i < elements.length; i++) {
                var element = elements[i];
                if (elementContainsText(element, text)) {
                    matches.push(element);
                }
            }
            return matches;
        }

        var UI = {
            // Core dependencies
            state: null,
            queueManager: null,
            scanner: null,
            apiHandler: null,

            // UI State Management
            isDownloading: false,
            isRendering: false,
            lastRenderTime: 0,
            renderDebounce: null,
            eventListeners: new Map(),

            _trackListClickHandler: null, // Performance: Stores the delegated event handler
            lastTrackVersion: -1, // Performance: Tracks the last rendered data version

            // Manual selection tracking
            manualSelectionsInProgress: new Map(),
            lastQueueUpdate: 0,
            lastStatsUpdate: 0,

            // Performance tracking
            performance: {
                renderCount: 0,
                averageRenderTime: 0,
                lastRenderDuration: 0
            },



            /**
             * Initialize UI with dependency injection
             */
    init(state, queueManager, scanner, apiHandler) {
                this._hasLoggedTrackData = false;
                this.state = state;
                this.queueManager = queueManager;
                this.scanner = scanner;
                this.apiHandler = apiHandler;

                this.state.log('[UI] Initializing professional interface with performance optimizations.');

                this.create();
                this.startAutoRender();
                this.setupGlobalListeners();
                this.addManualSelectionSupport();

                setTimeout(() => {
                    this.forceUIRefresh();
                    this.state.log('[UI] Professional interface fully initialized.');

                    if (this.state.capturedTracks.size === 0) {
                        setTimeout(() => {
                            this.showToast(
                                '💡 Manual selection: Right-click song links or Ctrl+Click to capture tracks',
                                'info',
                                5000
                            );
                        }, 2000);
                    }
                }, 500);
            },

            /**
             * Forces an immediate and complete refresh of all UI components.
             * This function is designed to be safe to call at any time, especially during initialization
             * or after major state changes like clearing all data.
             * It temporarily stops the scanner to prevent race conditions during the redraw.
             */
            forceUIRefresh() {
                // ATOMIC OPERATION: Prevent multiple concurrent refreshes using a proper lock
                if (this._refreshLock) {
                    this.state.debug('[UI] Refresh lock active, skipping duplicate request.');
                    return;
                }

                // Set lock immediately to prevent race conditions
                this._refreshLock = true;
                const refreshStartTime = performance.now();
                this.state.log('[UI] 🚀 Force immediate UI refresh triggered.');

                // Store original scanner state for precise restoration
                const originalScannerState = {
                    wasRunning: this.scanner && this.state.isAutoCapturing,
                    hadObserver: this.scanner?.observer ? true : false
                };

                // PHASE 1: PREPARE ENVIRONMENT - Stop background operations atomically
                try {
                    // CRITICAL: Stop scanner to prevent data races during UI rebuild
                    if (this.scanner) {
                        this.scanner.stop();
                        this.state.debug('[UI] Scanner paused for UI refresh.');
                    }

                    // Also pause any active queue processing during refresh
                    const wasProcessingQueue = this.state.isProcessingQueue;
                    if (wasProcessingQueue) {
                        this.state.isProcessingQueue = false;
                        this.state.debug('[UI] Queue processing paused for UI refresh.');
                    }

                    // PHASE 2: MARK COMPONENTS FOR FORCED UPDATE
                    const componentsToUpdate = {
                        trackList: document.getElementById('downloader-track-list'),
                        controls: document.getElementById('downloader-controls'),
                        queueStatus: document.getElementById('downloader-queue-status'),
                        headerStats: document.getElementById('ui-header-stats')
                    };

                    // Set force-update flags on all components
                    Object.values(componentsToUpdate).forEach(component => {
                        if (component) {
                            component.setAttribute('data-force-update', 'true');
                            component.setAttribute('data-refresh-id', Date.now().toString());
                        }
                    });

                    // PHASE 3: EXECUTE UI UPDATE IN SINGLE ANIMATION FRAME
                    requestAnimationFrame(() => {
                        try {
                            const renderStartTime = performance.now();

                            // BATCHED DOM UPDATES: Update all UI sections in optimal order
                            const updateOperations = [
                                () => this._updateHeaderStatsOptimized(),
                                () => this._updateQueueStatusOptimized(),
                                () => this._updateManualSelectionStatsOptimized(),
                                () => this.updateControls(),
                                () => this.updateTrackList() // Performs intelligent diff/rebuild
                            ];

                            // Execute all updates sequentially for predictable rendering
                            updateOperations.forEach(operation => {
                                try {
                                    operation();
                                } catch (opError) {
                                    this.state.error('[UI] Error in UI update operation:', opError);
                                    // Continue with other operations even if one fails
                                }
                            });

                            // PHASE 4: CLEANUP AND RESTORATION
                            const renderTime = performance.now() - renderStartTime;
                            const totalTime = performance.now() - refreshStartTime;

                            this.state.log(`[UI] ✅ UI refresh completed in ${totalTime.toFixed(1)}ms (render: ${renderTime.toFixed(1)}ms)`);

                            // Remove force-update flags now that refresh is complete
                            Object.values(componentsToUpdate).forEach(component => {
                                if (component) {
                                    component.removeAttribute('data-force-update');
                                }
                            });

                            // PHASE 5: RESTORE BACKGROUND OPERATIONS PRECISELY
                            const restoreOperations = () => {
                                try {
                                    // CRITICAL: Restore scanner only if it was originally running
                                    if (this.scanner && originalScannerState.wasRunning) {
                                        this.scanner.start();
                                        this.state.debug('[UI] Scanner restarted after UI refresh.');
                                    }

                                    // Restore queue processing if it was active
                                    if (wasProcessingQueue && this.queueManager) {
                                        // Small delay to ensure UI is stable before resuming processing
                                        setTimeout(() => {
                                            this.state.isProcessingQueue = true;
                                            if (this.tabCoordinator?.isMaster) {
                                                this.queueManager.processQueue();
                                            }
                                        }, 500);
                                    }

                                    // Trigger any pending state change notifications
                                    window.dispatchEvent(new CustomEvent('udio-dl-ui-refresh-complete'));

                                } catch (restoreError) {
                                    this.state.error('[UI] Error restoring operations:', restoreError);
                                } finally {
                                    // RELEASE LOCK: Always ensure lock is cleared
                                    setTimeout(() => {
                                        this._refreshLock = false;
                                        this.state.debug('[UI] Refresh lock released.');
                                    }, 100);
                                }
                            };

                            // Stagger restoration to ensure DOM is fully settled
                            setTimeout(restoreOperations, 50);

                        } catch (frameError) {
                            this.state.error('[UI] Critical error during animation frame:', frameError);
                            this._emergencyRecovery(originalScannerState, wasProcessingQueue);
                        }

                    });

                } catch (prepError) {
                    this.state.error('[UI] Critical error during refresh preparation:', prepError);
                    this._emergencyRecovery(originalScannerState, false);
                }
            },

            /**
             * EMERGENCY RECOVERY: Restore system to working state after critical failures
             */
            _emergencyRecovery(originalScannerState, wasProcessingQueue) {
                this.state.log('[UI] 🚨 Emergency recovery initiated.');

                try {
                    // Attempt to restore scanner state
                    if (this.scanner && originalScannerState.wasRunning) {
                        this.scanner.start();
                    }

                    // Attempt to restore queue processing
                    if (wasProcessingQueue && this.queueManager) {
                        this.state.isProcessingQueue = true;
                        if (this.tabCoordinator?.isMaster) {
                            setTimeout(() => this.queueManager.processQueue(), 1000);
                        }
                    }

                    // Force a basic UI rebuild as last resort
                    setTimeout(() => {
                        try {
                            const trackList = document.getElementById('downloader-track-list');
                            if (trackList && this.state.capturedTracks.size === 0) {
                                trackList.innerHTML = this.createEmptyState();
                            }
                            this.updateDownloadButtonState(); // Critical button state
                        } catch (e) {
                            // Final fallback - at least show error state
                            console.error('[UI] Complete UI failure:', e);
                        }
                    }, 500);

                } catch (recoveryError) {
                    this.state.error('[UI] Emergency recovery failed:', recoveryError);
                } finally {
                    // ABSOLUTE CLEANUP: Ensure lock is always released
                    setTimeout(() => {
                        this._refreshLock = false;
                        this.state.warn('[UI] Emergency lock release completed.');
                    }, 200);
                }
            },

            /**
             * SAFE REFRESH WRAPPER: Public method that can be called without worrying about locks
             */
            safeForceUIRefresh() {
                if (this._refreshLock) {
                    // If refresh is already in progress, schedule one for after completion
                    this.state.debug('[UI] Queueing refresh for after current operation.');
                    if (!this._queuedRefresh) {
                        this._queuedRefresh = setTimeout(() => {
                            this._queuedRefresh = null;
                            this.forceUIRefresh();
                        }, 500);
                    }
                    return;
                }

                this.forceUIRefresh();
            },

            /**
             * SCHEDULED REFRESH: For non-critical updates that can be batched
             */
            scheduleDelayedRefresh(delayMs = 100) {
                if (this._scheduledRefresh) {
                    clearTimeout(this._scheduledRefresh);
                }

                this._scheduledRefresh = setTimeout(() => {
                    this._scheduledRefresh = null;
                    if (!this._refreshLock) {
                        this.forceUIRefresh();
                    }
                    // If locked, the safeForceUIRefresh will handle it when called
                }, delayMs);
            },

            // NEW: Handle metadata upgrade events
            handleMetadataUpgrade(trackInfo, mediaUrl) {
                this.state.log(`[UI] Metadata upgrade detected for: "${trackInfo.title}"`);

                // Force immediate track list update
                var trackList = document.getElementById('downloader-track-list');
                if (trackList) {
                    trackList.setAttribute('data-force-update', 'true');
                    this.updateTrackList();
                }

                // Show upgrade notification
                this.showToast(`📊 Enhanced metadata captured for "${trackInfo.title}"`, 'success', 3000);
            },

            /**
             * NEW: Coordinated animation updates
             */
            animateUIUpdates() {
                // Batch all animations together
                var statElements = document.querySelectorAll('.stat-value');
                statElements.forEach((el, index) => {
                    setTimeout(() => {
                        el.style.transform = 'scale(1.1)';
                        el.style.color = '#ffeb3b';

                        setTimeout(() => {
                            el.style.transform = 'scale(1)';
                            el.style.color = '#03dac6';
                        }, 300);
                    }, index * 50); // Stagger animations
                });
            },

            /**
             * NEW: Add manual selection support
             */
            addManualSelectionSupport() {
                this.addContextMenuSupport();
                this.addKeyboardShortcutSupport();
                this.setupManualSelectionListeners();

                this.state.log('[UI] Manual selection support initialized');
            },

            /**
             * Create main UI structure
             */
                    create() {
                if (document.getElementById('udio-downloader-ui')) {
                    this.state.log('[UI] Interface already exists, skipping creation');
                    return;
                }

                this.injectStyles();
                this.createContainer();
                this.createToggleButton();
                this.initializeEventSystem();
                this.attachTrackListEvents(); // Add this line here

                this.state.log('[UI] Professional interface created successfully');
            },

            /**
             * NEW: Update header stats (called by optimized render)
             */
            updateHeaderStats() {
                this._updateHeaderStatsOptimized();
            },

            /**
             * NEW: Update queue status (called by optimized render)
             */
            updateQueueStatus() {
                this._updateQueueStatusOptimized();
            },

            /**
             * NEW: Update manual selection stats (called by optimized render)
             */
            updateManualSelectionStats() {
                this._updateManualSelectionStatsOptimized();
            },

            /**
             * Inject CSS styles with professional design system - ENHANCED FOR LINUX/OLDER FIREFOX COMPATIBILITY
             */
            injectStyles() {
                var css = `
                    /* === PROFESSIONAL DESIGN SYSTEM (Firefox/Linux Optimized) === */
                    #udio-downloader-ui {
                        position: fixed;
                        top: 80px;
                        right: 20px;
                        z-index: 10002;
                        width: 480px;
                        max-width: 90vw;
                        max-height: 85vh;
                        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
                        color: #e0e0e0;
                        border-radius: 16px;
                        box-shadow:
                            0 20px 40px rgba(0,0,0,0.4),
                            0 0 0 1px rgba(255,255,255,0.1);
                        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                        display: flex;
                        flex-direction: column;
                        transform: translateX(110%);
                        opacity: 0;
                        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                        overflow: hidden;
                    }

                    #udio-downloader-ui.open {
                        transform: translateX(0);
                        opacity: 1;
                    }

                    #udio-downloader-toggle {
                        position: fixed;
                        top: 130px;
                        right: 20px;
                        z-index: 10003;
                        background: linear-gradient(135deg, #e30b5d 0%, #c1074f 100%);
                        color: white;
                        border: none;
                        border-radius: 50%;
                        width: 60px;
                        height: 60px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        box-shadow:
                            0 8px 25px rgba(227, 11, 93, 0.3),
                            0 0 0 1px rgba(255,255,255,0.1);
                        font-size: 28px;
                        font-weight: bold;
                        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    }

                    #udio-downloader-toggle:hover {
                        transform: scale(1.1) rotate(5deg);
                    }

                    /* Header Styles */
                    .ui-header {
                        margin: 0;
                        padding: 16px 20px;
                        background: linear-gradient(135deg, #2a2a2a 0%, #3d3d3d 100%);
                        border-bottom: 1px solid rgba(255,255,255,0.1);
                        font-size: 1.2em;
                        font-weight: 700;
                        color: #bb86fc;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        flex-shrink: 0;
                    }

                    .ui-header-stats {
                        font-size: 0.7em;
                        font-weight: 600;
                        color: #03dac6;
                        background: rgba(3, 218, 198, 0.1);
                        padding: 4px 8px;
                        border-radius: 6px;
                        border: 1px solid rgba(3, 218, 198, 0.2);
                    }

                    /* FIXED: Track list with proper scroll bar */
                    #downloader-track-list {
                        max-height: 400px;
                        min-height: 100px;
                        overflow-y: auto;
                        overflow-x: hidden;
                        padding: 8px;
                        background: rgba(30, 30, 30, 0.5);
                        flex: 1;
                        scrollbar-width: thin;
                        scrollbar-color: #555 #2d2d2d;
                    }

                    #downloader-track-list::-webkit-scrollbar {
                        width: 8px;
                    }

                    #downloader-track-list::-webkit-scrollbar-track {
                        background: #2d2d2d;
                        border-radius: 4px;
                    }

                    #downloader-track-list::-webkit-scrollbar-thumb {
                        background: linear-gradient(135deg, #555, #666);
                        border-radius: 4px;
                        border: 1px solid #444;
                    }

                    #downloader-track-list::-webkit-scrollbar-thumb:hover {
                        background: linear-gradient(135deg, #666, #777);
                    }

                    /* Controls Section */
                    #downloader-controls {
                        padding: 16px 20px;
                        border-top: 1px solid rgba(255,255,255,0.1);
                        background: #2a2a2a;
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                        flex-shrink: 0;
                    }

                    /* Queue Status */
                    #downloader-queue-status {
                        padding: 12px 20px;
                        border-top: 1px solid rgba(255,255,255,0.1);
                        background: #2a2a2a;
                        font-size: 0.75em;
                        color: #888;
                        flex-shrink: 0;
                    }

                    /* Track Items - Compact Design */
                    .track-item {
                        display: flex;
                        align-items: center;
                        padding: 12px;
                        margin: 0 4px 6px 4px;
                        background: rgba(255,255,255,0.05);
                        border-radius: 10px;
                        border: 1px solid rgba(255,255,255,0.1);
                        transition: all 0.3s ease;
                        cursor: pointer;
                        position: relative;
                        overflow: hidden;
                        min-height: 60px;
                    }

                    .track-item::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                        transition: left 0.6s ease;
                    }

                    .track-item:hover::before {
                        left: 100%;
                    }

                    .track-item:hover {
                        background: rgba(255,255,255,0.08);
                        border-color: rgba(255,255,255,0.2);
                        transform: translateY(-2px);
                        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
                    }

                    .track-item:active {
                        transform: translateY(0);
                    }

                    .track-artwork {
                        width: 45px;
                        height: 45px;
                        border-radius: 6px;
                        object-fit: cover;
                        flex-shrink: 0;
                        border: 2px solid rgba(255,255,255,0.1);
                        transition: all 0.3s ease;
                    }

                    .track-item:hover .track-artwork {
                        border-color: rgba(255,255,255,0.3);
                        transform: scale(1.05);
                    }

                    .no-artwork {
                        width: 45px;
                        height: 45px;
                        border-radius: 6px;
                        background: linear-gradient(135deg, #333 0%, #444 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #666;
                        font-size: 10px;
                        flex-shrink: 0;
                        border: 2px solid rgba(255,255,255,0.1);
                    }

                    .track-info {
                        flex-grow: 1;
                        min-width: 0;
                        margin-left: 12px;
                    }

                    .track-title {
                        font-weight: 700;
                        font-size: 0.9em;
                        color: #ffffff;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        margin-bottom: 3px;
                        line-height: 1.2;
                    }

                    .track-artist {
                        font-size: 0.75em;
                        color: #aaa;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        margin-bottom: 6px;
                    }

                    .metadata-status {
                        font-size: 0.65em;
                        font-weight: 700;
                        margin-left: 4px;
                        padding: 2px 5px;
                        border-radius: 3px;
                        text-transform: uppercase;
                        letter-spacing: 0.3px;
                    }

                    .has-metadata {
                        color: #03dac6;
                        background: rgba(3, 218, 198, 0.15);
                        border: 1px solid rgba(3, 218, 198, 0.3);
                    }

                    .no-metadata {
                        color: #ffb300;
                        background: rgba(255, 179, 0, 0.15);
                        border: 1px solid rgba(255, 179, 0, 0.3);
                    }

                    .has-artwork {
                        color: #ff9800;
                        background: rgba(255, 152, 0, 0.15);
                        border: 1px solid rgba(255, 152, 0, 0.3);
                    }

                    .has-video {
                        color: #e91e63;
                        background: rgba(233, 30, 99, 0.15);
                        border: 1px solid rgba(233, 30, 99, 0.3);
                    }

                    .has-lyrics {
                        color: #9c27b0;
                        background: rgba(156, 39, 176, 0.15);
                        border: 1px solid rgba(156, 39, 176, 0.3);
                    }

                    .manual-selection-status {
                        font-size: 0.6em;
                        font-weight: 700;
                        margin-left: 4px;
                        padding: 1px 4px;
                        border-radius: 3px;
                        background: rgba(227, 11, 93, 0.2);
                        color: #e30b5d;
                        border: 1px solid rgba(227, 11, 93, 0.3);
                    }

                    /* Compact Export Options */
                    .export-options {
                        display: flex;
                        gap: 4px;
                        flex-wrap: wrap;
                    }

                    .export-btn {
                        padding: 4px 8px;
                        font-size: 0.65em;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        font-weight: 700;
                        opacity: 0.9;
                        text-transform: uppercase;
                        letter-spacing: 0.3px;
                    }

                    .export-btn:hover {
                        opacity: 1;
                        transform: translateY(-1px);
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    }

                    .export-btn:active {
                        transform: translateY(0);
                    }

                    .export-mp3 {
                        background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
                        color: white;
                    }

                    .export-mp4 {
                        background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%);
                        color: white;
                    }

                    .export-art {
                        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
                        color: white;
                    }

                    .export-lyrics {
                        background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
                        color: white;
                    }

                    .export-metadata {
                        background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
                        color: white;
                    }

                    .remove-btn {
                        background: linear-gradient(135deg, #ff5252 0%, #d32f2f 100%);
                        color: white;
                        border: none;
                        border-radius: 50%;
                        width: 26px;
                        height: 26px;
                        cursor: pointer;
                        font-weight: bold;
                        flex-shrink: 0;
                        margin-left: 10px;
                        transition: all 0.3s ease;
                        font-size: 14px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        opacity: 0.7;
                    }

                    .remove-btn:hover {
                        opacity: 1;
                        transform: scale(1.1) rotate(90deg);
                        box-shadow: 0 4px 12px rgba(255, 82, 82, 0.4);
                    }

                    .remove-btn:active {
                        transform: scale(0.95) rotate(0deg);
                    }

                    /* Compact Action Buttons */
                    .downloader-btn {
                        flex-grow: 1;
                        border: none;
                        padding: 12px 16px;
                        border-radius: 8px;
                        font-weight: 700;
                        cursor: pointer;
                        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                        font-size: 0.85em;
                        position: relative;
                        overflow: hidden;
                        min-width: 110px;
                    }

                    .downloader-btn::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                        transition: left 0.6s ease;
                    }

                    .downloader-btn:hover::before {
                        left: 100%;
                    }

                    .downloader-btn:active:not(:disabled) {
                        transform: translateY(0);
                    }

                    .downloader-btn:disabled {
                        background: #444 !important;
                        color: #888 !important;
                        cursor: not-allowed;
                        transform: none !important;
                        box-shadow: none !important;
                    }

                    #scan-page-btn {
                        background: linear-gradient(135deg, #3f51b5 0%, #303f9f 100%);
                        color: white;
                        flex-basis: 100%;
                    }

                    #force-rescan-btn {
                        background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
                        color: white;
                    }

                    #download-all-btn {
                        background: linear-gradient(135deg, #03dac6 0%, #00c4b4 100%);
                        color: #1a1a1a;
                        font-weight: 800;
                    }

                    #clear-list-btn {
                        background: linear-gradient(135deg, #ffb300 0%, #ff8f00 100%);
                        color: #1a1a1a;
                        font-weight: 800;
                    }

                    #auto-capture-toggle {
                        flex-basis: 100%;
                        background: linear-gradient(135deg, #6200ee 0%, #3700b3 100%);
                        color: white;
                    }

                    #auto-capture-toggle.active {
                        background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
                    }

                    #manual-capture-btn {
                        background: linear-gradient(135deg, #e30b5d 0%, #c1074f 100%);
                        color: white;
                        flex-basis: 100%;
                    }

                    /* Compact Queue Stats */
                    .queue-stats {
                        display: flex;
                        flex-direction: row;
                        justify-content: space-between;
                        align-items: center;
                        gap: 15px;
                    }

                    .stat-item {
                        display: flex;
                        flex-direction: row;
                        align-items: center;
                        gap: 4px;
                        flex: 1;
                        justify-content: center;
                    }

                    .stat-value {
                        font-weight: 800;
                        color: #03dac6;
                        font-size: 1em;
                        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    }

                    .stat-label {
                        font-size: 0.65em;
                        opacity: 0.8;
                        text-transform: uppercase;
                        letter-spacing: 0.3px;
                        white-space: nowrap;
                    }

                    .manual-stats {
                        display: flex;
                        justify-content: center;
                        margin-top: 6px;
                        padding-top: 6px;
                        border-top: 1px solid rgba(255,255,255,0.1);
                    }

                    .manual-stat {
                        font-size: 0.65em;
                        color: #e30b5d;
                        background: rgba(227, 11, 93, 0.1);
                        padding: 2px 6px;
                        border-radius: 4px;
                        border: 1px solid rgba(227, 11, 93, 0.2);
                    }

                    /* Options Section */
                    #downloader-options {
                        flex-basis: 100%;
                        display: flex;
                        flex-direction: column;
                        gap: 12px;
                        padding: 16px;
                        color: #ccc;
                        font-size: 0.8em;
                        border-top: 1px solid rgba(255,255,255,0.1);
                        margin-top: 6px;
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 10px;
                    }

                    .options-row {
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        flex-wrap: wrap;
                    }

                    .checkbox-container {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        cursor: pointer;
                        padding: 4px 0;
                        transition: all 0.2s ease;
                    }

                    .checkbox-container:hover {
                        color: #fff;
                    }

                    .options-label {
                        min-width: 120px;
                        font-weight: 600;
                        color: #fff;
                    }

                    .checkbox-container input[type="checkbox"] {
                        width: 16px;
                        height: 16px;
                        cursor: pointer;
                    }

                    /* Progress Bar */
                    .progress-bar {
                        width: 100%;
                        height: 6px;
                        background: rgba(255,255,255,0.1);
                        border-radius: 3px;
                        margin-top: 8px;
                        overflow: hidden;
                        position: relative;
                    }

                    .progress-fill {
                        height: 100%;
                        background: linear-gradient(90deg, #03dac6, #00c4b4);
                        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                        border-radius: 3px;
                        position: relative;
                    }

                    .progress-fill::after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                        animation: shimmer 2s infinite;
                    }

                    /* Compact Empty State */
                    .empty-state {
                        text-align: center;
                        padding: 40px 20px;
                        color: #666;
                        font-style: italic;
                        min-height: 120px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    }

                    .empty-state .icon {
                        font-size: 2em;
                        margin-bottom: 12px;
                        opacity: 0.5;
                        animation: float 3s ease-in-out infinite;
                    }

                    .empty-state .hint {
                        font-size: 0.75em;
                        margin-top: 8px;
                        opacity: 0.7;
                        line-height: 1.3;
                    }

                    /* Toast Notifications */
                    .udio-toast {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 14px 18px;
                        border-radius: 10px;
                        font-weight: 600;
                        z-index: 10004;
                        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                        border: 1px solid rgba(255,255,255,0.1);
                        transform: translateX(120%);
                        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                        max-width: 280px;
                        font-size: 0.85em;
                    }

                    .udio-toast.show {
                        transform: translateX(0);
                    }

                    .udio-toast.success {
                        background: linear-gradient(135deg, rgba(76, 175, 80, 0.9), rgba(56, 142, 60, 0.9));
                        color: white;
                    }

                    .udio-toast.error {
                        background: linear-gradient(135deg, rgba(244, 67, 54, 0.9), rgba(211, 47, 47, 0.9));
                        color: white;
                    }

                    .udio-toast.warning {
                        background: linear-gradient(135deg, rgba(255, 179, 0, 0.9), rgba(255, 143, 0, 0.9));
                        color: #1a1a1a;
                    }

                    .udio-toast.info {
                        background: linear-gradient(135deg, rgba(33, 150, 243, 0.9), rgba(21, 101, 192, 0.9));
                        color: white;
                    }

                    .udio-toast.manual {
                        background: linear-gradient(135deg, rgba(227, 11, 93, 0.9), rgba(193, 7, 79, 0.9));
                        color: white;
                    }

                    /* Context Menu */
                    #udio-context-menu {
                        position: fixed;
                        background: #2d2d2d;
                        border: 1px solid #555;
                        border-radius: 8px;
                        padding: 6px 0;
                        z-index: 10005;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                        min-width: 180px;
                        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                    }

                    .context-menu-item {
                        padding: 10px 14px;
                        cursor: pointer;
                        color: #e0e0e0;
                        font-size: 0.85em;
                        transition: all 0.2s ease;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }

                    .context-menu-item:hover {
                        background: rgba(227, 11, 93, 0.3);
                        color: #fff;
                    }

                    .context-menu-item:first-child {
                        border-radius: 6px 6px 0 0;
                    }

                    .context-menu-item:last-child {
                        border-radius: 0 0 6px 6px;
                    }

                    .manual-selection-highlight {
                        outline: 2px solid #e30b5d !important;
                        outline-offset: 2px;
                        border-radius: 4px;
                        animation: pulse-highlight 2s infinite;
                    }

                    /* Responsive Design */
                    @media (max-width: 768px) {
                        #udio-downloader-ui {
                            width: 95vw;
                            right: 2.5vw;
                            max-width: none;
                            max-height: 80vh;
                        }

                        #downloader-track-list {
                            max-height: 300px;
                        }

                        .track-item {
                            padding: 10px;
                            margin: 0 2px 4px 2px;
                            min-height: 55px;
                        }

                        .track-artwork, .no-artwork {
                            width: 40px;
                            height: 40px;
                        }

                        .export-options {
                            gap: 2px;
                        }

                        .export-btn {
                            padding: 3px 6px;
                            font-size: 0.6em;
                        }

                        .downloader-btn {
                            flex-basis: 100%;
                            padding: 10px 14px;
                            font-size: 0.8em;
                        }

                        #udio-context-menu {
                            min-width: 160px;
                            font-size: 0.8em;
                        }
                    }

                    /* High-density screens */
                    @media (max-height: 700px) {
                        #downloader-track-list {
                            max-height: 300px;
                        }

                        .track-item {
                            min-height: 50px;
                            padding: 8px;
                        }

                        .track-artwork, .no-artwork {
                            width: 40px;
                            height: 40px;
                        }

                        .empty-state {
                            padding: 30px 15px;
                            min-height: 100px;
                        }

                        .empty-state .icon {
                            font-size: 1.5em;
                        }
                    }

                    /* Very small screens */
                    @media (max-height: 500px) {
                        #udio-downloader-ui {
                            max-height: 70vh;
                        }

                        #downloader-track-list {
                            max-height: 200px;
                        }
                    }

                    .loading {
                        position: relative;
                        overflow: hidden;
                    }

                    .loading::after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                        animation: loading 1.5s infinite;
                    }

                    .downloader-btn:focus-visible, .export-btn:focus-visible, .remove-btn:focus-visible {
                        outline: 2px solid #03dac6;
                        outline-offset: 2px;
                    }

                    .checkbox-container:focus-within {
                        color: #03dac6;
                    }

                    .context-menu-item:focus {
                        background: rgba(227, 11, 93, 0.3);
                        color: #fff;
                        outline: none;
                    }

                    .downloader-btn.celebrate {
                        animation: celebrate-pulse 2s ease-in-out;
                        background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%) !important;
                    }

                    .queue-empty-state {
                        text-align: center;
                        padding: 16px;
                        color: #03dac6;
                        font-style: italic;
                        border: 2px dashed rgba(3, 218, 198, 0.3);
                        border-radius: 10px;
                        margin: 8px;
                        background: rgba(3, 218, 198, 0.05);
                        font-size: 0.8em;
                    }

                    .queue-empty-state .icon {
                        font-size: 1.5em;
                        margin-bottom: 8px;
                        display: block;
                        animation: float 3s ease-in-out infinite;
                    }

                    .stat-value.celebrating {
                        animation: count-celebration 1s ease-in-out;
                    }

                    @keyframes pulse-glow {
                        0%, 100% {
                            box-shadow: 0 8px 25px rgba(227, 11, 93, 0.3);
                        }
                        50% {
                            box-shadow: 0 8px 30px rgba(227, 11, 93, 0.6), 0 0 20px rgba(227, 11, 93, 0.4);
                        }
                    }

                    @keyframes shimmer {
                        0% {
                            left: -100%;
                        }
                        100% {
                            left: 100%;
                        }
                    }

                    @keyframes float {
                        0%, 100% {
                            transform: translateY(0);
                        }
                        50% {
                            transform: translateY(-8px);
                        }
                    }

                    @keyframes pulse-highlight {
                        0%, 100% {
                            outline-color: #e30b5d;
                        }
                        50% {
                            outline-color: #ff6b9d;
                        }
                    }

                    @keyframes loading {
                        0% {
                            left: -100%;
                        }
                        100% {
                            left: 100%;
                        }
                    }

                    @keyframes celebrate-pulse {
                        0%, 100% {
                            transform: scale(1);
                            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
                        }
                        25% {
                            transform: scale(1.1);
                            box-shadow: 0 12px 30px rgba(76, 175, 80, 0.6);
                        }
                        50% {
                            transform: scale(1.05);
                            box-shadow: 0 15px 35px rgba(76, 175, 80, 0.8);
                        }
                        75% {
                            transform: scale(1.08);
                            box-shadow: 0 12px 30px rgba(76, 175, 80, 0.6);
                        }
                    }

                    @keyframes count-celebration {
                        0% {
                            transform: scale(1);
                            color: #03dac6;
                        }
                        50% {
                            transform: scale(1.8) rotate(10deg);
                            color: #ffeb3b;
                        }
                        100% {
                            transform: scale(1.2);
                            color: #4caf50;
                        }
                    }

                    /* Additional stats row for options */
                    .stats-row {
                        display: flex;
                        justify-content: space-between;
                        gap: 8px;
                        margin-top: 8px;
                    }

                    .stats-row .stat-item {
                        flex-direction: column;
                        gap: 2px;
                    }

                    .stats-row .stat-value {
                        font-size: 0.9em;
                    }

                    .stats-row .stat-label {
                        font-size: 0.6em;
                    }

                    /* Failed items section */
                    .failed-info {
                        font-size: 0.75em;
                        color: #ff9800;
                        text-align: center;
                        flex-basis: 100%;
                        margin-bottom: 8px;
                    }

                    .retry-failed-btn {
                        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
                        color: #1a1a1a;
                        font-weight: 800;
                        flex-basis: 100%;
                    }

                    /* Pulse attention for buttons */
                    .pulse-attention {
                        animation: pulse-glow 2s ease-in-out infinite;
                    }
                `;

                GM_addStyle(css);
            },

            /**
             * Create main UI container
             */
            createContainer() {
                var uiContainer = document.createElement('div');
                uiContainer.id = 'udio-downloader-ui';
                uiContainer.setAttribute('role', 'dialog');
                uiContainer.setAttribute('aria-label', 'Udio Download Manager');
                uiContainer.innerHTML = `
                    <h3 class="ui-header">
                        <span>🎵 Udio Downloader</span>
                        <span class="ui-header-stats" id="ui-header-stats">0 tracks</span>
                    </h3>
                    <div id="downloader-track-list" role="list" aria-label="Captured tracks"></div>
                    <div id="downloader-controls"></div>
                    <div id="downloader-queue-status">
                        <div class="queue-stats">
                            <div class="stat-item">
                                <span class="stat-value" id="queue-count">0</span>
                                <span class="stat-label">Queued</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value" id="processing-count">0</span>
                                <span class="stat-label">Processing</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value" id="failed-count">0</span>
                                <span class="stat-label">Failed</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value" id="captured-count">0</span>
                                <span class="stat-label">Captured</span>
                            </div>
                        </div>
                        <div class="manual-stats" id="manual-stats" style="display: none;">
                            <span class="manual-stat" id="manual-count">0 manual in progress</span>
                        </div>
                    </div>
                `;

                document.body.appendChild(uiContainer);
            },

            /**
             * Create toggle button
             */
            createToggleButton() {
                var toggleButton = document.createElement('button');
                toggleButton.id = 'udio-downloader-toggle';
                toggleButton.innerHTML = '📥';
                toggleButton.title = 'Show/Hide Download Manager';
                toggleButton.setAttribute('aria-label', 'Toggle download manager');
                toggleButton.setAttribute('aria-expanded', 'false');

                document.body.appendChild(toggleButton);

                this.addEventListener(toggleButton, 'click', () => {
                    var uiContainer = document.getElementById('udio-downloader-ui');
                    var isOpen = uiContainer.classList.toggle('open');
                    toggleButton.setAttribute('aria-expanded', isOpen.toString());
                    GM_setValue('isUIOpen', isOpen);

                    if (isOpen) {
                        this.scheduleRender(); // FIX: Call the correct render scheduler
                    }
                });

                if (GM_getValue('isUIOpen', false)) {
                    var uiContainer = document.getElementById('udio-downloader-ui');
                    uiContainer.classList.add('open');
                    toggleButton.setAttribute('aria-expanded', 'true');
                }
            },

            /**
             * Initialize event listener system
             */
            initializeEventSystem() {
                this.eventListeners.clear();
            },

            /**
             * Add event listener with proper cleanup
             */
            addEventListener(element, event, handler) {
                element.addEventListener(event, handler);
                var key = `${event}-${Math.random().toString(36).substr(2, 9)}`;
                this.eventListeners.set(key, { element, event, handler });
            },

            /**
             * NEW: Force refresh UI when metadata becomes available
             */
            forceRefreshForMetadata() {
                this.state.log('[UI] Force refreshing UI for metadata display');

                // Update all UI components
                this.updateHeaderStats();
                this.updateQueueStatus();
                this.updateManualSelectionStats();
                this.updateTrackList();
                this.updateControls();

                // Mark that we've processed metadata updates
                var trackList = document.getElementById('downloader-track-list');
                if (trackList) {
                    trackList.removeAttribute('data-force-update');
                }

                this.state.debug('[UI] Complete UI refresh completed for metadata');
            },

    /**
             * NEW: Starts the optimized rendering loop. This replaces the old setInterval.
             */
            startAutoRender() {
                        // We only need to listen for state changes. The UI will only render when data actually changes.
                        window.addEventListener('udio-dl-state-change', () => this.scheduleRender());
                    },

            /**
             * NEW: Schedules a single, debounced render using the browser's native requestAnimationFrame.
             * This is the new primary way to trigger a UI update.
             */
            scheduleRender() {
                // If a render is already scheduled for the next frame, do nothing.
                if (this.isRendering) {
                    return;
                }
                this.isRendering = true;

                // Ask the browser to call our render function at the next available opportunity.
                requestAnimationFrame(() => this._render());
            },

        /**
             * NEW: The core render method, now prefixed with an underscore to indicate it's for internal use.
             * It contains all the logic for updating the UI.
             */
            _render() {
                try {
                    if (this.isDownloading) return;

                    // Batch all DOM reads and writes.
                    this._updateHeaderStatsOptimized();
                    this._updateQueueStatusOptimized();
                    this._updateManualSelectionStatsOptimized();

                    const uiContainer = document.getElementById('udio-downloader-ui');
                    if (uiContainer && uiContainer.classList.contains('open')) {
                        this.updateTrackList(); // This is the NEW intelligent function
                        this.updateControls();
                    }
                } catch (error) {
                    this.state.error('[UI] Render error:', error);
                } finally {
                    this.isRendering = false; // Allow the next render to be scheduled
                }
            },

            /**
             * NEW: Optimized version of updateHeaderStats.
             */
            _updateHeaderStatsOptimized() {
                const headerStats = document.getElementById('ui-header-stats');
                if (headerStats) {
                    const totalTracks = this.state.capturedTracks.size;
                    const tracksWithArt = Array.from(this.state.capturedTracks.values()).filter(track => track.albumArt).length;
                    const artPercentage = totalTracks > 0 ? Math.round((tracksWithArt / totalTracks) * 100) : 0;

                    const newText = `${totalTracks} tracks • ${artPercentage}% art`;
                    const newTitle = `${totalTracks} total tracks, ${tracksWithArt} with artwork`;

                    // Only write to the DOM if the content has changed.
                    if (headerStats.textContent !== newText) {
                        headerStats.textContent = newText;
                    }
                    if (headerStats.title !== newTitle) {
                        headerStats.title = newTitle;
                    }
                }
            },

            /**
             * NEW: Optimized version of updateQueueStatus.
             */
            _updateQueueStatusOptimized() {
                const elements = {
                    queue: document.getElementById('queue-count'),
                    processing: document.getElementById('processing-count'),
                    failed: document.getElementById('failed-count'),
                    captured: document.getElementById('captured-count'),
                };

                if (!elements.queue) return; // Assume others are missing too if one is.

                try {
                    const storageQueue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                    const failures = this.state.safeJSONParse(GM_getValue('failedUrls', '[]'), []);
                    const inMemoryQueue = this.queueManager?.inMemoryQueue?.length || 0;

                    const counts = {
                        queue: storageQueue.length + inMemoryQueue,
                        processing: this.state.activeRequests || 0,
                        failed: failures.length || 0,
                        captured: this.state.capturedTracks?.size || 0,
                    };

                    // Update each element only if its value has changed.
                    for (const key in counts) {
                        if (elements[key] && elements[key].textContent !== String(counts[key])) {
                            elements[key].textContent = counts[key];
                        }
                    }

                    this.showQueueEmptyState(counts.queue, counts.processing, counts.failed, counts.captured);

                } catch (error) {
                    this.state.error('[UI] Error in _updateQueueStatusOptimized:', error);
                }
            },

            /**
             * NEW: Optimized version of updateManualSelectionStats.
             */
            _updateManualSelectionStatsOptimized() {
                const manualStatsEl = document.getElementById('manual-stats');
                const manualCountEl = document.getElementById('manual-count');

                if (manualStatsEl && manualCountEl) {
                    const manualCount = this.manualSelectionsInProgress.size;
                    if (manualCount > 0) {
                        manualStatsEl.style.display = 'flex';
                        const newText = `${manualCount} manual selection${manualCount !== 1 ? 's' : ''} in progress`;
                        if (manualCountEl.textContent !== newText) {
                            manualCountEl.textContent = newText;
                        }
                    } else {
                        if (manualStatsEl.style.display !== 'none') {
                            manualStatsEl.style.display = 'none';
                        }
                    }
                }
            },

            /**
             * SIMPLIFIED: Setup global listeners
             */
            setupGlobalListeners() {
                // Remove existing listeners
                this.eventListeners.forEach(({ element, event, handler }) => {
                    element.removeEventListener(event, handler);
                });
                this.eventListeners.clear();

                // SIMPLE: Update UI on any relevant event
                var handleUIUpdate = (event) => {
                    this.state.debug(`[UI] Event: ${event.type}`);
                    this.scheduleRender();
                };

                var events = [
                    'udio-dl-player-track-updated',
                    'udio-dl-manual-selection-complete',
                    'udio-dl-state-change'
                ];

                events.forEach(eventName => {
                    var handler = (event) => handleUIUpdate(event);
                    window.addEventListener(eventName, handler, { passive: true });
                    this.eventListeners.set(`${eventName}-global`, {
                        element: window,
                        event: eventName,
                        handler
                    });
                });

                this.state.log('[UI] Simplified event system initialized');
            },

            /**
             * NEW: Show queue empty state with celebration animation
             */
            showQueueEmptyState(queueCount, processingCount, failedCount, capturedCount) {
                // Only show when queue is completely empty and no active processing
                var isQueueEmpty = queueCount === 0 && processingCount === 0 && failedCount === 0;

                if (isQueueEmpty && capturedCount > 0) {
                    // Check if we haven't shown the celebration recently
                    var lastCelebration = GM_getValue('lastQueueCelebration', 0);
                    var now = Date.now();

                    if (now - lastCelebration > 30000) { // Only show every 30 seconds
                        this.celebrateQueueCompletion();
                        GM_setValue('lastQueueCelebration', now);
                    }
                } else if (isQueueEmpty && capturedCount === 0) {
                    // Show initial empty state - ALWAYS show on fresh start/reset
                    this.showInitialEmptyState();

                    // NEW: Special animation for fresh reset state
                    this.showFreshStartAnimation();
                }
            },

            /**
             * NEW: Show fresh start animation for reset/empty state
             */
            showFreshStartAnimation() {
                // Check if this is a fresh start (no tracks, no queue, no processing)
                var queueData = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                var queueCount = Array.isArray(queueData) ? queueData.length : 0;
                var capturedCount = this.state.capturedTracks ? this.state.capturedTracks.size : 0;
                var processingCount = this.state.activeRequests || 0;

                var isFreshStart = queueCount === 0 && capturedCount === 0 && processingCount === 0;

                if (isFreshStart) {
                    // Show fresh start animation
                    var capturedEl = document.getElementById('captured-count');
                    if (capturedEl) {
                        capturedEl.style.transition = 'all 0.5s ease';
                        capturedEl.style.transform = 'scale(1.3)';
                        capturedEl.style.color = '#03dac6';

                        setTimeout(() => {
                            capturedEl.style.transform = 'scale(1)';
                            capturedEl.style.color = '#03dac6';
                        }, 800);
                    }

                    // Pulse the scan button to encourage action
                    var scanBtn = document.getElementById('scan-page-btn');
                    if (scanBtn) {
                        scanBtn.classList.add('pulse-attention');
                        setTimeout(() => scanBtn.classList.remove('pulse-attention'), 2000);
                    }

                    // Show welcome message (but only once per session to avoid spam)
                    if (!this._hasShownFreshStartMessage) {
                        setTimeout(() => {
                            this.showToast('🚀 Ready to capture songs! Use auto-capture or right-click links', 'info', 4000);
                            this._hasShownFreshStartMessage = true;
                        }, 1000);
                    }
                }
            },

            /**
             * NEW: Celebration animation for queue completion
             */
            celebrateQueueCompletion() {
                this.state.log('[UI] Queue completed! Showing celebration');

                // Show celebration toast
                this.showToast('🎉 All songs processed! Ready for download.', 'success', 5000);

                // Pulse the download button
                var downloadBtn = document.getElementById('download-all-btn');
                if (downloadBtn) {
                    downloadBtn.classList.add('celebrate');
                    setTimeout(() => downloadBtn.classList.remove('celebrate'), 3000);
                }

                // Animate the captured count
                var capturedEl = document.getElementById('captured-count');
                if (capturedEl) {
                    this.animateCelebration(capturedEl);
                }
            },

            /**
             * NEW: Initial empty state guidance
             */
            showInitialEmptyState() {
                var manualCount = this.manualSelectionsInProgress.size;
                var queueData = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                var queueCount = queueData.length;

                // Update the empty state hint dynamically
                var emptyState = document.querySelector('.empty-state');
                if (emptyState) {
                    var hintContent = '';

                    if (manualCount > 0) {
                        hintContent = '<div class="hint">🔄 Processing manual selections...</div>';
                    } else if (queueCount > 0) {
                        hintContent = `<div class="hint">⏳ Processing ${queueCount} songs in queue...</div>`;
                    } else {
                        hintContent = `
                            <div class="hint">
                                💡 Get started:<br>
                                • Enable auto-capture below<br>
                                • Right-click song links<br>
                                • Or Ctrl+Click to capture<br>
                                <small>Songs will appear here automatically</small>
                            </div>
                        `;
                    }

                    var hintElement = emptyState.querySelector('.hint');
                    if (hintElement) {
                        hintElement.innerHTML = hintContent;
                    }
                }
            },

            /**
             * NEW: Enhanced celebration animation
             */
            animateCelebration(element) {
                if (!element) return;

                // Store original values
                var originalTransform = element.style.transform;
                var originalColor = element.style.color;

                // Celebration animation sequence
                element.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                element.style.transform = 'scale(1.5) rotate(360deg)';
                element.style.color = '#ffeb3b';

                setTimeout(() => {
                    element.style.transform = 'scale(1.2)';
                    element.style.color = '#4caf50';
                }, 500);

                setTimeout(() => {
                    element.style.transform = originalTransform;
                    element.style.color = originalColor;
                }, 1000);
            },

            /**
             * NEW METHOD: Add visual animation when counts change
             */
            animateCountChange(element, newCount) {
                if (!element._lastCount || element._lastCount !== newCount) {
                    element._lastCount = newCount;
                    element.style.transform = 'scale(1.1)';
                    element.style.color = '#ffeb3b';

                    setTimeout(() => {
                        element.style.transform = 'scale(1)';
                        element.style.color = '#03dac6';
                    }, 300);
                }
            },

            /**
             * Legacy method for compatibility - creates full track list HTML
             */
            createTrackListHTML() {
                if (this.state.capturedTracks.size === 0) {
                    return this.createEmptyState();
                }

                let html = '';
                for (const [url, info] of this.state.capturedTracks.entries()) {
                    const trackDataVersion = this.generateTrackDataVersion(info);
                    html += `
                        <div class="track-item" data-url="${url}" data-version="${trackDataVersion}" role="listitem">
                            ${this.createTrackItemInnerHTML(url, info)}
                        </div>
                    `;
                }
                return html;
            },

            /**
             * EMERGENCY HOTFIX: Force immediate metadata display
             */
            forceMetadataDisplayNow() {
                this.state.log('[UI] 🚨 EMERGENCY: Forcing immediate metadata display');

                // Completely rebuild the entire UI
                var trackList = document.getElementById('downloader-track-list');
                if (trackList) {
                    if (this.state.capturedTracks.size === 0) {
                        trackList.innerHTML = this.createEmptyState();
                    } else {
                        trackList.innerHTML = this.createTrackListHTML();
                        this.attachTrackListEvents();
                    }
                    trackList.removeAttribute('data-force-update');
                }

                // Update all components
                this.updateHeaderStats();
                this.updateQueueStatus();
                this.updateManualSelectionStats();
                this.updateControls();

                this.state.log('[UI] 🚨 EMERGENCY: Complete UI rebuild completed');

                // Show confirmation
                this.showToast('Metadata display forced!', 'success', 2000);
            },

            /**
             * Intelligently updates the track list in the UI using a "diffing" approach.
             * Instead of rebuilding the entire list, it only adds, removes, or updates
             * the specific elements that have changed, dramatically improving performance
             * for large collections.
             */
            updateTrackList() {
                const trackList = document.getElementById('downloader-track-list');
                if (!trackList) return;

                // Use the version number from the State to check if an update is even needed.
                if (this.lastTrackVersion === this.state.trackVersion && !trackList.hasAttribute('data-force-update')) {
                    return; // No data has changed, so no UI work is needed. This is a huge performance win.
                }

                // Handle the simple case of an empty list.
                if (this.state.capturedTracks.size === 0) {
                    if (!trackList.querySelector('.empty-state')) {
                        trackList.innerHTML = this.createEmptyState();
                    }
                    this.lastTrackVersion = this.state.trackVersion; // Sync version
                    return;
                }

                // --- Intelligent Diffing Logic ---
                const emptyState = trackList.querySelector('.empty-state');
                if (emptyState) emptyState.remove();

                // 1. Create a map of existing DOM elements for fast O(1) lookup by URL.
                const existingDOMElements = new Map(
                    Array.from(trackList.querySelectorAll('.track-item')).map(el => [el.dataset.url, el])
                );
                const stateTrackUrls = new Set(this.state.capturedTracks.keys());

                // 2. Removal Pass: Iterate through what's in the DOM and remove anything not in the current state.
                existingDOMElements.forEach((element, url) => {
                    if (!stateTrackUrls.has(url)) {
                        element.remove();
                        existingDOMElements.delete(url);
                    }
                });

                // 3. Add/Update Pass: Iterate through the current state data.
                for (const [url, info] of this.state.capturedTracks.entries()) {
                    const existingEl = existingDOMElements.get(url);
                    const trackDataVersion = this.generateTrackDataVersion(info); // Generate a "signature" for the track's UI state.

                    if (existingEl) {
                        // Element already exists in the DOM. Check if its content needs updating.
                        if (existingEl.dataset.version !== trackDataVersion) {
                            // The data is different, so only replace this specific element's HTML.
                            // This is far cheaper than rebuilding the whole list.
                            existingEl.innerHTML = this.createTrackItemInnerHTML(url, info);
                            existingEl.dataset.version = trackDataVersion; // Update its version tag.
                        }
                    } else {
                        // This is a new track that isn't in the DOM yet. Create and append its element.
                        const newEl = document.createElement('div');
                        newEl.className = 'track-item';
                        newEl.dataset.url = url;
                        newEl.dataset.version = trackDataVersion;
                        newEl.setAttribute('role', 'listitem');
                        newEl.innerHTML = this.createTrackItemInnerHTML(url, info);
                        trackList.appendChild(newEl);
                    }
                }

                // Sync the UI's version with the state's version for the next check.
                this.lastTrackVersion = this.state.trackVersion;
                trackList.removeAttribute('data-force-update');
            },

            // You will also need to add/update this helper function inside the UI object
            createTrackItemInnerHTML(url, info) {
                const hasFullInfo = info.prompt && info.creationDate;
                const hasArtwork = !!info.albumArt;
                const hasVideo = !!info.videoUrl;
                const hasLyrics = !!info.lyrics;

                const statusHTML = this.createStatusHTML(hasFullInfo, hasArtwork, hasVideo, hasLyrics);
                const artworkHTML = this.createArtworkHTML(info.albumArt);
                const exportHTML = this.createExportHTML(url, hasVideo, hasArtwork, hasLyrics);
                const manualBadge = info.captureMethod === 'manual' ? '<span class="manual-selection-status">Manual</span>' : '';

                return `
                    ${artworkHTML}
                    <div class="track-info">
                        <div class="track-title" title="${this.escapeHTML(info.title)}">${this.escapeHTML(info.title)}</div>
                        <div class="track-artist" title="${this.escapeHTML(info.artist)}">
                            ${this.escapeHTML(info.artist)} ${statusHTML} ${manualBadge}
                        </div>
                        ${exportHTML}
                    </div>
                    <button class="remove-btn" data-url="${url}" title="Remove from list" aria-label="Remove track">
                        ×
                    </button>
                `;
            },

            /**
             * Generates a simple "signature" or "version" string for a track's data.
             * This is used by the diffing logic in updateTrackList to quickly check if a
             * track's UI needs to be re-rendered.
             * @param {object} info - The track's metadata.
             * @returns {string} A version string representing the track's UI state.
             */
            generateTrackDataVersion(info) {
                const hasFullInfo = info.prompt && info.creationDate;
                const hasArtwork = !!info.albumArt;
                const hasVideo = !!info.videoUrl;
                const hasLyrics = !!info.lyrics;
                const captureMethod = info.captureMethod || 'auto';
                // Create a simple version string. If any of these values change, the string will be different.
                return `${info.title}-${info.artist}-${hasFullInfo}-${hasArtwork}-${hasVideo}-${hasLyrics}-${captureMethod}`;
            },

            /**
             * ENHANCED: Create empty state with better messaging
             */
            createEmptyState() {
                var manualCount = this.manualSelectionsInProgress.size;
                var queueData = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                var queueCount = queueData.length;

                var hint = '';

                if (manualCount > 0) {
                    hint = '<div class="hint">🔄 Processing manual selections...</div>';
                } else if (queueCount > 0) {
                    hint = `<div class="hint">⏳ Processing ${queueCount} songs in queue...</div>`;
                } else {
                    hint = `
                        <div class="hint">
                            💡 Enable auto-capture or:<br>
                            • Right-click song links<br>
                            • Or Ctrl+Click to capture<br>
                            • Songs will appear here automatically
                        </div>
                    `;
                }

                return `
                    <div class="empty-state">
                        <div class="icon">🎵</div>
                        <div>No tracks captured yet</div>
                        ${hint}
                    </div>
                `;
            },

            /**
             * Create status indicator HTML
             */
            createStatusHTML(hasFullInfo, hasArtwork, hasVideo, hasLyrics) {
                var status = '';
                if (hasFullInfo) status += '<span class="metadata-status has-metadata">Full</span>';
                if (hasArtwork) status += '<span class="metadata-status has-artwork">Art</span>';
                if (hasVideo) status += '<span class="metadata-status has-video">Video</span>';
                if (hasLyrics) status += '<span class="metadata-status has-lyrics">Lyrics</span>';
                if (!hasFullInfo && !hasArtwork && !hasVideo && !hasLyrics) {
                    status = '<span class="metadata-status no-metadata">Basic</span>';
                }
                return status;
            },

            /**
             * Create artwork HTML with error handling
             */
            createArtworkHTML(albumArt) {
                if (albumArt) {
                    return `
                        <img src="${albumArt}"
                            class="track-artwork"
                            alt="Album artwork"
                            loading="lazy" />
                    `;
                }
                return '<div class="no-artwork">No Art</div>';
            },

        /**
             * Create export options HTML with new options
             */
            createExportHTML(url, hasVideo, hasArtwork, hasLyrics) {
                return `
                    <div class="export-options">
                        ${DOWNLOAD_OPTIONS.DOWNLOAD_AUDIO ? `
                            <button class="export-btn export-mp3" data-url="${url}" data-type="mp3" title="Download MP3">
                                MP3
                            </button>
                        ` : ''}
                        ${hasVideo && DOWNLOAD_OPTIONS.DOWNLOAD_VIDEO ? `
                            <button class="export-btn export-mp4" data-url="${url}" data-type="mp4" title="Download MP4 Video">
                                MP4
                            </button>
                        ` : ''}
                        ${hasArtwork && DOWNLOAD_OPTIONS.DOWNLOAD_ART ? `
                            <button class="export-btn export-art" data-url="${url}" data-type="art" title="Download Album Art">
                                Art
                            </button>
                        ` : ''}
                        ${hasLyrics && DOWNLOAD_OPTIONS.DOWNLOAD_LYRICS ? `
                            <button class="export-btn export-lyrics" data-url="${url}" data-type="lyrics" title="Download Lyrics">
                                Lyrics
                            </button>
                        ` : ''}
                        <button class="export-btn export-metadata" data-url="${url}" data-type="metadata" title="Download Metadata">
                            Info
                        </button>
                    </div>
                `;
            },

            /**
             * Attach event listeners to track list
             */
            attachTrackListEvents() {
                const trackList = document.getElementById('downloader-track-list');
                if (!trackList) return;

                // Remove the old listener to prevent duplicates if this function is ever called again.
                if (this._trackListClickHandler) {
                    trackList.removeEventListener('click', this._trackListClickHandler);
                }

                // The single event handler for all clicks inside the track list.
                this._trackListClickHandler = (e) => {
                    const target = e.target;

                    const removeBtn = target.closest('.remove-btn');
                    if (removeBtn) {
                        e.stopPropagation();
                        this.handleRemoveTrack(removeBtn.dataset.url);
                        return;
                    }

                    const exportBtn = target.closest('.export-btn');
                    if (exportBtn) {
                        e.stopPropagation();
                        this.exportSingleTrack(exportBtn.dataset.url, exportBtn.dataset.type);
                        return;
                    }

                    const trackItem = target.closest('.track-item');
                    if (trackItem) {
                        this.handleTrackClick(trackItem.dataset.url);
                    }
                };

                trackList.addEventListener('click', this._trackListClickHandler);

                // Attaching artwork error handlers still needs to be done individually, but now
                // it only runs once to set up the main delegated listener.
                trackList.addEventListener('error', (e) => {
                    if (e.target.matches('.track-artwork')) {
                        const noArtPlaceholder = document.createElement('div');
                        noArtPlaceholder.className = 'no-artwork';
                        noArtPlaceholder.textContent = 'No Art';
                        e.target.replaceWith(noArtPlaceholder);
                    }
                }, true); // Use capture phase to catch the event early.
            },

            /**
             * Handle track removal
             */
            handleRemoveTrack(url) {
                // 1. Optimistic UI update for instant feedback
                const trackEl = document.querySelector(`.track-item[data-url="${CSS.escape(url)}"]`);
                if (trackEl) {
                    trackEl.style.transition = 'opacity 0.3s, transform 0.3s';
                    trackEl.style.opacity = '0';
                    trackEl.style.transform = 'translateX(-20px)';
                    setTimeout(() => trackEl.remove(), 300);
                }

                // 2. Update the actual data state
                this.state.log(`[UI] Removing track: ${url}`);
                this.state.capturedTracks.delete(url);
                this.state.saveTracks(); // This triggers the debounced save and notifies UI of data change.
                this.showToast('Track removed', 'success');
            },

            /**
             * Handle track click
             */
            handleTrackClick(url) {
                var track = this.state.capturedTracks.get(url);
                if (track && track.songPageUrl) {
                    window.open(track.songPageUrl, '_blank');
                }
            },

            /**
             * Update the controls section with fresh HTML and reattach event listeners
             */
            updateControls() {
                var controls = document.getElementById('downloader-controls');
                if (!controls) {
                    console.warn('Controls element #downloader-controls not found in DOM');
                    return;
                }

                // Replace inner HTML with new controls
                controls.innerHTML = this.createControlsHTML();

                // Reattach event listeners to the newly injected elements
                this.attachControlListeners(controls);
            },

            /**
             * Create controls HTML
             */
            createControlsHTML() {
                var isListPage = this.isListPage();
                var urlQueue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                var failedUrls = this.state.safeJSONParse(GM_getValue('failedUrls', '[]'), []);

                return `
                    ${this.createActionButtons()}
                    ${isListPage ? this.createCaptureControls(urlQueue) : ''}
                    ${failedUrls.length > 0 ? this.createFailedSection(failedUrls) : ''}
                    ${this.createOptionsSection()}
                `;
            },

            /**
             * Create main action buttons
             */
            createActionButtons() {
                var trackCount = this.state.capturedTracks.size;
                var downloadText = this.getDownloadButtonText();

                // Check if any download option is selected. omitArtistName is a formatting option, not a download type.
                var noOptionsSelected = !DOWNLOAD_OPTIONS.DOWNLOAD_AUDIO &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_VIDEO &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_ART &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_LYRICS &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_METADATA_FILE;
                var isButtonDisabled = trackCount === 0 || noOptionsSelected;

                var buttonTitle = noOptionsSelected && trackCount > 0
                    ? "Enable at least one download option below to activate"
                    : "Download all captured tracks with current settings";

                return `
                    <button id="download-all-btn" class="downloader-btn" ${isButtonDisabled ? 'disabled' : ''} title="${buttonTitle}">
                        📥 ${downloadText} (${trackCount})
                    </button>
                    <button id="clear-list-btn" class="downloader-btn">
                        🗑️ Clear All
                    </button>
                `;
            },

            /**
             * Get download button text based on current settings
             */
            getDownloadButtonText() {
                var downloadTypes = [];
                // Build the list of types based on what's enabled.
                if (DOWNLOAD_OPTIONS.DOWNLOAD_AUDIO) downloadTypes.push('MP3');
                if (DOWNLOAD_OPTIONS.DOWNLOAD_VIDEO) downloadTypes.push('MP4');
                if (DOWNLOAD_OPTIONS.DOWNLOAD_ART) downloadTypes.push('Art');
                if (DOWNLOAD_OPTIONS.DOWNLOAD_LYRICS) downloadTypes.push('Lyrics');
                if (DOWNLOAD_OPTIONS.DOWNLOAD_METADATA_FILE) downloadTypes.push('Info'); // Add the metadata file type

                if (downloadTypes.length === 0) {
                    return 'Download'; // A sensible default if nothing is selected
                }

                // Join the selected types for a clear button label, e.g., "Download MP3+Art+Info"
                return `Download ${downloadTypes.join('+')}`;
            },

            /**
             * Create capture controls
             */
            createCaptureControls(urlQueue) {
                var autoCaptureState = this.getAutoCaptureState(urlQueue);

                return `
                    <button id="scan-page-btn" class="downloader-btn">
                        🔍 Scan This Page
                    </button>
                    <button id="force-rescan-btn" class="downloader-btn" title="Force deep rescan of all content">
                        🔄 Force Rescan
                    </button>
                    <button id="auto-capture-toggle" class="downloader-btn ${this.state.isAutoCapturing ? 'active' : 'inactive'}">
                        ${autoCaptureState.icon} ${autoCaptureState.text}
                    </button>
                `;
            },

            /**
             * Get auto-capture state for display
             */
            getAutoCaptureState(urlQueue) {
                if (!this.state.isAutoCapturing) {
                    return { icon: '🔍', text: 'Auto-Capture: OFF' };
                }

                if (this.state.isAddingToQueue) {
                    return { icon: '⏳', text: 'Scanning...' };
                } else if (this.state.isProcessingQueue) {
                    return { icon: '⚙️', text: 'Processing...' };
                } else if (this.state.activeRequests > 0) {
                    return { icon: '🔄', text: `Active: ${this.state.activeRequests}` };
                } else if (urlQueue.length > 0) {
                    return { icon: '📋', text: `Queue: ${urlQueue.length}` };
                } else {
                    return { icon: '✅', text: 'Auto-Capture: ON' };
                }
            },

            /**
             * Create failed items section
             */
            createFailedSection(failedUrls) {
                return `
                    <div class="failed-info">
                        ⚠️ ${failedUrls.length} items failed to process
                    </div>
                    <button id="retry-failed-btn" class="downloader-btn retry-failed-btn">
                        🔄 Retry Failed
                    </button>
                `;
            },

            /**
             * Create options section with new download options
             */
            /**
             * Create options section with new download options
             */
            createOptionsSection() {
                var totalTracks = this.state.capturedTracks.size;
                var tracksWithArt = Array.from(this.state.capturedTracks.values()).filter(track => track.albumArt).length;
                var tracksWithVideo = Array.from(this.state.capturedTracks.values()).filter(track => track.videoUrl).length;
                var tracksWithFullInfo = Array.from(this.state.capturedTracks.values()).filter(track => track.prompt).length;
                var tracksWithLyrics = Array.from(this.state.capturedTracks.values()).filter(track => track.lyrics).length;

                var artPercentage = totalTracks > 0 ? Math.round((tracksWithArt / totalTracks) * 100) : 0;

                // Get current settings from the updated DOWNLOAD_OPTIONS
                var downloadMetadataFile = DOWNLOAD_OPTIONS.DOWNLOAD_METADATA_FILE;
                var downloadArt = DOWNLOAD_OPTIONS.DOWNLOAD_ART;
                var downloadVideo = DOWNLOAD_OPTIONS.DOWNLOAD_VIDEO;
                var downloadAudio = DOWNLOAD_OPTIONS.DOWNLOAD_AUDIO;
                var downloadLyrics = DOWNLOAD_OPTIONS.DOWNLOAD_LYRICS;
                var omitArtistName = DOWNLOAD_OPTIONS.OMIT_ARTIST_NAME;

                return `
                    <div id="downloader-options">
                        <div class="options-row">
                            <label class="checkbox-container">
                                <input type="checkbox" id="download-audio-checkbox" ${downloadAudio ? 'checked' : ''}>
                                <span>Download MP3</span>
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" id="download-art-checkbox" ${downloadArt ? 'checked' : ''}>
                                <span>Download album art</span>
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" id="download-video-checkbox" ${downloadVideo ? 'checked' : ''}>
                                <span>Download MP4</span>
                            </label>
                        </div>

                        <div class="options-row">
                            <label class="checkbox-container">
                                <input type="checkbox" id="download-lyrics-checkbox" ${downloadLyrics ? 'checked' : ''}>
                                <span>Download lyrics</span>
                            </label>
                            <!-- REPLACED "Metadata only" with a clear, independent option -->
                            <label class="checkbox-container">
                                <input type="checkbox" id="download-metadata-file-checkbox" ${downloadMetadataFile ? 'checked' : ''}>
                                <span class="options-label">Download .txt Metadata</span>
                            </label>
                            <label class="checkbox-container">
                                <input type="checkbox" id="omit-artist-checkbox" ${omitArtistName ? 'checked' : ''}>
                                <span>Omit artist name</span>
                            </label>
                        </div>

                        <div class="stats-row">
                            <!-- ... stats display is fine ... -->
                        </div>

                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${artPercentage}%"></div>
                        </div>
                    </div>
                `;
            },

            /**
             * Attach control listeners
             */
            attachControlListeners(controls) {
                // Main action buttons
                this.attachButtonListener(controls, '#download-all-btn', () => this.downloadAllTracks());
                this.attachButtonListener(controls, '#clear-list-btn', () => this.clearWithConfirm());

                // Capture controls
                this.attachButtonListener(controls, '#scan-page-btn', () => {
                    this.state.log('[UI] Manual page scan triggered');
                    this.scanner.scheduleScan(); // ← FIX: Use the new method
                });
                this.attachButtonListener(controls, '#force-rescan-btn', () => {
                    this.state.log('[UI] Force rescan triggered');
                    this.scanner.scanPageForSongs(); // ← FIX: Use the new method
                });
                this.attachButtonListener(controls, '#auto-capture-toggle', () => this.toggleAutoCapture());
                this.attachButtonListener(controls, '#retry-failed-btn', () => this.queueManager.retryFailedUrls());

                // Checkbox handlers
                this.attachCheckboxListeners(controls);
            },

            /**
             * Attach button listener with error handling
             */
            attachButtonListener(container, selector, handler) {
                var button = container.querySelector(selector);
                if (button) {
                    this.addEventListener(button, 'click', handler);
                }
            },

            /**
             * Attach checkbox listeners with new options
             */
            attachCheckboxListeners(controls) {
                var checkboxes = {
                    '#download-metadata-file-checkbox': 'downloadMetadataFile',
                    '#download-art-checkbox': 'downloadArt',
                    '#download-video-checkbox': 'downloadVideo',
                    '#download-audio-checkbox': 'downloadAudio',
                    '#download-lyrics-checkbox': 'downloadLyrics',
                    '#omit-artist-checkbox': 'omitArtistName'
                };

                Object.entries(checkboxes).forEach(([selector, key]) => {
                    var checkbox = controls.querySelector(selector);
                    if (checkbox) {
                        this.addEventListener(checkbox, 'change', (e) => {
                            var isChecked = e.target.checked;
                            var optionKey = camelToUpperSnake(key);

                            // Update the in-memory options object
                            if (DOWNLOAD_OPTIONS.hasOwnProperty(optionKey)) {
                                DOWNLOAD_OPTIONS[optionKey] = isChecked;
                            }
                            // Save the setting for persistence
                            GM_setValue(key, isChecked);

                            this.state.log(`[UI] Option changed: ${key} is now ${isChecked ? 'ON' : 'OFF'}`);

                            // FIX: Directly update the download button instead of a full, potentially buggy re-render.
                            this.updateDownloadButtonState();

                            this.showToast(`${key.replace(/([A-Z])/g, ' $1')} ${isChecked ? 'enabled' : 'disabled'}`, 'info');
                        });
                    }
                });
            },

            /**
             * NEW: Specifically updates the download button's state and text.
             * This is a more targeted and reliable approach than a full UI re-render.
             */
            updateDownloadButtonState() {
                const btn = document.getElementById('download-all-btn');
                if (!btn) return;

                const trackCount = this.state.capturedTracks.size;
                const downloadText = this.getDownloadButtonText();
                const noOptionsSelected = !DOWNLOAD_OPTIONS.DOWNLOAD_AUDIO &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_VIDEO &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_ART &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_LYRICS &&
                                        !DOWNLOAD_OPTIONS.DOWNLOAD_METADATA_FILE;

                const isDisabled = trackCount === 0 || noOptionsSelected;

                btn.disabled = isDisabled;
                btn.innerHTML = `📥 ${downloadText} (${trackCount})`;
                btn.title = noOptionsSelected && trackCount > 0
                    ? "Enable at least one download option below to activate"
                    : "Download all captured tracks with current settings";
            },

            /**
             * UPDATED: Check if current page is a list page (includes /tags)
             */
            isListPage() {
                var listPaths = ['/library', '/home', '/search', '/creators', '/playlists', '/songs', '/create', '/tags'];
                return listPaths.some(path => window.location.pathname.startsWith(path));
            },

            /**
             * Utility: Escape HTML for safe rendering
             */
            escapeHTML(str) {
                if (!str) return '';
                var div = document.createElement('div');
                div.textContent = str;
                return div.innerHTML;
            },

            /**
             * UPDATED: Show toast notification with manual selection support
             */
            showToast(message, type = 'info', duration = 3000, toastId = null) {
                // Remove existing toasts
                document.querySelectorAll('.udio-toast').forEach(toast => {
                    if (!toastId || toast.dataset.toastId !== toastId) {
                        toast.remove();
                    }
                });

                var toast = document.createElement('div');
                toast.className = `udio-toast ${type}`;
                toast.textContent = message;
                toast.setAttribute('role', 'alert');
                toast.setAttribute('aria-live', 'polite');

                if (toastId) {
                    toast.dataset.toastId = toastId;
                }

                document.body.appendChild(toast);

                // Animate in
                requestAnimationFrame(() => {
                    toast.classList.add('show');
                });

                // Auto remove
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => {
                        if (toast.parentNode) {
                            toast.parentNode.removeChild(toast);
                        }
                    }, 400);
                }, duration);

                return toast;
            },

            /**
             * DEBUG: Check track data for folder context
             */
            debugTrackData() {
                // Only log in true debug mode and limit frequency
                if (!GM_getValue('debugMode', false)) return;

                // Anti-spam: Only log once per session or when explicitly requested
                if (this._hasLoggedTrackData) return;

                this.state.log('[DEBUG] Checking tracks for folder context (one-time):');
                let count = 0;
                for (const [url, info] of this.state.capturedTracks.entries()) {
                    if (count < 5) { // Only show first 5 tracks
                        this.state.log(`[DEBUG] "${info.title}" - Context: "${info.folderContext}"`);
                    }
                    count++;
                }
                if (count > 5) {
                    this.state.log(`[DEBUG] ... and ${count - 5} more tracks`);
                }
                this._hasLoggedTrackData = true;
            },

            /**
             * CORRECTED: Get playlist context - Focus on breadcrumb navigation
             */
            getPlaylistContext() {
                try {
                    const urlPath = window.location.pathname;

                    // Initialize context logging cache
                    if (!this._contextCache) {
                        this._contextCache = {
                            lastContext: null,
                            lastLogTime: 0,
                            detectionCount: 0
                        };
                    }

                    // --- PRIMARY: Breadcrumb detection for Library folders ---
                    if (urlPath.startsWith('/library')) {
                        const breadcrumbContext = this._getBreadcrumbContext();
                        if (breadcrumbContext) {
                            this._logContextDetection('breadcrumb', breadcrumbContext);
                            return breadcrumbContext;
                        }
                    }

                    // --- SECONDARY: Playlist page detection ---
                    if (urlPath.startsWith('/playlists/') || urlPath.includes('/playlist/')) {
                        const playlistContext = this._getPlaylistPageContext();
                        if (playlistContext) {
                            this._logContextDetection('playlist', playlistContext);
                            return playlistContext;
                        }
                    }

                    // --- FALLBACK: URL parameter detection for library filters ---
                    if (urlPath.startsWith('/library') && window.location.search) {
                        const filterContext = this._getFilterContext();
                        if (filterContext) {
                            this._logContextDetection('filter', filterContext);
                            return filterContext;
                        }
                    }

                    return null;

                } catch (error) {
                    this.state.debug('[UI Context] Error in context detection:', error);
                    return null;
                }
            },


            /**
             * NEW: Better validation for breadcrumb items
             */
            _isValidBreadcrumbItem(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 50) return false;

                const lowerText = trimmed.toLowerCase();

                // Exclude UI elements and navigation items
                const excludePatterns = [
                    'toggle sidebar',
                    'chevron',
                    'arrow',
                    'back',
                    'home',
                    'menu',
                    'navigation',
                    '...', // ellipsis
                    'more'
                ];

                if (excludePatterns.some(pattern => lowerText.includes(pattern))) {
                    return false;
                }

                // Must contain meaningful characters
                if (!/[a-zA-Z0-9]/.test(trimmed)) {
                    return false;
                }

                return true;
            },

            /**
             * ENHANCED: Check if folder is a generic root that should be filtered out
             */
            _isGenericRootFolder(text) {
                if (!text || typeof text !== 'string') return false;

                const lowerText = text.toLowerCase().trim();

                const genericRoots = [
                    'my library',
                    'library',
                    'home',
                    'dashboard',
                    'main',
                    'root',
                    'udio',
                    'all songs',
                    'all tracks',
                    'back to library'
                ];

                return genericRoots.some(root => lowerText === root || lowerText.includes(root));
            },

            /**
             * NEW: Improved breadcrumb detection that handles nested folders and prevents log spam.
             */
            _getEnhancedBreadcrumbContext() {
                try {
                    // Strategy 1: Try multiple breadcrumb selectors
                    const breadcrumbContainers = [
                        ...document.querySelectorAll('div.-ml-4.flex.items-center'),
                        ...document.querySelectorAll('[class*="breadcrumb"]'),
                        ...document.querySelectorAll('nav[aria-label*="breadcrumb"]'),
                        ...document.querySelectorAll('.flex.items-center.space-x-2'),
                        ...document.querySelectorAll('div.flex.items-center')
                    ];

                    for (const breadcrumb of breadcrumbContainers) {
                        const pathElements = this._extractBreadcrumbPath(breadcrumb);
                        if (pathElements.length >= 2) {
                            const cleanedPath = this._cleanBreadcrumbPath(pathElements);
                            if (cleanedPath && this._isValidFolderContext(cleanedPath)) {
                                // Use the smart logger to prevent spam
                                this._logContextDetection('breadcrumb (enhanced)', cleanedPath);
                                return cleanedPath;
                            }
                        }
                    }

                    // Strategy 2: Look for current folder context in page structure
                    const currentFolder = this._findCurrentFolderContext();
                    if (currentFolder && this._isValidFolderContext(currentFolder)) {
                        // Use the smart logger here as well
                        this._logContextDetection('breadcrumb (current folder)', currentFolder);
                        return currentFolder;
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Enhanced Breadcrumb] Error:', error);
                    return null;
                }
            },

            /**
             * Extract meaningful path from breadcrumb
             */
            _extractBreadcrumbPath(breadcrumb) {
                const elements = Array.from(breadcrumb.querySelectorAll('button, a, [class*="button"], span'));
                const pathElements = [];

                for (const el of elements) {
                    const text = el.textContent?.trim();
                    if (text && text.length > 0 && this._isValidBreadcrumbItem(text)) {
                        pathElements.push(text);
                    }
                }

                return pathElements;
            },

            /**
             * Clean breadcrumb path by removing generic roots and building hierarchy
             */
            _cleanBreadcrumbPath(pathElements) {
                if (pathElements.length === 0) return null;

                // Remove generic roots from the beginning
                const filteredElements = pathElements.filter(text =>
                    !this._isGenericRootFolder(text)
                );

                if (filteredElements.length === 0) {
                    // If everything was filtered out, use the last element
                    return pathElements[pathElements.length - 1];
                }

                // Build the path from remaining elements
                return filteredElements.join(' - ');
            },

            /**
             * Find current folder context from page structure
             */
            _findCurrentFolderContext() {
                try {
                    // Look for current folder indicators in the page
                    const folderIndicators = [
                        // Page titles and headers
                        'h1', 'h2', 'h3', 'h4',
                        // Current folder indicators
                        '[class*="current"]',
                        '[class*="selected"]',
                        '[class*="active"]',
                        // Folder context areas
                        '.flex.flex-col h4', // Playlist headers like "Effects"
                        'div.mb-\\[50px\\] h4',
                        'div.flex.w-full.flex-col h4'
                    ];

                    for (const selector of folderIndicators) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            const text = el.textContent?.trim();
                            if (text && this._isValidPlaylistContext(text) && !this._isGenericRootFolder(text)) {
                                const cleanedText = this._removeByArtist(text);
                                if (cleanedText && cleanedText.length >= 2) {
                                    return cleanedText;
                                }
                            }
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Current Folder] Error:', error);
                    return null;
                }
            },


            /**
             * NEW: Improved breadcrumb detection that handles nested folders and prevents log spam.
             */
            _getEnhancedBreadcrumbContext() {
                try {
                    // Strategy 1: Try multiple breadcrumb selectors
                    const breadcrumbContainers = [
                        ...document.querySelectorAll('div.-ml-4.flex.items-center'),
                        ...document.querySelectorAll('[class*="breadcrumb"]'),
                        ...document.querySelectorAll('nav[aria-label*="breadcrumb"]'),
                        ...document.querySelectorAll('.flex.items-center.space-x-2'),
                        ...document.querySelectorAll('div.flex.items-center')
                    ];

                    for (const breadcrumb of breadcrumbContainers) {
                        const pathElements = this._extractBreadcrumbPath(breadcrumb);
                        if (pathElements.length >= 2) {
                            const cleanedPath = this._cleanBreadcrumbPath(pathElements);
                            if (cleanedPath && this._isValidFolderContext(cleanedPath)) {
                                // Use the smart logger to prevent spam
                                this._logContextDetection('breadcrumb (enhanced)', cleanedPath);
                                return cleanedPath;
                            }
                        }
                    }

                    // Strategy 2: Look for current folder context in page structure
                    const currentFolder = this._findCurrentFolderContext();
                    if (currentFolder && this._isValidFolderContext(currentFolder)) {
                        // Use the smart logger here as well
                        this._logContextDetection('breadcrumb (current folder)', currentFolder);
                        return currentFolder;
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Enhanced Breadcrumb] Error:', error);
                    return null;
                }
            },

            /**
             * SIMPLE: Fallback breadcrumb detection
             */
            _getSimpleBreadcrumbContext() {
                try {
                    const breadcrumbSelectors = [
                        'div.-ml-4.flex.items-center',
                        '[class*="breadcrumb"]',
                        'nav[aria-label*="breadcrumb"]'
                    ];

                    for (const selector of breadcrumbSelectors) {
                        const breadcrumb = document.querySelector(selector);
                        if (breadcrumb) {
                            const elements = Array.from(breadcrumb.querySelectorAll('button, a, span'));
                            const validElements = elements.map(el => el.textContent?.trim())
                                .filter(text => text && text.length > 0 && this._isValidBreadcrumbItem(text));

                            if (validElements.length >= 2) {
                                // Remove generic roots and get the meaningful path
                                const filtered = validElements.filter(text => !this._isGenericRootFolder(text));
                                if (filtered.length > 0) {
                                    const path = filtered.join(' - ');
                                    this.state.log(`[Simple Breadcrumb] Path: "${path}"`);
                                    return path;
                                } else if (validElements.length > 0) {
                                    // Use last element if everything else was filtered
                                    return validElements[validElements.length - 1];
                                }
                            }
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Simple Breadcrumb] Error:', error);
                    return null;
                }
            },

            /**
             * NEW: Better validation for playlist context
             */
            _isValidPlaylistContext(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 100) return false;

                const lowerText = trimmed.toLowerCase();

                // Exclude obvious non-playlist content
                const excludePatterns = [
                    'udio.com',
                    'edit playlist',
                    'album artwork',
                    'session',
                    'generated on',
                    'click to',
                    'download',
                    'share this',
                    'undefined',
                    'null',
                    'chevron', // SVG icons
                    'search',
                    'filter',
                    'play all',
                    'shuffle'
                ];

                if (excludePatterns.some(pattern => lowerText.includes(pattern))) {
                    return false;
                }

                // Must contain meaningful characters
                if (!/[a-zA-Z0-9]/.test(trimmed)) {
                    return false;
                }

                return true;
            },


            /**
             * NEW: Apply "by Artist" removal to all context sources
             */
            _getFilterContext() {
                try {
                    const urlParams = new URLSearchParams(window.location.search);
                    const filter = urlParams.get('filter');

                    if (filter) {
                        let context = null;

                        // Handle filter patterns like "show.[liked]"
                        if (filter.startsWith('show.[') && filter.endsWith(']')) {
                            const contextType = filter.replace('show.[', '').replace(']', '');
                            const contextMap = {
                                'liked': 'Liked Songs',
                                'recent': 'Recently Played',
                                'created': 'My Creations',
                                'saved': 'Saved Songs',
                                'playlists': 'My Playlists'
                            };

                            context = contextMap[contextType] ||
                                    contextType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        }

                        // Additional patterns
                        if (!context) {
                            if (filter.includes('liked')) context = 'Liked Songs';
                            else if (filter.includes('created')) context = 'My Creations';
                            else if (filter.includes('saved')) context = 'Saved Songs';
                            else if (filter.includes('recent')) context = 'Recently Played';
                        }

                        // Apply "by Artist" removal to filter contexts too
                        if (context) {
                            const cleanedContext = this._removeByArtist(context);
                            if (cleanedContext !== context) {
                                this.state.log(`[Filter Context] Cleaned: "${context}" -> "${cleanedContext}"`);
                            }
                            return cleanedContext;
                        }
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[Filter] Error:', error);
                    return null;
                }
            },

            /**
             * ENHANCED: Better folder name validation for paths
             */
            _isValidFolderName(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 80) return false;

                const lowerText = trimmed.toLowerCase();

                // Exclude obvious non-folder content
                const excludePatterns = [
                    'udio.com',
                    'edit playlist',
                    'album artwork',
                    'session',
                    'generated on',
                    'click to',
                    'download',
                    'share this',
                    'undefined',
                    'null',
                    'by ', // Track artist indicator
                    'feat.',
                    'ft.',
                    'official',
                    'video',
                    'lyrics',
                    'chevron', // SVG icons
                    'search',
                    'filter'
                ];

                if (excludePatterns.some(pattern => lowerText.includes(pattern))) {
                    return false;
                }

                // Allow folder paths with separators
                if (trimmed.includes(' - ') || trimmed.includes(' › ') || trimmed.includes(' > ')) {
                    return true;
                }

                // Must contain meaningful characters
                if (!/[a-zA-Z0-9]/.test(trimmed)) {
                    return false;
                }

                return true;
            },

            /**
             * CORRECTED: Generate filename with proper folder context handling
             */
            generateFilenameBase(info) {
                const title = info.title || 'Untitled';
                const artist = info.artist || 'Unknown';
                const songId = info.id || getSongIdFromUrl(info.songPageUrl) || getSongIdFromTrack(info) || 'unknown';

                // Use the folder context that was saved with the track
                const folderContext = info.folderContext;

                const baseName = DOWNLOAD_OPTIONS.OMIT_ARTIST_NAME
                    ? title
                    : `${artist} - ${title}`;

                const filenameWithId = `${baseName} [${songId}]`;

                // ENHANCED: Always use folder context if available, unless it's clearly a track title
                if (folderContext &&
                    folderContext !== 'undefined' &&
                    folderContext !== 'null' &&
                    folderContext.length >= 2) {

                    // Check if it's a folder path (contains multiple parts with separators)
                    const isFolderPath = folderContext.includes(' - ') ||
                                        folderContext.includes(' › ') ||
                                        folderContext.includes(' > ') ||
                                        folderContext.split(' ').length >= 2;

                    if (isFolderPath || !this._isLikelyTrackTitle(folderContext)) {
                        const fullPath = `[${folderContext}] ${filenameWithId}`;
                        this.state.log(`[Filename] Using folder context: "${fullPath}"`);
                        return sanitizeForWindows(fullPath);
                    } else {
                        this.state.log(`[Filename] Skipping likely track title context: "${folderContext}"`);
                    }
                }

                // Fallback to standard filename
                this.state.log(`[Filename] No valid folder context, using: "${filenameWithId}"`);
                return sanitizeForWindows(filenameWithId);
            },

            /**
             * IMPROVED: Better track title detection that allows folder paths
             */
            _isLikelyTrackTitle(text) {
                if (!text || typeof text !== 'string') return false;

                const lowerText = text.toLowerCase();

                // If it's clearly a folder path with multiple parts, it's NOT a track title
                if (text.includes(' - ') && text.split(' - ').length >= 2) {
                    const parts = text.split(' - ');
                    // Check if any part looks like a track title
                    const hasTrackTitleIndicators = parts.some(part =>
                        part.includes('by ') ||
                        part.includes('feat.') ||
                        part.includes('ft.') ||
                        part.includes(' vs. ') ||
                        part.match(/\(.*\)/) || // Parentheses
                        part.match(/\[.*\]/)    // Brackets
                    );

                    if (!hasTrackTitleIndicators) {
                        return false; // This is likely a folder path, not a track title
                    }
                }

                // Common patterns that indicate this is DEFINITELY a track title
                const definitiveTrackIndicators = [
                    'by ',
                    'feat.',
                    'ft.',
                    ' vs. ',
                    'official',
                    'video',
                    'lyrics',
                    'remix',
                    'edit',
                    'mix',
                    'version',
                    'extended',
                    'radio'
                ];

                // If it contains definitive track indicators, it's a track title
                if (definitiveTrackIndicators.some(indicator => lowerText.includes(indicator))) {
                    return true;
                }

                // If it looks like "Artist - Song" format with specific patterns, it's a track
                if ((text.includes(' - ') || text.includes('–') || text.includes('—')) &&
                    (text.match(/.* - .*\[.*\]/) || // Artist - Song [something]
                    text.match(/.* - .*\(.*\)/) || // Artist - Song (something)
                    text.includes('by '))) {
                    return true;
                }

                return false;
            },

            /**
             * NEW: Extract context from page title
             */
            _extractContextFromPageTitle(pageTitle) {
                if (!pageTitle) return null;

                // Remove Udio branding and clean up
                let cleanTitle = pageTitle
                    .replace(/\s*\|\s*Udio\s*$/, '')
                    .replace(/\s*-\s*Udio\s*$/, '')
                    .replace(/\s*•\s*Udio\s*$/, '')
                    .trim();

                // Common library page titles to map
                const titleMap = {
                    'Liked Songs': 'Liked Songs',
                    'My Creations': 'My Creations',
                    'Recently Played': 'Recently Played',
                    'Saved Songs': 'Saved Songs',
                    'My Playlists': 'My Playlists'
                };

                // Check for exact matches first
                for (const [key, value] of Object.entries(titleMap)) {
                    if (cleanTitle.includes(key)) {
                        return value;
                    }
                }

                // Generic validation for other titles
                if (this.isValidPlaylistName(cleanTitle) && !this.isLikelyTrackTitle(cleanTitle)) {
                    return cleanTitle;
                }

                return null;
            },

            /**
             * NEW: Enhanced playlist name detection with specific selectors for "Effects"
             */
            getSpecificPlaylistContext() {
                try {
                    // Try very specific selectors first - these should find "Effects" from your HTML
                    const specificSelectors = [
                        'h4.text-2xl.font-semibold', // Main playlist title like "Effects"
                        'h4.text-2xl', // Alternative selector
                        'h1.text-2xl', // Main title
                        'h1.text-4xl', // Large title
                        '[class*="playlist-title"]',
                        '[class*="playlist-name"]',
                        'img[alt*="playlist"]',
                        'img[alt*="album"]',
                        // More specific Udio selectors
                        'div.flex.flex-col h4', // Container with h4
                        'div.mb-\\[50px\\] h4', // Specific container from your HTML
                        'div.flex.w-full.flex-col h4' // Another specific container
                    ];

                    for (const selector of specificSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            let text = '';

                            if (element.tagName === 'IMG' && element.alt) {
                                text = element.alt.trim();
                            } else if (element.textContent) {
                                text = element.textContent.trim();
                            }

                            if (text && this.isValidPlaylistName(text) && !this.isLikelyTrackTitle(text)) {
                                this.state.log(`[UI Context] Found playlist via specific selector "${selector}": "${text}"`);
                                return text;
                            }
                        }
                    }

                    // Strategy: Look for the main title that's NOT inside track listings
                    // This should distinguish between playlist title and track titles
                    const allHeadings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    const potentialTitles = [];

                    for (const heading of allHeadings) {
                        const text = heading.textContent?.trim();
                        if (text && this.isValidPlaylistName(text) && !this.isLikelyTrackTitle(text)) {
                            // Check if this heading is likely the main playlist title
                            const rect = heading.getBoundingClientRect();
                            const isTopLevel = rect.top < 300; // Should be near top of page
                            const isLargeFont = window.getComputedStyle(heading).fontSize >= '24px';
                            const hasPlaylistClass = heading.classList.toString().includes('text-2xl') ||
                                                heading.classList.toString().includes('text-4xl');

                            if (isTopLevel && (isLargeFont || hasPlaylistClass)) {
                                potentialTitles.push({ text, element: heading });
                            }
                        }
                    }

                    // Return the most likely playlist title
                    if (potentialTitles.length > 0) {
                        // Prefer larger fonts and higher positions
                        potentialTitles.sort((a, b) => {
                            const aRect = a.element.getBoundingClientRect();
                            const bRect = b.element.getBoundingClientRect();
                            const aSize = parseInt(window.getComputedStyle(a.element).fontSize);
                            const bSize = parseInt(window.getComputedStyle(b.element).fontSize);

                            if (aSize !== bSize) return bSize - aSize;
                            return aRect.top - bRect.top;
                        });

                        const bestTitle = potentialTitles[0].text;
                        this.state.log(`[UI Context] Selected best playlist title: "${bestTitle}"`);
                        return bestTitle;
                    }

                    return null;
                } catch (error) {
                    this.state.debug('[UI Context] Error in specific playlist detection:', error);
                    return null;
                }
            },

            /**
             * NEW: Check if text is likely a track title rather than a playlist name
             */
            isLikelyTrackTitle(text) {
                if (!text || typeof text !== 'string') return false;

                const lowerText = text.toLowerCase();

                // Common patterns that indicate this is a track title, not a playlist
                const trackIndicators = [
                    'by ', // "by ArtistName"
                    'feat.', // "Song feat. Artist"
                    'ft.', // "Song ft. Artist"
                    'vs.', // "Artist vs. Artist"
                    ' - ', // "Artist - Song"
                    '–', // "Artist – Song" (en dash)
                    '—', // "Artist — Song" (em dash)
                    '(', // "Song (Remix)"
                    '[', // "Song [Extended]"
                    'official',
                    'video',
                    'lyrics',
                    'remix',
                    'edit',
                    'mix',
                    'version',
                    'extended',
                    'radio'
                ];

                // If it contains any track indicators, it's likely a track title
                if (trackIndicators.some(indicator => lowerText.includes(indicator))) {
                    return true;
                }

                // If it looks like "Artist - Song" format, it's likely a track
                if (text.includes(' - ') || text.includes('–') || text.includes('—')) {
                    return true;
                }

                // If it's very short (less than 3 words) and doesn't sound like a playlist, it might be a track
                const wordCount = text.split(/\s+/).length;
                if (wordCount < 2) {
                    return true;
                }

                return false;
            },

            /**
             * Helper method to log context detection with anti-spam protection
             */
            _logContextDetection(type, context) {
                const now = Date.now();
                const cache = this._contextCache;

                // Only log if it's a new context or enough time has passed (prevents console spam)
                if (context !== cache.lastContext || (now - cache.lastLogTime) > 30000) {
                    this.state.log(`[UI Context] ${type}: ${context}`);
                    cache.lastContext = context;
                    cache.lastLogTime = now;
                    cache.detectionCount++;
                }
            },

            /**
             * Extract playlist name from meta tag content
             */
            _extractPlaylistNameFromMeta(metaContent) {
                if (!metaContent) return null;

                // Common patterns in Udio meta descriptions
                const patterns = [
                    /Listen to (.+?) on Udio/i,
                    /Check out (.+?) on Udio/i,
                    /Playlist: (.+?) \|/i,
                    /^(.+?) - .*?Udio/i,
                    /(.+?) by .*? on Udio/i
                ];

                for (const pattern of patterns) {
                    const match = metaContent.match(pattern);
                    if (match && match[1]) {
                        const extracted = match[1].trim();
                        if (this.isValidPlaylistName(extracted)) {
                            return extracted;
                        }
                    }
                }

                // Fallback: return first meaningful segment
                const segments = metaContent.split(/[|-•·]/);
                for (const segment of segments) {
                    const cleanSegment = segment.trim();
                    if (this.isValidPlaylistName(cleanSegment) && cleanSegment.length > 2) {
                        return cleanSegment;
                    }
                }

                return null;
            },

            /**
             * IMPROVED: More permissive playlist name validation
             */
            isValidPlaylistName(text) {
                if (!text || typeof text !== 'string') return false;

                const trimmed = text.trim();
                if (trimmed.length < 2 || trimmed.length > 100) return false;

                const lowerText = trimmed.toLowerCase();

                // Only exclude obvious non-playlist content
                const excludePatterns = [
                    'udio.com',
                    'my library',
                    'edit playlist',
                    'album artwork',
                    'session',
                    'generated on',
                    'click to',
                    'download',
                    'share this',
                    'undefined',
                    'null'
                ];

                if (excludePatterns.some(pattern => lowerText.includes(pattern))) {
                    return false;
                }

                // Exclude pure numbers or IDs (but allow mixed content)
                if (/^[0-9]+$/.test(trimmed)) {
                    return false;
                }

                // Allow longer IDs if they contain meaningful text
                if (/^[a-zA-Z0-9]{20,}$/.test(trimmed) && !/[a-zA-Z]/.test(trimmed)) {
                    return false;
                }

                // Must contain at least one letter or number
                if (!/[a-zA-Z0-9]/.test(trimmed)) {
                    return false;
                }

                return true;
            },

            /**
             * Get clean page title without Udio branding
             */
            getCleanPageTitle() {
                var title = document.title;
                // Remove Udio branding and clean up
                title = title.replace(/\s*\|\s*Udio\s*$/, '')
                            .replace(/\s*-\s*Udio\s*$/, '')
                            .trim();

                return title && title.length > 0 && title.length < 50 ? title : null;
            },

            /**
             * Export single track with new filename format including song ID
             */
            async exportSingleTrack(url, type) {
                var info = this.state.capturedTracks.get(url);
                if (!info) return;

                var filenameBase = this.generateFilenameBase(info);
                var songId = info.id || getSongIdFromUrl(info.songPageUrl) || 'unknown';

                try {
                    switch (type) {
                        case 'mp3':
                            if (url && DOWNLOAD_OPTIONS.DOWNLOAD_AUDIO) {
                                GM_download({
                                    url: url,
                                    name: `${filenameBase}.mp3`,
                                    saveAs: false
                                });
                                this.state.log(`[Export] MP3: ${filenameBase} (ID: ${songId})`);
                                this.showToast('MP3 download started', 'success');
                            } else {
                                this.showToast('Audio download is disabled in settings', 'warning');
                            }
                            break;

                        case 'mp4':
                            if (info.videoUrl && DOWNLOAD_OPTIONS.DOWNLOAD_VIDEO) {
                                GM_download({
                                    url: info.videoUrl,
                                    name: `${filenameBase}.mp4`,
                                    saveAs: false
                                });
                                this.state.log(`[Export] MP4: ${filenameBase} (ID: ${songId})`);
                                this.showToast('MP4 download started', 'success');
                            } else {
                                this.showToast('No video available or video download disabled', 'warning');
                            }
                            break;

                        case 'art':
                            if (info.albumArt && DOWNLOAD_OPTIONS.DOWNLOAD_ART) {
                                await this.apiHandler.downloadAlbumArt(info.albumArt, filenameBase);
                                this.state.log(`[Export] Artwork: ${filenameBase} (ID: ${songId})`);
                                this.showToast('Album art download started', 'success');
                            } else {
                                this.showToast('No album art available or art download disabled', 'warning');
                            }
                            break;

                        case 'lyrics':
                            if (info.lyrics && DOWNLOAD_OPTIONS.DOWNLOAD_LYRICS) {
                                var lyricsContent = this.generateLyricsContent(info);
                                GM_download({
                                    url: 'data:text/plain;charset=utf-8,' + encodeURIComponent(lyricsContent),
                                    name: `${filenameBase} - Lyrics.txt`,
                                    saveAs: false
                                });
                                this.state.log(`[Export] Lyrics: ${filenameBase} (ID: ${songId})`);
                                this.showToast('Lyrics download started', 'success');
                            } else {
                                this.showToast('No lyrics available or lyrics download disabled', 'warning');
                            }
                            break;

                        case 'metadata':
                            var textContent = this.generateMetadataContent(info);
                            GM_download({
                                url: 'data:text/plain;charset=utf-8,' + encodeURIComponent(textContent),
                                name: `${filenameBase}.txt`,
                                saveAs: false
                            });
                            this.state.log(`[Export] Metadata: ${filenameBase} (ID: ${songId})`);
                            this.showToast('Metadata download started', 'success');
                            break;
                    }
                } catch (e) {
                    this.state.error(`[Export] Failed to export ${type} for "${filenameBase}":`, e);
                    this.showToast(`Failed to export ${type}`, 'error');
                }
            },

            /**
             * Generate lyrics-only content
             */
            generateLyricsContent(info) {
                var content = `=== LYRICS: ${info.title || 'Unknown'} ===\n\n`;

                if (info.artist) {
                    content += `Artist: ${info.artist}\n`;
                }

                if (info.lyrics) {
                    content += `\n${info.lyrics}\n`;
                } else {
                    content += `No lyrics available for this track.\n`;
                }

                content += `\nExported: ${new Date().toLocaleString()}\n`;
                content += `Source: ${info.songPageUrl || 'N/A'}\n`;

                return content;
            },


            /**
             * Initiates an aggressive, concurrent download process for all captured tracks.
             * Features include real-time progress updates, cancellation, and robust retries.
             *
             * CRITICAL LOGIC: This function relies on the `folderContext` that was saved with each
             * track at the time of its capture. It does NOT re-detect the context, which is the
             * correct approach to ensure files from different playlists are named properly.
             */
            async downloadAllTracks() {
                // --- 1. PRE-DOWNLOAD CHECKS ---
                if (this.isDownloading) {
                    this.showToast('A download is already in progress.', 'warning');
                    return;
                }
                if (this.state.capturedTracks.size === 0) {
                    this.showToast('No tracks captured to download.', 'warning');
                    return;
                }

                // --- 2. SETUP & CONFIGURATION ---
                this.isDownloading = true;
                this.isCancelled = false;
                const btn = document.getElementById('download-all-btn');
                const progressFill = document.querySelector('#downloader-options .progress-fill');
                const allDownloadTasks = [];
                const CONCURRENT_DOWNLOADS = 8;
                const MAX_DOWNLOAD_RETRIES = 2;

                // --- 3. PREPARE DOWNLOAD TASKS (THE CORE LOGIC) ---
                this.state.log(`[Download] Preparing files using individually saved contexts.`);

                this.state.capturedTracks.forEach((info, url) => {
                    // Use the `info` object which already contains the correct `folderContext`.
                    const filenameBase = this.generateFilenameBase(info);

                    // A helper function to create a download task (a function that returns a Promise).
                    const createTask = (downloadPromise, type, filename) => {
                        return () => processDownload(downloadPromise, type, filename);
                    };

                    // Create tasks based on user's selected download options.
                    if (DOWNLOAD_OPTIONS.DOWNLOAD_AUDIO) {
                        allDownloadTasks.push(createTask(
                            () => promisifiedGmDownload({ url, name: `${filenameBase}.mp3`, saveAs: false }),
                            'audio',
                            `${filenameBase}.mp3`
                        ));
                    }
                    if (DOWNLOAD_OPTIONS.DOWNLOAD_VIDEO && info.videoUrl) {
                        allDownloadTasks.push(createTask(
                            () => this.apiHandler.downloadVideo(info.videoUrl, filenameBase),
                            'video',
                            `${filenameBase}.mp4`
                        ));
                    }
                    if (DOWNLOAD_OPTIONS.DOWNLOAD_ART && info.albumArt) {
                        allDownloadTasks.push(createTask(
                            () => this.apiHandler.downloadAlbumArt(info.albumArt, filenameBase),
                            'art',
                            `${filenameBase} - Artwork`
                        ));
                    }
                    if (DOWNLOAD_OPTIONS.DOWNLOAD_LYRICS && info.lyrics) {
                        const lyricsContent = this.generateLyricsContent(info);
                        allDownloadTasks.push(createTask(
                            () => promisifiedGmDownload({ url: 'data:text/plain;charset=utf-8,' + encodeURIComponent(lyricsContent), name: `${filenameBase} - Lyrics.txt`, saveAs: false }),
                            'lyrics',
                            `${filenameBase} - Lyrics.txt`
                        ));
                    }
                    if (DOWNLOAD_OPTIONS.DOWNLOAD_METADATA_FILE) {
                        const textContent = this.generateMetadataContent(info);
                        allDownloadTasks.push(createTask(
                            () => promisifiedGmDownload({ url: 'data:text/plain;charset=utf-8,' + encodeURIComponent(textContent), name: `${filenameBase}.txt`, saveAs: false }),
                            'metadata',
                            `${filenameBase}.txt`
                        ));
                    }
                });

                const totalOperations = allDownloadTasks.length;
                if (totalOperations === 0) {
                    this.showToast('No download options are selected in settings!', 'warning');
                    this.isDownloading = false;
                    return;
                }

                // --- 4. INITIALIZE UI FOR DOWNLOADING STATE ---
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = '📥 Preparing...';
                    // Set up the cancellation handler.
                    if (this._cancelHandler) btn.removeEventListener('click', this._cancelHandler);
                    this._cancelHandler = () => {
                        this.isCancelled = true;
                        this.showToast('Cancelling downloads...', 'warning');
                        btn.disabled = true;
                        btn.textContent = '🛑 Cancelling...';
                    };
                    btn.addEventListener('click', this._cancelHandler);
                }
                if (progressFill) {
                    progressFill.style.transition = 'width 0.1s linear';
                    progressFill.style.width = '0%';
                }

                this.state.log(`[Download] Starting download of ${totalOperations} files with ${CONCURRENT_DOWNLOADS} concurrent workers.`);

                // --- 5. EXECUTE CONCURRENT DOWNLOADS ---
                let operationsCompleted = 0;
                const successCounts = { art: 0, video: 0, lyrics: 0, metadata: 0, audio: 0 };
                const failedFiles = new Set();

                // The core worker function that processes a single download with retries.
                const processDownload = async (downloadPromise, type, filename) => {
                    for (let attempt = 1; attempt <= MAX_DOWNLOAD_RETRIES + 1; attempt++) {
                        if (this.isCancelled) return;
                        try {
                            await downloadPromise();
                            operationsCompleted++;
                            if (successCounts[type] !== undefined) successCounts[type]++;
                            // Update UI progress in a single block.
                            const progress = Math.round((operationsCompleted / totalOperations) * 100);
                            if (btn && !this.isCancelled) btn.textContent = `❌ Cancel (${progress}%)`;
                            if (progressFill) progressFill.style.width = `${progress}%`;
                            return; // Success, exit the retry loop.
                        } catch (error) {
                            if (attempt <= MAX_DOWNLOAD_RETRIES) {
                                this.state.warn(`[Download] Error on "${filename}" (Attempt ${attempt}). Retrying...`);
                                await new Promise(resolve => setTimeout(resolve, 1500 * attempt)); // Exponential backoff.
                            } else {
                                this.state.error(`[Download] Failed "${filename}" after all retries:`, error.message);
                                failedFiles.add(filename);
                                operationsCompleted++; // Increment to ensure progress bar completes.
                                return; // Failure, exit the retry loop.
                            }
                        }
                    }
                };

                try {
                    const downloadQueue = [...allDownloadTasks];
                    // The runner function for each concurrent worker.
                    const worker = async () => {
                        while (downloadQueue.length > 0 && !this.isCancelled) {
                            const task = downloadQueue.shift();
                            if (task) await task();
                        }
                    };
                    // Start all workers and wait for them to complete.
                    await Promise.all(Array(CONCURRENT_DOWNLOADS).fill(null).map(worker));

                    // --- 6. FINALIZE AND REPORT ---
                    const finalStatus = this.isCancelled ? "Cancelled" : "Complete";
                    const successCount = operationsCompleted - failedFiles.size;
                    let resultMessage = `✅ Download ${finalStatus}!\n\nFiles downloaded: ${successCount}/${totalOperations}\n`;
                    if (failedFiles.size > 0) resultMessage += `Files with errors: ${failedFiles.size}\n\n`;
                    // Build a detailed summary of successful downloads.
                    const summary = Object.entries(successCounts)
                                        .filter(([type, count]) => count > 0)
                                        .map(([type, count]) => `${type.charAt(0).toUpperCase() + type.slice(1)}: ${count}`)
                                        .join('\n');
                    if (summary) resultMessage += `Summary:\n${summary}`;

                    this.showToast(`Download ${finalStatus}! (${successCount}/${totalOperations})`, this.isCancelled ? 'info' : 'success', 5000);
                    if (!this.isCancelled && totalOperations > 0) {
                        setTimeout(() => alert(resultMessage), 500);
                    }

                } catch (error) {
                    this.state.error('[Download] A critical error occurred during the download process:', error);
                    this.showToast('Batch download failed critically', 'error');
                } finally {
                    // --- 7. CLEANUP UI ---
                    this.isDownloading = false;
                    if (btn) {
                        if (this._cancelHandler) {
                            btn.removeEventListener('click', this._cancelHandler);
                            this._cancelHandler = null;
                        }
                        this.updateDownloadButtonState(); // Resets the button text and state correctly.
                    }
                    // Animate the progress bar back to its default state (artwork percentage).
                    if (progressFill) {
                        setTimeout(() => {
                            if (!this.isDownloading) {
                                progressFill.style.transition = 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                                const artPercentage = (() => {
                                    const total = this.state.capturedTracks.size;
                                    if (total === 0) return 0;
                                    const withArt = Array.from(this.state.capturedTracks.values()).filter(t => t.albumArt).length;
                                    return Math.round((withArt / total) * 100);
                                })();
                                progressFill.style.width = `${artPercentage}%`;
                            }
                        }, 2000);
                    }
                }
            },


            /**
             * Generates the complete metadata content for a track's .txt file.
             * This version correctly uses the `folderContext` saved in the track's `info` object,
             * ensuring consistency with the downloaded filename and preventing incorrect context application.
             * @param {object} info - The track's complete metadata object.
             * @returns {string} The formatted text content for the metadata file.
             */
            generateMetadataContent(info) {
                let content = `=== UDIO TRACK METADATA ===\n\n`;

                // --- Core Metadata ---
                content += `Title: ${info.title || 'N/A'}\n`;
                content += `Artist: ${info.artist || 'N/A'}\n`;
                content += `Created: ${info.creationDate || 'N/A'}\n`;
                content += `Source URL: ${info.songPageUrl || 'N/A'}\n`;

                // ***** CORRECT IMPLEMENTATION *****
                // Use the folder context that was saved with the track when it was captured.
                // This ensures the metadata file matches the filename's context.
                if (info.folderContext) {
                    content += `Playlist/Folder Context: ${info.folderContext}\n`;
                }
                // ********************************

                // --- Generation & Technical IDs ---
                if (info.id) content += `Song ID: ${info.id}\n`;
                if (info.generationId) content += `Generation ID: ${info.generationId}\n`;
                if (info.parentId) content += `Parent ID: ${info.parentId}\n`;
                if (info.styleId) content += `Style ID: ${info.styleId}\n`;
                if (info.styleSourceSongId) content += `Style Source Song ID: ${info.styleSourceSongId}\n`;

                // --- Statistics ---
                if (info.plays !== undefined && info.plays !== null) content += `Plays: ${info.plays}\n`;
                if (info.likes !== undefined && info.likes !== null) content += `Likes: ${info.likes}\n`;

                // --- Media URLs ---
                if (info.audioUrl) content += `Audio URL: ${info.audioUrl}\n`;
                if (info.albumArt) content += `Album Art URL: ${info.albumArt}\n`;
                if (info.videoUrl) content += `Video URL: ${info.videoUrl}\n`;
                if (info.originalSongPath) content += `Original Song Path: ${info.originalSongPath}\n`;

                // --- Audio Properties ---
                if (info.duration) content += `Duration: ${info.duration} seconds\n`;
                if (info.bpm) content += `BPM: ${info.bpm}\n`;
                if (info.key) content += `Key: ${info.key}\n`;
                if (info.genre) content += `Genre: ${info.genre}\n`;
                if (info.mood) content += `Mood: ${info.mood}\n`;
                if (info.tempo) content += `Tempo: ${info.tempo}\n`;
                if (info.energy) content += `Energy: ${info.energy}\n`;
                if (info.danceability) content += `Danceability: ${info.danceability}\n`;
                if (info.valence) content += `Valence: ${info.valence}\n`;

                // --- Technical Metadata ---
                if (info.audioConditioningType) content += `Audio Conditioning Type: ${info.audioConditioningType}\n`;
                if (info.styleSourceType) content += `Style Source Type: ${info.styleSourceType}\n`;

                // --- User Information ---
                if (info.userId) content += `User ID: ${info.userId}\n`;
                if (info.userDisplayName) content += `User Display Name: ${info.userDisplayName}\n`;

                // --- Status Flags ---
                if (info.finished !== undefined) content += `Finished: ${info.finished}\n`;
                if (info.publishable !== undefined) content += `Publishable: ${info.publishable}\n`;
                if (info.disliked !== undefined) content += `Disliked: ${info.disliked}\n`;
                if (info.publishedAt) content += `Published At: ${info.publishedAt}\n`;

                // --- Content Sections ---
                if (info.prompt) {
                    content += `\n--- PROMPT ---\n${info.prompt}\n`;
                }
                if (info.description) {
                    content += `\n--- DESCRIPTION ---\n${info.description}\n`;
                }
                if (info.attribution) {
                    content += `\n--- ATTRIBUTION ---\n${info.attribution}\n`;
                }
                if (info.tags && info.tags.length > 0) {
                    content += `\n--- TAGS ---\n${info.tags.join(', ')}\n`;
                }
                if (info.userTags && info.userTags.length > 0) {
                    content += `\n--- USER TAGS ---\n${info.userTags.join(', ')}\n`;
                }
                if (info.replacedTags && info.replacedTags.length > 0) {
                    content += `\n--- REPLACED TAGS ---\n${info.replacedTags.join(', ')}\n`;
                }
                if (info.instruments && info.instruments.length > 0) {
                    content += `\n--- INSTRUMENTS ---\n${info.instruments.join(', ')}\n`;
                }
                if (info.lyrics) {
                    content += `\n--- LYRICS ---\n${info.lyrics}\n`;
                }

                // --- Complex Object Sections ---
                if (info.audioFeatures && typeof info.audioFeatures === 'object') {
                    content += `\n--- AUDIO FEATURES ---\n${JSON.stringify(info.audioFeatures, null, 2)}\n`;
                }
                if (info.errorInfo) {
                    content += `\n--- ERROR INFORMATION ---\n`;
                    if (info.errorInfo.code) content += `Error Code: ${info.errorInfo.code}\n`;
                    if (info.errorInfo.type) content += `Error Type: ${info.errorInfo.type}\n`;
                    if (info.errorInfo.detail) content += `Error Detail: ${info.errorInfo.detail}\n`;
                }
                if (info.userInfo && typeof info.userInfo === 'object') {
                    content += `\n--- USER INFORMATION ---\n${JSON.stringify(info.userInfo, null, 2)}\n`;
                }

                // --- Catch-all for any remaining data ---
                content += `\n--- ADDITIONAL METADATA ---\n`;
                const handledKeys = new Set([
                    'title', 'artist', 'creationDate', 'songPageUrl', 'id', 'generationId', 'folderContext',
                    'parentId', 'styleId', 'styleSourceSongId', 'plays', 'likes', 'audioUrl',
                    'albumArt', 'videoUrl', 'originalSongPath', 'duration', 'bpm', 'key',
                    'genre', 'mood', 'tempo', 'energy', 'danceability', 'valence',
                    'audioConditioningType', 'styleSourceType', 'userId', 'userDisplayName',
                    'finished', 'publishable', 'disliked', 'publishedAt', 'prompt',
                    'description', 'attribution', 'tags', 'userTags', 'replacedTags',
                    'instruments', 'lyrics', 'audioFeatures', 'errorInfo', 'userInfo',
                    'mediaType', 'captureTime', 'mediaDuration', 'mediaReadyState', 'pageContext',
                    'videoDimensions' // Added this for completeness
                ]);

                for (const [key, value] of Object.entries(info)) {
                    if (!handledKeys.has(key) && value !== null && value !== undefined) {
                        const formattedValue = (typeof value === 'object') ? JSON.stringify(value) : value;
                        content += `${key}: ${formattedValue}\n`;
                    }
                }

                content += `\nExported: ${new Date().toLocaleString()}\n`;
                content += `Export Tool: Udio Downloader v36.0\n`;

                return content;
            },

            /**
             * Clear all tracks with confirmation dialog
             */
            clearWithConfirm() {
                if (this.state.capturedTracks.size === 0 && this.manualSelectionsInProgress.size === 0) {
                    this.showToast('No tracks to clear', 'info');
                    return;
                }

                var manualCount = this.manualSelectionsInProgress.size;
                var trackCount = this.state.capturedTracks.size;
                var message = manualCount > 0 ?
                    `Are you sure you want to clear all ${trackCount} tracks and ${manualCount} manual selections?\n\nThis action cannot be undone.` :
                `Are you sure you want to clear all ${trackCount} tracks and stop capture?\n\nThis action cannot be undone.`;

                if (confirm(message)) {
                    this.manualSelectionsInProgress.clear();
                    this.state.clearAllData();
                    this.showToast('All tracks cleared', 'success');
                    this.scheduleRender();
                }
            },

            /**
             * Toggle auto-capture mode
             */
            toggleAutoCapture() {
                this.state.isAutoCapturing = !this.state.isAutoCapturing;
                GM_setValue('isAutoCapturing', this.state.isAutoCapturing);
                this.state.log(`[Auto-Capture] Toggled ${this.state.isAutoCapturing ? 'ON' : 'OFF'}`);

                if (this.state.isAutoCapturing) {
                    if (!this.state.bearerToken) {
                        this.state.bearerToken = this.state.extractBearerToken();
                    }
                    if (this.state.bearerToken) {
                        // FIX: Use the new scanner.start() method
                        this.scanner.start();

                        const queue = this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                        if (queue.length > 0) {
                            this.queueManager.processQueue();
                        }
                        this.showToast('Auto-capture started', 'success');
                    } else {
                        this.showToast('Authentication token not found. Please reload.', 'error');
                        this.state.isAutoCapturing = false;
                        GM_setValue('isAutoCapturing', false);
                    }
                } else {
                    // FIX: Use the new scanner.stop() method
                    this.scanner.stop();
                    this.showToast('Auto-capture stopped', 'info');
                }
                this.scheduleRender();
            },

            /**
             * NEW: Add context menu for manual track selection
             */
            addContextMenuSupport() {
                document.addEventListener('contextmenu', (e) => {
                    // Find song link in right-clicked element
                    var songLink = this.findSongLink(e.target);
                    if (songLink && this.isValidSongElement(songLink)) {
                        e.preventDefault();
                        e.stopPropagation();
                        this.showSongContextMenu(e, songLink.href);
                    }
                }, true);
            },

            /**
             * NEW: Find song link in element or parents
             */
            findSongLink(element) {
                if (!element) return null;

                var currentElement = element;
                var depth = 0;
                var maxDepth = 10;

                while (currentElement && currentElement !== document.body && depth < maxDepth) {
                    if (currentElement.tagName === 'A' &&
                        currentElement.href &&
                        currentElement.href.includes('/songs/') &&
                        !currentElement.href.includes('/songs/create')) {
                        return currentElement;
                    }
                    currentElement = currentElement.parentElement;
                    depth++;
                }
                return null;
            },

            /**
             * NEW: Check if element is visible and valid for manual selection
             */
            isValidSongElement(element) {
                if (!element || !element.getBoundingClientRect) return false;

                var rect = element.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 &&
                    rect.top >= 0 && rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth);

                return isVisible && element.offsetParent !== null;
            },

            /**
             * NEW: Show context menu for song links
             */
            showSongContextMenu(event, songUrl) {
                // Remove existing context menu
                var existingMenu = document.getElementById('udio-context-menu');
                if (existingMenu) existingMenu.remove();

                var menu = document.createElement('div');
                menu.id = 'udio-context-menu';
                menu.innerHTML = `
                    <div class="context-menu-item" data-action="capture">🎵 Capture This Track</div>
                    <div class="context-menu-item" data-action="open">🔗 Open Song Page</div>
                    <div class="context-menu-item" data-action="copy">📋 Copy Song URL</div>
                `;

                menu.style.cssText = `
                    position: fixed;
                    left: ${event.pageX}px;
                    top: ${event.pageY}px;
                    background: #2d2d2d;
                    border: 1px solid #555;
                    border-radius: 8px;
                    padding: 8px 0;
                    z-index: 10005;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                    min-width: 200px;
                    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                    backdrop-filter: blur(10px);
                `;

                document.body.appendChild(menu);

                // Add event listeners
                menu.querySelector('[data-action="capture"]').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.handleManualTrackSelection(songUrl);
                    menu.remove();
                });

                menu.querySelector('[data-action="open"]').addEventListener('click', (e) => {
                    e.stopPropagation();
                    window.open(songUrl, '_blank');
                    menu.remove();
                });

                menu.querySelector('[data-action="copy"]').addEventListener('click', (e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(songUrl).then(() => {
                        this.showToast('URL copied to clipboard', 'success');
                    }).catch(() => {
                        // Fallback for older browsers
                        var textArea = document.createElement('textarea');
                        textArea.value = songUrl;
                        document.body.appendChild(textArea);
                        textArea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textArea);
                        this.showToast('URL copied to clipboard', 'success');
                    });
                    menu.remove();
                });

                // Close menu when clicking elsewhere
                setTimeout(() => {
                    var closeMenu = (e) => {
                        if (!menu.contains(e.target)) {
                            menu.remove();
                            document.removeEventListener('click', closeMenu);
                        }
                    };
                    document.addEventListener('click', closeMenu);
                }, 100);
            },

            /**
             * NEW: Add keyboard shortcut support
             */
            addKeyboardShortcutSupport() {
                document.addEventListener('click', (e) => {
                    // Check if clicked element is a song link with Ctrl key
                    var songLink = this.findSongLink(e.target);
                    if (songLink && !songLink.href.includes('/songs/create') && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        e.stopPropagation();
                        this.handleManualTrackSelection(songLink.href);
                    }
                }, true);
            },

            /**
             * NEW: Setup manual selection listeners
             */
            setupManualSelectionListeners() {
                // Listen for manual selection completion
                window.addEventListener('udio-dl-manual-selection-complete', (event) => {
                    var { url, track } = event.detail;
                    this.handleManualSelectionComplete(url, track);
                });

                // Listen for state changes that might indicate manual selection completion
                window.addEventListener('udio-dl-state-change', () => {
                    this.checkManualSelectionProgress();
                });
            },

            /**
             * NEW: Handle manual track selection
             */
            handleManualTrackSelection(songUrl) {
                if (!songUrl || this.state.isClearing) return;

                var normalizedUrl = normalizeUrl(songUrl);
                var songId = getSongIdFromUrl(normalizedUrl);

                if (!songId) {
                    this.showToast('Invalid song URL', 'error');
                    return;
                }

                // Check if already captured
                var isAlreadyCaptured = Array.from(this.state.capturedTracks.values())
                .some(track => {
                    var trackSongId = getSongIdFromTrack(track);
                    return trackSongId === songId || track.songPageUrl === normalizedUrl;
                });

                if (isAlreadyCaptured) {
                    this.showToast('Track already captured', 'info');
                    return;
                }

                // Check if already being processed
                if (this.manualSelectionsInProgress.has(normalizedUrl)) {
                    this.showToast('Track is already being processed', 'info');
                    return;
                }

                // Track this manual selection
                this.manualSelectionsInProgress.set(normalizedUrl, {
                    startTime: Date.now(),
                    status: 'queued',
                    songId: songId
                });

                // Add to queue as manual selection (prioritized)
                this.queueManager.addToQueue([normalizedUrl], true);
                this.showManualSelectionFeedback(normalizedUrl);

                // Force UI update
                this.scheduleRender();

                this.state.log(`[Manual Selection] Added track to queue: ${songId}`);
            },

            /**
             * NEW: Enhanced manual selection verification
             */
            verifyManualSelectionCompletion(url, expectedSongId) {
                return new Promise((resolve) => {
                    var attempts = 0;
                    var maxAttempts = 10; // 5 seconds total

                    var checkInterval = setInterval(() => {
                        attempts++;

                        // Multiple verification methods
                        var capturedTrack = null;

                        // Method 1: Check by URL
                        capturedTrack = this.state.capturedTracks.get(url);

                        // Method 2: Check by song ID
                        if (!capturedTrack && expectedSongId) {
                            capturedTrack = Array.from(this.state.capturedTracks.values())
                                .find(track => {
                                var trackSongId = getSongIdFromTrack(track);
                                return trackSongId === expectedSongId;
                            });
                        }

                        // Method 3: Check by normalized URL
                        if (!capturedTrack) {
                            var normalizedUrl = normalizeUrl(url);
                            for (var [trackUrl, track] of this.state.capturedTracks.entries()) {
                                if (normalizeUrl(trackUrl) === normalizedUrl) {
                                    capturedTrack = track;
                                    break;
                                }
                            }
                        }

                        if (capturedTrack) {
                            clearInterval(checkInterval);
                            resolve(capturedTrack);
                        } else if (attempts >= maxAttempts) {
                            clearInterval(checkInterval);
                            resolve(null);
                        }
                    }, 500); // Check every 500ms
                });
            },

            /**
             * NEW: Show processing status for manual selections with verification
             */
            showManualSelectionFeedback(songUrl) {
                var toastId = 'manual-selection-' + Date.now();
                var songId = getSongIdFromUrl(songUrl);

                // Show initial toast
                var toast = this.showToast('🔄 Processing manual selection...', 'info', 10000, toastId);

                // Track this manual selection
                this.manualSelectionsInProgress.set(songUrl, {
                    startTime: Date.now(),
                    status: 'queued',
                    songId: songId
                });

                // Enhanced completion checking with verification
                this.verifyManualSelectionCompletion(songUrl, songId)
                    .then(capturedTrack => {
                    if (capturedTrack) {
                        this.manualSelectionsInProgress.delete(songUrl);

                        // Force UI updates
                        this.forceUIRefresh();

                        // Update toast to success
                        this.showToast(`✅ "${capturedTrack.title}" captured successfully!`, 'success', 3000);

                        this.state.log(`[Manual Selection] Verified completion: "${capturedTrack.title}"`);
                    } else {
                        this.manualSelectionsInProgress.delete(songUrl);
                        this.showToast('❌ Manual selection failed or timed out', 'error', 5000);
                    }
                })
                    .catch(error => {
                    this.manualSelectionsInProgress.delete(songUrl);
                    this.showToast('❌ Manual selection error', 'error', 5000);
                    this.state.error('[Manual Selection] Error:', error);
                });

                // Fallback timeout after 30 seconds
                setTimeout(() => {
                    if (this.manualSelectionsInProgress.has(songUrl)) {
                        this.manualSelectionsInProgress.delete(songUrl);
                        this.showToast('❌ Manual selection timed out', 'error', 5000);
                    }
                }, 30000);
            },

            /**
             * NEW: Check manual selection progress
             */
            checkManualSelectionProgress() {
                this.manualSelectionsInProgress.forEach((selection, url) => {
                    if (selection.status === 'queued' || selection.status === 'processing') {
                        var capturedTrack = Array.from(this.state.capturedTracks.values())
                        .find(track => {
                            var trackSongId = getSongIdFromTrack(track);
                            return trackSongId === selection.songId;
                        });

                        if (capturedTrack) {
                            selection.status = 'completed';
                            this.state.log(`[Manual Selection] Detected completion: "${capturedTrack.title}"`);
                        }
                    }
                });
            },

            /**
             * NEW: Handle manual selection completion with better data handling
             */
            handleManualSelectionComplete(url, track) {
                this.state.log(`[UI] Manual selection completed: "${track.title}"`);

                // Remove from progress tracking
                this.manualSelectionsInProgress.delete(url);

                // CRITICAL: Force immediate storage sync to ensure data is available
                setTimeout(() => {
                    // Verify the track is actually in capturedTracks
                    var capturedTrack = Array.from(this.state.capturedTracks.values())
                    .find(t => getSongIdFromTrack(t) === getSongIdFromTrack(track));

                    if (capturedTrack) {
                        this.state.log(`[UI] Verified manual selection in storage: "${capturedTrack.title}"`);

                        // Force comprehensive UI updates
                        this.forceUIRefresh();

                        // Show success notification with track info
                        this.showToast(`✅ "${capturedTrack.title}" captured successfully!`, 'success', 3000);

                        // Pulse the toggle button for attention
                        this.pulseToggleButton();
                    } else {
                        this.state.warn(`[UI] Manual selection completed but track not found in storage: "${track.title}"`);
                        // Fallback: try to add the track manually
                        this.state.capturedTracks.set(track.audioUrl || url, track);
                        this.state.saveTracks();
                        this.forceUIRefresh();
                    }
                }, 200);
            },

            /**
             * NEW: Pulse the toggle button for attention
             */
            pulseToggleButton() {
                var toggle = document.getElementById('udio-downloader-toggle');
                if (toggle) {
                    toggle.classList.add('pulse');
                    setTimeout(() => toggle.classList.remove('pulse'), 2000);
                }
            },

            /**
             * Get performance metrics
             */
            getPerformanceMetrics() {
                return {
                    ...this.performance,
                    memoryUsage: this.getMemoryUsage(),
                    eventListeners: this.eventListeners.size,
                    manualSelections: this.manualSelectionsInProgress.size
                };
            },

            /**
             * Estimate memory usage
             */
            getMemoryUsage() {
                var tracksSize = JSON.stringify(Array.from(this.state.capturedTracks.entries())).length;
                var queueSize = JSON.stringify(this.state.safeJSONParse(GM_getValue('urlQueue', '[]'), [])).length;

                return {
                    tracksKB: Math.round(tracksSize / 1024),
                    queueKB: Math.round(queueSize / 1024),
                    totalKB: Math.round((tracksSize + queueSize) / 1024)
                };
            },

            /**
             * Cleanup and destroy UI
             */
            destroy() {
                // Clear intervals
                if (this.renderInterval) {
                    clearInterval(this.renderInterval);
                    this.renderInterval = null;
                }

                if (this.renderDebounce) {
                    clearTimeout(this.renderDebounce);
                    this.renderDebounce = null;
                }

                // Remove event listeners
                this.eventListeners.forEach(({ element, event, handler }) => {
                    element.removeEventListener(event, handler);
                });
                this.eventListeners.clear();

                // Clear manual selections
                this.manualSelectionsInProgress.clear();

                // Remove DOM elements
                var uiContainer = document.getElementById('udio-downloader-ui');
                var toggleButton = document.getElementById('udio-downloader-toggle');
                var contextMenu = document.getElementById('udio-context-menu');

                if (uiContainer) uiContainer.remove();
                if (toggleButton) toggleButton.remove();
                if (contextMenu) contextMenu.remove();

                this.state.log('[UI] Interface destroyed successfully');
            }
        };

        // Export for potential external access
        window.UdioDownloaderUI = UI;

    // ====================================================================================
    // --- 9. INITIALIZATION - PROFESSIONAL GRADE WITH DEPENDENCY INJECTION ---
    // ====================================================================================

    async function onPageLoad() {
        console.log(`${LOG_PREFIX} --- Udio Downloader v36.0 Initializing ---`);
        const initStartTime = performance.now();

        try {
            // Step 1: Instantiate all core components first.
            const state = new State();
            const tabCoordinator = new TabCoordinator(state);
            const apiHandler = new ApiHandler(state);
            const queueManager = new QueueManager(state, apiHandler, tabCoordinator);
            const scanner = new Scanner(state, queueManager);
            const playerObserver = new PlayerObserver(state, apiHandler);

            // Step 2: COMPREHENSIVE DEPENDENCY INJECTION - Connect all components
            // This resolves all "Cannot read properties of undefined" errors.
            state.queueManager = queueManager;
            state.tabCoordinator = tabCoordinator;
            state.scanner = scanner;
            state.playerObserver = playerObserver;
            state.apiHandler = apiHandler;

            // Ensure coordinator has necessary references
            tabCoordinator.state = state; // Make sure coordinator can access state
            tabCoordinator.state.queueManager = queueManager;

            // Step 3: Initialize each component in the correct order.
            await state.initialize();
            tabCoordinator.initialize();
            const queueStatus = await queueManager.validateAndCleanQueue();

            // --- ENHANCED LOGGING ---
            state.log(`Queue validation complete. Cleaned ${queueStatus.queueCleaned} queue items and ${queueStatus.failedCleaned} failed items.`);

            // Initialize UI with all dependencies
            UI.init(state, queueManager, scanner, apiHandler);
            playerObserver.observe();

            // Step 4: Setup global event listeners AFTER UI.init() has completed.
            window.addEventListener('beforeunload', () => {
                // Save any in-memory queue items before unloading
                if (queueManager.inMemoryQueue?.length > 0) {
                    state.log(`[Queue] Page unloading. Saving ${queueManager.inMemoryQueue.length} unprocessed items.`);
                    const existingQueue = state.safeJSONParse(GM_getValue('urlQueue', '[]'), []);
                    GM_setValue('urlQueue', JSON.stringify([...queueManager.inMemoryQueue, ...existingQueue]));
                }
                // Clean up tab coordination
                tabCoordinator.cleanup();

                // Stop all active operations
                if (scanner && typeof scanner.stop === 'function') {
                    scanner.stop();
                }
                if (playerObserver && typeof playerObserver.cleanup === 'function') {
                    playerObserver.cleanup();
                }
            });

            // Cross-tab coordination listeners
            GM_addValueChangeListener('bufferQueue', (k, o, n, r) => {
                if (r && tabCoordinator.isMaster) {
                    state.log('[TabCoordinator] Buffer updated by another tab, waking up to process...');
                    setTimeout(() => queueManager.processQueue(), 250);
                }
            });

            GM_addValueChangeListener('failedUrls', (k, o, n, r) => {
                if (r) UI.scheduleRender();
            });

            GM_addValueChangeListener('capturedTracks', (k, o, n, r) => {
                if (r) {
                    state.capturedTracks = new Map(state.safeJSONParse(n, []));
                    UI.scheduleRender();
                }
            });

            // Listen for auto-capture setting changes
            GM_addValueChangeListener('isAutoCapturing', (k, o, n, r) => {
                if (r) {
                    state.isAutoCapturing = n;
                    if (n && state.bearerToken) {
                        scanner.start();
                    } else {
                        scanner.stop();
                    }
                    UI.scheduleRender();
                }
            });

            // Step 5: Start operational logic (Auto-Capture).
            if (state.isAutoCapturing && state.bearerToken) {
                state.log('Auto-Capture is ON. Starting all services...');

                // Start scanner with aggressive mode if configured
                if (scanner && typeof scanner.start === 'function') {
                    scanner.start();
                } else {
                    state.error('Scanner start method not available');
                }

                // Start queue processing if this tab is master
                if (tabCoordinator.isMaster) {
                    setTimeout(() => {
                        state.log('[Queue] Starting initial queue processing');
                        queueManager.processQueue();
                    }, 1500);
                }

            } else if (!state.isAutoCapturing) {
                state.log('Auto-Capture is OFF. Script is in manual/player-only mode.');
                setTimeout(() => {
                    UI.showToast('Manual mode active. Right-click or Ctrl+Click to capture.', 'info', 4000);
                }, 1500);
            } else if (!state.bearerToken) {
                state.warn('Auto-Capture enabled but authentication token is missing.');
                state.isAutoCapturing = false;
                GM_setValue('isAutoCapturing', false);

                setTimeout(() => {
                    UI.showToast('Authentication required. Please reload the page to enable auto-capture.', 'warning', 5000);
                }, 2000);
            }

            // Step 6: Final setup and comprehensive logging
            const initTime = performance.now() - initStartTime;

            // Performance and status report
            const statusReport = {
                initializationTime: `${initTime.toFixed(2)}ms`,
                tabRole: tabCoordinator.isMaster ? 'MASTER' : 'SLAVE',
                autoCapture: state.isAutoCapturing ? 'ENABLED' : 'DISABLED',
                tracksCaptured: state.capturedTracks.size,
                queueLength: state.safeJSONParse(GM_getValue('urlQueue', '[]'), []).length,
                bufferLength: state.safeJSONParse(GM_getValue('bufferQueue', '[]'), []).length,
                authToken: state.bearerToken ? 'PRESENT' : 'MISSING'
            };

            state.log(`✅ Enhanced initialization completed`, statusReport);

            console.log(`${LOG_PREFIX} === Udio Downloader v36.0 Fully Initialized ===`);
            console.log(`${LOG_PREFIX} Tab Role: ${tabCoordinator.isMaster ? '🎯 MASTER' : '📡 SLAVE'}`);
            console.log(`${LOG_PREFIX} Components: State ✅ | TabCoordinator ✅ | API ✅ | Queue ✅ | Scanner ✅ | Player ✅ | UI ✅`);

            // Expose for debugging and external access
            window.UdioDownloaderDebug = {
                state,
                queueManager,
                scanner,
                playerObserver,
                apiHandler,
                tabCoordinator,
                UI,
                version: '36.0'
            };

            // Global access for manual debugging
            window.udioDownloader = {
                forceRescan: () => scanner.scanPageForSongs(),
                processQueue: () => queueManager.processQueue(),
                getStatus: () => state.getPerformanceReport(),
                toggleAutoCapture: () => UI.toggleAutoCapture(),
                openUI: () => {
                    const ui = document.getElementById('udio-downloader-ui');
                    const toggle = document.getElementById('udio-downloader-toggle');
                    if (ui && toggle) {
                        ui.classList.add('open');
                        toggle.setAttribute('aria-expanded', 'true');
                        GM_setValue('isUIOpen', true);
                    }
                }
            };

        } catch (error) {
            console.error(`${LOG_PREFIX} 🚨 Initialization failed:`, error);

            // User-friendly error message
            const errorMessage = `Udio Downloader failed to initialize.

    Error: ${error.message}

    Please:
    1. Refresh the page and try again
    2. Check the browser console for details
    3. Ensure you're logged into Udio`;

            setTimeout(() => {
                if (window.UdioDownloaderUI && typeof window.UdioDownloaderUI.showToast === 'function') {
                    window.UdioDownloaderUI.showToast('Initialization failed - check console', 'error', 5000);
                } else {
                    alert(errorMessage);
                }
            }, 1000);

            // Re-throw for further debugging
            throw error;
        }
    }

    // Track initialization start time
    window.udioDlStartTime = performance.now();

    // Enhanced page load handling with manual selection readiness
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', onPageLoad, { once: true });
    } else {
        // If DOM is already loaded, wait a bit for Udio's JS to initialize
        setTimeout(onPageLoad, 500);
    }

    // Early setup for manual selection context menu prevention
    document.addEventListener('DOMContentLoaded', () => {
        // Add a small delay to ensure our context menu handler is registered first
        setTimeout(() => {
            console.log(`${LOG_PREFIX} Enhanced initialization system ready`);
            console.log(`${LOG_PREFIX} Manual selection handlers registered`);

            // Early context menu prevention setup
            if (typeof UI !== 'undefined' && UI.addContextMenuSupport) {
                UI.addContextMenuSupport();
            }
        }, 100);
    });
    })();