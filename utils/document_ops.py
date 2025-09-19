from __future__ import annotations
from pathlib import Path
from typing import Iterable, List
from fastapi import UploadFile
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
)
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import DocumentPortalException

# -------------------------------
# Supported file extensions
# -------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".pptx", ".csv", ".xlsx", ".md"}


# -------------------------------
# Document Loading Functions
# -------------------------------
def load_documents(paths: Iterable[Path]) -> List[Document]:
    """
    Load documents using the appropriate loader based on file extension.
    
    Args:
        paths (Iterable[Path]): List of file paths.
    
    Returns:
        List[Document]: List of loaded documents.
    
    Raises:
        DocumentPortalException: If any document fails to load.
    """
    docs: List[Document] = []

    try:
        for p in paths:
            ext = p.suffix.lower()

            if ext == ".pdf":
                loader = PyPDFLoader(str(p))
            elif ext == ".docx":
                loader = Docx2txtLoader(str(p))
            elif ext == ".txt":
                loader = TextLoader(str(p), encoding="utf-8")
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(str(p))
            elif ext == ".pptx":
                loader = UnstructuredPowerPointLoader(str(p))
            elif ext == ".csv":
                # Load CSV as plain text (each row treated as text)
                loader = TextLoader(str(p), encoding="utf-8")
            elif ext == ".xlsx":
                loader = UnstructuredExcelLoader(str(p))
            else:
                log.warning("Unsupported extension skipped", path=str(p))
                continue

            # Load documents and append
            docs.extend(loader.load())

        log.info("Documents loaded", count=len(docs))
        return docs

    except Exception as e:
        log.error("Failed loading documents", error=str(e))
        raise DocumentPortalException("Error loading documents", e) from e


# -------------------------------
# Document Concatenation Functions
# -------------------------------
def concat_for_analysis(docs: List[Document]) -> str:
    """
    Concatenate documents for analysis.
    
    Args:
        docs (List[Document]): List of documents.
    
    Returns:
        str: Concatenated string with document sources.
    """
    parts = []

    for d in docs:
        src = d.metadata.get("source") or d.metadata.get("file_path") or "unknown"
        parts.append(f"\n--- SOURCE: {src} ---\n{d.page_content}")

    return "\n".join(parts)


def concat_for_comparison(ref_docs: List[Document], act_docs: List[Document]) -> str:
    """
    Concatenate reference and actual documents for comparison.
    
    Args:
        ref_docs (List[Document]): Reference documents.
        act_docs (List[Document]): Actual documents.
    
    Returns:
        str: Combined string for comparison.
    """
    left = concat_for_analysis(ref_docs)
    right = concat_for_analysis(act_docs)
    return f"<<REFERENCE_DOCUMENTS>>\n{left}\n\n<<ACTUAL_DOCUMENTS>>\n{right}"


# -------------------------------
# File Adapter for FastAPI UploadFile
# -------------------------------
class FastAPIFileAdapter:
    """
    Adapt FastAPI UploadFile to provide `.name` and `.getbuffer()` API.
    """

    def __init__(self, uf: UploadFile):
        self._uf = uf
        self.name = uf.filename

    def read(self) -> bytes:
        """Read the full file content."""
        self._uf.file.seek(0)  # Reset file pointer
        return self._uf.file.read()

    def getbuffer(self) -> bytes:
        """Return file content as bytes (alias for read)."""
        return self.read()


# -------------------------------
# Generalized File Reader via Handler
# -------------------------------
def read_file_via_handler(handler, path: str) -> str:
    """
    Generalized file reading function using a handler.
    
    Supports PDF, DOCX, PPTX, TXT, MD, CSV, XLSX.
    
    Args:
        handler: Object with read methods.
        path (str): Path to the file.
    
    Returns:
        str: File content as text.
    
    Raises:
        RuntimeError: If handler has no suitable read method.
    """
    if hasattr(handler, "read_file"):
        return handler.read_file(path)  # Preferred method
    elif hasattr(handler, "read_pdf"):
        return handler.read_pdf(path)  # Fallback for PDF-only handlers
    elif hasattr(handler, "read_"):
        return handler.read_(path)  # Another fallback
    else:
        raise RuntimeError("Handler does not have a suitable read method.")
