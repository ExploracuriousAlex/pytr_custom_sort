# pytr_custom_sort

Personalized sorting of documents downloaded with [pytr](https://github.com/pytr-org/pytr) from Trade Republic.

## Overview

If you want to organize your Trade Republic documents downloaded with pytr in your own custom way, this tool provides a flexible, rule-based sorting system. Define your sorting rules in YAML format and let the tool automatically organize your documents.

## Prerequisites

- Python with [uv](https://docs.astral.sh/uv/) package manager (recommended for easier dependency management)
- [pytr](https://github.com/pytr-org/pytr) for downloading Trade Republic documents

> **💡 Tip:** I recommend using the [uv package manager](https://docs.astral.sh/uv/) for a more comfortable Python experience. It's fast, reliable, and handles dependencies seamlessly. If you don't have it yet, install it with:
>
> ```bash
> # Windows (PowerShell)
> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
> 
> # Windows (WinGet)
> winget install --id=astral-sh.uv  -e
>
> # macOS/Linux
> curl -LsSf https://astral.sh/uv/install.sh | sh
> ```

## Installation

Clone the repository:

```bash
git clone https://github.com/ExploracuriousAlex/pytr_custom_sort.git
cd pytr_custom_sort
```

Install dependencies:

```bash
uv sync
```

## Usage

### 1. Download Documents with pytr

First, download your Trade Republic documents using pytr's `--flat` option:

```bash
uvx pytr dl_docs <your_download_folder> --flat
```

For more details about pytr, visit: <https://github.com/pytr-org/pytr>

### 2. Configure Sorting Rules

Adapt the `config/tr_sorting_rules.yaml` file to define your preferred sorting rules.

For detailed information on how to configure sorting rules, see [docs/rules_documentation.md](docs/rules_documentation.md).

### 3. Run the Sorting Tool

Execute the sorting script on your downloaded documents:

```bash
uv run sort_tr_docs.py <your_download_folder>
```

## Documentation

- [config/tr_sorting_rules.yaml](config/tr_sorting_rules.yaml) - Configuration file for sorting rules
- [docs/rules_documentation.md](docs/rules_documentation.md) - Detailed guide on creating and customizing sorting rules

## Project Structure

```
pytr_custom_sort/
├── rule_based_sort/           # Generic rule-based sorting module
│   ├── __init__.py
│   └── rule_based_sorter.py   # Sorting business logic
├── tests/                     # Test suite
│   └── test_rule_based_sorter.py
├── config/                    # Configuration files
│   ├── tr_sorting_rules.yaml
│   └── tr_sorting_rules.schema.json
├── docs/                      # Documentation
│   └── rules_documentation.md
├── sort_tr_docs.py            # Main CLI script
├── README.md
├── LICENSE
└── pyproject.toml
```

## License

See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
