# v3 working
import re
import json

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
    Remove all occurrences of **...** or _**...**_ anywhere in the string,
    including trailing numeric markers. Then remove repeated punctuation runs,
    collapse multiple spaces and strip.
    """
    s = normalize_punctuation(s)
    # Remove bold markers
    s = re.sub(r'_?\*\*(.*?)\*\*_?', r"\1", s)
    # Remove trailing numeric markers
    s = re.sub(r'(?:\b)(\d+)$', '', s)
    # Remove any runs of 2 or more repeated punctuation characters
    s = re.sub(r'[\.\-\,\"\=]{2,}', '', s)
    # Normalize whitespace
    return ' '.join(s.split()).strip()


def parse_markdown_outline(md_text, page):
    outline = []
    for line in md_text.splitlines():
        # Skip separator lines
        if re.fullmatch(r"^[\.\-\*,=\"']{2,}\s*$", line.strip()):
            continue
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

        if level and text:
            outline.append({
                'level': level,
                'text': text,
                'page': page + 1
            })

    return outline


def extract_outline_and_title(md_text):
    title = 'Untitled'
    # Find first H1 as title
    for page in md_text:
        for line in page['text'].splitlines():
            stripped = normalize_punctuation(line.strip())
            if stripped.startswith('# '):
                title = strip_inline_bold(stripped[2:].strip())
                break
        if title != 'Untitled':
            break

    result = {'title': title, 'outline': []}
    for i, page in enumerate(md_text):
        result['outline'].extend(parse_markdown_outline(page['text'], i))
    return result

# Example usage:
print(json.dumps(extract_outline_and_title(md_text), indent=2))
