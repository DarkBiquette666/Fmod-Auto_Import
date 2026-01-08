/**
 * FMOD Importer - Import From JSON
 *
 * This script reads import data from a JSON file and creates events in FMOD Studio.
 * It is called by the Python FMOD Importer Tool via fmodstudiocl.exe
 *
 * Supports two modes:
 * - Template mode: Uses native FMOD Duplicate action to copy an existing event,
 *   preserving ALL properties: effects, parameters, mixer settings, etc.
 * - From-scratch mode: Create a new empty event
 */

(function() {
    "use strict";

    // Get JSON path from global variable set by wrapper script
    if (typeof FMOD_IMPORTER_JSON_PATH === 'undefined') {
        studio.ui.showModalDialog("Error", "FMOD_IMPORTER_JSON_PATH not defined. This script must be called via the wrapper.");
        return;
    }

    var jsonPath = FMOD_IMPORTER_JSON_PATH;
    var logPath = (typeof FMOD_IMPORTER_LOG_PATH !== 'undefined') ? FMOD_IMPORTER_LOG_PATH : "";

    // ========== HELPER FUNCTIONS ==========

    // Debug logging to file
    function debugLog(message) {
        // Always log to console
        console.log(message);
        
        // Log to file if path is available
        if (logPath && logPath.length > 0) {
            try {
                var file = studio.system.getFile(logPath);
                file.open(studio.system.openMode.WriteOnly | studio.system.openMode.Append);
                file.writeText("[" + new Date().toISOString() + "] " + message + "\n");
                file.close();
            } catch (e) {
                // Fail silently on log error to not break the script
            }
        }
    }

    debugLog("=== FMOD IMPORT SCRIPT STARTED ===");
    debugLog("JSON Path: " + jsonPath);
    debugLog("Result Path: " + ((typeof resultPath !== 'undefined') ? resultPath : "undefined"));

    // Read JSON file
    function readJsonFile(path) {
        var file = studio.system.getFile(path);
        file.open(studio.system.openMode.ReadOnly);
        var text = file.readText(file.size());
        file.close();
        return JSON.parse(text);
    }

    // Write JSON result file with robust error handling
    function writeJsonFile(path, data) {
        try {
            debugLog("DEBUG: Writing JSON to: " + path);

            // Valider le chemin
            if (!path || path.length === 0) {
                throw new Error("Invalid path: empty or null");
            }

            // Sérialiser les données
            var jsonString = JSON.stringify(data, null, 2);
            if (!jsonString || jsonString.length === 0) {
                throw new Error("Failed to serialize data to JSON");
            }

            debugLog("DEBUG: JSON serialized (" + jsonString.length + " chars)");

            // Écrire le fichier
            var file = studio.system.getFile(path);
            if (!file) {
                throw new Error("Cannot get file handle for: " + path);
            }

            file.open(studio.system.openMode.WriteOnly);
            file.writeText(jsonString);
            file.close();

            debugLog("DEBUG: File written successfully");
            return true;

        } catch (writeErr) {
            debugLog("ERROR: writeJsonFile failed: " + writeErr.message);

            // Fallback : essayer d'écrire dans le dossier du projet
            try {
                var projectDir = studio.project.filePath.replace(/[^\/\\]+$/, '');
                var fallbackPath = projectDir + "fmod_import_result_fallback.json";
                debugLog("DEBUG: Attempting fallback write to: " + fallbackPath);

                var fallbackFile = studio.system.getFile(fallbackPath);
                fallbackFile.open(studio.system.openMode.WriteOnly);
                fallbackFile.writeText(JSON.stringify(data, null, 2));
                fallbackFile.close();

                debugLog("DEBUG: Fallback write successful");
                return true;
            } catch (fallbackErr) {
                debugLog("CRITICAL: Fallback write also failed: " + fallbackErr.message);
                return false;
            }
        }
    }

    // Find event by path (adds event:/ prefix if needed)
    function findEventByPath(path) {
        if (!path) return null;

        // Try with event:/ prefix first
        try {
            var lookupPath = path;
            if (!path.startsWith("event:/")) {
                lookupPath = "event:/" + path;
            }
            var result = studio.project.lookup(lookupPath);
            if (result && result.isOfType("Event")) {
                return result;
            }
        } catch (e) {
            // Lookup failed, try fallback search
        }

        // Fallback: search by event name (last part of path)
        var parts = path.replace("event:/", "").split('/');
        var eventName = parts[parts.length - 1];

        var allEvents = studio.project.model.Event.findInstances();
        for (var i = 0; i < allEvents.length; i++) {
            if (allEvents[i].name === eventName) {
                return allEvents[i];
            }
        }

        return null;
    }

    // Find folder by path (adds folder:/ prefix if needed)
    function findFolderByPath(path) {
        if (!path) return null;
        try {
            // Add folder:/ prefix if not present
            var lookupPath = path;
            if (!path.startsWith("folder:/")) {
                lookupPath = "folder:/" + path;
            }
            return studio.project.lookup(lookupPath);
        } catch (e) {
            return null;
        }
    }

    // Find bank by name (search all banks)
    function findBankByName(bankName) {
        if (!bankName) return null;

        // Use model to find all Bank instances
        var banks = studio.project.model.Bank.findInstances();
        for (var i = 0; i < banks.length; i++) {
            if (banks[i].name === bankName) {
                return banks[i];
            }
        }
        return null;
    }

    // Find or create bank by name/ID
    function findOrCreateBank(bankId, bankName, messages) {
        // Try lookup by ID first (most reliable)
        if (bankId) {
            try {
                var bankById = studio.project.lookup(bankId);
                if (bankById && bankById.isOfType("Bank")) {
                    return bankById;
                }
            } catch (e) {
                // Lookup failed
            }
        }

        if (!bankName) return null;

        var bank = findBankByName(bankName);
        if (bank) return bank;

        // Bank doesn't exist, create it
        try {
            bank = studio.project.create("Bank");
            bank.name = bankName;
            // Add to master bank folder
            bank.folder = studio.project.workspace.masterBankFolder;
            messages.push("INFO: Created bank '" + bankName + "'");
            return bank;
        } catch (e) {
            messages.push("WARN: Failed to create bank '" + bankName + "': " + e.message);
            return null;
        }
    }

    // Clear audio modules from an event (used when duplicating from template)
    // Removes SingleSound and MultiSound modules so we can add our own audio
    function clearAudioModules(event) {
        if (!event) return;

        try {
            // Clear audio from all group tracks
            var tracks = event.groupTracks;
            for (var t = 0; t < tracks.length; t++) {
                var track = tracks[t];
                var modules = track.modules;

                // Iterate backwards to safely remove
                for (var m = modules.length - 1; m >= 0; m--) {
                    var module = modules[m];
                    if (module.isOfType("SingleSound") || module.isOfType("MultiSound")) {
                        module.delete();
                    }
                }
            }

            // Also clear from timeline if present
            if (event.timeline) {
                var timelineModules = event.timeline.modules;
                for (var tm = timelineModules.length - 1; tm >= 0; tm--) {
                    var tlModule = timelineModules[tm];
                    if (tlModule.isOfType("SingleSound") || tlModule.isOfType("MultiSound")) {
                        tlModule.delete();
                    }
                }
            }
        } catch (e) {
            // Silent fail - we'll add new audio anyway
        }
    }

    // Find bus by path or name
    function findBusByPath(busPath) {
        if (!busPath) return null;

        // Try lookup with bus:/ prefix first
        try {
            var lookupPath = busPath;
            if (!busPath.startsWith("bus:/")) {
                lookupPath = "bus:/" + busPath;
            }
            var result = studio.project.lookup(lookupPath);
            if (result) return result;
        } catch (e) {
            // Lookup failed, try by name
        }

        // Search by name (last part of path)
        var parts = busPath.replace("bus:/", "").split('/');
        var searchName = parts[parts.length - 1];

        // Search all MixerGroup instances
        try {
            var mixerGroups = studio.project.model.MixerGroup.findInstances();
            for (var i = 0; i < mixerGroups.length; i++) {
                if (mixerGroups[i].name === searchName) {
                    return mixerGroups[i];
                }
            }
        } catch (e) {
            // Search failed
        }

        return null;
    }

    // Find or create folder by path/ID
    function findOrCreateFolder(folderId, folderPath, messages) {
        // Try lookup by ID first (most reliable)
        if (folderId) {
            try {
                var folderById = studio.project.lookup(folderId);
                if (folderById && (folderById.isOfType("EventFolder") || folderById.isOfType("MasterEventFolder"))) {
                    return folderById;
                }
            } catch (e) {
                // Lookup failed
            }
        }

        if (!folderPath) return null;

        var folder = findFolderByPath(folderPath);
        if (folder) return folder;

        // Folder doesn't exist, create it recursively
        try {
            var parts = folderPath.split('/');
            var currentFolder = studio.project.workspace.masterEventFolder;

            for (var i = 0; i < parts.length; i++) {
                var partName = parts[i];
                if (!partName) continue;

                // Look for existing subfolder
                var found = null;
                var items = currentFolder.items;
                for (var j = 0; j < items.length; j++) {
                    if (items[j].isOfType("EventFolder") && items[j].name === partName) {
                        found = items[j];
                        break;
                    }
                }

                if (found) {
                    currentFolder = found;
                } else {
                    // Create new folder
                    var newFolder = studio.project.create("EventFolder");
                    newFolder.name = partName;
                    newFolder.folder = currentFolder;
                    currentFolder = newFolder;
                }
            }

            messages.push("INFO: Created folder '" + folderPath + "'");
            return currentFolder;
        } catch (e) {
            messages.push("WARN: Failed to create folder '" + folderPath + "': " + e.message);
            return null;
        }
    }

    // Find or import audio file (handles both existing and new files)
    function findOrImportAudioFile(audioPath) {
        if (!audioPath) return null;

        // STEP 1: Try to find existing audio file in project
        // This handles files that were already copied to Assets/ by Python
        try {
            var allAudioFiles = studio.project.model.AudioFile.findInstances();
            for (var i = 0; i < allAudioFiles.length; i++) {
                var audioFile = allAudioFiles[i];

                // Normalize paths for comparison (handle Windows backslash vs forward slash)
                var normalizedAssetPath = audioFile.assetPath.replace(/\\/g, '/').toLowerCase();
                var normalizedAudioPath = audioPath.replace(/\\/g, '/').toLowerCase();

                // Extract filenames for comparison
                var assetFilename = normalizedAssetPath.split('/').pop();
                var searchFilename = normalizedAudioPath.split('/').pop();

                // Match by full path, suffix, or filename
                if (normalizedAssetPath === normalizedAudioPath ||
                    normalizedAssetPath.endsWith(normalizedAudioPath) ||
                    normalizedAudioPath.endsWith(normalizedAssetPath) ||
                    assetFilename === searchFilename) {
                    return audioFile;  // FOUND - return existing file
                }
            }
        } catch (e) {
            // Lookup failed, fall through to import
        }

        // STEP 2: Not found in project - import as external file
        try {
            return studio.project.importAudioFile(audioPath);
        } catch (importErr) {
            return null;
        }
    }

    // ========== MAIN IMPORT LOGIC ==========

    try {
        var importData = readJsonFile(jsonPath);
        // resultPath already defined by wrapper - no need to reassign
        var events = importData.events;

        var result = {
            imported: 0,
            failed: 0,
            skipped: 0,
            messages: []
        };

        for (var i = 0; i < events.length; i++) {
            var eventData = events[i];

            try {
                // 1. Import audio files first
                var audioAssets = [];
                if (eventData.audioFilePaths && eventData.audioFilePaths.length > 0) {
                    for (var a = 0; a < eventData.audioFilePaths.length; a++) {
                        var audioPath = eventData.audioFilePaths[a];
                        result.messages.push("DEBUG: Processing audio file: " + audioPath);

                        try {
                            var asset = findOrImportAudioFile(audioPath);
                            if (asset) {
                                audioAssets.push(asset);
                                result.messages.push("DEBUG: Audio obtained successfully: " + asset.assetPath);
                            } else {
                                result.messages.push("ERROR: Failed to obtain audio (null returned): " + audioPath);
                            }
                        } catch (audioErr) {
                            result.messages.push("ERROR: Exception while processing audio '" + audioPath + "': " + audioErr.message);
                        }
                    }
                }

                if (audioAssets.length === 0) {
                    result.messages.push("SKIP: No audio imported for '" + eventData.newEventName + "'");
                    result.skipped++;
                    continue;
                }

                // 2. Create event - TWO MODES
                var event;

                if (eventData.templateEventPath) {
                    // MODE A: Duplicate from template using native FMOD action
                    // This preserves ALL template properties: effects, parameters, mixer settings
                    var template = findEventByPath(eventData.templateEventPath);
                    if (template && template.isOfType("Event")) {
                        try {
                            // Collect existing event IDs before duplication
                            var existingEvents = studio.project.model.Event.findInstances();
                            var existingIds = {};
                            for (var ei = 0; ei < existingEvents.length; ei++) {
                                existingIds[existingEvents[ei].id] = true;
                            }

                            // Navigate to template and trigger native Duplicate action
                            // This copies EVERYTHING: effects, parameters, mixer settings, etc.
                            studio.window.navigateTo(template);
                            studio.window.triggerAction(studio.window.actions.Duplicate);

                            // Find the newly created event (the one not in existingIds)
                            var allEventsAfter = studio.project.model.Event.findInstances();
                            for (var ea = 0; ea < allEventsAfter.length; ea++) {
                                if (!existingIds[allEventsAfter[ea].id]) {
                                    event = allEventsAfter[ea];
                                    break;
                                }
                            }

                            if (!event) {
                                throw new Error("Could not find duplicated event after Duplicate action");
                            }

                            // Clear existing audio modules from the duplicated event
                            // (template may have placeholder audio that we need to replace)
                            clearAudioModules(event);

                            result.messages.push("INFO: Duplicated event from template '" + template.name + "' (preserving effects)");
                        } catch (dupErr) {
                            result.messages.push("WARN: Failed to duplicate template '" + eventData.templateEventPath + "': " + dupErr.message + ", creating from scratch");
                            event = studio.project.create("Event");
                        }
                    } else {
                        result.messages.push("WARN: Template not found '" + eventData.templateEventPath + "', creating from scratch");
                        event = studio.project.create("Event");
                    }
                } else {
                    // MODE B: Create from scratch
                    event = studio.project.create("Event");
                }

                // 3. Set event name
                event.name = eventData.newEventName;
                result.messages.push("DEBUG: Created event with ID: " + event.id + ", name: " + event.name);

                // 4. Assign to folder (create if doesn't exist)
                if (eventData.destFolderPath) {
                    var folder = findOrCreateFolder(eventData.destFolderId, eventData.destFolderPath, result.messages);
                    if (folder) {
                        event.folder = folder;
                    }
                }

                // 5. Assign to bank (create if doesn't exist)
                if (eventData.bankName) {
                    var bank = findOrCreateBank(eventData.bankId, eventData.bankName, result.messages);
                    if (bank) {
                        event.relationships.banks.add(bank);
                    }
                }

                // 6. Get or create track for audio
                var track;
                if (event.groupTracks.length > 0) {
                    track = event.groupTracks[0];
                } else {
                    track = event.addGroupTrack();
                }

                // 7. Add audio to track using FMOD's track.addSound() API
                var timeline = event.timeline;

                if (eventData.isMulti && audioAssets.length > 1) {
                    // Multiple files -> create MultiSound with all audio files
                    var maxLength = 0;
                    for (var ml = 0; ml < audioAssets.length; ml++) {
                        var assetLen = audioAssets[ml].length || 1.0;
                        if (assetLen > maxLength) maxLength = assetLen;
                    }

                    // Create MultiSound on the track
                    var multiSound = track.addSound(timeline, "MultiSound", 0, maxLength);

                    // Add each audio file as a SingleSound inside the MultiSound
                    for (var ai = 0; ai < audioAssets.length; ai++) {
                        var innerSound = studio.project.create("SingleSound");
                        innerSound.audioFile = audioAssets[ai];
                        innerSound.owner = multiSound;  // Owner is the MultiSound
                    }
                } else {
                    // Single file -> create SingleSound directly on track
                    var audioAsset = audioAssets[0];
                    var audioLength = audioAsset.length || 1.0;

                    var singleSound = track.addSound(timeline, "SingleSound", 0, audioLength);
                    singleSound.audioFile = audioAsset;
                }

                result.messages.push("DEBUG: Assigned " + audioAssets.length + " audio file(s) to track");

                // 8. Bus routing - use mixerInput.output (correct FMOD API)
                if (eventData.busName) {
                    try {
                        var bus = findBusByPath(eventData.busName);
                        if (bus) {
                            // Correct method: event.mixerInput.output = bus
                            // NOT: event.masterTrack.mixerGroup.output (creates parasitic groups)
                            if (event.mixerInput) {
                                event.mixerInput.output = bus;
                            }
                        } else {
                            result.messages.push("WARN: Bus not found '" + eventData.busName + "'");
                        }
                    } catch (busErr) {
                        result.messages.push("WARN: Could not assign bus '" + eventData.busName + "': " + busErr.message);
                    }
                }

                result.imported++;
                result.messages.push("OK: " + eventData.newEventName);

            } catch (eventError) {
                result.failed++;
                result.messages.push("FAIL: '" + eventData.newEventName + "' - " + eventError.message);
            }
        }

        // Save project
        studio.project.save();

        // Write result file
        writeJsonFile(resultPath, result);

        // IMPORTANT: Give FMOD time to finalize save operations
        // Without this delay, FMOD Studio may crash on exit (0xC0000005)
        // This doesn't affect data - everything is saved correctly
        // But prevents the crash reporter dialog from appearing
        result.messages.push("INFO: Waiting for FMOD to finalize operations...");

        // Wait 1 second to let FMOD finish background operations
        var startTime = Date.now();
        while (Date.now() - startTime < 1000) {
            // Busy wait
        }

        // Don't show modal dialog - Python displays the results
        // Modal dialogs can sometimes trigger crashes when FMOD exits
        result.messages.push("INFO: Import completed successfully. Check Python output for details.");

    } catch (e) {
        studio.ui.showModalDialog("Import Error", "Failed to execute import:\n\n" + e.message + "\n\nStack:\n" + e.stack);

        // Try to write error result
        try {
            var errorResult = {
                imported: 0,
                failed: 0,
                skipped: 0,
                messages: ["Critical error: " + e.message]
            };
            if (importData && importData.resultPath) {
                writeJsonFile(importData.resultPath, errorResult);
            }
        } catch (writeError) {
            // Silent fail on error result write
        }
    } finally {
        debugLog("=== Import Finally Block ===");

        // Toujours essayer d'écrire le résultat
        var resultWritten = false;

        if (typeof result !== 'undefined' && result) {
            if (typeof resultPath !== 'undefined' && resultPath) {
                resultWritten = writeJsonFile(resultPath, result);
            } else {
                debugLog("WARNING: resultPath is undefined, using fallback");

                // Fallback: utiliser le chemin du projet
                var projectDir = studio.project.filePath.replace(/[^\/\\]+$/, '');
                var fallbackPath = projectDir + "fmod_import_result_emergency.json";
                resultWritten = writeJsonFile(fallbackPath, result);
            }
        } else {
            debugLog("WARNING: result is undefined, creating emergency result");

            // Créer un résultat d'urgence
            var emergencyResult = {
                success: false,
                error: "Script executed but result object was not created",
                imported: 0,
                skipped: 0,
                failed: 0,
                messages: ["CRITICAL: Result object undefined - script may have crashed"]
            };

            // Essayer d'écrire dans le dossier du projet
            var projectDir = studio.project.filePath.replace(/[^\/\\]+$/, '');
            var emergencyPath = projectDir + "fmod_import_result_emergency.json";
            resultWritten = writeJsonFile(emergencyPath, emergencyResult);
        }

        if (!resultWritten) {
            debugLog("CRITICAL: Failed to write result file after all attempts");

            // Dernière tentative : afficher un message modal pour alerter l'utilisateur
            try {
                studio.ui.showModalDialog(
                    "Import Result Write Failed",
                    "CRITICAL ERROR: Could not write import result file.\\n\\n" +
                    "The import may have succeeded, but the tool cannot verify the status.\\n\\n" +
                    "Please check FMOD Studio console for details."
                );
            } catch (dialogErr) {
                debugLog("CRITICAL: Cannot even show error dialog: " + dialogErr.message);
            }
        } else {
            debugLog("Result file written successfully");
        }

        debugLog("=== Import Script Complete ===");
    }
})();
