# PDF Outline Extractor

A Python tool that extracts structured outlines and titles from PDF documents using LLM-based text processing.

## Features

- Extract document titles and hierarchical outlines from PDFs
- Support for multiple heading levels (H1, H2, H3)
- Clean text processing with punctuation normalization
- Both programmatic API and command-line interface
- JSON output format
- Batch processing: Process all PDFs in a directory at once
- Automatic output directory creation for batch operations

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Requirements

- Python 3.10+
- PyMuPDF
- pymupdf4llm

## Usage

### Command Line Interface

#### Process all PDFs in batch:
```bash
python3 llm4_to_json.py -all
```
This will process all PDF files from the `Pdfs/` directory and save individual JSON files to the `output_json/` folder.

#### Save outline to JSON file:
```bash
python llm4_to_json.py -o adobe_outline.json Pdfs/Adobe_60pages.pdf
```

#### Print outline to stdout:
```bash
python llm4_to_json.py Pdfs/Adobe_60pages.pdf
```

#### Handle paths with spaces:
```bash
python llm4_to_json.py -o output.json My Document With Spaces.pdf
```

### Programmatic API

```python
from llm4_to_json import extract_outline_from_pdf

# Extract outline from PDF
result = extract_outline_from_pdf("path/to/your/document.pdf")

# The result contains:
# - title: Document title
# - outline: List of headings with level, text, and page number
print(result['title'])
for item in result['outline']:
    print(f"Page {item['page']}: {item['level']} - {item['text']}")
```

## Output Format

The tool generates JSON output with the following structure:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1: Introduction",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "Overview",
      "page": 2
    }
  ]
}
```

## Command Line Options

- `-all, --all-pdfs`: Process all PDFs from `Pdfs/` directory and save to `output_json/` folder
- `-o, --output`: Specify output JSON file (default: stdout)
- `pdf_path`: Path to the PDF file (supports spaces without quotes)

## Examples

### Single File Processing
```bash
# Process a single PDF and print to stdout
python llm4_to_json.py Pdfs/1.pdf

# Process a single PDF and save to file
python llm4_to_json.py -o my_output.json Pdfs/1.pdf
```

### Batch Processing
```bash
# Process all PDFs in Pdfs/ directory
python llm4_to_json.py -all

# This will create:
# output_json/1.json
# output_json/2.json
# output_json/3.json
# output_json/4.json
# output_json/5.json
```

The `Pdfs/` directory contains sample PDF files for testing:
- Various numbered PDFs (1.pdf, 2.pdf, 3.pdf, 4.pdf, 5.pdf)
