def import_assets(self):
    """Import assets using FMOD JavaScript API via auto-execute script"""
    try:
        # 1. Validate inputs
        if not self.project:
            messagebox.showerror("Error", "No FMOD Studio project is loaded.")
            return

        asset_id = getattr(self, "selected_asset_id", None)
        if not asset_id:
            messagebox.showerror("Error", "Please select an audio asset folder.")
            return

        asset_info = self.project.asset_folders.get(asset_id)
        if not asset_info:
            messagebox.showerror("Error", "Selected audio asset folder could not be found.")
            return

        asset_folder = asset_info["path"] or ""
        if asset_folder and not asset_folder.endswith(("/", "\\\\")):
            asset_folder += "/"

        media_path_input = self.media_entry.get()
        media_root = Path(media_path_input) if media_path_input else None

        # 2. Get event-audio mapping from preview tree
        event_audio_map = {}
        for item in self.preview_tree.get_children():
            event_name = self.preview_tree.item(item, "text")
            audio_files = []
            for child in self.preview_tree.get_children(item):
                audio_label = self.preview_tree.item(child, "text") or ""
                if "→" in audio_label:
                    audio_label = audio_label.split("→", 1)[1]
                audio_label = audio_label.strip()

                values = self.preview_tree.item(child, "values") or []
                audio_path = values[0] if len(values) > 0 and values[0] else None

                if not audio_path:
                    if media_root:
                        audio_path = str((media_root / audio_label).resolve())
                    else:
                        audio_path = audio_label

                audio_path = os.path.normpath(audio_path)
                audio_files.append((audio_label, audio_path))

            if audio_files:
                event_audio_map[event_name] = audio_files

        if not event_audio_map:
            messagebox.showerror("Error", "No events in the preview tree to import.")
            return

        # 3. Validate other fields
        media_path = media_path_input
        if not media_path or not os.path.exists(media_path):
            messagebox.showerror("Error", "Please specify a valid media path.")
            return

        prefix = self._get_entry_value(self.prefix_entry, "e.g. Cat")
        character = self._get_entry_value(self.character_entry, "e.g. Infiltrator")
        if not prefix or not character:
            messagebox.showerror("Error", "Please specify prefix and character name.")
            return

        template_folder_id = getattr(self, "selected_template_id", None)
        dest_folder_id = getattr(self, "selected_dest_id", None)
        bank_id = getattr(self, "selected_bank_id", None)
        bus_id = getattr(self, "selected_bus_id", None)

        if not all([template_folder_id, dest_folder_id, bank_id, bus_id]):
            messagebox.showerror("Error", "Please select template folder, destination folder, bank, and bus.")
            return

        # 4. Load templates
        template_events = self.project.get_events_in_folder(template_folder_id)
        if not template_events:
            messagebox.showerror("Error", "No template events found.")
            return

        template_map = {}
        for tmpl in template_events:
            parts = tmpl["name"].split("_", 2)
            if len(parts) >= 3:
                expected_name = f"{prefix}_{character}_{parts[2]}"
                template_map[expected_name] = tmpl

        # 5. Build import data
        import_events = []
        template_folder_path = self._get_folder_path(template_folder_id)
        dest_folder_path = self._get_folder_path(dest_folder_id)
        bank_name = self.project.banks[bank_id]["name"]
        bus_name = self.project.buses[bus_id]["name"]

        for event_name, audio_entries in event_audio_map.items():
            template_event = template_map.get(event_name)
            if not template_event:
                continue

            audio_paths = []
            for label, path_str in audio_entries:
                resolved_path = Path(path_str)
                if not resolved_path.is_absolute():
                    resolved_path = Path(media_path) / resolved_path
                if not resolved_path.exists():
                    continue
                audio_paths.append(resolved_path.resolve().as_posix())

            if not audio_paths:
                continue

            import_events.append({
                "templateEventPath": f"{template_folder_path}/{template_event['name']}",
                "newEventName": event_name,
                "destFolderPath": dest_folder_path,
                "audioFilePaths": audio_paths,
                "assetFolderPath": asset_folder,
                "bankName": bank_name,
                "busName": bus_name,
                "isMulti": len(audio_paths) > 1,
            })

        if not import_events:
            messagebox.showerror("Error", "No events ready for import.")
            return

        # 6. Create JSON and auto-exec script
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        json_path = temp_dir / f"moco_import_data_{uuid.uuid4().hex}.json"
        result_path = temp_dir / f"moco_import_result_{uuid.uuid4().hex}.json"

        import_payload = {
            "projectPath": str(self.project.project_path),
            "resultPath": str(result_path),
            "bankName": bank_name,
            "busName": bus_name,
            "defaultDestFolderPath": dest_folder_path,
            "events": import_events,
        }

        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(import_payload, fh, indent=2)

        # 7. Create auto-execute script
        scripts_folder = Path(r"C:/Users/antho/AppData/Local/FMOD Studio/Scripts")
        auto_exec_script = scripts_folder / "_MocoAutoImport_Execute.js"
        script_path = Path(__file__).resolve().parent / "Script" / "MocoImportFromJson.js"

        js_code = f"""// Auto-generated by Moco Auto Import

// Helper functions
function readTextFile(path) {{
    var file = studio.system.getFile(path);
    file.open(studio.system.openMode.ReadOnly);
    var size = file.size();
    var text = file.readText(size);
    file.close();
    return text;
}}

function writeTextFile(path, text) {{
    var file = studio.system.getFile(path);
    file.open(studio.system.openMode.WriteOnly);
    file.writeText(text);
    file.close();
}}

(function() {{
    try {{
        var jsonPath = "{str(json_path).replace(chr(92), '/')}";
        var importScript = "{str(script_path).replace(chr(92), '/')}";

        // Load and execute the import script
        var importScriptCode = readTextFile(importScript);
        // Remove the run() call at the end before eval
        var lastRunIndex = importScriptCode.lastIndexOf('run();');
        if (lastRunIndex !== -1) {{
            importScriptCode = importScriptCode.substring(0, lastRunIndex);
        }}
        eval(importScriptCode);

        // Read JSON data
        var payload = JSON.parse(readTextFile(jsonPath));

        var result = importEventsFromJson(payload);

        var msg = "Moco Import: " + result.imported + " imported, " + result.failed + " failed";
        studio.system.message(msg);

        if (payload.resultPath) {{
            var rf = studio.system.getFile(payload.resultPath);
            rf.open(studio.system.openMode.WriteOnly);
            rf.writeText(JSON.stringify(result, null, 2));
            rf.close();
        }}

        // Auto-delete not supported, script will remain until manually deleted
    }} catch (e) {{
        studio.system.message("ERROR: " + e.toString());
    }}
}})();
"""

        with open(auto_exec_script, 'w', encoding='utf-8') as f:
            f.write(js_code)

        # 8. Show instructions
        num_events = len(import_events)
        msg = (f"Import script created for {num_events} event(s).\\n\\n"
               "In FMOD Studio, go to:\\n"
               "  Scripts > Reload\\n\\n"
               "The import will execute automatically!")
        messagebox.showinfo("Import Ready!", msg)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to prepare import: {str(e)}")
        import traceback
        traceback.print_exc()
