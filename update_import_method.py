#!/usr/bin/env python
"""Script to update import_assets method to use FMOD JavaScript API"""

import re

# Read the file
with open('moco_auto_import.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add subprocess import if not present
if 'import subprocess' not in content:
    content = content.replace('import uuid', 'import uuid\nimport subprocess\nimport tempfile')

# New import method that uses JavaScript API
new_method = '''    def import_assets(self):
        """Import assets using FMOD JavaScript API instead of XML manipulation"""
        try:
            # 1. Validate inputs
            if not self.project:
                messagebox.showerror("Error", "No FMOD Studio project is loaded.")
                return

            if not hasattr(self, 'selected_asset_id') or not self.selected_asset_id:
                messagebox.showerror("Error", "Please select an audio asset folder.")
                return

            asset_folder = self.project.asset_folders[self.selected_asset_id]['path']

            # 2. Get event-audio mapping from preview tree
            event_audio_map = {}
            for item in self.preview_tree.get_children():
                event_name = self.preview_tree.item(item, "text")
                audio_files = []
                for child in self.preview_tree.get_children(item):
                    audio_filename = self.preview_tree.item(child, "text")
                    audio_filename = audio_filename.strip().lstrip("→").strip()
                    audio_files.append(audio_filename)
                event_audio_map[event_name] = audio_files

            if not event_audio_map:
                messagebox.showerror("Error", "No events in preview tree to import.")
                return

            # 3. Validate other required fields
            media_path = self.media_entry.get()
            if not media_path or not os.path.exists(media_path):
                messagebox.showerror("Error", "Please specify a valid media path.")
                return

            prefix = self._get_entry_value(self.prefix_entry, 'e.g. Cat')
            character = self._get_entry_value(self.character_entry, 'e.g. Infiltrator')
            if not prefix or not character:
                messagebox.showerror("Error", "Please specify prefix and character name.")
                return

            if not self.selected_template_id or not self.selected_dest_id or not self.selected_bank_id or not self.selected_bus_id:
                messagebox.showerror("Error", "Please select template folder, destination folder, bank, and bus.")
                return

            # 4. Load templates and create mapping
            template_events = self.project.get_events_in_folder(self.selected_template_id)
            if not template_events:
                messagebox.showerror("Error", "No template events found.")
                return

            template_map = {}
            for tmpl in template_events:
                parts = tmpl['name'].split('_', 2)
                if len(parts) >= 3:
                    expected_name = f"{prefix}_{character}_{parts[2]}"
                    template_map[expected_name] = tmpl

            # 5. Build import data for JavaScript
            import_data = {
                "events": [],
                "resultPath": str(Path(self.project.project_path).parent / "import_result.json")
            }

            bank_name = self.project.banks[self.selected_bank_id]['name']
            bus_name = self.project.buses[self.selected_bus_id]['name']
            template_folder_path = self._get_folder_path(self.selected_template_id)
            dest_folder_path = self._get_folder_path(self.selected_dest_id)

            for event_name, audio_filenames in event_audio_map.items():
                template_event = template_map.get(event_name)
                if not template_event:
                    continue

                audio_paths = [os.path.join(media_path, f) for f in audio_filenames]
                if not all(os.path.exists(p) for p in audio_paths):
                    continue

                import_data["events"].append({
                    "templateEventPath": template_folder_path + "/" + template_event['name'],
                    "newEventName": event_name,
                    "destFolderPath": dest_folder_path,
                    "audioFilePaths": audio_paths,
                    "assetFolderPath": asset_folder,
                    "bankName": bank_name,
                    "busName": bus_name
                })

            # 6. Write JSON and show instructions
            import json
            temp_dir = tempfile.gettempdir()
            json_path = os.path.join(temp_dir, "moco_import_data.json")

            with open(json_path, 'w') as f:
                json.dump(import_data, f, indent=2)

            messagebox.showinfo("Import Ready",
                f"Import data prepared!\\n\\n" +
                f"In FMOD Studio:\\n" +
                f"1. Go to Scripts > Reload\\n" +
                f"2. Go to Scripts > Moco Auto Import > Import from JSON\\n" +
                f"3. Select: {json_path}\\n\\n" +
                f"{len(import_data['events'])} events ready to import.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to prepare import:\\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _get_folder_path(self, folder_id):
        """Get full path of an event folder"""
        parts = []
        current_id = folder_id

        while current_id and current_id in self.project.event_folders:
            folder = self.project.event_folders[current_id]
            parts.insert(0, folder['name'])
            current_id = folder.get('parent')

        return '/'.join(parts)
'''

# Find the old import_assets method and replace it
pattern = r'    def import_assets\(self\):.*?(?=\n    def [a-z_]+\(self)'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content[:match.start()] + new_method + '\n' + content[match.end():]
    print("Found and replaced import_assets method")
else:
    print("Could not find import_assets method pattern")

# Write back
with open('moco_auto_import.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Update complete!")
