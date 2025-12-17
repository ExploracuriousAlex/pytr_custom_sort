"""
Comprehensive unit tests for the rule_based_sorter module.
Tests all functions, rules, operators, and edge cases.
"""

import os
import shutil
import tempfile

import pytest
import yaml

from rule_based_sort.rule_based_sorter import FileSorter

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_dir():
    """Creates a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_file(temp_dir):
    """Creates a sample file for testing."""
    file_path = os.path.join(temp_dir, "test_document.pdf")
    with open(file_path, "w") as f:
        f.write("test content")
    return file_path


@pytest.fixture
def basic_config(temp_dir):
    """Creates a basic YAML config file."""
    config = {
        "templates": {
            "standard": "{date_time_str} - {event_title}.pdf",
            "with_fallback": "{date_time_str} - {event_title|document_title|'Unknown'}.pdf",
        },
        "rules": [
            {
                "name": "Test Rule",
                "when": {"postbox_type": "TEST"},
                "path": "Test",
                "filename": "{event_title}.pdf",
            }
        ],
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def output_dir(temp_dir):
    """Creates an output directory."""
    output_path = os.path.join(temp_dir, "output")
    os.makedirs(output_path, exist_ok=True)
    return output_path


# ============================================================================
# TEST: INITIALIZATION
# ============================================================================


def test_initialization(basic_config, output_dir):
    """Test that FileSorter initializes correctly."""
    sorter = FileSorter(basic_config, output_dir)
    assert sorter is not None
    assert sorter.config is not None
    assert sorter.templates is not None
    assert sorter.base_output_dir == os.path.abspath(output_dir)


def test_load_config_with_templates(basic_config, output_dir):
    """Test that templates are loaded correctly."""
    sorter = FileSorter(basic_config, output_dir)
    assert "standard" in sorter.templates
    assert "with_fallback" in sorter.templates
    assert sorter.templates["standard"] == "{date_time_str} - {event_title}.pdf"


# ============================================================================
# TEST: WHEN SYNTAX CONVERSION
# ============================================================================


def test_convert_when_single_value(basic_config, output_dir):
    """Test conversion of when syntax with single value."""
    sorter = FileSorter(basic_config, output_dir)
    when = {"postbox_type": "INCOME"}
    conditions = sorter._convert_when_to_conditions(when)

    assert conditions["logic"] == "AND"
    assert len(conditions["rules"]) == 1
    assert conditions["rules"][0]["field"] == "postbox_type"
    assert conditions["rules"][0]["operator"] == "equals"
    assert conditions["rules"][0]["value"] == "INCOME"


def test_convert_when_array_values(basic_config, output_dir):
    """Test conversion of when syntax with array values (OR logic)."""
    sorter = FileSorter(basic_config, output_dir)
    when = {"postbox_type": ["INCOME", "DIVIDEND"]}
    conditions = sorter._convert_when_to_conditions(when)

    assert conditions["logic"] == "OR"
    assert len(conditions["rules"]) == 2
    assert conditions["rules"][0]["value"] == "INCOME"
    assert conditions["rules"][1]["value"] == "DIVIDEND"


def test_convert_when_multiple_fields(basic_config, output_dir):
    """Test conversion of when syntax with multiple fields (AND logic)."""
    sorter = FileSorter(basic_config, output_dir)
    when = {"postbox_type": "INCOME", "event_title": "Interest"}
    conditions = sorter._convert_when_to_conditions(when)

    assert conditions["logic"] == "AND"
    assert len(conditions["rules"]) == 2


# ============================================================================
# TEST: CONDITION OPERATORS
# ============================================================================


def test_operator_equals(basic_config, output_dir):
    """Test equals operator."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "type", "operator": "equals", "value": "INCOME"}

    assert sorter._evaluate_condition(condition, {"type": "INCOME"}) is True
    assert sorter._evaluate_condition(condition, {"type": "EXPENSE"}) is False


def test_operator_not_equals(basic_config, output_dir):
    """Test not_equals operator."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "type", "operator": "not_equals", "value": "INCOME"}

    assert sorter._evaluate_condition(condition, {"type": "EXPENSE"}) is True
    assert sorter._evaluate_condition(condition, {"type": "INCOME"}) is False


def test_operator_contains(basic_config, output_dir):
    """Test contains operator."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "title", "operator": "contains", "value": "Dividend"}

    assert sorter._evaluate_condition(condition, {"title": "Apple Dividend"}) is True
    assert sorter._evaluate_condition(condition, {"title": "Interest Payment"}) is False


def test_operator_starts_with(basic_config, output_dir):
    """Test starts_with operator."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "title", "operator": "starts_with", "value": "Apple"}

    assert sorter._evaluate_condition(condition, {"title": "Apple Inc."}) is True
    assert sorter._evaluate_condition(condition, {"title": "Microsoft Corp."}) is False


def test_operator_ends_with(basic_config, output_dir):
    """Test ends_with operator."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "title", "operator": "ends_with", "value": "Inc."}

    assert sorter._evaluate_condition(condition, {"title": "Apple Inc."}) is True
    assert sorter._evaluate_condition(condition, {"title": "Microsoft Corp."}) is False


def test_operator_regex(basic_config, output_dir):
    """Test regex operator."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "title", "operator": "regex", "value": r"^[A-Z]"}

    assert sorter._evaluate_condition(condition, {"title": "Apple"}) is True
    assert sorter._evaluate_condition(condition, {"title": "apple"}) is False


def test_operator_regex_invalid(basic_config, output_dir):
    """Test regex operator with invalid pattern."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "title", "operator": "regex", "value": r"[invalid("}

    # Should return False on regex error
    assert sorter._evaluate_condition(condition, {"title": "test"}) is False


def test_condition_missing_field(basic_config, output_dir):
    """Test condition evaluation when field is missing."""
    sorter = FileSorter(basic_config, output_dir)
    condition = {"field": "missing_field", "operator": "equals", "value": "test"}

    assert sorter._evaluate_condition(condition, {"other_field": "value"}) is False


# ============================================================================
# TEST: CONDITIONS LOGIC (AND/OR)
# ============================================================================


def test_evaluate_conditions_and_all_true(basic_config, output_dir):
    """Test AND logic when all conditions are true."""
    sorter = FileSorter(basic_config, output_dir)
    conditions = {
        "logic": "AND",
        "rules": [
            {"field": "type", "operator": "equals", "value": "INCOME"},
            {"field": "status", "operator": "equals", "value": "PAID"},
        ],
    }
    metadata = {"type": "INCOME", "status": "PAID"}

    assert sorter._evaluate_conditions(conditions, metadata) is True


def test_evaluate_conditions_and_one_false(basic_config, output_dir):
    """Test AND logic when one condition is false."""
    sorter = FileSorter(basic_config, output_dir)
    conditions = {
        "logic": "AND",
        "rules": [
            {"field": "type", "operator": "equals", "value": "INCOME"},
            {"field": "status", "operator": "equals", "value": "PAID"},
        ],
    }
    metadata = {"type": "INCOME", "status": "PENDING"}

    assert sorter._evaluate_conditions(conditions, metadata) is False


def test_evaluate_conditions_or_one_true(basic_config, output_dir):
    """Test OR logic when at least one condition is true."""
    sorter = FileSorter(basic_config, output_dir)
    conditions = {
        "logic": "OR",
        "rules": [
            {"field": "type", "operator": "equals", "value": "INCOME"},
            {"field": "type", "operator": "equals", "value": "DIVIDEND"},
        ],
    }
    metadata = {"type": "DIVIDEND"}

    assert sorter._evaluate_conditions(conditions, metadata) is True


def test_evaluate_conditions_or_all_false(basic_config, output_dir):
    """Test OR logic when all conditions are false."""
    sorter = FileSorter(basic_config, output_dir)
    conditions = {
        "logic": "OR",
        "rules": [
            {"field": "type", "operator": "equals", "value": "INCOME"},
            {"field": "type", "operator": "equals", "value": "DIVIDEND"},
        ],
    }
    metadata = {"type": "EXPENSE"}

    assert sorter._evaluate_conditions(conditions, metadata) is False


def test_evaluate_conditions_empty_rules(basic_config, output_dir):
    """Test that empty rule list returns True."""
    sorter = FileSorter(basic_config, output_dir)
    conditions = {"logic": "AND", "rules": []}

    assert sorter._evaluate_conditions(conditions, {}) is True


# ============================================================================
# TEST: PLACEHOLDER REPLACEMENT
# ============================================================================


def test_replace_placeholders_simple(basic_config, output_dir):
    """Test simple placeholder replacement."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{date_time_str} - {event_title}.pdf"
    metadata = {"date_time_str": "2024-03-15", "event_title": "Apple"}

    result = sorter._replace_placeholders(template, metadata, "original.pdf")
    assert result == "2024-03-15 - Apple.pdf"


def test_replace_placeholders_special_original(basic_config, output_dir):
    """Test {original} placeholder."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{date_time_str} - {original}.pdf"
    metadata = {"date_time_str": "2024-03-15"}

    result = sorter._replace_placeholders(template, metadata, "document_123.pdf")
    assert result == "2024-03-15 - document_123.pdf"


def test_replace_placeholders_special_ext(basic_config, output_dir):
    """Test {ext} placeholder."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{date_time_str} - document{ext}"
    metadata = {"date_time_str": "2024-03-15"}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == "2024-03-15 - document.pdf"


def test_replace_placeholders_fallback_first_exists(basic_config, output_dir):
    """Test fallback placeholder when first option exists."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{event_title|document_title|'Unknown'}.pdf"
    metadata = {"event_title": "Apple", "document_title": "Document"}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == "Apple.pdf"


def test_replace_placeholders_fallback_second_exists(basic_config, output_dir):
    """Test fallback placeholder when first is missing, second exists."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{event_title|document_title|'Unknown'}.pdf"
    metadata = {"document_title": "Document"}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == "Document.pdf"


def test_replace_placeholders_fallback_literal(basic_config, output_dir):
    """Test fallback placeholder using literal default."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{event_title|document_title|'Unknown'}.pdf"
    metadata = {}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == "Unknown.pdf"


def test_replace_placeholders_fallback_empty_values(basic_config, output_dir):
    """Test fallback placeholder skips empty values."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{event_title|document_title|'Unknown'}.pdf"
    metadata = {"event_title": "", "document_title": "Document"}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == "Document.pdf"


def test_replace_placeholders_fallback_no_match(basic_config, output_dir):
    """Test fallback placeholder when no option matches."""
    sorter = FileSorter(basic_config, output_dir)
    template = "{event_title|document_title}.pdf"
    metadata = {}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == ".pdf"


def test_replace_placeholders_template_reference(basic_config, output_dir):
    """Test template reference resolution."""
    sorter = FileSorter(basic_config, output_dir)
    template = "$template.standard"
    metadata = {"date_time_str": "2024-03-15", "event_title": "Apple"}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == "2024-03-15 - Apple.pdf"


def test_replace_placeholders_template_with_fallback(basic_config, output_dir):
    """Test template reference that contains fallback syntax."""
    sorter = FileSorter(basic_config, output_dir)
    template = "$template.with_fallback"
    metadata = {"date_time_str": "2024-03-15", "document_title": "Document"}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    assert result == "2024-03-15 - Document.pdf"


def test_replace_placeholders_nonexistent_template(basic_config, output_dir):
    """Test template reference when template doesn't exist."""
    sorter = FileSorter(basic_config, output_dir)
    template = "$template.nonexistent"
    metadata = {}

    result = sorter._replace_placeholders(template, metadata, "file.pdf")
    # Should leave the reference as is
    assert result == "$template.nonexistent"


# ============================================================================
# TEST: RULE MATCHING
# ============================================================================


def test_find_matching_rules_single_match(temp_dir, output_dir):
    """Test finding a single matching rule."""
    config = {
        "rules": [
            {
                "name": "Rule 1",
                "conditions": {
                    "logic": "AND",
                    "rules": [
                        {"field": "type", "operator": "equals", "value": "INCOME"}
                    ],
                },
                "path": "Income",
                "filename": "{event_title}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    metadata = {"type": "INCOME"}

    matching = sorter._find_all_matching_rules(metadata)
    assert len(matching) == 1
    assert matching[0]["name"] == "Rule 1"


def test_find_matching_rules_no_match(temp_dir, output_dir):
    """Test finding no matching rules."""
    config = {
        "rules": [
            {
                "name": "Rule 1",
                "conditions": {
                    "logic": "AND",
                    "rules": [
                        {"field": "type", "operator": "equals", "value": "INCOME"}
                    ],
                },
                "path": "Income",
                "filename": "{event_title}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    metadata = {"type": "EXPENSE"}

    matching = sorter._find_all_matching_rules(metadata)
    assert len(matching) == 0


def test_find_matching_rules_multiple_matches(temp_dir, output_dir):
    """Test finding multiple matching rules."""
    config = {
        "rules": [
            {
                "name": "Rule 1",
                "conditions": {
                    "logic": "AND",
                    "rules": [
                        {"field": "type", "operator": "equals", "value": "INCOME"}
                    ],
                },
                "path": "Income",
                "filename": "{event_title}.pdf",
            },
            {
                "name": "Rule 2",
                "conditions": {
                    "logic": "AND",
                    "rules": [
                        {"field": "type", "operator": "equals", "value": "INCOME"}
                    ],
                },
                "path": "Income2",
                "filename": "{event_title}.pdf",
            },
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    metadata = {"type": "INCOME"}

    matching = sorter._find_all_matching_rules(metadata)
    assert len(matching) == 2


# ============================================================================
# TEST: GET_NEW_LOCATION
# ============================================================================


def test_get_new_location_basic(sample_file, basic_config, output_dir):
    """Test get_new_location with basic rule."""
    sorter = FileSorter(basic_config, output_dir)

    path, filename, rule_name = sorter.get_new_location(
        sample_file, postbox_type="TEST", event_title="Apple"
    )

    assert rule_name == "Test Rule"
    assert filename == "Apple.pdf"
    assert path.endswith("Test")


def test_get_new_location_file_not_found(basic_config, output_dir):
    """Test get_new_location with non-existent file."""
    sorter = FileSorter(basic_config, output_dir)

    with pytest.raises(FileNotFoundError):
        sorter.get_new_location(
            "nonexistent.pdf", postbox_type="TEST", event_title="Apple"
        )


def test_get_new_location_no_matching_rule(sample_file, basic_config, output_dir):
    """Test get_new_location when no rule matches."""
    sorter = FileSorter(basic_config, output_dir)

    with pytest.raises(ValueError, match="No matching rule found"):
        sorter.get_new_location(sample_file, postbox_type="NOMATCH")


def test_get_new_location_multiple_matching_rules(sample_file, temp_dir, output_dir):
    """Test get_new_location when multiple rules match."""
    config = {
        "rules": [
            {
                "name": "Rule 1",
                "when": {"type": "TEST"},
                "path": "Test1",
                "filename": "file1.pdf",
            },
            {
                "name": "Rule 2",
                "when": {"type": "TEST"},
                "path": "Test2",
                "filename": "file2.pdf",
            },
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    with pytest.raises(ValueError, match="Multiple rules matched"):
        sorter.get_new_location(sample_file, type="TEST")


def test_get_new_location_with_nested_path(sample_file, temp_dir, output_dir):
    """Test get_new_location with nested path."""
    config = {
        "rules": [
            {
                "name": "Nested Rule",
                "when": {"type": "TEST"},
                "path": "Level1/Level2/Level3",
                "filename": "{title}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    path, filename, rule_name = sorter.get_new_location(
        sample_file, type="TEST", title="Document"
    )

    assert "Level1" in path
    assert "Level2" in path
    assert "Level3" in path
    assert filename == "Document.pdf"


def test_get_new_location_sanitizes_filename(sample_file, temp_dir, output_dir):
    """Test that get_new_location sanitizes invalid characters."""
    config = {
        "rules": [
            {
                "name": "Sanitize Test",
                "when": {"type": "TEST"},
                "path": "Test",
                "filename": "{title}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    path, filename, rule_name = sorter.get_new_location(
        sample_file, type="TEST", title="Invalid:Chars<>|"
    )

    # Should have sanitized the invalid characters
    assert ":" not in filename
    assert "<" not in filename
    assert ">" not in filename
    assert "|" not in filename


# ============================================================================
# TEST: MOVE_FILE
# ============================================================================


def test_move_file_basic(sample_file, output_dir):
    """Test basic file moving."""
    config = {
        "rules": [
            {
                "name": "Test",
                "when": {"type": "TEST"},
                "path": "Test",
                "filename": "moved.pdf",
            }
        ]
    }
    config_path = os.path.join(os.path.dirname(sample_file), "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    dest_path = os.path.join(output_dir, "TestDir")
    dest_file = "moved.pdf"

    result = sorter.move_file(sample_file, dest_path, dest_file)

    assert os.path.exists(result)
    assert not os.path.exists(sample_file)
    assert result == os.path.join(dest_path, dest_file)


def test_move_file_creates_directories(sample_file, output_dir):
    """Test that move_file creates directories."""
    config = {"rules": []}
    config_path = os.path.join(os.path.dirname(sample_file), "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    dest_path = os.path.join(output_dir, "New", "Nested", "Dir")
    dest_file = "moved.pdf"

    result = sorter.move_file(sample_file, dest_path, dest_file, create_dirs=True)

    assert os.path.exists(result)
    assert os.path.exists(dest_path)


def test_move_file_without_create_dirs(sample_file, output_dir):
    """Test that move_file fails when directories don't exist and create_dirs=False."""
    config = {"rules": []}
    config_path = os.path.join(os.path.dirname(sample_file), "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    dest_path = os.path.join(output_dir, "Nonexistent")
    dest_file = "moved.pdf"

    # Should fail because directory doesn't exist
    with pytest.raises(Exception):
        sorter.move_file(sample_file, dest_path, dest_file, create_dirs=False)


def test_move_file_overwrite(sample_file, output_dir):
    """Test file overwriting behavior."""
    config = {"rules": []}
    config_path = os.path.join(os.path.dirname(sample_file), "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)
    dest_path = output_dir
    dest_file = "existing.pdf"

    # Create existing file
    existing_path = os.path.join(dest_path, dest_file)
    with open(existing_path, "w") as f:
        f.write("existing content")

    # Should fail without overwrite
    with pytest.raises(FileExistsError):
        sorter.move_file(sample_file, dest_path, dest_file, overwrite=False)

    # Should succeed with overwrite
    result = sorter.move_file(sample_file, dest_path, dest_file, overwrite=True)
    assert os.path.exists(result)


def test_move_file_nonexistent_source(output_dir):
    """Test move_file with non-existent source file."""
    config = {"rules": []}
    config_path = os.path.join(output_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    with pytest.raises(FileNotFoundError):
        sorter.move_file("nonexistent.pdf", output_dir, "moved.pdf")


# ============================================================================
# TEST: INTEGRATION TESTS
# ============================================================================


def test_integration_full_workflow(sample_file, temp_dir, output_dir):
    """Test complete workflow: load config, get location, move file."""
    config = {
        "templates": {"standard": "{date_time_str} - {event_title}.pdf"},
        "rules": [
            {
                "name": "Dividends",
                "conditions": {
                    "logic": "AND",
                    "rules": [
                        {
                            "logic": "OR",
                            "rules": [
                                {
                                    "field": "postbox_type",
                                    "operator": "equals",
                                    "value": "CA_INCOME_INVOICE",
                                },
                                {
                                    "field": "postbox_type",
                                    "operator": "equals",
                                    "value": "INCOME",
                                },
                            ],
                        },
                        {
                            "field": "event_subtitle",
                            "operator": "equals",
                            "value": "Dividend",
                        },
                    ],
                },
                "path": "Income/Dividends/{event_title}",
                "filename": "$template.standard",
            }
        ],
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    # Get new location
    path, filename, rule_name = sorter.get_new_location(
        sample_file,
        postbox_type="INCOME",
        event_subtitle="Dividend",
        event_title="Apple Inc",
        date_time_str="2024-03-15 14:30",
    )

    assert rule_name == "Dividends"
    assert "Apple Inc" in path
    assert (
        filename == "2024-03-15 14_30 - Apple Inc.pdf"
    )  # Colon is sanitized to underscore

    # Move file
    result = sorter.move_file(sample_file, path, filename)
    assert os.path.exists(result)
    assert not os.path.exists(sample_file)


def test_integration_with_fallback_placeholders(sample_file, temp_dir, output_dir):
    """Test integration with fallback placeholders."""
    config = {
        "rules": [
            {
                "name": "Flexible Rule",
                "when": {"type": "TRANSFER"},
                "path": "Transfers",
                "filename": "{date_time_str} - {event_title|document_title|'Transfer'}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    # Test with event_title
    path1, filename1, _ = sorter.get_new_location(
        sample_file, type="TRANSFER", event_title="SEPA Transfer", date_time_str="2024-03-15"
    )
    assert filename1 == "2024-03-15 - SEPA Transfer.pdf"

    # Create another sample file for second test
    sample_file2 = os.path.join(temp_dir, "test2.pdf")
    with open(sample_file2, "w") as f:
        f.write("test")

    # Test without event_title, with document_title
    path2, filename2, _ = sorter.get_new_location(
        sample_file2,
        type="TRANSFER",
        document_title="Transfer Details",
        date_time_str="2024-03-16",
    )
    assert filename2 == "2024-03-16 - Transfer Details.pdf"

    # Create third sample file
    sample_file3 = os.path.join(temp_dir, "test3.pdf")
    with open(sample_file3, "w") as f:
        f.write("test")

    # Test with neither, should use literal
    path3, filename3, _ = sorter.get_new_location(
        sample_file3, type="TRANSFER", date_time_str="2024-03-17"
    )
    assert filename3 == "2024-03-17 - Transfer.pdf"


def test_integration_complex_conditions(sample_file, temp_dir, output_dir):
    """Test integration with complex OR/AND conditions."""
    config = {
        "rules": [
            {
                "name": "Complex Rule",
                "conditions": {
                    "logic": "AND",
                    "rules": [
                        {
                            "logic": "OR",
                            "rules": [
                                {
                                    "field": "type",
                                    "operator": "equals",
                                    "value": "INCOME",
                                },
                                {
                                    "field": "type",
                                    "operator": "equals",
                                    "value": "DIVIDEND",
                                },
                            ],
                        },
                        {"field": "status", "operator": "equals", "value": "COMPLETED"},
                    ],
                },
                "path": "Completed",
                "filename": "{title}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    path, filename, rule_name = sorter.get_new_location(
        sample_file, type="DIVIDEND", status="COMPLETED", title="Apple Dividend"
    )

    assert rule_name == "Complex Rule"
    assert filename == "Apple Dividend.pdf"


# ============================================================================
# TEST: EDGE CASES
# ============================================================================


def test_edge_case_empty_metadata_value(sample_file, temp_dir, output_dir):
    """Test handling of empty metadata values."""
    config = {
        "rules": [
            {
                "name": "Test",
                "when": {"type": "TEST"},
                "path": "Test",
                "filename": "{title|'Default'}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    # Empty string should be skipped
    path, filename, _ = sorter.get_new_location(sample_file, type="TEST", title="")
    assert filename == "Default.pdf"


def test_edge_case_none_metadata_value(sample_file, temp_dir, output_dir):
    """Test handling of None metadata values."""
    config = {
        "rules": [
            {
                "name": "Test",
                "when": {"type": "TEST"},
                "path": "Test",
                "filename": "{title|'Default'}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    # None should be skipped
    path, filename, _ = sorter.get_new_location(sample_file, type="TEST", title=None)
    assert filename == "Default.pdf"


def test_edge_case_special_characters_in_metadata(sample_file, temp_dir, output_dir):
    """Test handling of special characters in metadata."""
    config = {
        "rules": [
            {
                "name": "Test",
                "when": {"type": "TEST"},
                "path": "Test",
                "filename": "{title}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    path, filename, _ = sorter.get_new_location(
        sample_file, type="TEST", title="Test<>:|?*"
    )

    # Should be sanitized
    assert "<" not in filename
    assert ">" not in filename
    assert ":" not in filename
    assert "|" not in filename
    assert "?" not in filename
    assert "*" not in filename


def test_edge_case_unicode_in_metadata(sample_file, temp_dir, output_dir):
    """Test handling of unicode characters in metadata."""
    config = {
        "rules": [
            {
                "name": "Test",
                "when": {"type": "TEST"},
                "path": "Test",
                "filename": "{title}.pdf",
            }
        ]
    }
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    sorter = FileSorter(config_path, output_dir)

    path, filename, _ = sorter.get_new_location(
        sample_file, type="TEST", title="Überweisung äöü 中文"
    )

    assert (
        "Überweisung" in filename or "_" in filename
    )  # May be sanitized depending on platform


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
