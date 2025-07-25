import re
import json

def parse_markdown_outline(md_text, page):
    """
    Parses one page of markdown and returns:
      {
        "outline": [
          {"level": "H1", "text": "...", "page": <1-based>},
          …
        ]
      }
    - First '# ' → H1
    - '## ' → H1
    - '### ' → H2
    - '#### ' → H3
    - full-line **bold** or _**bold**_ → H3
    - strips surrounding **…** or _**…**_
    """
    def strip_bold(s: str) -> str:
        return re.sub(r'^_?\*\*(.*?)\*\*_?$', r'\1', s).strip()

    outline = []

    for line in md_text.splitlines():
        stripped = line.strip()
        level = None
        text  = None

        if stripped.startswith('# '):
            text = strip_bold(stripped[2:].strip())
            level = "H1"

        elif stripped.startswith('## '):
            text = strip_bold(stripped[3:].strip())
            level = "H1"

        elif stripped.startswith('### '):
            text = strip_bold(stripped[4:].strip())
            level = "H2"

        elif stripped.startswith('#### '):
            text = strip_bold(stripped[5:].strip())
            level = "H3"

        # full-line **…** or _**…**_ 
        elif re.fullmatch(r'_?\*\*(.*?)\*\*_?', stripped):
            text = strip_bold(stripped)
            level = "H3"

        if level and text:
            outline.append({
                "level": level,
                "text":  text,
                "page":  page + 1
            })

    return outline

# Extract title from the first page with '# ' heading
title = "Untitled"
for page in md_text:
    for line in page['text'].splitlines():
        stripped = line.strip()
        if stripped.startswith('# '):
            # Remove markdown bold if present
            title = re.sub(r'^_?\*\*(.*?)\*\*_?$', r'\1', stripped[2:].strip())
            break
    if title != "Untitled":
        break

result = {}
result["outline"] = []
for page_no in range(len(md_text)):
    result["outline"].extend(parse_markdown_outline(md_text[page_no]['text'], page_no))

result["title"] = title
print(json.dumps(result, indent=2))
