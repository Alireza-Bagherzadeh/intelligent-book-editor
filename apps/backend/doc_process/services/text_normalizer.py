# doc_process/services/text_normalizer.py
from __future__ import annotations

import re


class TextNormalizationService:
    """
    A lightweight text normalizer for Persian documents.
    Handles basic character normalization, half-spaces (ZWNJ), and punctuation.
    """

    ZWNJ = "\u200c"
    PERSIAN_LETTERS = "اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"
    ARABIC_TO_PERSIAN = str.maketrans({
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "هٔ",
        "ة": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
    })

    def normalize(self, text: str) -> str:
        """
        Applies basic cleanups suitable for database indexing and pipeline preparation.
        """
        if not text:
            return ""
        text = self.normalize_letters(text)
        text = self.fix_half_spaces(text)
        text = self.fix_punctuation(text)
        return text.strip()

    def normalize_letters(self, text: str) -> str:
        # Translate Arabic specific characters to standard Persian characters
        text = text.translate(self.ARABIC_TO_PERSIAN)
        # Remove Kashida and standard control characters
        text = text.replace("ـ", "")
        text = text.replace("\u200f", "").replace("\u200e", "")
        text = text.replace("\ufeff", "").replace("\u00a0", " ")
        return text

    def fix_half_spaces(self, text: str) -> str:
        # Collapse spaces around existing ZWNJs
        text = re.sub(rf"\s*{self.ZWNJ}\s*", self.ZWNJ, text)
        
        # Apply ZWNJ for standard Persian prefixes (e.g., mi/nemi)
        text = re.sub(
            rf"(?<![{self.PERSIAN_LETTERS}])(ن?می)\s+([{self.PERSIAN_LETTERS}])",
            rf"\1{self.ZWNJ}\2",
            text,
        )
        
        # Apply ZWNJ for standard Persian suffixes (e.g., plural 'ha', comparison tags)
        text = re.sub(
            rf"([{self.PERSIAN_LETTERS}])\s+(ها|های|هایی|تر|ترین|ای)(?![self.PERSIAN_LETTERS])",
            rf"\1{self.ZWNJ}\2",
            text,
        )
        return text

    def fix_punctuation(self, text: str) -> str:
        # Standardize spaces near punctuation marks
        text = re.sub(r"[ \t]+([،؛؟!,:])", r"\1", text)
        text = re.sub(r"([،؛؟!:])(?=[^\s\n\r،؛؟!,:])", r"\1 ", text)
        text = re.sub(r"\.\s+", ". ", text)
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)
        text = re.sub(r"\s+([»”])", r"\1", text)
        text = re.sub(r"([«“])\s+", r"\1", text)
        text = re.sub(r" {2,}", " ", text)
        return text
