import os
import json
from openai import OpenAI
from pageindex.utils import get_text_of_pages
from lang_chain.pageindex_indexer import load_index

# Supports both OpenAI and Gemini (via OpenAI-compatible endpoint).
# Set OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
# and GEMINI_KEY=<your-key> in .env to use Gemini.
_api_key = os.getenv("GEMINI_KEY") or os.getenv("OPENAI_API_KEY")
_base_url = os.getenv("OPENAI_BASE_URL") or None   # None → uses OpenAI default

client = OpenAI(api_key=_api_key, base_url=_base_url)

# Model used for both tree navigation and answer generation.
# For Gemini set CHAT_MODEL=gemini-2.0-flash in .env
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")


# ---------------------------------------------------------------------------
# Tree formatting
# ---------------------------------------------------------------------------

def _format_node(node: dict, indent: int = 0) -> str:
    prefix = "  " * indent
    summary = node.get("summary", "")
    if len(summary) > 160:
        summary = summary[:160] + "..."
    line = (
        f"{prefix}[{node['node_id']}] {node['title']} "
        f"(pages {node['start_index']}–{node['end_index']})"
    )
    if summary:
        line += f"\n{prefix}    ↳ {summary}"
    for child in node.get("nodes", []):
        line += "\n" + _format_node(child, indent + 1)
    return line


def _format_tree_as_toc(tree: dict) -> str:
    structure = tree.get("structure", [])
    if isinstance(structure, dict):
        structure = [structure]
    return "\n".join(_format_node(n) for n in structure)


def _find_node(structure, node_id: str) -> dict | None:
    nodes = structure if isinstance(structure, list) else [structure]
    for node in nodes:
        if node.get("node_id") == node_id:
            return node
        found = _find_node(node.get("nodes", []), node_id)
        if found:
            return found
    return None


def _extract_text_for_nodes(pdf_path: str, node_ids: list[str], tree: dict) -> str:
    """Extract raw page text for the given node IDs from the PDF."""
    structure = tree.get("structure", [])
    texts = []
    seen = set()

    for nid in node_ids:
        node = _find_node(structure, nid)
        if not node:
            print(f"Node '{nid}' not found — skipping")
            continue

        start, end = node["start_index"], node["end_index"]
        if (start, end) in seen:
            continue
        seen.add((start, end))

        try:
            text = get_text_of_pages(pdf_path, start, end)
            texts.append(f"### {node['title']} (pages {start}–{end})\n\n{text}")
        except Exception as e:
            print(f"Could not extract pages {start}–{end}: {e}")

    return "\n\n---\n\n".join(texts)


# ---------------------------------------------------------------------------
# Public query function
# ---------------------------------------------------------------------------

def chat_with_pageindex(
    user_input: str,
    filename: str,
    history: list[dict],
) -> tuple[str, list[dict]]:
    """
    Two-step vectorless RAG using the self-hosted PageIndex tree:

    Step 1 — Navigation:  LLM reads the document TOC (with summaries) and
                          identifies the most relevant section node IDs.
    Step 2 — Answer:      Extract raw page text for those sections and let
                          the LLM answer using the extracted text + full history.

    No embeddings, no Qdrant, no cloud API key — only OpenAI + the local tree.

    Returns (reply, updated_history).
    """
    tree, pdf_path = load_index(filename)
    doc_name = tree.get("doc_name", filename)
    toc_str = _format_tree_as_toc(tree)

    # ------------------------------------------------------------------
    # Step 1: Tree Navigation — LLM picks relevant sections
    # ------------------------------------------------------------------
    nav_response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a document navigation assistant. "
                    "Given a document's table of contents (with page ranges and section summaries), "
                    "identify the most relevant section node_ids for the user's query. "
                    "Return ONLY a valid JSON object: {\"node_ids\": [\"0001\", \"0003\"]}. "
                    "Choose 1–4 specific sections. Prefer depth over breadth."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Document: {doc_name}\n\n"
                    f"Table of Contents:\n{toc_str}\n\n"
                    f"Query: {user_input}"
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    try:
        nav_result = json.loads(nav_response.choices[0].message.content)
        node_ids: list[str] = nav_result.get("node_ids", [])
    except Exception as e:
        print(f"Navigation parse error: {e} — using empty selection")
        node_ids = []

    print(f"PageIndex selected nodes: {node_ids}")

    # ------------------------------------------------------------------
    # Step 2: Extract page text + Generate answer
    # ------------------------------------------------------------------
    extracted_text = _extract_text_for_nodes(pdf_path, node_ids, tree)

    # Fallback: use TOC summaries if no text could be extracted
    if not extracted_text:
        print("No page text extracted — falling back to TOC summaries")
        extracted_text = f"Document structure and summaries:\n{toc_str}"

    system_msg = (
        f"You are an expert AI assistant helping users understand '{doc_name}'. "
        f"Answer the user's question based only on the document context below. "
        f"Be concise and accurate. Cite section names or page numbers when relevant.\n\n"
        f"<document_context>\n{extracted_text}\n</document_context>"
    )

    answer_messages = [{"role": "system", "content": system_msg}]
    answer_messages.extend(history)
    answer_messages.append({"role": "user", "content": user_input})

    answer_response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=answer_messages,
        temperature=0.3,
    )

    reply = answer_response.choices[0].message.content or ""

    updated_history = history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": reply},
    ]

    return reply, updated_history
