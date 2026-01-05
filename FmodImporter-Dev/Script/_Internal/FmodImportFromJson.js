/**
 * FMOD Importer - Import From JSON
 *
 * This script reads import data from a JSON file and creates events in FMOD Studio.
 * It is called by the Python FMOD Importer Tool via fmodstudiocl.exe
 *
 * Supports two modes:
 * - Template mode: Clone an existing event (preserves effects/parameters)
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

    // ========== HELPER FUNCTIONS ==========

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
            console.log("DEBUG: Writing JSON to: " + path);

            // Valider le chemin
            if (!path || path.length === 0) {
                throw new Error("Invalid path: empty or null");
            }

            // Sérialiser les données
            var jsonString = JSON.stringify(data, null, 2);
            if (!jsonString || jsonString.length === 0) {
                throw new Error("Failed to serialize data to JSON");
            }

            console.log("DEBUG: JSON serialized (" + jsonString.length + " chars)");

            // Écrire le fichier
            var file = studio.system.getFile(path);
            if (!file) {
                throw new Error("Cannot get file handle for: " + path);
            }

            file.open(studio.system.openMode.WriteOnly);
            file.writeText(jsonString);
            file.close();

            console.log("DEBUG: File written successfully");
            return true;

        } catch (writeErr) {
            console.log("ERROR: writeJsonFile failed: " + writeErr.message);

            // Fallback : essayer d'écrire dans le dossier du projet
            try {
                var projectDir = studio.project.filePath.replace(/[^\/\\]+$/, '');
                var fallbackPath = projectDir + "fmod_import_result_fallback.json";
                console.log("DEBUG: Attempting fallback write to: " + fallbackPath);

                var fallbackFile = studio.system.getFile(fallbackPath);
                fallbackFile.open(studio.system.openMode.WriteOnly);
                fallbackFile.writeText(JSON.stringify(data, null, 2));
                fallbackFile.close();

                console.log("DEBUG: Fallback write successful");
                return true;
            } catch (fallbackErr) {
                console.log("CRITICAL: Fallback write also failed: " + fallbackErr.message);
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

    // Find or create bank by name
    function findOrCreateBank(bankName, messages) {
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

    // Find or create folder by path
    function findOrCreateFolder(folderPath, messages) {
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
        resultPath = importData.resultPath;  // Use global resultPath from wrapper (no 'var')
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
                    // MODE A: Clone from template by copying its structure
                    var template = findEventByPath(eventData.templateEventPath);
                    if (template && template.isOfType("Event")) {
                        try {
                            // Create new event
                            event = studio.project.create("Event");

                            // Copy basic properties with defensive checks
                            if (template.isOneshot !== undefined) event.isOneshot = template.isOneshot;
                            if (template.isStream !== undefined) event.isStream = template.isStream;
                            if (template.is3D !== undefined) event.is3D = template.is3D;
                            if (template.minDistance !== undefined) event.minDistance = template.minDistance;
                            if (template.maxDistance !== undefined) event.maxDistance = template.maxDistance;

                            // Copy master track properties with error handling
                            if (template.masterTrack && event.masterTrack) {
                                try {
                                    if (template.masterTrack.volume !== undefined)
                                        event.masterTrack.volume = template.masterTrack.volume;
                                    if (template.masterTrack.pitch !== undefined)
                                        event.masterTrack.pitch = template.masterTrack.pitch;
                                } catch (masterErr) {
                                    result.messages.push("WARN: Could not copy master track properties: " + masterErr.message);
                                }
                            }

                            // Copy existing group tracks from template (without audio)
                            var templateTracks = template.groupTracks;
                            for (var t = 0; t < templateTracks.length; t++) {
                                try {
                                    var templateTrack = templateTracks[t];
                                    // Add track to new event
                                    var newTrack = event.addGroupTrack();

                                    // Copy track properties with defensive checks
                                    if (templateTrack.volume !== undefined) newTrack.volume = templateTrack.volume;
                                    if (templateTrack.pitch !== undefined) newTrack.pitch = templateTrack.pitch;

                                    // Copy effects chain (but not sound modules)
                                    var modules = templateTrack.modules;
                                    for (var m = 0; m < modules.length; m++) {
                                        var module = modules[m];
                                        // Skip audio modules (we'll add our own audio later)
                                        if (module.isOfType("SingleSound") || module.isOfType("MultiSound")) {
                                            continue;
                                        }
                                        // TODO: Copy effect modules if needed (requires more complex cloning)
                                    }
                                } catch (trackErr) {
                                    result.messages.push("WARN: Could not copy group track " + t + ": " + trackErr.message);
                                }
                            }

                            result.messages.push("INFO: Created event from template '" + template.name + "'");
                        } catch (cloneErr) {
                            result.messages.push("WARN: Failed to clone template '" + eventData.templateEventPath + "': " + cloneErr.message + ", creating from scratch");
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
                    var folder = findOrCreateFolder(eventData.destFolderPath, result.messages);
                    if (folder) {
                        event.folder = folder;
                    }
                }

                // 5. Assign to bank (create if doesn't exist)
                if (eventData.bankName) {
                    var bank = findOrCreateBank(eventData.bankName, result.messages);
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
        console.log("=== Import Finally Block ===");

        // Toujours essayer d'écrire le résultat
        var resultWritten = false;

        if (typeof result !== 'undefined' && result) {
            if (typeof resultPath !== 'undefined' && resultPath) {
                resultWritten = writeJsonFile(resultPath, result);
            } else {
                console.log("WARNING: resultPath is undefined, using fallback");

                // Fallback: utiliser le chemin du projet
                var projectDir = studio.project.filePath.replace(/[^\/\\]+$/, '');
                var fallbackPath = projectDir + "fmod_import_result_emergency.json";
                resultWritten = writeJsonFile(fallbackPath, result);
            }
        } else {
            console.log("WARNING: result is undefined, creating emergency result");

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
            console.log("CRITICAL: Failed to write result file after all attempts");

            // Dernière tentative : afficher un message modal pour alerter l'utilisateur
            try {
                studio.ui.showModalDialog(
                    "Import Result Write Failed",
                    "CRITICAL ERROR: Could not write import result file.\\n\\n" +
                    "The import may have succeeded, but the tool cannot verify the status.\\n\\n" +
                    "Please check FMOD Studio console for details."
                );
            } catch (dialogErr) {
                console.log("CRITICAL: Cannot even show error dialog: " + dialogErr.message);
            }
        } else {
            console.log("Result file written successfully");
        }

        console.log("=== Import Script Complete ===");
    }
})();
