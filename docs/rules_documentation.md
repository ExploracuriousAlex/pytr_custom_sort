# Trade Republic Document Sorting - Rule Configuration

This documentation explains how to use the YAML configuration file (`tr_sorting_rules.yaml`) to create custom sorting rules for your Trade Republic documents.

## Table of Contents

1. [Basic Structure](#basic-structure)
2. [Available Fields](#available-fields)
3. [Templates](#templates)
4. [Rule Syntax](#rule-syntax)
5. [Placeholders for Paths and Filenames](#placeholders-for-paths-and-filenames)
6. [Examples](#examples)
7. [Best Practices](#best-practices)

---

## Basic Structure

A YAML configuration file consists of an optional templates section and a list of rules:

```yaml
# Optional: Define reusable templates
templates:
  template_name: "pattern with {placeholders}"
  another_template: "{date_time_str} - {event_title}.pdf"

rules:
  - name: "Rule Name"
    when:
      # Conditions here
    path: "Target Folder"
    filename: $template.template_name  # Reference a template
```

### Required Fields for Each Rule

- **`name`**: A descriptive name for the rule (for logging and debugging)
- **`when`** or **`conditions`**: The conditions that must be met
- **`path`**: The target folder (relative to base directory)
- **`filename`**: The filename pattern with placeholders or template reference

### Flexible Path and Filename Definitions

Both `path` and `filename` support three different formats:

#### 1. Fixed String (Static)

```yaml
path: "Dividends"                    # Fixed folder name
filename: "document.pdf"             # Fixed filename
```

#### 2. Pattern with Placeholders (Dynamic)

```yaml
path: "Dividends/{event_title}"                           # Dynamic path
filename: "{date_time_str} - {event_title}.pdf"                # Dynamic filename
filename: "{event_title|document_title|'Unknown'}.pdf"    # With fallback
```

#### 3. Template Reference

```yaml
templates:
  my_path: "Income/{event_title}"
  my_filename: "{date_time_str} - {event_title}.pdf"

rules:
  - name: "Example"
    when:
      postbox_type: "INCOME"
    path: $template.my_path          # Reference to path template
    filename: $template.my_filename  # Reference to filename template
```

**Note**: You can mix these formats freely. For example, use a template for the filename but a fixed string for the path, or vice versa.

---

## Available Fields

The following fields are available from Trade Republic events:

| Field Name | Description | Example Value |
|------------|-------------|---------------|
| `postbox_type` | Document type from TR API | `"INCOME"`, `"SECURITIES_SETTLEMENT"` |
| `document_title` | Title of the document | `"Settlement"`, `"Account Statement"` |
| `document_detail` | Additional document details | Varies |
| `event_title` | Event title | `"Apple Inc."`, `"Interest"` |
| `event_subtitle` | Event subtitle | `"Dividend"`, `"Information"` |
| `date_time_str` | Formatted timestamp | `"2024-03-15 14:30"` |
| `timestamp` | ISO timestamp | `"2024-03-15T14:30:22.000Z"` |
| `filename` | Original filename | `"document_12345.pdf"` |

---

## Templates

Templates allow you to define reusable filename patterns once and reference them in multiple rules. This reduces repetition and makes maintenance easier.

### Defining Templates

Templates are defined in a `templates` section at the top of your configuration file:

```yaml
templates:
  # Standard timestamp with event title
  event_with_time: "{date_time_str} - {event_title}.pdf"
  
  # Standard timestamp with document title
  document_with_time: "{date_time_str} - {document_title}.pdf"
  
  # Event with subtitle
  event_with_subtitle: "{date_time_str} - {event_title} - {event_subtitle}.pdf"
  
  # Custom pattern
  my_custom_format: "{event_title} ({date_time_str}).pdf"
```

### Using Templates in Rules

Reference a template in your rules using `$template.template_name`:

```yaml
rules:
  - name: "Dividends"
    when:
      postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
    path: "Dividends"
    filename: $template.event_with_time  # Uses the template
  
  - name: "Account Statements"
    when:
      postbox_type: "CASH_ACCOUNT_STATEMENT_V2"
    path: "Account Statements"
    filename: $template.event_with_time  # Reuses the same template
```

### Benefits of Templates

✅ **DRY (Don't Repeat Yourself)**: Define patterns once, use everywhere  
✅ **Consistency**: All related documents use the same naming convention  
✅ **Easy Updates**: Change the pattern in one place, affects all rules using it  
✅ **Readability**: Rules are shorter and easier to understand

### Template Examples

```yaml
templates:
  # Basic patterns
  simple_time: "{date_time_str}.pdf"
  event_only: "{event_title}.pdf"
  document_only: "{document_title}.pdf"
  
  # Combined patterns
  event_with_time: "{date_time_str} - {event_title}.pdf"
  document_with_time: "{date_time_str} - {document_title}.pdf"
  event_with_subtitle: "{date_time_str} - {event_title} - {event_subtitle}.pdf"
  document_with_event: "{date_time_str} - {document_title} - {event_title}.pdf"
  
  # Advanced patterns
  detailed: "{date_time_str} - {postbox_type} - {event_title}.pdf"
  archive: "{event_title}/{date_time_str} - {document_title}.pdf"
```

### Mixing Templates and Direct Patterns

You can mix template references with direct patterns:

```yaml
rules:
  # Using a template
  - name: "Most Documents"
    when:
      postbox_type: "INCOME"
    path: "Income"
    filename: $template.event_with_time
  
  # Using a direct pattern (for unique cases)
  - name: "Special Case"
    when:
      postbox_type: "SPECIAL_TYPE"
    path: "Special"
    filename: "{date_time_str} - Custom Pattern - {event_title}.pdf"
```

---

## Rule Syntax

There are two ways to define rules: the **simplified `when` syntax** (recommended) and the **extended `conditions` syntax** (for complex cases).

### 1. Simplified `when` Syntax (Recommended)

The `when` syntax is easier to read and write. It's suitable for most use cases.

#### a) Simple Condition (One Field = One Value)

```yaml
- name: "Interest"
  when:
    event_title: "Interest"
  path: "Interest"
  filename: "{date_time_str} - {event_title}.pdf"
```

**Meaning**: Sort all documents where `event_title` is exactly `"Interest"`.

#### b) Multiple Conditions (AND Logic)

When you specify multiple fields, **all** conditions must be met (AND logic):

```yaml
- name: "Tax Exchange"
  when:
    postbox_type: "SHAREBOOKING"
    document_title: "Execution Notice"
    event_subtitle: "Tax Exchange"
  path: "Tax Exchange"
  filename: "{date_time_str} - {event_title}.pdf"
```

**Meaning**: All three conditions must be met simultaneously.

#### c) OR Logic with Array

If a field can have multiple possible values, use an array:

```yaml
- name: "Dividends"
  when:
    postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
  path: "Dividends"
  filename: "{date_time_str} - {event_title}.pdf"
```

**Meaning**: The document is sorted if `postbox_type` is either `"CA_INCOME_INVOICE"` **or** `"INCOME"`.

#### d) Combination: Multiple Fields with OR

```yaml
- name: "Base Information"
  when:
    postbox_type: ["BASE_INFO", "INFO"]
    event_subtitle: "Product Information"
  path: "Base Information"
  filename: "{date_time_str} - {document_title}.pdf"
```

**Meaning**:

- `postbox_type` must be `"BASE_INFO"` **or** `"INFO"` **AND**
- `event_subtitle` must be `"Product Information"`

---

### 2. Extended `conditions` Syntax

For complex conditions (e.g., mixed AND/OR logic, other operators), use the `conditions` syntax.

#### Structure

```yaml
- name: "Rule Name"
  conditions:
    logic: AND  # or OR
    rules:
      - field: field_name
        operator: operator_type
        value: value
      - field: other_field
        operator: operator_type
        value: other_value
  path: "Target Folder"
  filename: "pattern.pdf"
```

#### Available Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Exact match | `value: "INCOME"` |
| `not_equals` | No match | `value: "CANCELLED"` |
| `contains` | Contains substring | `value: "Dividend"` |
| `starts_with` | Starts with | `value: "Depot"` |
| `ends_with` | Ends with | `value: "report"` |
| `regex` | Regular expression | `value: "^(A\|B).*"` |

#### Example with contains

```yaml
- name: "All Tax Documents"
  conditions:
    logic: OR
    rules:
      - field: document_title
        operator: contains
        value: "Tax"
      - field: event_title
        operator: contains
        value: "Tax"
  path: "Taxes"
  filename: "{date_time_str} - {document_title}.pdf"
```

#### Example with Regex

```yaml
- name: "Account Statements by Pattern"
  conditions:
    logic: AND
    rules:
      - field: document_title
        operator: regex
        value: "^Account Statement (No\\. )?\\d+$"
  path: "Account Statements"
  filename: "{date_time_str} - {document_title}.pdf"
```

#### Nested Conditions

You can nest conditions for complex logic:

```yaml
- name: "Complex Rule"
  conditions:
    logic: AND
    rules:
      - field: postbox_type
        operator: equals
        value: "INFORMATIVE_CA"
      - logic: OR  # Nested OR condition
        rules:
          - field: event_subtitle
            operator: equals
            value: "Annual General Meeting"
          - field: event_subtitle
            operator: equals
            value: "General Meeting"
  path: "General Meetings"
  filename: "{date_time_str} - {event_title}.pdf"
```

---

## Placeholders for Paths and Filenames

You can use dynamic values in `path` and `filename`:

### Available Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{date_time_str}` | Formatted timestamp | `2024-03-15 14:30` |
| `{event_title}` | Event title | `Apple Inc.` |
| `{event_subtitle}` | Event subtitle | `Dividend` |
| `{document_title}` | Document title | `Settlement` |
| `{document_detail}` | Document details | Varies |
| `{postbox_type}` | Type from API | `INCOME` |
| `{original}` | Original filename (without extension) | `document_12345` |
| `{ext}` | File extension with dot | `.pdf` |

### Fallback Placeholders

You can specify multiple fields with fallback values using the pipe `|` operator. The system will use the first non-empty value:

**Syntax**: `{field1|field2|'default'}`

**How it works**:

1. Try to use `field1` - if it exists and is not empty, use it
2. If `field1` is empty/missing, try `field2`
3. If all fields are empty, use the literal string `'default'`

**Examples**:

```yaml
# Use event_title, fallback to document_title, then to 'Document'
filename: "{date_time_str} - {event_title|document_title|'Document'}.pdf"

# Use event_subtitle if available, otherwise 'Info'
filename: "{date_time_str} - {event_title} - {event_subtitle|'Info'}.pdf"

# Multiple fallbacks without default
filename: "{event_title|document_title|postbox_type}.pdf"

# Use in paths too
path: "Documents/{event_title|'Unknown'}"
```

**When to use fallbacks**:

- ✅ When a field might be empty for some documents
- ✅ To ensure files always have valid names
- ✅ To provide user-friendly defaults
- ✅ To make rules more robust

### Path Examples

```yaml
# Simple folder
path: "Dividends"

# Nested folder
path: "Finance/Dividends"

# With placeholders
path: "Dividends/{event_title}"
# Result: Dividends/Apple Inc.

# With fallback in path
path: "Documents/{event_title|document_title|'Unsorted'}"
# Result: Documents/Apple Inc. (or Documents/Settlement, or Documents/Unsorted)

# Sorted by year (requires timestamp processing)
path: "Archive/2024/Dividends"
```

### Filename Examples

```yaml
# With timestamp and event title
filename: "{date_time_str} - {event_title}.pdf"
# Result: 2024-03-15 14:30 - Apple Inc..pdf

# With fallback
filename: "{date_time_str} - {event_title|document_title|'Unknown'}.pdf"
# Result: 2024-03-15 14:30 - Apple Inc..pdf
# Or:     2024-03-15 14:30 - Settlement.pdf
# Or:     2024-03-15 14:30 - Unknown.pdf

# Document title only
filename: "{document_title}.pdf"
# Result: Settlement.pdf

# Combined
filename: "{date_time_str} - {event_title} - {event_subtitle}.pdf"
# Result: 2024-03-15 14:30 - Apple Inc. - Dividend.pdf

# With original name
filename: "{date_time_str} - {original}{ext}"
# Result: 2024-03-15 14:30 - document_12345.pdf"
```

---

## Examples

### Example 1: Using Templates

```yaml
templates:
  standard_name: "{date_time_str} - {event_title}.pdf"

rules:
  - name: "Dividends"
    when:
      postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
    path: "Dividends"
    filename: $template.standard_name
  
  - name: "Interest"
    when:
      event_title: "Interest"
    path: "Interest"
    filename: $template.standard_name
```

### Example 2: Simple Rule (Single Value)

```yaml
- name: "Account Statements"
  when:
    postbox_type: "CASH_ACCOUNT_STATEMENT_V2"
  path: "Account Statements"
  filename: "{date_time_str} - {event_title}.pdf"
```

### Example 3: OR Condition with Array

```yaml
- name: "Annual Tax Report"
  when:
    postbox_type: ["yearlyTaxReport", "YEAR_END_TAX_REPORT"]
  path: "Annual Tax Report"
  filename: "{date_time_str} - {document_title}.pdf"
```

### Example 4: Multiple Fields (AND Logic)

```yaml
- name: "Company Announcements"
  when:
    postbox_type: "GENERAL_CORPACTION_V2"
    event_subtitle: "Company Announcement"
  path: "Company Announcements"
  filename: "{date_time_str} - {document_title} - {event_title}.pdf"
```

### Example 5: Complex Condition with contains

```yaml
- name: "All Documents with 'Dividend' in Title"
  conditions:
    logic: OR
    rules:
      - field: event_title
        operator: contains
        value: "Dividend"
      - field: document_title
        operator: contains
        value: "Dividend"
  path: "Dividends"
  filename: "{date_time_str} - {event_title}.pdf"
```

### Example 6: Nested Folders

```yaml
- name: "Dividends by Company"
  when:
    postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
  path: "Income/Dividends/{event_title}"
  filename: "{date_time_str} - Dividend.pdf"
```

This would create folders like:

```
Income/
  Dividends/
    Apple Inc./
      2024-03-15 14:30 - Dividend.pdf
    Microsoft Corp./
      2024-03-20 10:15 - Dividend.pdf
```

### Example 7: Static Filename

```yaml
- name: "Outgoing Transfers"
  when:
    postbox_type: "OUTGOING_TRANSFER"
  path: "Outgoing Transfers"
  filename: "{date_time_str} - Transfer Confirmation.pdf"
```

### Example 8: Using Fallback Placeholders

```yaml
templates:
  # Template with fallback - works for different document types
  flexible_title: "{date_time_str} - {event_title|document_title|'Document'}.pdf"

rules:
  - name: "Incoming Transfers"
    when:
      postbox_type: ["INCOMING_TRANSFER", "TRANSFER_BOOKING_DETAILS"]
    path: "Incoming Transfers"
    # Uses event_title if available, otherwise document_title, or 'Transfer' as fallback
    filename: "{date_time_str} - {document_title|event_title|'Transfer'}.pdf"
  
  - name: "Flexible Income"
    when:
      postbox_type: "INCOME"
    path: "Income"
    # Use template with fallback
    filename: $template.flexible_title
```

### Example 9: Complete Configuration with Templates

```yaml
templates:
  # Define common patterns
  event_time: "{date_time_str} - {event_title}.pdf"
  doc_time: "{date_time_str} - {document_title}.pdf"
  event_subtitle: "{date_time_str} - {event_title} - {event_subtitle}.pdf"
  flexible_title: "{date_time_str} - {event_title|document_title|'Document'}.pdf"

rules:
  # Income documents
  - name: "Dividends"
    when:
      postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
    path: "Income/Dividends"
    filename: $template.event_time
  
  - name: "Interest"
    when:
      event_title: "Interest"
    path: "Income/Interest"
    filename: $template.event_time
  
  # Account statements
  - name: "Account Statements"
    when:
      postbox_type: "CASH_ACCOUNT_STATEMENT_V2"
    path: "Statements/Cash"
    filename: $template.event_time
  
  - name: "Securities Statements"
    when:
      postbox_type: "SECURITIES_ACCOUNT_STATEMENT_V2"
    path: "Statements/Securities"
    filename: $template.event_time
  
  # Transactions
  - name: "Securities Settlements"
    when:
      postbox_type: "SECURITIES_SETTLEMENT"
    path: "Transactions/Settlements"
    filename: $template.doc_time
```

---

## Best Practices

### 1. Use Templates for Common Patterns

✅ **Good**: Define templates for patterns used multiple times

```yaml
templates:
  standard: "{date_time_str} - {event_title}.pdf"

rules:
  - name: "Rule 1"
    when:
      postbox_type: "TYPE_A"
    path: "FolderA"
    filename: $template.standard
  
  - name: "Rule 2"
    when:
      postbox_type: "TYPE_B"
    path: "FolderB"
    filename: $template.standard
```

❌ **Bad**: Repeat the same pattern everywhere

```yaml
rules:
  - name: "Rule 1"
    when:
      postbox_type: "TYPE_A"
    path: "FolderA"
    filename: "{date_time_str} - {event_title}.pdf"
  
  - name: "Rule 2"
    when:
      postbox_type: "TYPE_B"
    path: "FolderB"
    filename: "{date_time_str} - {event_title}.pdf"
```

### 2. Unique Rules (No Overlaps)

Each file must match **exactly one rule**. The system checks all rules against each document, and if multiple rules match, an error is raised.

❌ **Wrong**: These rules overlap - a document with both conditions would match both rules

```yaml
- name: "All Income Documents"
  when:
    postbox_type: "INCOME"
  path: "Income"
  filename: "{date_time_str} - {event_title}.pdf"

- name: "Interest"
  when:
    postbox_type: "INCOME"
    event_title: "Interest"
  path: "Interest"
  filename: "{date_time_str} - {event_title}.pdf"
```

**Problem**: A document with `postbox_type: "INCOME"` and `event_title: "Interest"` matches both rules → Error!

✅ **Correct**: Rules are mutually exclusive

```yaml
- name: "Interest"
  when:
    postbox_type: "INCOME"
    event_title: "Interest"
  path: "Interest"
  filename: "{date_time_str} - {event_title}.pdf"

- name: "Other Income Documents"
  when:
    postbox_type: "INCOME"
  conditions:
    logic: AND
    rules:
      - field: postbox_type
        operator: equals
        value: "INCOME"
      - field: event_title
        operator: not_equals
        value: "Interest"
  path: "Income"
  filename: "{date_time_str} - {event_title}.pdf"
```

**Solution**: Add `not_equals` condition to ensure rules don't overlap.

✅ **Alternative**: Use different fields to distinguish

```yaml
- name: "Dividends"
  when:
    postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
    event_subtitle: "Dividend"
  path: "Dividends"
  filename: "{date_time_str} - {event_title}.pdf"

- name: "Interest"
  when:
    postbox_type: "INCOME"
    event_title: "Interest"
  path: "Interest"
  filename: "{date_time_str} - {event_title}.pdf"
```

**This works**: Documents with `event_subtitle: "Dividend"` won't have `event_title: "Interest"`, so rules are exclusive.

### 3. Rule Order Doesn't Matter

Since all rules are checked and overlaps cause errors, the order of rules in your configuration file doesn't affect which rule gets applied. However, for readability, it's still good practice to organize rules logically:

```yaml
rules:
  # ============================================================================
  # INCOME DOCUMENTS
  # ============================================================================
  
  - name: "Dividends"
    when:
      postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
      event_subtitle: "Dividend"
    path: "Dividends"
    filename: "{date_time_str} - {event_title}.pdf"
  
  - name: "Interest"
    when:
      event_title: "Interest"
    path: "Interest"
    filename: "{date_time_str} - {event_title}.pdf"
  
  # ============================================================================
  # STATEMENTS
  # ============================================================================
  
  - name: "Account Statements"
    when:
      postbox_type: "CASH_ACCOUNT_STATEMENT_V2"
    path: "Statements"
    filename: "{date_time_str} - {event_title}.pdf"
```

### 4. Use Comments for Documentation

Use comments to document your rules:

```yaml
templates:
  standard: "{date_time_str} - {event_title}.pdf"

rules:
  # ============================================================================
  # INCOME
  # ============================================================================
  
  # Dividends from stocks
  - name: "Dividends"
    when:
      postbox_type: ["CA_INCOME_INVOICE", "INCOME"]
    path: "Dividends"
    filename: $template.standard
  
  # Interest payments on cash account
  - name: "Interest"
    when:
      event_title: "Interest"
    path: "Interest"
    filename: $template.standard
```

### 5. Use Fallback Placeholders

Use fallback placeholders when fields might be empty or missing:

```yaml
# ✅ Good - gracefully handles missing fields
filename: "{date_time_str} - {event_title|document_title|'Unknown'}.pdf"

# ✅ Good - ensures subtitle is always present
filename: "{event_title} - {event_subtitle|'Info'}.pdf"

# ❌ Risky - may result in incomplete filenames
filename: "{date_time_str} - {event_title}.pdf"  # if event_title is empty
```

**Benefits**:

- Prevents empty or invalid filenames
- Makes rules more robust
- Provides user-friendly defaults
- Works across different document types

### 6. Filename Sanitization

The system automatically removes invalid characters from filenames. The following characters are replaced with `_`:

- Windows: `< > : " / \ | ? *`
- Leading/trailing spaces

You don't need to worry about this.

### 7. Test Your Rules

Recommended workflow:

1. Export a backup of your existing documents
2. Create a test folder with some sample files
3. Test your new rules
4. Check the logs for errors
5. Apply the rules to all documents

### 8. Use Descriptive Names

```yaml
# ✅ Good
- name: "Dividends from US Stocks"
  
# ✅ Good
- name: "Securities Settlements - Purchases"

# ❌ Too generic
- name: "Rule 1"

# ❌ Unclear
- name: "Docs"
```

### 9. Prefer the Simplified Syntax

Whenever possible, use the `when` syntax:

```yaml
# ✅ Easier to read
- name: "Interest"
  when:
    event_title: "Interest"
  path: "Interest"
  filename: "{date_time_str} - {event_title}.pdf"

# ❌ Unnecessarily complex for this case
- name: "Interest"
  conditions:
    logic: AND
    rules:
      - field: event_title
        operator: equals
        value: "Interest"
  path: "Interest"
  filename: "{date_time_str} - {event_title}.pdf"
```

Use `conditions` only for:

- Operators other than `equals` (contains, regex, etc.)
- Complex nested logic
- Mixed AND/OR conditions

### 9. Group Related Templates

Organize your templates logically:

```yaml
templates:
  # Basic patterns
  event_time: "{date_time_str} - {event_title}.pdf"
  doc_time: "{date_time_str} - {document_title}.pdf"
  
  # Combined patterns
  event_subtitle: "{date_time_str} - {event_title} - {event_subtitle}.pdf"
  doc_event: "{date_time_str} - {document_title} - {event_title}.pdf"
  
  # Special formats
  archive_format: "{event_title}/{date_time_str}.pdf"
```

---

## Troubleshooting

### Problem: "No matching rule found"

**Cause**: No rule matches the document.

**Solution**:

1. Check the CSV file `docs_with_metadata.csv` for the document's metadata
2. Create a matching rule or a fallback rule

### Problem: "Multiple rules matched"

**Cause**: More than one rule matches the document.

**Solution**:

1. Make rules more specific
2. Check the order
3. Add additional conditions to make rules unique

### Problem: Template not found

**Cause**: Referenced a template that doesn't exist in the `templates` section.

**Solution**:

1. Check the spelling of `$template.template_name`
2. Ensure the template is defined in the `templates` section
3. Template names are case-sensitive

### Problem: Invalid characters in filename

**Cause**: Placeholders contain characters not allowed in the file system.

**Solution**: Sanitization happens automatically. If problems occur, use different placeholders.

### Problem: Folders are not created

**Cause**: `create_dirs` is set to `False` (default is `True`).

**Solution**: Check the code, configuration will automatically create folders.

---

## Advanced Features

### Custom Metadata Fields

If you have custom fields in your metadata, you can use them directly:

```yaml
- name: "Custom Rule"
  when:
    custom_field: "custom_value"
  path: "Custom"
  filename: "{date_time_str} - {custom_field}.pdf"
```

### Templates with Path Variables

Templates can also be used in paths (though less common):

```yaml
templates:
  income_path: "Finance/Income/{event_title}"
  
rules:
  - name: "Dividends"
    when:
      postbox_type: "INCOME"
    path: $template.income_path
    filename: "{date_time_str} - Dividend.pdf"
```

### Dynamic Paths with Multiple Levels

```yaml
- name: "Archive by Year and Month"
  when:
    postbox_type: "INCOME"
  path: "Archive/2024/03/Dividends"  # Static
  filename: "{date_time_str} - {event_title}.pdf"
```

For dynamic year/month, you would need to extend the metadata accordingly or parse `date_time_str`.

---

## Summary

- **Templates**: Define reusable patterns with `$template.name`
  - Reduces repetition
  - Easier maintenance
  - Better consistency

- **`when`**: Simple syntax for most cases
  - Single field: `field: "value"`
  - OR: `field: ["value1", "value2"]`
  - AND: Specify multiple fields
  
- **`conditions`**: Extended syntax for complex cases
  - Different operators: `equals`, `contains`, `regex`, etc.
  - Nested logic possible
  
- **Placeholders**: Dynamic values in paths and filenames
  - `{date_time_str}`, `{event_title}`, `{document_title}`, etc.
  
- **Best Practices**:
  - Use templates for common patterns
  - Specific rules first
  - Unique rules (no overlaps)
  - Descriptive names
  - Comments for documentation
  - Prefer simplified syntax

Good luck sorting your Trade Republic documents! 🎯
