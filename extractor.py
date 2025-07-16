import fitz  # PyMuPDF
import json
from typing import List, Dict, Any
from multiprocessing import Pool, cpu_count

# Global PDF document handle for worker processes
doc = None

def _init_worker(pdf_path: str):
    """
    Worker initializer: opens the PDF once per process.
    
    This function is called once for each worker process in the multiprocessing pool.
    It opens the PDF document and stores it in a global variable to avoid reopening
    the same PDF multiple times within each worker process.
    
    Args:
        pdf_path (str): Path to the PDF file to be opened
    """
    global doc
    doc = fitz.open(pdf_path)


def _extract_spans_for_range(page_range: tuple) -> List[Dict[str, Any]]:
    """
    Extract spans for a contiguous range of pages to reduce IPC overhead.
    
    This function processes a range of PDF pages and extracts text spans from each page.
    It's designed to work with multiprocessing to efficiently process large PDFs by
    reducing inter-process communication overhead.
    
    Args:
        page_range (tuple): A tuple containing (start_page, end_page) where both are inclusive
    
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing span information with keys:
            - page (int): Page number where the span was found
            - size (float): Font size of the text span
            - text (str): The actual text content of the span
    """
    start_page, end_page = page_range
    spans: List[Dict[str, Any]] = []
    for page_num in range(start_page, end_page + 1):
        try:
            page = doc.load_page(page_num - 1)
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
        except Exception:
            continue
    return spans

class PDFOutlineExtractor:
    """
    Extracts an outline by parallel extraction of page ranges to minimize task overhead.
    
    This class provides functionality to extract document outline/table of contents
    from PDF files by analyzing text spans and their font sizes to identify headings.
    It uses multiprocessing for efficient processing of large PDF files.
    
    Attributes:
        pdf_path (str): Path to the PDF file
        max_levels (int): Maximum number of heading levels to extract
        doc: PyMuPDF document object
    """
    def __init__(self, pdf_path: str, max_levels: int = 3):
        """
        Initialize the PDF outline extractor.
        
        Args:
            pdf_path (str): Path to the PDF file to process
            max_levels (int, optional): Maximum number of heading levels to extract. Defaults to 3.
        """
        self.pdf_path = pdf_path
        self.max_levels = max_levels
        self.doc = fitz.open(pdf_path)

    def extract_spans(self) -> List[Dict[str, Any]]:
        """
        Distribute page ranges across processes instead of individual pages.
        
        This method divides the PDF into chunks and processes them in parallel using
        multiprocessing to extract text spans from all pages efficiently.
        
        Returns:
            List[Dict[str, Any]]: A list of text spans with their metadata including
                page number, font size, and text content
        """
        num_pages = self.doc.page_count
        self.doc.close()

        num_workers = cpu_count()
        # Determine chunk sizes for each worker
        chunk_size = (num_pages + num_workers - 1) // num_workers
        ranges = []
        for i in range(num_workers):
            start = i * chunk_size + 1
            end = min((i + 1) * chunk_size, num_pages)
            if start <= end:
                ranges.append((start, end))

        # Parallel extraction
        with Pool(processes=num_workers, initializer=_init_worker, initargs=(self.pdf_path,)) as pool:
            results = pool.map(_extract_spans_for_range, ranges)

        # Flatten results
        spans = [span for chunk in results for span in chunk]
        return spans

    def assign_headings(self, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map the top font sizes to heading levels.
        
        This method analyzes the font sizes of all text spans and assigns heading levels
        (h1, h2, h3, etc.) to the largest font sizes, which typically correspond to headings.
        
        Args:
            spans (List[Dict[str, Any]]): List of text spans with their metadata
            
        Returns:
            List[Dict[str, Any]]: List of headings with assigned levels, containing only
                spans that correspond to the top font sizes up to max_levels
        """
        unique_sizes = sorted({s['size'] for s in spans}, reverse=True)
        heading_sizes = unique_sizes[: self.max_levels]
        size_to_level = {size: f"h{i+1}" for i, size in enumerate(heading_sizes)}
        # Fix variable naming: use 's' consistently
        return [ {**s, 'level': size_to_level[s['size']]} for s in spans if s['size'] in size_to_level ]

    def build_outline(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build the final outline structure from identified headings.
        
        This method creates a structured outline by:
        1. Extracting the document title from the largest text on page 1
        2. Sorting headings by page number, then by heading level, then by font size
        3. Creating a formatted outline with uppercase level indicators
        
        Args:
            headings (List[Dict[str, Any]]): List of identified headings with levels
            
        Returns:
            Dict[str, Any]: Dictionary containing:
                - title (str): Document title extracted from page 1
                - outline (List[Dict]): Ordered list of headings with level, text, and page
        """
        page1 = [h for h in headings if h['page'] == 1]
        title = max(page1, key=lambda h: h['size'], default={'text': ''})['text']
        order = {f"h{i+1}": i for i in range(self.max_levels)}
        sorted_h = sorted(headings, key=lambda h: (h['page'], order[h['level']], -h['size']))
        outline = [ {'level': h['level'].upper(), 'text': h['text'], 'page': h['page']} for h in sorted_h ]
        return {'title': title, 'outline': outline}

    def run(self) -> Dict[str, Any]:
        """
        Execute the complete outline extraction process.
        
        This is the main method that orchestrates the entire outline extraction workflow:
        1. Extract text spans from all PDF pages
        2. Identify and assign heading levels based on font sizes
        3. Build the final structured outline
        
        Returns:
            Dict[str, Any]: Complete outline structure with title and hierarchical headings
        """
        spans = self.extract_spans()
        headings = self.assign_headings(spans)
        return self.build_outline(headings)

if __name__ == "__main__":
    extractor = PDFOutlineExtractor("merged150mb.pdf")
    outline = extractor.run()
    with open("outline.json", "w", encoding="utf-8") as f:
        json.dump(outline, f, ensure_ascii=False, indent=2)
