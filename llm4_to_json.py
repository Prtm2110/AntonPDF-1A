#!/usr/bin/env python3
import re
import os
import sys
import json
import argparse
import pymupdf4llm
import glob

def normalize_punctuation(s: str) -> str:
    """
    Convert common unicode punctuation to ASCII equivalents.
    """
    replacements = {
        "‘": "'",  # left single quote
        "’": "'",  # right single quote
        "“": '"',  # left double quote
        "”": '"',  # right double quote
        "–": '-',  # en dash
        "—": '-',  # em dash
        "…": '...',  # ellipsis
    }
    for uni, ascii_rep in replacements.items():
        s = s.replace(uni, ascii_rep)
    return s

def strip_inline_bold(s: str) -> str:
    """
    Remove backticks, bold markers (**...** or _**...**_),
    trailing numeric markers, repeated punctuation runs,
    collapse multiple spaces, and strip.
    """
    s = normalize_punctuation(s)
    s = re.sub(r'`([^`]+)`', r"\1", s)           # Remove backtick code markers
    s = s.replace('`', '')                       # Remove any leftover backticks
    s = re.sub(r'_?\*\*(.*?)\*\*_?', r"\1", s)   # Remove bold markers
    s = re.sub(r'(?:\b)(\d+)$', '', s)           # Remove trailing numeric markers
    s = re.sub(r'[\.\-\,\"\=]{2,}', '', s)       # Remove runs of punctuation
    return ' '.join(s.split()).strip()           # Normalize whitespace

def parse_markdown_outline(md_text: str, page: int):
    outline = []
    for line in md_text.splitlines():
        if re.fullmatch(r"^[\.\-\*,=\"']{2,}\s*$", line.strip()):
            continue  # Skip separators
        stripped = normalize_punctuation(line.strip())

        level = None
        text = None
        if stripped.startswith('# '):
            level = 'H1'
            text = strip_inline_bold(stripped[2:].strip())
        elif stripped.startswith('## '):
            level = 'H1'
            text = strip_inline_bold(stripped[3:].strip())
        elif stripped.startswith('### '):
            level = 'H2'
            text = strip_inline_bold(stripped[4:].strip())
        elif stripped.startswith('#### '):
            level = 'H3'
            text = strip_inline_bold(stripped[5:].strip())
        elif re.fullmatch(r'_?\*\*(.*?)\*\*_?', stripped):
            level = 'H3'
            text = strip_inline_bold(stripped)

        # Filter out anything starting with lowercase
        if text and re.match(r'^[a-z]', text):
            continue

        if level and text:
            outline.append({
                'level': level,
                'text': text,
                'page': page + 1
            })
    return outline

def extract_outline_and_title(md_text):
    title = 'Untitled'
    # Find first non-lowercase H1 as title
    for page in md_text:
        for line in page.get('text', '').splitlines():
            stripped = normalize_punctuation(line.strip())
            if stripped.startswith('# '):
                candidate = strip_inline_bold(stripped[2:].strip())
                if not re.match(r'^[a-z]', candidate):
                    title = candidate
                    break
        if title != 'Untitled':
            break

    result = {'title': title, 'outline': []}
    for i, page in enumerate(md_text):
        items = parse_markdown_outline(page.get('text', ''), i)
        # Include any extra toc_items if present
        for item in page.get('toc_items', []):
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                lvl, txt = item[0], strip_inline_bold(item[1])
                if not re.match(r'^[a-z]', txt) and txt not in {e['text'] for e in items}:
                    level = f'H{lvl if 1 <= lvl <= 3 else 3}'
                    items.append({'level': level, 'text': txt, 'page': i + 1})
        result['outline'].extend(items)
    return result

def extract_outline_from_pdf(file_path):
    md_text = pymupdf4llm.to_markdown(file_path, page_chunks=True)
    return extract_outline_and_title(md_text)

def main():
    parser = argparse.ArgumentParser(
        description="Extract title and outline from a single PDF (handles spaces in path)"
    )
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file (default: stdout)',
        default=None
    )
    parser.add_argument(
        '-all', '--all-pdfs',
        action='store_true',
        help='Process all PDFs from Pdfs directory and save to output_json folder'
    )
    # Capture all remaining args as the PDF path (allows unquoted spaces)
    parser.add_argument(
        'pdf_path',
        nargs='*',  # Changed from REMAINDER to * to make it optional
        help='Path to the PDF file (can include spaces without quoting)'
    )
    args = parser.parse_args()

    if args.all_pdfs:
        # Process all PDFs from Pdfs directory
        pdfs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Pdfs')
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output_json')
        
        if not os.path.exists(pdfs_dir):
            print(f"Error: Pdfs directory '{pdfs_dir}' not found", file=sys.stderr)
            sys.exit(1)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all PDF files
        pdf_files = glob.glob(os.path.join(pdfs_dir, '*.pdf'))
        
        if not pdf_files:
            print(f"Error: No PDF files found in '{pdfs_dir}'", file=sys.stderr)
            sys.exit(1)
        
        print(f"Processing {len(pdf_files)} PDF files...")
        
        for pdf_file in pdf_files:
            try:
                result = extract_outline_from_pdf(pdf_file)
                
                # Create output filename based on PDF filename
                pdf_basename = os.path.splitext(os.path.basename(pdf_file))[0]
                output_file = os.path.join(output_dir, f"{pdf_basename}.json")
                
                with open(output_file, 'w') as out_f:
                    json.dump(result, out_f, indent=2)
                
                print(f"Processed: {os.path.basename(pdf_file)} ➔ {output_file}")
                
            except Exception as e:
                print(f"Error processing '{pdf_file}': {e}", file=sys.stderr)
        
        print(f"All JSON files saved to: {output_dir}")
        return

    if not args.pdf_path:
        print("Error: no PDF path provided", file=sys.stderr)
        sys.exit(1)
    pdf_path = ' '.join(args.pdf_path)

    try:
        result = extract_outline_from_pdf(pdf_path)
        # no longer adding result['source']
    except Exception as e:
        print(f"Error processing '{pdf_path}': {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, 'w') as out_f:
            json.dump(result, out_f, indent=2)
        print(f"Saved JSON ➔ {args.output}")
    else:
        json.dump(result, sys.stdout, indent=2)

if __name__ == '__main__':
    main()
