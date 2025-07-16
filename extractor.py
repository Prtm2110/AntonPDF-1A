import fitz  # PyMuPDF
import json
from typing import List, Dict, Any

class PDFOutlineExtractor:
    """
    Extracts a structured outline (Title and headings H1, H2, H3) from a PDF document.

    Usage:
        extractor = PDFOutlineExtractor("path/to/file.pdf")
        outline_data = extractor.run()
        # outline_data is a dict: {"title": ..., "outline": [...]}
    """
    def __init__(self, pdf_path: str, max_levels: int = 3):
        self.pdf_path = pdf_path
        self.max_levels = max_levels
        self.doc = None

    def open(self) -> None:
        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            raise IOError(f"Cannot open PDF file: {e}")

    def extract_spans(self) -> List[Dict[str, Any]]:
        """
        Iterate over pages and collect all text spans with their font sizes.
        Returns a list of dicts: [{'page': int, 'size': float, 'text': str}, ...]
        """
        spans: List[Dict[str, Any]] = []
        for page_num, page in enumerate(self.doc, start=1):
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", '').strip()
                        size = span.get("size", 0)
                        if text:
                            spans.append({
                                "page": page_num,
                                "size": size,
                                "text": text
                            })
        return spans

    def assign_headings(self, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determine unique font sizes and map the largest sizes to heading levels h1... up to max_levels.
        Annotate spans with 'level': 'h1', 'h2', etc.
        """
        unique_sizes = sorted({s['size'] for s in spans}, reverse=True)
        heading_sizes = unique_sizes[: self.max_levels]
        size_to_level = {size: f"h{i+1}" for i, size in enumerate(heading_sizes)}

        headings = [
            {**span, 'level': size_to_level[span['size']]} 
            for span in spans if span['size'] in size_to_level
        ]
        return headings

    def build_outline(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Constructs outline dict with document title and ordered list of headings.
        Title is taken as the span with the largest font size on the first page.
        """
        page1_headings = [h for h in headings if h['page'] == 1]
        title_span = max(page1_headings, key=lambda h: h['size'], default=None)
        title = title_span['text'] if title_span else ''

        level_order = {f"h{i+1}": i for i in range(self.max_levels)}
        outline_list = sorted(
            headings,
            key=lambda h: (h['page'], level_order[h['level']], -h['size'])
        )

        outline = []
        for h in outline_list:
            outline.append({
                'level': h['level'].upper(),
                'text': h['text'],
                'page': h['page']
            })

        return {'title': title, 'outline': outline}

    def run(self) -> Dict[str, Any]:
        """
        Full pipeline: open PDF, extract spans, assign headings, build and return outline dict.
        """
        self.open()
        spans = self.extract_spans()
        headings = self.assign_headings(spans)
        outline_data = self.build_outline(headings)
        return outline_data

# Example usage (not part of a CLI):
# extractor = PDFOutlineExtractor("my_document.pdf")
# outline = extractor.run()
# with open("outline.json", "w", encoding="utf-8") as f:
#     json.dump(outline, f, ensure_ascii=False, indent=2)
