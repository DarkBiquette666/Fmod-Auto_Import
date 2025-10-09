// Moco Auto Import - FMOD Studio Script
// This script is called from Python via command line to import events using FMOD API

function normalizePath(path) {
    return path ? path.replace(/\\/g, "/") : "";
}

function readTextFile(path) {
    var file = studio.system.getFile(path);
    file.open(studio.system.openMode.ReadOnly);
    var size = file.size();
    var text = file.readText(size);
    file.close();
    return text;
}

function writeTextFile(path, text) {
    var file = studio.system.getFile(path);
    file.open(studio.system.openMode.WriteOnly);
    file.writeText(text);
    file.close();
}

// Find event folder by path string (e.g., "Events/Characters/Cat")
function findEventFolderByPath(pathStr) {
    var master = studio.project.workspace.masterEventFolder;
    if (!pathStr || !pathStr.length) {
        return master;
    }

    var parts = pathStr.split("/").filter(function (p) { return p.length > 0; });
    var current = master;

    for (var i = 0; i < parts.length; i++) {
        var found = false;

        // Search in current folder's items
        if (current.items) {
            for (var j = 0; j < current.items.length; j++) {
                var item = current.items[j];
                if (item.entity === "EventFolder" && item.name === parts[i]) {
                    current = item;
                    found = true;
                    break;
                }
            }
        }

        if (!found) {
            return null;
        }
    }

    return current;
}

// Find event by full path (e.g., "Events/Template/Prefix_Character_Action")
function findEventByPath(pathStr) {
    var allEvents = studio.project.model.Event.findInstances();

    for (var i = 0; i < allEvents.length; i++) {
        var event = allEvents[i];
        var eventPath = getEventFullPath(event);

        if (eventPath === pathStr) {
            return event;
        }
    }

    console.log("Template event NOT found: " + pathStr);
    return null;
}

// Get full path of an event including folder hierarchy (excluding master folder)
function getEventFullPath(event) {
    var parts = [];
    parts.push(event.name);

    var folder = event.folder;

    while (folder && folder.name) {
        parts.unshift(folder.name);
        folder = folder.folder;
    }

    // Remove "Master" from the beginning if present
    if (parts.length > 0 && parts[0] === "Master") {
        parts.shift();
    }

    return parts.join('/');
}

// Find or create bank
function ensureBank(bankName) {
    if (!bankName || !bankName.length) {
        return null;
    }

    var banks = studio.project.model.Bank.findInstances();
    for (var i = 0; i < banks.length; i++) {
        if (banks[i].name === bankName) {
            return banks[i];
        }
    }

    var bank = studio.project.create("Bank");
    bank.name = bankName;
    bank.folder = studio.project.workspace.masterBankFolder;
    return bank;
}

// Find bus/mixer group by name
function findBusByName(busName) {
    if (!busName || !busName.length) {
        return null;
    }

    var buses = studio.project.model.MixerGroup.findInstances();
    for (var i = 0; i < buses.length; i++) {
        if (buses[i].name === busName) {
            return buses[i];
        }
    }

    return null;
}

// Get filename from full path
function getFilename(fullPath) {
    var normalized = fullPath.replace(/\\/g, "/");
    var lastSlash = normalized.lastIndexOf("/");
    return lastSlash >= 0 ? normalized.substring(lastSlash + 1) : normalized;
}

// Copy file from source to destination
function copyFile(sourcePath, destPath) {
    try {
        var sourceFile = studio.system.getFile(sourcePath);
        sourceFile.open(studio.system.openMode.ReadOnly);
        var data = sourceFile.read(sourceFile.size());
        sourceFile.close();

        var destFile = studio.system.getFile(destPath);
        destFile.open(studio.system.openMode.WriteOnly);
        destFile.write(data);
        destFile.close();

        return true;
    } catch (e) {
        return false;
    }
}

// Get project's Assets folder path
function getProjectAssetsPath(projectPath) {
    var normalized = normalizePath(projectPath);
    var lastSlash = normalized.lastIndexOf("/");
    var projectDir = lastSlash >= 0 ? normalized.substring(0, lastSlash) : normalized;
    return projectDir + "/Assets";
}

// Create directory recursively
function createDirectory(dirPath) {
    try {
        // Use Node.js style directory creation via system command
        var createCmd = 'mkdir "' + dirPath.replace(/\//g, "\\") + '"';
        studio.system.start(createCmd);
        return true;
    } catch (e) {
        return false;
    }
}

// Debug helper to dump object structure
function dumpObjectStructure(obj, name, maxDepth) {
    maxDepth = maxDepth || 2;
    var lines = ["\n=== " + name + " ==="];

    function dumpLevel(o, depth, prefix) {
        if (depth > maxDepth || !o) return;

        try {
            if (o.entity) lines.push(prefix + "entity: " + o.entity);
            if (o.name) lines.push(prefix + "name: " + o.name);
            if (o.id) lines.push(prefix + "id: " + o.id);

            // Check relationships
            if (o.relationships) {
                lines.push(prefix + "relationships:");
                for (var key in o.relationships) {
                    try {
                        var rel = o.relationships[key];
                        if (rel && rel.length !== undefined) {
                            lines.push(prefix + "  " + key + ": [" + rel.length + " items]");
                        } else if (rel) {
                            lines.push(prefix + "  " + key + ": exists");
                        }
                    } catch (e) {}
                }
            }
        } catch (e) {
            lines.push(prefix + "ERROR: " + e.toString());
        }
    }

    dumpLevel(obj, 0, "  ");
    return lines.join("\n");
}

// Main import function
function importEventsFromJson(data) {
    var result = {
        imported: 0,
        failed: 0,
        messages: [],
        debugLog: []
    };

    var bank = ensureBank(data.bankName);
    var bus = findBusByName(data.busName);
    var events = data.events || [];

    // Get Assets folder path
    var assetsPath = getProjectAssetsPath(data.projectPath);
    result.debugLog.push("=== IMPORT SESSION START ===");
    result.debugLog.push("Project: " + data.projectPath);
    result.debugLog.push("Assets folder: " + assetsPath);
    result.debugLog.push("Bank: " + (bank ? bank.name : "NONE"));
    result.debugLog.push("Bus: " + (bus ? bus.name : "NONE"));
    result.debugLog.push("Events to import: " + events.length);

    for (var i = 0; i < events.length; i++) {
        var entry = events[i];
        result.debugLog.push("\n--- Event " + (i + 1) + "/" + events.length + ": " + entry.newEventName + " ---");

        try {
            // Find destination folder
            var destFolderPath = entry.destFolderPath || data.defaultDestFolderPath || "";
            var destFolder = findEventFolderByPath(destFolderPath);
            if (!destFolder) {
                throw new Error("Destination folder not found: " + destFolderPath);
            }
            result.debugLog.push("Dest folder: " + destFolderPath + " - FOUND");

            // Find template event
            var templateEvent = null;
            if (entry.templateEventPath) {
                templateEvent = findEventByPath(entry.templateEventPath);
                if (!templateEvent) {
                    throw new Error("Template event not found: " + entry.templateEventPath);
                }
                result.debugLog.push("Template: " + entry.templateEventPath + " - FOUND");
            }

            // Create new event (templates not used for now - manual duplication not supported in API)
            var newEvent = studio.project.create("Event");
            newEvent.name = entry.newEventName;
            newEvent.folder = destFolder;
            result.debugLog.push("Event created: " + newEvent.name);

            // Assign event to bank
            if (bank) {
                newEvent.relationships.banks.add(bank);
                result.debugLog.push("Bank assigned: " + bank.name);
            }

            result.debugLog.push("Audio files to import: " + (entry.audioFilePaths ? entry.audioFilePaths.length : 0));
            result.debugLog.push("Is multi-sound: " + entry.isMulti);
            result.debugLog.push("Asset folder path: " + (entry.assetFolderPath || "NONE"));

            // Store asset folder path for later use
            var assetFolderPath = entry.assetFolderPath || "";

            // Import and assign audio files
            if (entry.audioFilePaths && entry.audioFilePaths.length > 0) {
                // Add group track to event
                var groupTrack = newEvent.addGroupTrack();
                result.debugLog.push("GroupTrack created: " + (groupTrack ? "YES" : "NO"));

                if (!groupTrack) {
                    throw new Error("Failed to create group track");
                }

                result.debugLog.push(dumpObjectStructure(groupTrack, "GroupTrack Structure", 1));

                // Assign bus to group track's mixer group
                if (bus && groupTrack.mixerGroup) {
                    groupTrack.mixerGroup.output = bus;
                    result.debugLog.push("Bus assigned to GroupTrack: " + bus.name);
                }

                // Import audio files and create sounds
                // Note: Python has already copied files to Assets folder
                if (entry.isMulti && entry.audioFilePaths.length > 1) {
                    result.debugLog.push("Creating MultiSound with " + entry.audioFilePaths.length + " files");

                    // Import first audio file
                    var firstAudioPath = normalizePath(entry.audioFilePaths[0]);
                    result.debugLog.push("Importing first asset from: " + firstAudioPath);
                    var firstAsset = studio.project.importAudioFile(firstAudioPath);

                    if (!firstAsset) {
                        throw new Error("Failed to import first audio file: " + firstAudioPath);
                    }
                    result.debugLog.push("First asset imported: " + firstAsset.assetPath);

                    // Create MultiSound using addSound() which properly integrates it
                    var multiSound = groupTrack.addSound(newEvent.timeline, "MultiSound", 0, firstAsset.length);
                    result.debugLog.push("MultiSound created via addSound: " + (multiSound ? "YES" : "NO"));

                    // Import remaining audio files and add as SingleSounds (skip first file)
                    var soundsAdded = 1; // First one was added by addSound
                    var maxLength = firstAsset.length;

                    for (var j = 1; j < entry.audioFilePaths.length; j++) {
                        var audioPath = normalizePath(entry.audioFilePaths[j]);
                        result.debugLog.push("  Importing audio " + (j + 1) + ": " + audioPath);

                        var asset = studio.project.importAudioFile(audioPath);
                        result.debugLog.push("    Import: " + (asset ? "OK" : "FAILED"));

                        if (asset) {
                            result.debugLog.push("    Asset assetPath: " + asset.assetPath);

                            // Track longest audio file for MultiSound length
                            if (asset.length > maxLength) {
                                maxLength = asset.length;
                            }

                            // Create SingleSound and add to MultiSound
                            var singleSound = studio.project.create("SingleSound");
                            singleSound.relationships.audioFile.add(asset);
                            multiSound.relationships.sounds.add(singleSound);
                            soundsAdded++;
                            result.debugLog.push("    SingleSound added to MultiSound");
                        }
                    }

                    multiSound.length = maxLength;
                    result.debugLog.push("MultiSound final sounds count: " + soundsAdded + ", length: " + maxLength);
                } else if (entry.audioFilePaths && entry.audioFilePaths.length === 1) {
                    result.debugLog.push("Creating SingleSound");

                    // Single audio file -> SingleSound
                    var audioPath = normalizePath(entry.audioFilePaths[0]);
                    result.debugLog.push("Importing audio from: " + audioPath);

                    var asset = studio.project.importAudioFile(audioPath);
                    result.debugLog.push("Asset imported: " + (asset ? "YES" : "NO"));

                    if (asset) {
                        result.debugLog.push("Asset assetPath: " + asset.assetPath);

                        // Create SingleSound using addSound() which properly integrates it
                        var singleSound = groupTrack.addSound(newEvent.timeline, "SingleSound", 0, asset.length);
                        singleSound.relationships.audioFile.add(asset);
                        result.debugLog.push("SingleSound created via addSound and linked to audio");
                    }
                }

                result.debugLog.push(dumpObjectStructure(newEvent, "Final Event Structure", 1));
            }

            result.imported += 1;
            result.debugLog.push("SUCCESS: Event imported");

        } catch (error) {
            result.failed += 1;
            result.messages.push(entry.newEventName + ": " + error.toString());
            result.debugLog.push("FAILED: " + error.toString());
        }
    }

    result.debugLog.push("\n=== IMPORT SESSION END ===");
    result.debugLog.push("Imported: " + result.imported + " | Failed: " + result.failed);

    // Save project
    try {
        studio.project.save();
    } catch (saveError) {
        result.messages.push("Failed to save project: " + saveError.toString());
    }

    return result;
}

// Entry point
function run() {
    if (!studio.arguments || studio.arguments.length === 0) {
        studio.system.message("ERROR: No JSON path provided to MocoImportFromJson.js");
        return;
    }

    var jsonPath = normalizePath(studio.arguments[0]);
    var payload = null;

    try {
        payload = JSON.parse(readTextFile(jsonPath));
    } catch (error) {
        studio.system.message("ERROR: Failed to read import JSON: " + error.toString());
        return;
    }

    var result = importEventsFromJson(payload);

    // Add skipped events to messages
    if (payload.skippedEvents && payload.skippedEvents.length) {
        for (var i = 0; i < payload.skippedEvents.length; i++) {
            var skipped = payload.skippedEvents[i];
            result.messages.push('Skipped: ' + skipped[0] + ' - ' + skipped[1]);
        }
    }

    // Write result file
    if (payload.resultPath) {
        try {
            writeTextFile(
                normalizePath(payload.resultPath),
                JSON.stringify(result, null, 2)
            );
        } catch (error) {
            studio.system.message("ERROR: Failed to write result file: " + error.toString());
        }
    }

    // Write debug log to separate file
    if (payload.resultPath) {
        try {
            var debugPath = normalizePath(payload.resultPath).replace(".json", "_debug.txt");
            writeTextFile(debugPath, result.debugLog.join("\n"));
        } catch (error) {
            studio.system.message("ERROR: Failed to write debug file: " + error.toString());
        }
    }

    // Print summary
    studio.system.message(
        "Moco Import Complete: " + result.imported + " imported, " + result.failed + " failed"
    );

    if (result.messages.length > 0) {
        studio.system.message("Messages: " + result.messages.join("; "));
    }
}

run();
