"""
A module for sorting and renaming files based on configurable rules.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from pathvalidate import sanitize_filename, sanitize_filepath


class FileSorter:
    """
    A file sorting engine that applies configurable rules to determine
    new file paths and names based on file metadata.
    """

    def __init__(self, config_path: str, base_output_dir: str):
        """
        Initializes the FileSorter with a configuration file.

        Args:
            config_path: Path to the YAML configuration file
            base_output_dir: Base directory for all output paths
        """
        self.templates = {}  # Initialize before loading config
        self.config = self._load_config(config_path)
        self.base_output_dir = os.path.abspath(base_output_dir)

    def _load_config(self, config_path: str) -> Dict:
        """Loads the YAML configuration file."""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # Store templates for later use
        self.templates = config.get("templates", {})
        
        # Convert simplified 'when' syntax to 'conditions' format
        if "rules" in config:
            for rule in config["rules"]:
                if "when" in rule and "conditions" not in rule:
                    rule["conditions"] = self._convert_when_to_conditions(rule["when"])
                    del rule["when"]
        
        return config
    
    def _convert_when_to_conditions(self, when: Dict) -> Dict:
        """
        Converts simplified 'when' syntax to full 'conditions' syntax.
        
        Examples:
            when: {field: "value"} -> equals condition
            when: {field: ["val1", "val2"]} -> OR condition
            when: {field1: "val1", field2: "val2"} -> AND conditions
        
        Args:
            when: Dictionary with simplified condition syntax
            
        Returns:
            Dictionary with full conditions syntax
        """
        rules = []
        
        for field, value in when.items():
            if isinstance(value, list):
                # Array of values = OR condition for this field
                for v in value:
                    rules.append({
                        "field": field,
                        "operator": "equals",
                        "value": v
                    })
            else:
                # Simple value = equals condition
                rules.append({
                    "field": field,
                    "operator": "equals",
                    "value": value
                })
        
        # Determine logic based on structure
        if len(rules) == 1:
            # Single rule, use AND as default
            return {
                "logic": "AND",
                "rules": rules
            }
        else:
            # Check if all rules are for the same field (OR case)
            fields = [r["field"] for r in rules]
            if len(set(fields)) == 1:
                # All same field = OR
                return {
                    "logic": "OR",
                    "rules": rules
                }
            else:
                # Different fields = AND
                return {
                    "logic": "AND",
                    "rules": rules
                }

    def _evaluate_condition(self, condition: Dict, metadata: Dict) -> bool:
        """
        Evaluates a single condition.

        Args:
            condition: Dictionary with field, operator, value or nested rule
            metadata: Dictionary with file metadata

        Returns:
            True if the condition is met, otherwise False
        """
        # Nested rule (with logic and rules)
        if "logic" in condition:
            return self._evaluate_conditions(condition, metadata)

        # Simple condition
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if field not in metadata:
            return False

        file_value = metadata[field]

        if operator == "equals":
            return file_value == value
        elif operator == "not_equals":
            return file_value != value
        elif operator == "contains":
            return value in str(file_value)
        elif operator == "starts_with":
            return str(file_value).startswith(value)
        elif operator == "ends_with":
            return str(file_value).endswith(value)
        elif operator == "regex":
            try:
                return bool(re.search(value, str(file_value)))
            except re.error:
                return False

        return False

    def _evaluate_conditions(self, conditions: Dict, metadata: Dict) -> bool:
        """
        Evaluates multiple conditions with AND/OR logic.

        Args:
            conditions: Dictionary with 'logic' (AND/OR) and 'rules' (list of conditions)
            metadata: Dictionary with file metadata

        Returns:
            True if all conditions are met (for AND) or at least one (for OR)
        """
        logic = conditions.get("logic", "AND").upper()
        rules = conditions.get("rules", [])

        # Empty rule list = always True (for fallback rules)
        if not rules:
            return True

        if logic == "AND":
            return all(self._evaluate_condition(rule, metadata) for rule in rules)
        elif logic == "OR":
            return any(self._evaluate_condition(rule, metadata) for rule in rules)

        return False

    def _replace_placeholders(
        self, template: str, metadata: Dict, original_filename: str
    ) -> str:
        """
        Replaces placeholders in the template with actual values.
        Also resolves template references (e.g., $template.name).
        Supports fallback syntax: {field1|field2|'default'}

        Args:
            template: String with placeholders like {metadata_key} or $template.template_name
                     Can include fallbacks: {field1|field2|'default'}
            metadata: Dictionary with file metadata
            original_filename: Original filename

        Returns:
            String with replaced placeholders
        """
        result = template

        # First, resolve template references ($template.name)
        import re
        template_pattern = r'\$template\.(\w+)'
        matches = re.findall(template_pattern, result)
        for template_name in matches:
            if template_name in self.templates:
                template_value = self.templates[template_name]
                result = result.replace(f"$template.{template_name}", template_value)
            else:
                # If template not found, leave it as is (or could raise an error)
                pass

        # Process placeholders with fallback support
        # Pattern matches {field1|field2|'default'} or {field}
        placeholder_pattern = r'\{([^}]+)\}'
        
        def replace_with_fallback(match):
            placeholder_content = match.group(1)
            
            # Check if this is a special placeholder
            if placeholder_content == "original":
                return Path(original_filename).stem
            elif placeholder_content == "ext":
                return Path(original_filename).suffix
            
            # Split by pipe to get fallback options
            options = [opt.strip() for opt in placeholder_content.split('|')]
            
            for option in options:
                # Check if option is a quoted literal (string)
                if (option.startswith("'") and option.endswith("'")) or \
                   (option.startswith('"') and option.endswith('"')):
                    # Return the literal value without quotes
                    return option[1:-1]
                
                # Check if option is a metadata field
                if option in metadata and option != "filename":
                    value = metadata[option]
                    # Return value if it's not None or empty string
                    if value is not None and str(value).strip():
                        return str(value)
            
            # If no fallback worked, return empty string or original placeholder
            return ""
        
        result = re.sub(placeholder_pattern, replace_with_fallback, result)

        return result

    def _find_all_matching_rules(self, metadata: Dict) -> List[Dict]:
        """
        Finds ALL matching rules for the given file metadata.

        Args:
            metadata: Dictionary with file metadata

        Returns:
            List of all matching rules
        """
        matching_rules = []
        for rule in self.config.get("rules", []):
            conditions = rule.get("conditions", {})
            if self._evaluate_conditions(conditions, metadata):
                matching_rules.append(rule)

        return matching_rules

    def get_new_location(
        self, original_filepath: str, **metadata
    ) -> Tuple[str, str, Optional[str]]:
        """
        Determines a new path and filename based on file metadata.

        Args:
            original_filepath: Full path to the original file
            **metadata: File metadata with arbitrary names (e.g., DocumentType='Invoice', Customer='A', etc.)

        Returns:
            Tuple of (absolute_new_path, new_filename, rule_name)
            The new_path is relative to base_output_dir (set in __init__)

        Raises:
            FileNotFoundError: If the original file doesn't exist

        Example:
            sorter = FileSorter('config.yaml', base_output_dir='/archive')
            path, name, rule = sorter.get_new_location(
                'C:/files/document.pdf',
                DocumentType='Invoice',
                Customer='Customer_A',
                Quarter='Q1',
                Project='Project_X',
                Status='Paid'
            )
            # path will be: /archive/Customers/Customer_A/Invoices/Q1
        """
        # Check if file exists
        if not os.path.exists(original_filepath):
            raise FileNotFoundError(f"File not found: {original_filepath}")

        # Extract filename from path
        original_filename = os.path.basename(original_filepath)

        # Prepare metadata
        file_metadata = {"filename": original_filename}
        file_metadata.update(metadata)

        # Find ALL matching rules
        matching_rules = self._find_all_matching_rules(file_metadata)

        if len(matching_rules) == 0:
            raise ValueError(
                f"No matching rule found for file '{original_filename}' with metadata: {metadata}"
            )

        if len(matching_rules) > 1:
            rule_names = [rule.get("name", "Unnamed") for rule in matching_rules]
            raise ValueError(
                f"Multiple rules matched for file '{original_filename}': {', '.join(rule_names)}. "
                f"Each file must match exactly one rule. Metadata: {metadata}"
            )

        # Exactly one rule matched
        rule = matching_rules[0]
        rule_name = rule.get("name", "Unnamed")
        path_template = rule.get("path", ".")
        filename_template = rule.get("filename", "{original}")

        relative_path = self._replace_placeholders(
            path_template, file_metadata, original_filename
        )
        new_filename = self._replace_placeholders(
            filename_template, file_metadata, original_filename
        )

        # Combine base output dir with relative path from config
        absolute_path = os.path.join(self.base_output_dir, relative_path)

        return (
            sanitize_filepath(absolute_path, replacement_text="_"),
            sanitize_filename(new_filename, replacement_text="_"),
            rule_name,
        )

    def move_file(
        self,
        original_filepath: str,
        new_path: str,
        new_filename: str,
        create_dirs: bool = True,
        overwrite: bool = False,
    ) -> str:
        """
        Moves/renames the file to the new location.

        Args:
            original_filepath: Full path to the original file
            new_path: Directory path where the file should be moved
            new_filename: New filename for the file
            create_dirs: If True, creates directories if they don't exist
            overwrite: If True, overwrites existing files at destination

        Returns:
            Full path to the new file location

        Raises:
            FileNotFoundError: If original file doesn't exist
            FileExistsError: If destination exists and overwrite=False

        Example:
            sorter = FileSorter('config.yaml', 'output_directory')
            # Option 1: Specify path and name manually
            new_location = sorter.move_file(
                'C:/files/document.pdf',
                'Archive/2024',
                'invoice_2024.pdf'
            )

            # Option 2: Get path from rules first
            path, name, rule = sorter.get_new_location(
                'C:/files/document.pdf',
                DocumentType='Invoice', Customer='CustomerA', Quarter='Q1'
            )
            new_location = sorter.move_file(
                'C:/files/document.pdf',
                path,
                name
            )
        """
        # Check if original file exists
        if not os.path.exists(original_filepath):
            raise FileNotFoundError(f"Original file not found: {original_filepath}")

        # Create full destination path
        destination_dir = new_path
        if create_dirs and not os.path.exists(destination_dir):
            os.makedirs(destination_dir, exist_ok=True)

        destination_filepath = os.path.join(destination_dir, new_filename)

        # Check if destination already exists
        if os.path.exists(destination_filepath) and not overwrite:
            raise FileExistsError(
                f"Destination file already exists: {destination_filepath}"
            )

        # Move the file
        shutil.move(original_filepath, destination_filepath)

        return destination_filepath
