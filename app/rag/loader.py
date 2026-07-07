# app/rag/loader.py
import os
from typing import List
from PyPDF2 import PdfReader

class DocumentLoader:
    @staticmethod
    def load(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".txt" or ext == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        else:
            raise ValueError(f"Unsupported file type: {ext}")