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

    // Write JSON result file
    function writeJsonFile(path, data) {
        var file = studio.system.getFile(path);
        file.open(studio.system.openMode.WriteOnly);
        file.writeText(JSON.stringify(data, null, 2));
        file.close();
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

    // Find bus/mixer group by path or name (NO CREATION - just find existing)
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
            // Lookup failed, try other methods
        }

        // Search by name (last part of path or full name)
        var parts = busPath.replace("bus:/", "").split('/');
        var searchName = parts[parts.length - 1];

        // Check master bus
        try {
            var masterBus = studio.project.workspace.masterBus;
            if (masterBus && masterBus.name === searchName) {
                return masterBus;
            }
        } catch (e) {
            // Master bus not accessible
        }

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

    // ========== MAIN IMPORT LOGIC ==========

    try {
        var importData = readJsonFile(jsonPath);
        var resultPath = importData.resultPath;
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
                        try {
                            var asset = studio.project.importAudioFile(audioPath);
                            if (asset) {
                                audioAssets.push(asset);
                            }
                        } catch (audioErr) {
                            result.messages.push("WARN: Failed to import audio '" + audioPath + "': " + audioErr.message);
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
                    // MODE A: Clone from template
                    var template = findEventByPath(eventData.templateEventPath);
                    if (template && template.isOfType("Event")) {
                        // Try duplicate() first (FMOD Studio 2.x), then copy()
                        if (typeof template.duplicate === "function") {
                            event = template.duplicate();
                        } else if (typeof template.copy === "function") {
                            event = template.copy();
                        } else {
                            // No clone method available, create from scratch
                            result.messages.push("WARN: Template found but cannot clone (no duplicate/copy method), creating from scratch");
                            event = studio.project.create("Event");
                        }

                        // Clear existing audio from cloned template (if we successfully cloned)
                        if (event && event !== template) {
                            var tracks = event.groupTracks;
                            for (var t = 0; t < tracks.length; t++) {
                                var modules = tracks[t].modules;
                                for (var m = modules.length - 1; m >= 0; m--) {
                                    if (modules[m].isOfType("SingleSound") || modules[m].isOfType("MultiSound")) {
                                        modules[m].deleteObject();
                                    }
                                }
                            }
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

                // 8. Assign bus/mixer output (find existing bus only - no creation)
                if (eventData.busName) {
                    try {
                        var bus = findBusByPath(eventData.busName);
                        if (bus) {
                            // Route event output to this bus
                            if (event.mixer && event.mixer.output !== undefined) {
                                event.mixer.output = bus;
                            } else if (event.masterTrack && event.masterTrack.mixerGroup) {
                                event.masterTrack.mixerGroup.output = bus;
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

        // Show completion summary
        var summary = "Import Complete!\n\n";
        summary += "Imported: " + result.imported + "\n";
        summary += "Failed: " + result.failed + "\n";
        summary += "Skipped: " + result.skipped;

        if (result.messages.length > 0) {
            var messagesToShow = result.messages.length <= 10 ? result.messages : result.messages.slice(0, 10);
            summary += "\n\nDetails:\n" + messagesToShow.join("\n");
            if (result.messages.length > 10) {
                summary += "\n... and " + (result.messages.length - 10) + " more (see result file)";
            }
        }

        studio.ui.showModalDialog("FMOD Importer", summary);

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
    }
})();
