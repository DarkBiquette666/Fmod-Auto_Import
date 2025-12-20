"""
Preset Reference Resolver Module
Handles smart UUID resolution for FMOD project references (folders, banks, buses, assets).
"""

from typing import Optional, Tuple


class PresetResolver:
    """
    Helper class for resolving FMOD references when loading presets.

    Implements 3-step resolution strategy:
    1. Try UUID match (exact match in current project)
    2. Try path/name match (find by path even if UUID changed)
    3. Create missing resource using stored path/name

    This allows presets to work across different FMOD projects by:
    - Using UUIDs when they match (most reliable)
    - Falling back to paths when UUIDs differ
    - Auto-creating missing resources to avoid user errors
    """

    def __init__(self, project):
        """
        Initialize resolver with FMOD project instance.

        Args:
            project: FMODProject instance with loaded XML data
        """
        self.project = project

    # ==================== FOLDER RESOLUTION ====================

    def resolve_folder_reference(self, ref: dict) -> Optional[str]:
        """
        Resolve folder reference (UUID + path).

        3-step resolution:
        1. Try UUID match
        2. Try path match (different UUID)
        3. Create hierarchy if missing

        Args:
            ref: Dict with 'id' and 'path' keys

        Returns:
            Folder UUID or None if project not loaded
        """
        if not self.project:
            return None

        folder_id = ref.get('id', '')
        folder_path = ref.get('path', '')

        # Step 1: Try UUID match
        if folder_id and folder_id in self.project.event_folders:
            return folder_id

        # Step 2: Try path match
        if folder_path:
            existing_id = self.find_folder_by_path(folder_path)
            if existing_id:
                return existing_id

            # Step 3: Create hierarchy
            try:
                new_id = self.create_folder_hierarchy(folder_path)
                return new_id
            except Exception as e:
                print(f"Failed to create folder hierarchy '{folder_path}': {e}")
                return None

        return None

    def find_folder_by_path(self, path: str) -> Optional[str]:
        """
        Search event_folders for matching path.

        Args:
            path: Folder path (e.g., "Events/Enemies/Mechaflora")

        Returns:
            Folder UUID if found, None otherwise
        """
        if not self.project or not path:
            return None

        # Build paths for all folders and search for match
        for folder_id in self.project.event_folders:
            folder_path = self.get_folder_path(folder_id)
            if folder_path == path:
                return folder_id

        return None

    def create_folder_hierarchy(self, full_path: str) -> str:
        """
        Create nested folder structure.

        Example: "Events/Enemies/Mechaflora" creates:
          - Events/ (if missing)
          - Events/Enemies/ (if missing)
          - Events/Enemies/Mechaflora/

        Args:
            full_path: Full folder path with / separators

        Returns:
            UUID of final (deepest) folder
        """
        if not self.project:
            raise ValueError("No project loaded")

        parts = full_path.split('/')
        parts = [p for p in parts if p]  # Remove empty parts

        master_id = self.project.workspace.get('masterEventFolder')
        current_parent = master_id

        for part in parts:
            # Find child with this name
            child_id = None
            for folder_id, folder_data in self.project.event_folders.items():
                if (folder_data.get('parent') == current_parent and
                    folder_data.get('name') == part):
                    child_id = folder_id
                    break

            # Create if not found
            if not child_id:
                child_id = self.project.create_event_folder(part, current_parent)
                print(f"Created folder: {part}")

            current_parent = child_id

        return current_parent

    # ==================== BANK RESOLUTION ====================

    def resolve_bank_reference(self, ref: dict) -> Optional[str]:
        """
        Resolve bank reference (try UUID → name match → create).

        Args:
            ref: Dict with 'id', 'name', 'parent_id', 'parent_name' keys

        Returns:
            Bank UUID or None if project not loaded
        """
        if not self.project:
            return None

        bank_id = ref.get('id', '')
        bank_name = ref.get('name', '')

        # Step 1: Try UUID match
        if bank_id and bank_id in self.project.banks:
            return bank_id

        # Step 2: Try name match
        if bank_name:
            for bid, bdata in self.project.banks.items():
                if bdata.get('name') == bank_name:
                    return bid

            # Step 3: Create bank
            try:
                parent_id = ref.get('parent_id', '')
                new_id = self.project.create_bank(bank_name, parent_id or None)
                print(f"Created bank: {bank_name}")
                return new_id
            except Exception as e:
                print(f"Failed to create bank '{bank_name}': {e}")
                return None

        return None

    # ==================== BUS RESOLUTION ====================

    def resolve_bus_reference(self, ref: dict) -> Optional[str]:
        """
        Resolve bus reference (try UUID → path match → create hierarchy).

        Args:
            ref: Dict with 'id' and 'path' keys

        Returns:
            Bus UUID or None if project not loaded
        """
        if not self.project:
            return None

        bus_id = ref.get('id', '')
        bus_path = ref.get('path', '')

        # Step 1: Try UUID match
        if bus_id and bus_id in self.project.buses:
            return bus_id

        # Step 2: Try path match
        if bus_path:
            for bid in self.project.buses:
                if self.get_bus_path(bid) == bus_path:
                    return bid

            # Step 3: Create bus hierarchy (simplified - just create leaf bus)
            try:
                parts = bus_path.split('/')
                bus_name = parts[-1] if parts else bus_path
                master_bus_id = self.project._get_master_bus_id()
                new_id = self.project.create_bus(bus_name, master_bus_id)
                print(f"Created bus: {bus_name}")
                return new_id
            except Exception as e:
                print(f"Failed to create bus '{bus_path}': {e}")
                return None

        return None

    # ==================== ASSET FOLDER RESOLUTION ====================

    def resolve_asset_folder_reference(self, ref: dict) -> Optional[str]:
        """
        Resolve asset folder reference (try UUID → path match → create).

        Args:
            ref: Dict with 'id' and 'path' keys

        Returns:
            Asset folder UUID or None if project not loaded
        """
        if not self.project:
            return None

        asset_id = ref.get('id', '')
        asset_path = ref.get('path', '')

        # Step 1: Try UUID match
        if asset_id and asset_id in self.project.asset_folders:
            return asset_id

        # Step 2: Try path match
        if asset_path:
            for aid, adata in self.project.asset_folders.items():
                if adata.get('path') == asset_path:
                    return aid

            # Step 3: Create asset folder (simplified - single level)
            try:
                # Extract parent path and folder name
                parts = asset_path.rstrip('/').split('/')
                folder_name = parts[-1] if parts else ''
                parent_path = '/'.join(parts[:-1]) + '/' if len(parts) > 1 else ''

                new_id = self.project.create_asset_folder(folder_name, parent_path)
                print(f"Created asset folder: {folder_name}")
                return new_id
            except Exception as e:
                print(f"Failed to create asset folder '{asset_path}': {e}")
                return None

        return None

    # ==================== PATH BUILDING HELPERS ====================

    def get_folder_path(self, folder_id: str) -> str:
        """
        Build full path from folder ID.

        Traverses parent hierarchy to build path like "Events/Enemies/Mechaflora".
        Checks both committed (event_folders) and pending (_pending_event_folders).

        Args:
            folder_id: Folder UUID

        Returns:
            Full path string
        """
        if not self.project or not folder_id:
            return ""

        # Merge committed and pending folders
        all_folders = {**self.project.event_folders}
        if hasattr(self.project, '_pending_event_folders'):
            all_folders.update(self.project._pending_event_folders)

        # Build path from folder chain
        path_parts = []
        current_id = folder_id
        master_id = self.project.workspace.get('masterEventFolder')

        while current_id and current_id in all_folders and current_id != master_id:
            folder_data = all_folders[current_id]
            path_parts.insert(0, folder_data.get('name', ''))
            current_id = folder_data.get('parent')

        return '/'.join(path_parts)

    def get_bus_path(self, bus_id: str) -> str:
        """
        Build full path from bus ID.

        Traverses parent hierarchy to build path like "bus:/SFX/Enemies".

        Args:
            bus_id: Bus UUID

        Returns:
            Full path string with "bus:/" prefix
        """
        if not self.project or not bus_id:
            return ""

        path_parts = []
        current_id = bus_id
        master_bus_id = self.project._get_master_bus_id()

        while current_id and current_id in self.project.buses:
            bus_data = self.project.buses[current_id]
            bus_name = bus_data.get('name', '')

            # Stop at master bus
            if current_id == master_bus_id:
                break

            path_parts.insert(0, bus_name)
            current_id = bus_data.get('parent')

        return "bus:/" + '/'.join(path_parts)

    def get_bank_name_and_parent(self, bank_id: str) -> Tuple[str, str]:
        """
        Get bank name and parent ID.

        Args:
            bank_id: Bank UUID

        Returns:
            Tuple of (bank_name, parent_bank_id)
        """
        if not self.project or not bank_id or bank_id not in self.project.banks:
            return ("", "")

        bank_data = self.project.banks[bank_id]
        bank_name = bank_data.get('name', '')
        parent_id = bank_data.get('parent', '')

        return (bank_name, parent_id)
