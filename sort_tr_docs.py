"""
Sort and organize PDF files based on metadata from Trade Republic events.

This module processes PDF files in a specified directory by:
- Matching filenames with events in all_events.json
- Extracting metadata (postboxType, title, subtitle, timestamp)
- Organizing files into categorized subdirectories
- Renaming files with timestamps and descriptive names
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import coloredlogs
from jsonpath_ng.ext import parse

from rule_based_sort.rule_based_sorter import FileSorter
import csv

# Setup logging with coloredlogs
logger = logging.getLogger(__name__)
coloredlogs.install(
    level="DEBUG",
    logger=logger,
    fmt="%(asctime)s - %(levelname)s - %(message)s",
)


def main(target_directory: Path):
    """
    Process PDF files from the specified directory:
    - Search corresponding event for the filename in all_events.json
    - Retrieve meta data from that event
    - Rename and sort files accordingly
    """

    sorter = FileSorter("config/tr_sorting_rules.yaml", base_output_dir=target_directory)
    events_file = Path(target_directory, "all_events.json")

    # Check if directory exists
    if not target_directory.exists():
        logger.error("Directory '%s' does not exist", target_directory)
        return

    # Check if events file exists
    if not events_file.exists():
        logger.error("File '%s' does not exist", events_file)
        return

    # Load all events
    logger.info("Loading events from '%s'...", events_file)
    with open(events_file, "r", encoding="utf-8") as f:
        events = json.load(f)

    logger.info("Loaded %d events", len(events))

    # Build index of documents from events (performance optimization)
    logger.info("Building document index...")
    document_index = {}
    jsonpath_expr = parse("$.details.sections[?(@.type=='documents')].data[*]")
    
    for event in events:
        matches = jsonpath_expr.find(event)
        for match in matches:
            payload = match.value.get("action", {}).get("payload", "")
            if payload:
                # Extract filename from payload (assuming it's a URL or path)
                # Store the match object with the full context
                document_index[payload] = match
    
    logger.info("Document index built with %d entries", len(document_index))

    # Process all PDF files
    pdf_files = list(target_directory.glob("*.pdf"))
    logger.info("Found %d PDF files in '%s'", len(pdf_files), target_directory)

    if not pdf_files:
        logger.warning("No PDF files found")
        return

    matched_count = 0
    not_found_count = 0
    sorted_count = 0
    not_sorted_count = 0

    for pdf_file in pdf_files:
        filename = pdf_file.name

        # Find matching document in index
        all_matches = [match for payload, match in document_index.items() if filename in payload]

        if len(all_matches) == 0:
            logger.error("No matches found for file '%s'", filename)
            not_found_count += 1
            continue
        elif len(all_matches) > 1:
            logger.error(
                "Multiple matches (%d) found for file '%s'", len(all_matches), filename
            )
            not_found_count += 1
            continue

        match = all_matches[0]
        matched_count += 1

        postbox_type = match.value.get("postboxType")
        document_title = match.value.get("title")
        document_detail = match.value.get("detail")
        event_title = match.context.context.context.context.context.value.get("title")
        event_subtitle = match.context.context.context.context.context.value.get(
            "subtitle"
        )
        timestamp = match.context.context.context.context.context.value.get("timestamp")
        date_time_str = (
            datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
            if timestamp
            else None
        )

        # Write document metadata to CSV file
        csv_file = target_directory / "docs_with_metadata.csv"
        file_exists = csv_file.exists()

        with open(csv_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["filename", "postbox_type", "document_title", "document_detail", "event_title", "event_subtitle"])
            writer.writerow([filename, postbox_type, document_title, document_detail, event_title, event_subtitle])

        try:
            path, name, _rule = sorter.get_new_location(
                original_filepath=pdf_file,
                postbox_type=postbox_type,
                document_title=document_title,
                document_detail=document_detail,
                event_title=event_title,
                event_subtitle=event_subtitle,
                date_time_str=date_time_str,
            )

            # Move the file
            sorter.move_file(
                original_filepath=pdf_file,
                new_path=path,
                new_filename=name,
                create_dirs=True,
                overwrite=False,
            )

            sorted_count += 1
            logger.info("Successfully sorted file '%s'", filename)
        except Exception as e:
            logger.error("Failed to sort file '%s': %s", filename, str(e))
            not_sorted_count += 1

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Processing Summary:")
    logger.info("=" * 60)
    logger.info("Total PDF files found:      %d", len(pdf_files))
    logger.info("Events matched:             %d", matched_count)
    logger.info("Events not found:           %d", not_found_count)
    logger.info("Files successfully sorted:  %d", sorted_count)
    logger.info("Files failed to sort:       %d", not_sorted_count)
    logger.info("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sort_tr_docs.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    main(directory)
