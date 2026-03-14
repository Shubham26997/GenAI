import os
import json
import shutil

# page_index_main and config come from the open-source PageIndex repo
# cloned to /pageindex_src and added to PYTHONPATH in Dockerfile.
# Uses CHATGPT_API_KEY env var (same value as OPENAI_API_KEY) — no cloud API key needed.
from pageindex import page_index_main
from pageindex.utils import ConfigLoader

STORE_DIR = os.getenv("PAGEINDEX_STORE_DIR", "pageindex_store")

_config_loader = ConfigLoader()
_opt = _config_loader.load()  # loads defaults from config.yaml


# ---------------------------------------------------------------------------
# Non-PDF → PDF conversion helpers
# ---------------------------------------------------------------------------

def _extract_raw_text(file_path: str) -> str:
    """Extract all text content from any supported file type."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".xlsx", ".xls"):
        import pandas as pd
        xl = pd.ExcelFile(file_path)
        parts = []
        for sheet in xl.sheet_names:
            df = xl.parse(sheet).fillna("")
            parts.append(f"=== Sheet: {sheet} ===\n{df.to_string(index=False)}")
        return "\n\n".join(parts)

    if ext == ".csv":
        import pandas as pd
        df = pd.read_csv(file_path).fillna("")
        return df.to_string(index=False)

    if ext == ".docx":
        import docx2txt
        return docx2txt.process(file_path) or ""

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    raise ValueError(f"Cannot extract text from unsupported type: '{ext}'")


def _text_to_pdf(text: str, output_path: str) -> None:
    """
    Write arbitrary text as a paginated PDF using reportlab (Courier 9 pt).
    Each page holds ~57 wrapped lines — this gives PageIndex meaningful
    page boundaries to build its tree against.
    """
    from reportlab.pdfgen import canvas as rl_canvas

    c = rl_canvas.Canvas(output_path)
    c.setFont("Courier", 9)

    MARGIN_X = 40
    MARGIN_TOP = 780
    MARGIN_BOTTOM = 40
    LINE_HEIGHT = 13
    MAX_CHARS = 95
    LINES_PER_PAGE = int((MARGIN_TOP - MARGIN_BOTTOM) / LINE_HEIGHT)  # ~57

    # Expand raw text into display lines with word-wrap
    display_lines: list[str] = []
    for raw in text.split("\n"):
        # Strip non-Latin-1 characters that Courier can't encode
        raw = raw.encode("latin-1", errors="replace").decode("latin-1")
        if not raw:
            display_lines.append("")
            continue
        while len(raw) > MAX_CHARS:
            split_at = raw.rfind(" ", 0, MAX_CHARS)
            if split_at <= 0:
                split_at = MAX_CHARS
            display_lines.append(raw[:split_at])
            raw = raw[split_at:].lstrip()
        display_lines.append(raw)

    if not display_lines:
        display_lines = ["(empty document)"]

    for page_start in range(0, len(display_lines), LINES_PER_PAGE):
        y = MARGIN_TOP
        for line in display_lines[page_start: page_start + LINES_PER_PAGE]:
            c.drawString(MARGIN_X, y, line)
            y -= LINE_HEIGHT
        c.showPage()

    c.save()


def _prepare_pdf(file_path: str, doc_dir: str) -> str:
    """
    Copy / convert the source file into doc_dir as document.pdf.
    Returns the path to the stored PDF.
    """
    stored_pdf = os.path.join(doc_dir, "document.pdf")
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        shutil.copy2(file_path, stored_pdf)
    else:
        print(f"Converting '{os.path.basename(file_path)}' → PDF for PageIndex...")
        text = _extract_raw_text(file_path)
        _text_to_pdf(text, stored_pdf)
        print(f"Conversion done ({len(text):,} chars).")

    return stored_pdf


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_index(file_path: str, filename: str) -> dict:
    """
    Build a PageIndex tree for any supported file type.
    Non-PDF files are converted to a paginated PDF first, then processed
    identically to a native PDF — no change to the query path.

    Returns the tree structure dict.
    """
    doc_dir = os.path.join(STORE_DIR, filename)
    os.makedirs(doc_dir, exist_ok=True)

    stored_pdf = _prepare_pdf(file_path, doc_dir)

    print(f"Building PageIndex tree for '{filename}'...")
    tree = page_index_main(stored_pdf, _opt)

    index_path = os.path.join(doc_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)

    print(f"Tree saved → {index_path}")
    return tree


def load_index(filename: str) -> tuple[dict, str]:
    """
    Load the saved tree and return (tree_dict, pdf_path).
    Raises FileNotFoundError if the document has not been indexed yet.
    """
    doc_dir = os.path.join(STORE_DIR, filename)
    index_path = os.path.join(doc_dir, "index.json")
    pdf_path = os.path.join(doc_dir, "document.pdf")

    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"No PageIndex found for '{filename}'. Upload the file first."
        )

    with open(index_path, "r", encoding="utf-8") as f:
        tree = json.load(f)

    return tree, pdf_path


def index_exists(filename: str) -> bool:
    doc_dir = os.path.join(STORE_DIR, filename)
    return os.path.exists(os.path.join(doc_dir, "index.json"))
