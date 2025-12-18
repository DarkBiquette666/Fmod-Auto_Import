"""
Naming Pattern Module
Handles pattern-based parsing and building of event names.
"""

import os
import re
from typing import List, Dict, Optional, Tuple


def normalize_for_comparison(s: str) -> str:
    """
    Normalize a string for comparison.

    Removes underscores, spaces, and converts to lowercase.
    This allows matching between different naming conventions:
    - "Strong_Repair" -> "strongrepair"
    - "StrongRepair" -> "strongrepair"

    Args:
        s: String to normalize

    Returns:
        Normalized string
    """
    return s.replace('_', '').replace(' ', '').lower()


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

    def parse_asset_flexible(self, asset_name: str, user_values: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Parse an asset filename with flexible feature matching.

        Instead of requiring an exact feature match, this method:
        1. Extracts the feature from the filename (without validating it)
        2. Validates that it matches the user's feature when normalized

        This allows matching between different naming conventions:
        - User enters: "StrongRepair"
        - File has: "Mechaflora_Strong_Repair_Attack_01.wav"
        - Both normalize to "strongrepair" -> Match!

        Args:
            asset_name: Asset filename (with or without extension)
            user_values: Dict with 'prefix' and 'feature' values from user input

        Returns:
            Dict of extracted components or None if no match
        """
        # Build regex without user_values for feature (let it capture anything)
        flexible_values = {k: v for k, v in user_values.items() if k != 'feature'}

        # Parse with flexible regex (only validates prefix, extracts feature)
        result = self.parse_asset(asset_name, flexible_values)
        if not result:
            return None

        # Validate feature matches when normalized
        file_feature = result.get('feature', '')
        user_feature = user_values.get('feature', '')

        if normalize_for_comparison(file_feature) == normalize_for_comparison(user_feature):
            return result

        return None

    def extract_action_generic(self, name: str, prefix: str, feature: str) -> Optional[str]:
        """
        Extract action from a name by removing known prefix and feature.

        GENERIC - no hardcoded action names. Works by:
        1. Removing the known prefix
        2. Finding where the known feature ends (normalized comparison)
        3. Everything remaining is the action

        Args:
            name: Full name (file or template)
            prefix: Known prefix value
            feature: Known feature value

        Returns:
            Extracted action or None

        Examples:
            name="Mechaflora_Strong_Repair_Stun_Loop_01", prefix="Mechaflora", feature="StrongRepair"
            -> "Stun_Loop"

            name="PrefixFeatureNameStunLoop", prefix="Prefix", feature="FeatureName"
            -> "StunLoop"
        """
        # Strip extension if present
        if '.' in name:
            name = os.path.splitext(name)[0]

        # Strip iterator suffix
        name = self._strip_iterator(name)

        name_lower = name.lower()
        prefix_lower = prefix.lower()
        feature_normalized = normalize_for_comparison(feature)

        # Remove prefix (with or without separator)
        if name_lower.startswith(prefix_lower + '_'):
            remaining = name[len(prefix) + 1:]  # +1 for separator
        elif name_lower.startswith(prefix_lower + '-'):
            remaining = name[len(prefix) + 1:]  # +1 for separator
        elif name_lower.startswith(prefix_lower):
            remaining = name[len(prefix):]
        else:
            return None

        if not remaining:
            return None

        # Strategy 1: Try with separators (file pattern: Strong_Repair_Stun_Loop)
        parts = remaining.replace('-', '_').replace(' ', '_').split('_')
        parts = [p for p in parts if p]  # Remove empty parts

        if parts:
            # Try to find where feature ends and action begins
            for i in range(1, len(parts) + 1):
                candidate_feature = '_'.join(parts[:i])
                if normalize_for_comparison(candidate_feature) == feature_normalized:
                    # Found feature boundary! Action is what remains
                    action_parts = parts[i:]
                    if action_parts:
                        return '_'.join(action_parts)  # Preserve original separators
                    break

        # Strategy 2: Try without separators (CamelCase: FeatureNameStunLoop)
        remaining_normalized = normalize_for_comparison(remaining)
        if remaining_normalized.startswith(feature_normalized):
            # Feature found at start of remaining - action is what follows
            # Need to find the boundary in the original string

            # Count characters consumed by feature in normalized form
            feature_len = len(feature_normalized)

            # Find where action starts in original 'remaining' string
            # by tracking normalized character consumption
            norm_pos = 0
            orig_pos = 0

            while norm_pos < feature_len and orig_pos < len(remaining):
                char = remaining[orig_pos]
                # Skip separators (they're removed in normalization)
                if char in '_- ':
                    orig_pos += 1
                    continue
                norm_pos += 1
                orig_pos += 1

            # Action is everything after the feature
            action = remaining[orig_pos:].lstrip('_- ')
            if action:
                return action

        return None

    def parse_asset_generic(self, asset_name: str, user_values: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Parse asset using generic action extraction (no hardcoded actions).

        Works by:
        1. Removing known prefix
        2. Finding feature boundary (normalized comparison)
        3. What remains = action

        Args:
            asset_name: Asset filename (with or without extension)
            user_values: Dict with 'prefix' and 'feature' values from user input

        Returns:
            Dict of extracted components or None if no match
        """
        prefix = user_values.get('prefix', '')
        feature = user_values.get('feature', '')

        action = self.extract_action_generic(asset_name, prefix, feature)
        if not action:
            return None

        return {
            'prefix': prefix,
            'feature': feature,  # Use user's feature for event building
            'action': action
        }

    def parse_asset_fuzzy(self, asset_name: str, user_values: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Parse asset using generic action extraction.

        This is now an alias for parse_asset_generic() for backward compatibility.

        Args:
            asset_name: Asset filename (with or without extension)
            user_values: Dict with 'prefix' and 'feature' values from user input

        Returns:
            Dict of extracted components or None if no match
        """
        return self.parse_asset_generic(asset_name, user_values)

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

        Looks for common action keywords and captures any suffix (A, B, C, 1, 2, etc.)

        Args:
            name: Name to extract action from (e.g., "PrefixCharacterNameAlert")

        Returns:
            Extracted action with suffix or None if no action found

        Examples:
            "MechafloraStrongRepairIdleA" -> "IdleA"
            "Mechaflora_Strong_Repair_Idle_A" -> "Idle_A"
            "Mechaflora_Strong_Repair_Attack_1" -> "Attack_1"
            "PrefixFeatureNameAlert" -> "Alert"
        """
        # Common action keywords to look for (case-insensitive)
        # Only base actions - suffixes will be captured separately
        common_actions = [
            # Multi-word actions (must come first)
            'StunLoop', 'StunEnd', 'VFXHeal', 'StunRecover',
            # Basic actions
            'Alert', 'Ambush', 'Attack', 'Idle', 'Walk', 'Run', 'Jump', 'Die', 'Death',
            'Hit', 'Damage', 'Heal', 'Cast', 'Shoot', 'Fire', 'Reload',
            'Open', 'Close', 'Start', 'Stop', 'Loop', 'End', 'Stun',
            'Spawn', 'Despawn', 'Appear', 'Disappear',
            'Victory', 'Defeat', 'Win', 'Lose',
            'Footstep', 'Land', 'Fall', 'Slide',
            'Swing', 'Block', 'Parry', 'Dodge',
            'Pickup', 'Drop', 'Use', 'Equip',
            'Charge', 'Release', 'Hold',
            'Enter', 'Exit', 'Transition', 'Recover', 'VFX'
        ]

        # Normalize the name for matching
        name_lower = name.lower()

        # Try to find action keywords
        for base_action in common_actions:
            action_lower = base_action.lower()

            # Find the position of the action in the name
            pos = name_lower.rfind(action_lower)
            if pos == -1:
                continue

            # Get what comes after the base action
            action_end = pos + len(action_lower)
            remaining = name[action_end:]

            # Check if this is a valid action position
            # Valid positions:
            # 1. Start of string
            # 2. After underscore separator
            # 3. CamelCase boundary (lowercase before, uppercase action start)
            if pos > 0:
                char_before = name[pos - 1]
                action_first_char = name[pos]

                # Allow underscore separator
                if char_before == '_':
                    pass  # Valid
                # Allow CamelCase boundary (e.g., "NameAlert" -> "Alert")
                elif char_before.islower() and action_first_char.isupper():
                    pass  # Valid CamelCase boundary
                # Otherwise, action is in the middle of a word - skip
                elif char_before.isalnum():
                    continue

            # Capture suffix pattern: _A, _B, _1, _2, A, B, 1, 2, etc.
            # But not if followed by more letters (like "Idle" in "IdleAnimation")
            suffix_match = re.match(r'^([_]?[A-Za-z0-9])(?:[_]|$|\.)', remaining)
            if suffix_match:
                # Has a suffix (letter or number)
                suffix = suffix_match.group(1)
                # Preserve original case from the name
                original_action = name[pos:action_end]
                return original_action + suffix
            elif remaining == '' or remaining.startswith('_') or remaining.startswith('.'):
                # No suffix, just the base action
                return name[pos:action_end]

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
