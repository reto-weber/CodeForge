"""
Eiffel Class Name Mapping Manager
Handles loading and applying class name mappings from XML configuration.
"""

import xml.etree.ElementTree as ET
from typing import Dict
from pathlib import Path


class EiffelMappingManager:
    """Manages Eiffel class name mappings from XML configuration."""

    def __init__(self):
        self.mappings: Dict[str, str] = {}
        # Fix the path to be relative to the current file
        current_dir = Path(__file__).parent
        self.config_path = current_dir / "config" / "eiffel_mappings.xml"
        self.load_mappings()

    def load_mappings(self) -> None:
        """Load class name mappings from XML configuration file."""
        try:
            if not self.config_path.exists():
                print(f"Warning: Eiffel mappings file not found at {self.config_path}")
                return

            tree = ET.parse(self.config_path)
            root = tree.getroot()

            # Clear existing mappings
            self.mappings.clear()

            # Load mappings from XML
            for mapping in root.findall('mapping'):
                old_name = mapping.get('old_name')
                new_name = mapping.get('new_name')

                if old_name and new_name:
                    # Store mappings in uppercase for case-insensitive lookup
                    self.mappings[old_name.upper()] = new_name.upper()
                    print(f"Loaded mapping: {old_name} -> {new_name}")

            print(f"Loaded {len(self.mappings)} Eiffel class name mappings")

        except ET.ParseError as e:
            print(f"Error parsing Eiffel mappings XML: {e}")
        except Exception as e:
            print(f"Error loading Eiffel mappings: {e}")

    def apply_mapping(self, class_name: str) -> str:
        """
        Apply mapping to a class name if it exists.

        Args:
            class_name: The original class name

        Returns:
            The mapped class name if a mapping exists, otherwise the original name
        """
        if not class_name:
            return class_name

        # Convert to uppercase for lookup
        upper_name = class_name.upper()

        # Check if mapping exists
        if upper_name in self.mappings:
            mapped_name = self.mappings[upper_name]
            print(f"Applied mapping: {class_name} -> {mapped_name}")
            return mapped_name

        # Return original name if no mapping found
        return class_name

    def get_all_mappings(self) -> Dict[str, str]:
        """Get all loaded mappings."""
        return self.mappings.copy()

    def reload_mappings(self) -> None:
        """Reload mappings from the XML file."""
        print("Reloading Eiffel class name mappings...")
        self.load_mappings()

    def add_mapping(self, old_name: str, new_name: str) -> None:
        """
        Add a new mapping programmatically.
        Note: This only affects the current session, not the XML file.
        """
        if old_name and new_name:
            self.mappings[old_name.upper()] = new_name.upper()
            print(f"Added runtime mapping: {old_name} -> {new_name}")


# Global instance for easy access
_mapping_manager = None


def get_mapping_manager() -> EiffelMappingManager:
    """Get the global mapping manager instance."""
    global _mapping_manager
    if _mapping_manager is None:
        _mapping_manager = EiffelMappingManager()
    return _mapping_manager
