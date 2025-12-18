"""
Naming Pattern Module
Handles pattern-based parsing and building of event names.
"""

import os
import re
from typing import List, Dict, Optional, Tuple


class NamingPattern:
    """
    Parse and build event names according to a user-defined tag pattern.

    Supported tags:
        $prefix     - Project prefix (user input)
        $feature    - Feature name (user input)
        $action     - Action/suffix (auto-extracted)
        $variation  - Variation letter A, B, C... (auto-extracted, optional)

    Iterator numbers (_01, _02, etc.) at the end of asset names are automatically
    stripped and not part of the pattern - they're used to group multiple audio
    files under the same event.

    Example:
        pattern = NamingPattern("$prefix_$feature_$action_$variation")

        # Parse an asset name (strips iterator)
        result = pattern.parse_asset("Mechaflora_Strong_Repair_Attack_A_01")
        # -> {'prefix': 'Mechaflora', 'feature': 'Strong_Repair',
        #    'action': 'Attack', 'variation': 'A'}

        # Build an event name
        event_name = pattern.build(prefix='Mechaflora', feature='Strong_Repair',
                                   action='Attack', variation='A')
        # -> "Mechaflora_Strong_Repair_Attack_A"
    """

    # Supported tags and their regex patterns
    TAG_PATTERNS = {
        '$prefix': r'(?P<prefix>[^_]+)',
        '$feature': r'(?P<feature>[^_]+(?:_[^_]+)*?)',  # Greedy for multi-part features
        '$action': r'(?P<action>[^_]+(?:_[^_]+)*?)',  # Allow underscores in action (e.g., Attack_Heavy)
        '$variation': r'(?P<variation>[A-Z])',
    }

    # Tags that are provided by user input (not extracted from filename)
    USER_INPUT_TAGS = {'$prefix', '$feature'}

    # Tags that are optional (pattern still matches if missing)
    OPTIONAL_TAGS = {'$variation'}

    # Pattern to detect iterator at end of filename (_01, _02, _1, _2, etc.)
    ITERATOR_PATTERN = re.compile(r'[_]?\d+$')

    def __init__(self, pattern: str):
        """
        Initialize with a pattern string.

        Args:
            pattern: Pattern string like "$prefix_$feature_$action_$variation"
        """
        self.pattern = pattern
        self.separator = '_'  # Default separator
        self.tags = self._extract_tags()
        self._regex_cache = {}

    def _extract_tags(self) -> List[str]:
        """Extract tags from pattern in order of appearance."""
        # Use [a-zA-Z] instead of \w to avoid capturing underscores
        tag_regex = re.compile(r'\$[a-zA-Z]+')
        return tag_regex.findall(self.pattern)

    def _build_regex(self, user_values: Dict[str, str] = None) -> re.Pattern:
        """
        Build regex pattern for parsing names.

        Args:
            user_values: Dict of user-provided values like {'prefix': 'Mechaflora', 'feature': 'Strong_Repair'}
                        These are used as literal matches instead of capture groups.
        """
        # Create cache key
        cache_key = tuple(sorted(user_values.items())) if user_values else ()
        if cache_key in self._regex_cache:
            return self._regex_cache[cache_key]

        regex_pattern = self.pattern

        for tag in self.TAG_PATTERNS:
            if tag in regex_pattern:
                tag_name = tag[1:]  # Remove $ prefix

                # If user provided a value for this tag, use literal match
                if user_values and tag_name in user_values:
                    # Escape special regex chars and use literal value
                    literal = re.escape(user_values[tag_name])
                    regex_pattern = regex_pattern.replace(tag, f'(?P<{tag_name}>{literal})')
                else:
                    # Use capture pattern
                    if tag in self.OPTIONAL_TAGS:
                        # Make optional tags... optional
                        regex_pattern = regex_pattern.replace(tag, f'(?:{self.TAG_PATTERNS[tag]})?')
                    else:
                        regex_pattern = regex_pattern.replace(tag, self.TAG_PATTERNS[tag])

        # Handle separator between optional tag and end (e.g., "_$variation" at end)
        # If variation is optional, the preceding underscore should also be optional
        for tag in self.OPTIONAL_TAGS:
            tag_name = tag[1:]
            # Pattern like "_(?P<variation>...)?" should become "(?:_(?P<variation>...))?"
            regex_pattern = re.sub(
                rf'_\(\?:(\(\?P<{tag_name}>[^)]+\))\)\?',
                rf'(?:_\1)?',
                regex_pattern
            )

        compiled = re.compile(f'^{regex_pattern}$')
        self._regex_cache[cache_key] = compiled
        return compiled

    def _strip_iterator(self, name: str) -> str:
        """
        Strip iterator suffix from asset name.

        Examples:
            "Attack_A_01" -> "Attack_A"
            "Attack_01" -> "Attack"
            "Attack_1" -> "Attack"
            "Attack" -> "Attack" (unchanged)
        """
        return self.ITERATOR_PATTERN.sub('', name)

    def parse_asset(self, asset_name: str, user_values: Dict[str, str] = None) -> Optional[Dict[str, str]]:
        """
        Parse an asset filename and extract components.

        Automatically strips iterator suffix (_01, _02, etc.) before parsing.

        Args:
            asset_name: Asset filename without extension (e.g., "Mechaflora_Strong_Repair_Attack_A_01")
            user_values: Optional dict of known values to match literally

        Returns:
            Dict of extracted components or None if no match
        """
        # Strip file extension if present
        if '.' in asset_name:
            asset_name = os.path.splitext(asset_name)[0]

        # Strip iterator suffix
        name_without_iterator = self._strip_iterator(asset_name)

        # Build and apply regex
        regex = self._build_regex(user_values)
        match = regex.match(name_without_iterator)

        if match:
            result = {k: v for k, v in match.groupdict().items() if v is not None}
            return result

        return None

    def build(self, **components) -> str:
        """
        Build an event name from components.

        Args:
            **components: Tag values like prefix='Mechaflora', feature='Strong_Repair', action='Attack'

        Returns:
            Built event name string
        """
        name = self.pattern

        for tag in self.tags:
            tag_name = tag[1:]  # Remove $ prefix
            value = components.get(tag_name, '')

            if value:
                name = name.replace(tag, value)
            elif tag in self.OPTIONAL_TAGS:
                # Remove optional tag and its preceding separator
                name = name.replace(f'_{tag}', '')
                name = name.replace(tag, '')
            else:
                # Required tag missing - leave as placeholder for debugging
                name = name.replace(tag, f'[{tag_name}]')

        return name

    def extract_action_fuzzy(self, name: str) -> Optional[str]:
        """
        Try to extract action from a name using fuzzy matching.

        This is useful for template names that don't follow the exact pattern
        (e.g., "PrefixCharacterNameAlert" without underscores).

        Looks for common action keywords at the end of the name.

        Args:
            name: Name to extract action from (e.g., "PrefixCharacterNameAlert")

        Returns:
            Extracted action or None if no action found
        """
        # Common action keywords to look for (case-insensitive)
        common_actions = [
            'Alert', 'Attack', 'Idle', 'Walk', 'Run', 'Jump', 'Die', 'Death',
            'Hit', 'Damage', 'Heal', 'Cast', 'Shoot', 'Fire', 'Reload',
            'Open', 'Close', 'Start', 'Stop', 'Loop', 'End',
            'Spawn', 'Despawn', 'Appear', 'Disappear',
            'Victory', 'Defeat', 'Win', 'Lose',
            'Footstep', 'Land', 'Fall', 'Slide',
            'Swing', 'Block', 'Parry', 'Dodge',
            'Pickup', 'Drop', 'Use', 'Equip',
            'Charge', 'Release', 'Hold',
            'Enter', 'Exit', 'Transition'
        ]

        # Normalize the name for matching
        name_lower = name.lower()

        # Try to find action keywords
        for action in common_actions:
            action_lower = action.lower()

            # Check if action appears at the end
            if name_lower.endswith(action_lower):
                return action

            # Check if action appears followed by variation (e.g., "AlertA")
            if re.search(rf'{action_lower}[a-z]?$', name_lower):
                return action

            # Check with underscore separator
            if re.search(rf'_{action_lower}(?:_[a-z])?$', name_lower):
                return action

        return None

    def get_event_name(self, asset_name: str, user_values: Dict[str, str]) -> Optional[str]:
        """
        Extract the event name from an asset filename.

        This combines parsing and building: it parses the asset to extract
        auto-detected components (action, variation), then builds the event
        name using user-provided values for prefix/feature.

        Args:
            asset_name: Asset filename (with or without extension)
            user_values: Dict with 'prefix' and 'feature' values from user input

        Returns:
            Event name string or None if asset doesn't match pattern
        """
        parsed = self.parse_asset(asset_name, user_values)

        if parsed is None:
            return None

        # Merge user values with parsed values (user values take precedence)
        components = {**parsed, **user_values}

        return self.build(**components)

    def validate(self) -> Tuple[bool, str]:
        """
        Validate the pattern.

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        # Check for at least one tag
        if not self.tags:
            errors.append("Pattern must contain at least one tag (e.g., $prefix, $action)")

        # Check for unknown tags
        known_tags = set(self.TAG_PATTERNS.keys())
        for tag in self.tags:
            if tag not in known_tags:
                errors.append(f"Unknown tag: {tag}")

        # Check for required tags
        if '$action' not in self.tags:
            errors.append("Pattern should contain $action tag to identify events")

        # Check pattern structure
        if self.pattern.startswith('_') or self.pattern.endswith('_'):
            errors.append("Pattern should not start or end with separator")

        if errors:
            return False, '\n'.join(errors)

        return True, ""

    def get_required_user_inputs(self) -> List[str]:
        """
        Get list of tags that require user input.

        Returns:
            List of tag names (without $) that need user-provided values
        """
        return [tag[1:] for tag in self.tags if tag in self.USER_INPUT_TAGS]

    def get_auto_extracted_tags(self) -> List[str]:
        """
        Get list of tags that are auto-extracted from filenames.

        Returns:
            List of tag names (without $) that are extracted automatically
        """
        return [tag[1:] for tag in self.tags if tag not in self.USER_INPUT_TAGS]

    def get_pattern_preview(self, user_values: Dict[str, str] = None) -> str:
        """
        Generate a preview of what the pattern will produce.

        Args:
            user_values: Optional dict of user-provided values

        Returns:
            Preview string showing the pattern with placeholders
        """
        preview = self.pattern

        if user_values:
            for key, value in user_values.items():
                preview = preview.replace(f'${key}', value)

        # Replace remaining tags with bracketed placeholders
        for tag in self.tags:
            tag_name = tag[1:]
            if tag in self.OPTIONAL_TAGS:
                preview = preview.replace(tag, f'[{tag_name}?]')
            else:
                preview = preview.replace(tag, f'[{tag_name}]')

        return preview

    def __repr__(self) -> str:
        return f"NamingPattern('{self.pattern}')"
