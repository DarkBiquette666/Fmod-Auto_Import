"""
Audio Matcher Module
Handles intelligent matching between audio files and event templates.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .naming import NamingPattern


class AudioMatcher:
    """Handles intelligent matching between audio files and event templates"""

    @staticmethod
    def normalize_string(s: str) -> str:
        """Normalize a string for fuzzy matching by removing separators and converting to lowercase

        Handles: underscores, dashes, spaces, and converts to lowercase
        Examples:
            "Strong Repair" -> "strongrepair"
            "Strong_Repair" -> "strongrepair"
            "StrongRepair" -> "strongrepair"
        """
        return s.replace('_', '').replace('-', '').replace(' ', '').lower()

    @staticmethod
    def get_feature_variants(feature: str) -> List[str]:
        """Generate all possible variants of a feature name for matching

        Args:
            feature: Feature name (e.g., "Strong Repair", "Strong_Repair", "StrongRepair")

        Returns:
            List of variants to try for matching, ordered by preference
        """
        variants = []

        # Normalize the feature name first (remove all separators)
        normalized = AudioMatcher.normalize_string(feature)

        # Original as-is
        if feature not in variants:
            variants.append(feature)

        # With underscores instead of spaces
        underscore_version = feature.replace(' ', '_')
        if underscore_version not in variants:
            variants.append(underscore_version)

        # With spaces instead of underscores
        space_version = feature.replace('_', ' ')
        if space_version not in variants:
            variants.append(space_version)

        # No separators (concatenated)
        no_sep_version = feature.replace('_', '').replace(' ', '')
        if no_sep_version not in variants:
            variants.append(no_sep_version)

        # Split by any separator and rejoin with underscore
        parts = feature.replace('_', ' ').replace('-', ' ').split()
        if len(parts) > 1:
            rejoined = '_'.join(parts)
            if rejoined not in variants:
                variants.append(rejoined)

        return variants

    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """Calculate similarity score between two strings (0.0 to 1.0)"""
        # Exact match (case sensitive)
        if str1 == str2:
            return 1.0

        # Normalized comparison (no underscores, lowercase)
        norm1 = AudioMatcher.normalize_string(str1)
        norm2 = AudioMatcher.normalize_string(str2)

        if norm1 == norm2:
            return 0.95  # High confidence for normalized match (e.g., "Attack_A" == "AttackA")

        # Check if one contains the other
        if norm1 in norm2:
            # norm1 is contained in norm2
            # Special case: if norm2 is just norm1 + single character, likely a variant (e.g., "attack" vs "attacka")
            if len(norm2) - len(norm1) <= 1:
                return 0.92  # High confidence for single character difference
            return min(len(norm1), len(norm2)) / max(len(norm1), len(norm2)) * 0.9
        elif norm2 in norm1:
            # norm2 is contained in norm1
            if len(norm1) - len(norm2) <= 1:
                return 0.92  # High confidence for single character difference
            return min(len(norm1), len(norm2)) / max(len(norm1), len(norm2)) * 0.9

        # Levenshtein-like simple ratio
        max_len = max(len(norm1), len(norm2))
        if max_len == 0:
            return 0.0

        # Simple character overlap ratio
        set1 = set(norm1)
        set2 = set(norm2)
        overlap = len(set1 & set2)
        total = len(set1 | set2)

        return (overlap / total) * 0.7 if total > 0 else 0.0  # 70% max for character overlap

    @staticmethod
    def extract_suffix_from_basename(basename: str, prefix: str, feature: str) -> Optional[str]:
        """Extract the event suffix from an audio file basename

        Tries multiple strategies to extract the suffix:
        1. Try all feature variants (spaces, underscores, concatenated)
        2. Normalized matching (handles "StrongRepair" vs "Strong_Repair" vs "Strong Repair")
        3. Partial feature match for multi-word features

        Args:
            basename: Audio file name without extension (e.g., "Mechaflora_StrongRepair_Attack_01")
            prefix: Event prefix (e.g., "Mechaflora")
            feature: Feature name - can have spaces, underscores, or be concatenated
                     (e.g., "Strong Repair", "Strong_Repair", "StrongRepair")

        Returns the suffix or None if no match found
        """
        # Get all possible variants of the feature name
        feature_variants = AudioMatcher.get_feature_variants(feature)

        # Strategy 1: Try exact match with each variant
        for variant in feature_variants:
            exact_pattern = f"{prefix}_{variant}_"
            if basename.startswith(exact_pattern):
                suffix_part = basename[len(exact_pattern):]
                return AudioMatcher._clean_suffix(suffix_part)

        # Strategy 2: Try with prefix only, then analyze what comes after
        prefix_pattern = f"{prefix}_"
        if basename.startswith(prefix_pattern):
            after_prefix = basename[len(prefix_pattern):]

            # Try each variant
            for variant in feature_variants:
                # Split variant into parts (handles both "Strong_Repair" and "Strong Repair")
                variant_parts = variant.replace(' ', '_').split('_')

                # Try to match all variant parts
                variant_pattern = '_'.join(variant_parts) + '_'
                if after_prefix.startswith(variant_pattern):
                    suffix_part = after_prefix[len(variant_pattern):]
                    return AudioMatcher._clean_suffix(suffix_part)

                # Try to match partial variant parts
                for i in range(len(variant_parts), 0, -1):
                    partial_variant = '_'.join(variant_parts[:i]) + '_'
                    if after_prefix.startswith(partial_variant):
                        suffix_part = after_prefix[len(partial_variant):]
                        return AudioMatcher._clean_suffix(suffix_part)

            # Strategy 3: Normalized matching (handles "StrongRepair" vs "Strong_Repair")
            # Try to find where the feature name ends in the filename using fuzzy matching
            norm_feature = AudioMatcher.normalize_string(feature)

            # Split the after_prefix into potential feature and suffix parts
            # Try different split points to find best match
            parts = after_prefix.split('_')
            for split_idx in range(1, len(parts)):
                potential_feature_part = '_'.join(parts[:split_idx])
                norm_potential = AudioMatcher.normalize_string(potential_feature_part)

                # Check if this matches the normalized feature name
                if norm_potential == norm_feature:
                    # Found a match! The rest is the suffix
                    suffix_part = '_'.join(parts[split_idx:])
                    return AudioMatcher._clean_suffix(suffix_part)

            # Strategy 4: Try matching concatenated feature directly in the after_prefix
            # For cases like "Mechaflora_StrongRepairAttack" where feature is "Strong Repair"
            concatenated_feature = feature.replace(' ', '').replace('_', '')
            if after_prefix.startswith(concatenated_feature):
                # Found concatenated feature, extract suffix
                suffix_start = len(concatenated_feature)
                if suffix_start < len(after_prefix):
                    remainder = after_prefix[suffix_start:]
                    # Check if remainder starts with underscore or capital letter
                    if remainder.startswith('_'):
                        suffix_part = remainder[1:]  # Remove leading underscore
                    elif remainder[0].isupper():
                        # CamelCase continuation - this is the suffix
                        suffix_part = remainder
                    else:
                        suffix_part = remainder
                    return AudioMatcher._clean_suffix(suffix_part)

        return None

    @staticmethod
    def _clean_suffix(suffix: str) -> str:
        """Clean suffix by removing trailing numbers (_01, _02, etc.) and file extensions"""
        # Remove file extension first
        suffix_no_ext = os.path.splitext(suffix)[0]

        # Remove trailing variation numbers (_01, _02, _A, _B, etc.)
        if '_' in suffix_no_ext:
            parts = suffix_no_ext.rsplit('_', 1)
            if parts[-1].isdigit() or parts[-1].upper() in ['A', 'B', 'C', 'D', 'E']:
                # Could be _01, _02 or _A, _B variation numbers
                return parts[0]
        return suffix_no_ext

    @staticmethod
    def collect_audio_files(directory: str) -> List[Dict]:
        """Collect all audio files from directory"""
        audio_extensions = {'.wav', '.mp3', '.ogg', '.flac', '.aif', '.aiff'}
        files = []

        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext in audio_extensions:
                    full_path = Path(root) / filename
                    base_name = Path(filename).stem

                    files.append({
                        'path': str(full_path),
                        'filename': filename,
                        'basename': base_name
                    })

        return files

    @staticmethod
    def build_event_name(prefix: str, feature: str, template_name: str) -> str:
        """Build event name from template"""
        # Extract suffix from template (last part after underscore)
        parts = template_name.split('_')
        suffix = parts[-1]
        # Normalize feature name (replace spaces with underscores)
        normalized_feature = feature.replace(' ', '_')
        return f"{prefix}_{normalized_feature}_{suffix}"

    @staticmethod
    def match_files_to_events(audio_files: List[Dict], prefix: str, feature: str,
                              expected_events: Optional[Dict[str, Dict]] = None) -> Dict[str, List[Dict]]:
        """Group audio files by their base names to create events with intelligent matching

        Args:
            audio_files: List of audio file dictionaries
            prefix: Event prefix (e.g., 'Mechaflora')
            feature: Feature name (e.g., 'Weak_Ranged')
            expected_events: Optional dict of expected event names to match against

        Returns:
            Dictionary mapping event names to their audio files with confidence scores
            Example: {'Mechaflora_Weak_Ranged_Attack': {'files': [file1, file2], 'confidence': 1.0}}
        """
        groups = {}

        # If we have expected events, try to match each file to an event
        if expected_events:
            matched_files = set()

            for file in audio_files:
                basename = file['basename']
                best_match = None
                best_score = 0.0
                best_suffix = None

                # Extract suffix from the file
                extracted_suffix = AudioMatcher.extract_suffix_from_basename(basename, prefix, feature)

                if extracted_suffix:
                    # Try to match against expected events
                    for event_name in expected_events.keys():
                        # Extract the suffix from the expected event name
                        # Expected format: Prefix_Feature_Suffix
                        # Need to remove Prefix_Feature_ to get the suffix

                        # Get all possible variants of the feature name
                        feature_variants = AudioMatcher.get_feature_variants(feature)
                        event_suffix = None

                        # Try exact pattern with each variant first
                        for variant in feature_variants:
                            exact_pattern = f"{prefix}_{variant}_"
                            if event_name.startswith(exact_pattern):
                                event_suffix = event_name[len(exact_pattern):]
                                break

                        if not event_suffix:
                            # Try partial feature matching
                            prefix_pattern = f"{prefix}_"
                            if event_name.startswith(prefix_pattern):
                                after_prefix = event_name[len(prefix_pattern):]

                                # Try each variant
                                for variant in feature_variants:
                                    # Split variant into parts
                                    variant_parts = variant.replace(' ', '_').split('_')
                                    for i in range(len(variant_parts), 0, -1):
                                        partial_variant = '_'.join(variant_parts[:i]) + '_'
                                        if after_prefix.startswith(partial_variant):
                                            event_suffix = after_prefix[len(partial_variant):]
                                            break
                                    if event_suffix:
                                        break

                                # If still no match, try normalized matching
                                if not event_suffix:
                                    norm_feature = AudioMatcher.normalize_string(feature)
                                    parts = after_prefix.split('_')

                                    # Try different split points
                                    for split_idx in range(1, len(parts)):
                                        potential_feature_part = '_'.join(parts[:split_idx])
                                        norm_potential = AudioMatcher.normalize_string(potential_feature_part)

                                        if norm_potential == norm_feature:
                                            event_suffix = '_'.join(parts[split_idx:])
                                            break

                        if event_suffix:
                            # Calculate similarity between suffixes
                            score = AudioMatcher.calculate_similarity(extracted_suffix, event_suffix)

                            if score > best_score and score >= 0.7:  # Minimum 70% confidence
                                best_score = score
                                best_match = event_name
                                best_suffix = event_suffix

                # If we found a good match, assign it
                if best_match:
                    if best_match not in groups:
                        groups[best_match] = {'files': [], 'confidence': best_score}
                    groups[best_match]['files'].append(file)
                    # Update confidence to the average if multiple files
                    if len(groups[best_match]['files']) > 1:
                        groups[best_match]['confidence'] = (groups[best_match]['confidence'] + best_score) / 2
                    matched_files.add(file['filename'])

        # Fallback to original logic for unmatched files (build event names from file names)
        for file in audio_files:
            if expected_events and file['filename'] in matched_files:
                continue  # Already matched

            basename = file['basename']
            extracted_suffix = AudioMatcher.extract_suffix_from_basename(basename, prefix, feature)

            if extracted_suffix:
                # Normalize feature name for event creation (replace spaces with underscores)
                normalized_feature = feature.replace(' ', '_')
                event_name = f"{prefix}_{normalized_feature}_{extracted_suffix}"

                if event_name not in groups:
                    groups[event_name] = {'files': [], 'confidence': 0.5}  # Lower confidence for auto-generated
                groups[event_name]['files'].append(file)

        return groups

    @staticmethod
    def match_files_with_pattern(audio_files: List[Dict],
                                  parse_pattern: 'NamingPattern',
                                  build_pattern: 'NamingPattern',
                                  user_values: Dict[str, str],
                                  expected_events: Optional[Dict[str, Dict]] = None) -> Tuple[Dict, List[Dict]]:
        """
        Group audio files by event name using NamingPatterns.

        This is a cleaner alternative to match_files_to_events that uses
        the user-defined naming patterns for parsing and building.

        Args:
            audio_files: List of audio file dictionaries with 'basename', 'filename', 'path'
            parse_pattern: NamingPattern for parsing asset filenames (e.g., $prefix_$feature_$action)
            build_pattern: NamingPattern for building event names (e.g., $prefix$feature$action)
            user_values: Dict with user-provided values like {'prefix': 'Mechaflora', 'feature': 'Strong_Repair'}
            expected_events: Optional dict of expected event names (from templates) to match against

        Returns:
            Tuple of:
            - groups: Dict mapping event names to {'files': [...], 'confidence': float, 'from_template': bool}
            - unmatched: List of files that couldn't be matched to the pattern
        """
        groups = {}
        unmatched = []

        # Helper function to normalize strings for fuzzy matching
        def normalize_for_matching(s: str) -> str:
            """Remove underscores, spaces, convert to lowercase for fuzzy comparison"""
            return s.replace('_', '').replace(' ', '').lower()

        # Store templates for generic matching
        # We'll match by checking if template name ends with the file's action (normalized)
        template_names = list(expected_events.keys()) if expected_events else []
        expected_normalized = {}  # For fuzzy matching by normalized event name

        if expected_events:
            for exp_name in expected_events.keys():
                # Store normalized version for fuzzy matching
                norm_name = normalize_for_matching(exp_name)
                expected_normalized[norm_name] = exp_name

        for file in audio_files:
            basename = file['basename']

            # Parse the asset file using fuzzy action extraction
            # This extracts action first (like "Alert"), then deduces feature as everything between prefix and action
            # Allows matching even if user enters "StrongRepair" but file has "Strong_Repair"
            parsed = parse_pattern.parse_asset_fuzzy(basename, user_values)

            if not parsed:
                unmatched.append(file)
                continue

            # Build event name using build_pattern (e.g., without underscores)
            event_name = build_pattern.build(**{**parsed, **user_values})

            # Check if this matches an expected event (from template)
            from_template = False
            confidence = 0.8  # Default confidence for pattern match
            matched_template_name = event_name  # Will be replaced if we find a template match

            if expected_events:
                # Try 1: Exact match with template
                if event_name in expected_events:
                    from_template = True
                    confidence = 1.0
                # Try 2: Fuzzy match by normalized string (StrongRepair = Strong_Repair)
                elif expected_normalized:
                    norm_event = normalize_for_matching(event_name)
                    if norm_event in expected_normalized:
                        matched_template_name = expected_normalized[norm_event]
                        from_template = True
                        confidence = 0.98  # High confidence for normalized match

            # Try 3: GENERIC matching - check if template ends with file's action (normalized)
            # This handles cases like:
            # - File action: "Stun_Loop" (normalized: "stunloop")
            # - Template: "PrefixFeatureNameStunLoop" (normalized ends with "stunloop")
            if not from_template and template_names and 'action' in parsed:
                file_action = parsed.get('action', '')
                file_action_normalized = normalize_for_matching(file_action)

                for template_name in template_names:
                    template_normalized = normalize_for_matching(template_name)
                    # Check if template ends with the file's action (normalized)
                    if template_normalized.endswith(file_action_normalized):
                        matched_template_name = template_name
                        from_template = True
                        confidence = 0.92  # Good confidence for suffix match
                        break

            # Add to groups (use matched_template_name if found, otherwise use constructed event_name)
            final_event_name = matched_template_name if from_template else event_name

            if final_event_name not in groups:
                groups[final_event_name] = {
                    'files': [],
                    'confidence': confidence,
                    'from_template': from_template
                }
            groups[final_event_name]['files'].append(file)

            # Update confidence (average for multiple files)
            if len(groups[final_event_name]['files']) > 1:
                current_conf = groups[final_event_name]['confidence']
                groups[final_event_name]['confidence'] = (current_conf + confidence) / 2

        return groups, unmatched
