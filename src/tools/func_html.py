from html.parser import HTMLParser
from typing import List, Optional, Dict, Tuple
import re
from typing import List, Dict
import os


def read_html_lines(html_file_path: str) -> list[str]:
    """
    Read all lines from an HTML file and return them as a list of strings.

    Args:
        html_file_path (str): Path to the HTML file.

    Returns:
        list[str]: List of lines from the file, or an empty list if the file is not found or cannot be read.
    """

    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File '{html_file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    return lines


def get_html_report_name_data(lines: str) -> List[Dict]:
    """
    Extract structured information from HTML comments that start with 'FullName:'.
    This is useful for finding report/table metadata in EnergyPlus HTML reports.

    Args:
        lines (str or list[str]): Path to the HTML file or list of lines from the file.

    Returns:
        List[Dict]: List of dictionaries with report_name, report_for, table_name, and line info.
    """

    if isinstance(lines, str):
        if os.path.exists(lines):
            lines = read_html_lines(lines)

    results = []


    # Process each line to find comments
    for line_num, line in enumerate(lines, 1):
        # Find all HTML comments in the line
        comment_pattern = r'<!--\s*(.*?)\s*-->'
        comments = re.finditer(comment_pattern, line, re.DOTALL)

        for comment_match in comments:
            comment_content = comment_match.group(1).strip()

            # Check if this is a FullName comment
            if comment_content.startswith('FullName:'):
                # Extract the content after "FullName:"
                fullname_content = comment_content[9:].strip()  # Remove "FullName:" prefix

                # Split by underscores
                parts = fullname_content.split('_') if fullname_content else []


                if len(parts) != 3:
                    report_name = fullname_content.split("_")[0]
                    report_for = "_".join(fullname_content.split("_")[1:-1])
                    table_name = fullname_content.split("_")[-1]

                else:
                    report_name, report_for, table_name = parts

                result = {
                    'report_name': report_name,
                    'report_for': report_for,
                    'table_name': table_name,
                    'line_number': line_num,
                    'table_start_line': line_num + 1,
                    'raw_comment': comment_content,
                    # 'fullname_content': fullname_content,
                    # 'parts': parts,
                    # 'full_line': line.rstrip(),
                    # 'comment_start_pos': comment_match.start(),
                    # 'comment_end_pos': comment_match.end()
                }

                results.append(result)

    nones = [x for x in results if x['report_name'] == None]

    return results


class TableParser(HTMLParser):
    """
    Custom HTML parser to extract table data from HTML files.
    Tracks when inside a table, row, or cell, and builds a list of rows and cells.
    Use feed_with_line_tracking to parse HTML with line numbers.
    """

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell = ""
        self.current_row = []
        self.table_data = []
        self.table_found = False
        self.table_start_line = None
        self.table_end_line = None
        self.current_line = 1

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'table':
            self.in_table = True
            self.table_found = True
            self.table_start_line = self.current_line
            self.table_data = []
        elif tag.lower() == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag.lower() in ['td', 'th'] and self.in_row:
            self.in_cell = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag.lower() == 'table' and self.in_table:
            self.in_table = False
            self.table_end_line = self.current_line
        elif tag.lower() == 'tr' and self.in_row:
            self.in_row = False
            if self.current_row:  # Only add non-empty rows
                self.table_data.append(self.current_row)
        elif tag.lower() in ['td', 'th'] and self.in_cell:
            self.in_cell = False
            # Clean up cell content
            cell_content = self.current_cell.strip()
            cell_content = re.sub(r'\s+', ' ', cell_content)  # Normalize whitespace
            self.current_row.append(cell_content)

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data

    def feed_with_line_tracking(self, html_content: str):
        """Feed HTML content while tracking line numbers."""
        lines = html_content.split('\n')
        for line_num, line in enumerate(lines, 1):
            self.current_line = line_num
            super().feed(line + '\n')


def find_table_at_line(lines: str, start_line: int) -> Optional[Dict]:
    """
    Find and parse the first HTML <table> tag starting at or after a specific line number.

    Args:
        lines (str or list[str]): HTML file path or list of lines from the file.
        start_line (int): Line number to start searching from (1-based).

    Returns:
        Optional[Dict]: Dictionary with table data, start/end line, raw HTML, row/column count, or None if not found.
    """

    if isinstance(lines, str):
        if os.path.exists(lines):
            lines = read_html_lines(lines)

    # Get content from start_line onwards
    if start_line > len(lines):
        print(f"Start line {start_line} exceeds file length ({len(lines)} lines)")
        return None

    # Join lines from start_line onwards (convert to 0-based index)
    content_from_line = '\n'.join(lines[start_line - 1:])

    # Find the first table tag
    table_match = re.search(r'<table\b[^>]*>.*?</table>', content_from_line, re.DOTALL | re.IGNORECASE)

    if not table_match:
        print(f"No table found starting from line {start_line}")
        return None

    # Extract the table HTML
    table_html = table_match.group(0)

    # Calculate actual line numbers
    lines_before_table = content_from_line[:table_match.start()].count('\n')
    actual_start_line = start_line + lines_before_table

    lines_in_table = table_html.count('\n')
    actual_end_line = actual_start_line + lines_in_table

    # Parse the table
    parser = TableParser()
    try:
        parser.feed(table_html)
    except Exception as e:
        print(f"Error parsing table: {e}")
        return None

    return {
        'table_data': parser.table_data,
        'start_line': actual_start_line,
        'end_line': actual_end_line,
        'raw_html': table_html,
        'row_count': len(parser.table_data),
        'column_count': max(len(row) for row in parser.table_data) if parser.table_data else 0
    }


def get_all_table_data(html_file_path: str):
    """
    Extract all tables and their metadata from an HTML file, using FullName comments as anchors.

    Args:
        html_file_path (str): Path to the HTML file.

    Returns:
        list[dict]: List of dictionaries, each with report info and table data.
    """

    html_str = read_html_lines(html_file_path)

    table_names = get_html_report_name_data(html_str)

    table_data = []

    for t in table_names:
        report_for = t['report_for']
        report_name = t['report_name']
        table_name = t['table_name']

        table_obj = find_table_at_line(html_str, t['table_start_line'])
        table_data.append({
            'report_for': report_for,
            'report_name': report_name,
            'table_name': table_name,
            'table_data': table_obj['table_data'],
            'html_file': html_file_path
        })
    return table_data
