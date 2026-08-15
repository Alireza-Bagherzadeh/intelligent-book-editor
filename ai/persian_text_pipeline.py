from collections import Counter
import difflib
from enum import Enum
from functools import lru_cache
import json
import os
import re
import time
from typing import Dict, List, Optional, Set, Tuple
import unicodedata

from pydantic import BaseModel, Field

try:
    from hazm import (
        Lemmatizer,
        Normalizer,
        SentenceTokenizer,
        Stemmer,
        WordTokenizer,
        words_list,
    )
    HAZM_AVAILABLE = True
except ImportError:
    HAZM_AVAILABLE = False

try:
    from symspellpy import SymSpell, Verbosity
    SYMSPELL_AVAILABLE = True
except ImportError:
    SYMSPELL_AVAILABLE = False


# ====================================================================
# 1. PYDANTIC SCHEMAS (Unified Output Models)
# ====================================================================
class ChangeType(str, Enum):
    MECHANICAL_NORM = "MECHANICAL_NORM"  # Mechanical normalization / repeated characters / spacing
    SUGGESTED_FIX = "SUGGESTED_FIX"      # Half-space correction suggestion
    AMBIGUOUS = "AMBIGUOUS"              # Ambiguous compound phrase
    SUSPECT_TYPO = "SUSPECT_TYPO"        # Suspected typographical error


class ContextInfo(BaseModel):
    before: str = Field(default="", description="A few words before the error segment")
    target: str = Field(..., description="Target word or phrase containing the error")
    after: str = Field(default="", description="A few words after the error segment")
    full_context: str = Field(..., description="Full context including before, target, and after segments")


class ChangeLogItemSchema(BaseModel):
    change_type: ChangeType
    category_title: str
    original_segment: str
    modified_segment: str
    start_char: int
    end_char: int
    paragraph_idx: int
    context: Optional[ContextInfo] = Field(
        default=None, description="Textual context for typos and half-spaces"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="List of suggestions (half-space or SymSpell)"
    )
    llm_choice: Optional[str] = Field(
        default=None,
        description="Word selected or corrected by the LLM model in the corresponding node"
    )


class ProcessingResult(BaseModel):
    original_text: str
    corrected_text: str
    total_changes: int
    change_logs: List[ChangeLogItemSchema]


# ====================================================================
# UTILITY: PERSIAN DETOKENIZER
# ====================================================================
class PersianDetokenizer:
    ATTACH_TO_PREVIOUS = {".", "،", "!", "؟", "؛", ":", ")", "»", "]", "}", "…"}
    ATTACH_TO_NEXT = {"(", "«", "[", "{"}

    @classmethod
    def detokenize(cls, tokens: List[str]) -> str:
        if not tokens:
            return ""
        result = []
        for i, token in enumerate(tokens):
            if i == 0:
                result.append(token)
                continue
            prev_token = tokens[i - 1]
            if token in cls.ATTACH_TO_PREVIOUS or prev_token in cls.ATTACH_TO_NEXT:
                result.append(token)
            else:
                result.append(" " + token)
        return "".join(result)


# ====================================================================
# PHASE 0: STRUCTURAL CLEANER
# ====================================================================
TERMINAL_PUNCTUATION = (".", "؟", "?", "!", "؛", "»", '"', ")", "”")
DIALOGUE_PREFIXES = ("—", "–", "-", "«", '"', "“")
HEADING_KEYWORDS = re.compile(
    r"^(فصل|بخش|قسمت|مقدمه|نتیجه‌گیری|گفتار|درس)\s+\S+", re.UNICODE
)


class CleanParagraph(BaseModel):
    text: str
    is_heading: bool = False
    is_dialogue: bool = False
    source_line_indices: List[int] = Field(default_factory=list)


class StructuralCleaner:
    def __init__(self, max_heading_length: int = 40):
        self.max_heading_length = max_heading_length

    def _is_terminal(self, line: str) -> bool:
        line = line.strip()
        return bool(line) and line.endswith(TERMINAL_PUNCTUATION)

    def _is_dialogue(self, line: str) -> bool:
        return line.strip().startswith(DIALOGUE_PREFIXES)

    def _is_heading(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False
        if HEADING_KEYWORDS.match(line):
            return True
        if line.endswith(("،", ",", ":", "؛")):
            return False
        return len(line) <= self.max_heading_length and not self._is_terminal(line)

    def process(self, raw_text: str) -> List[CleanParagraph]:
        lines = raw_text.split("\n")
        paragraphs: List[CleanParagraph] = []
        buffer_lines: List[str] = []
        buffer_indices: List[int] = []

        def flush_buffer():
            nonlocal buffer_lines, buffer_indices
            if not buffer_lines:
                return
            merged_text = " ".join(buffer_lines).strip()
            merged_text = re.sub(r"\s+", " ", merged_text)

            if merged_text:
                first_line = buffer_lines[0].strip()
                is_heading = (len(buffer_lines) == 1) and self._is_heading(first_line)
                is_dialogue = self._is_dialogue(first_line)
                paragraphs.append(
                    CleanParagraph(
                        text=merged_text,
                        is_heading=is_heading,
                        is_dialogue=is_dialogue,
                        source_line_indices=list(buffer_indices),
                    )
                )
            buffer_lines = []
            buffer_indices = []

        for line_index, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                flush_buffer()
                continue
            if not buffer_lines:
                buffer_lines.append(line)
                buffer_indices.append(line_index)
                continue

            prev_line = buffer_lines[-1]
            prev_ends_terminally = self._is_terminal(prev_line)
            curr_is_dialogue = self._is_dialogue(line)

            if curr_is_dialogue or bool(HEADING_KEYWORDS.match(line)) or prev_ends_terminally:
                flush_buffer()
                buffer_lines.append(line)
                buffer_indices.append(line_index)
            else:
                buffer_lines.append(line)
                buffer_indices.append(line_index)

        flush_buffer()
        return paragraphs


# ====================================================================
# PHASE 1: MECHANICAL NORMALIZER
# ====================================================================
class NormalizedParagraph(BaseModel):
    original_text: str
    normalized_text: str
    sentences: List[str] = Field(default_factory=list)
    sentence_tokens: List[List[str]] = Field(default_factory=list)
    is_heading: bool = False
    is_dialogue: bool = False
    opcodes: List[Tuple[str, int, int, int, int]] = Field(default_factory=list)
    mechanical_change_logs: List[ChangeLogItemSchema] = Field(default_factory=list)


class MechanicalNormalizer:
    _hazm_normalizer: Optional["Normalizer"] = None
    _sent_tokenizer: Optional["SentenceTokenizer"] = None
    _word_tokenizer: Optional["WordTokenizer"] = None
    _is_initialized: bool = False

    def __init__(self, fix_numbers: bool = True):
        MechanicalNormalizer._ensure_initialized(fix_numbers)

    @classmethod
    def _ensure_initialized(cls, fix_numbers: bool) -> None:
        if cls._is_initialized:
            return
        if HAZM_AVAILABLE:
            cls._hazm_normalizer = Normalizer(
                persian_style=True,
                persian_numbers=fix_numbers,
                remove_diacritics=True,
            )
            cls._sent_tokenizer = SentenceTokenizer()
            cls._word_tokenizer = WordTokenizer(join_verb_parts=False)
        cls._is_initialized = True

    def _fix_punctuation_spacing(self, text: str) -> str:
        text = re.sub(r"([.،!؟؛:])\s+(?=[.،!؟؛:])", r"\1", text)
        text = re.sub(r"\s*([.،!؟؛:]+)\s*", r"\1 ", text)
        text = re.sub(r"\(\s*(.*?)\s*\)", r"(\1)", text)
        text = re.sub(r"«\s*(.*?)\s*»", r"«\1»", text)
        return re.sub(r"\s+", " ", text).strip()

    def normalize_text(self, raw_text: str) -> str:
        raw_text = re.sub(r"[\xa0\u200b\u202f\u205f\u3000]+", " ", raw_text)
        raw_text = re.sub(r"(?<=[\u0600-\u06FF])_(?=[\u0600-\u06FF])", "\u200c", raw_text)
        if self._hazm_normalizer:
            text = self._hazm_normalizer.normalize(raw_text)
        else:
            text = raw_text
        text = self._fix_punctuation_spacing(text)
        return text

    def _categorize_diff(self, orig_sub: str, norm_sub: str) -> str:
        if "_" in orig_sub and "\u200c" in norm_sub:
            return "Convert underscore (_) to half-space"
        if len(orig_sub) > len(norm_sub) and len(set(orig_sub)) < len(orig_sub):
            return "Fix extra repeated characters"
        if "\u200c" in norm_sub and "\u200c" not in orig_sub:
            return "Half-space correction by Hazm"
        if any(c.isdigit() for c in orig_sub):
            return "Convert numbers/keyboard to Persian"
        if any(c in ".,;!?«»()" for c in orig_sub + norm_sub):
            return "Fix punctuation mark spacing"
        return "General Hazm normalization"

    def process_paragraph(
        self,
        raw_text: str,
        paragraph_idx: int = 1,
        is_heading: bool = False,
        is_dialogue: bool = False,
    ) -> NormalizedParagraph:
        normalized_str = self.normalize_text(raw_text)
        matcher = difflib.SequenceMatcher(None, raw_text, normalized_str)
        opcodes = matcher.get_opcodes()
        change_logs: List[ChangeLogItemSchema] = []

        for tag, i1, i2, j1, j2 in opcodes:
            if tag != "equal":
                orig_sub = raw_text[i1:i2]
                norm_sub = normalized_str[j1:j2]
                category = self._categorize_diff(orig_sub, norm_sub)

                change_logs.append(
                    ChangeLogItemSchema(
                        change_type=ChangeType.MECHANICAL_NORM,
                        category_title=category,
                        original_segment=orig_sub,
                        modified_segment=norm_sub,
                        start_char=i1,
                        end_char=i2,
                        paragraph_idx=paragraph_idx,
                        suggestions=[norm_sub],
                    )
                )

        if self._sent_tokenizer and self._word_tokenizer:
            sentences = self._sent_tokenizer.tokenize(normalized_str)
            sentence_tokens = [self._word_tokenizer.tokenize(sentence) for sentence in sentences]
        else:
            sentences = [normalized_str]
            sentence_tokens = [normalized_str.split()]

        return NormalizedParagraph(
            original_text=raw_text,
            normalized_text=normalized_str,
            sentences=sentences,
            sentence_tokens=sentence_tokens,
            is_heading=is_heading,
            is_dialogue=is_dialogue,
            opcodes=opcodes,
            mechanical_change_logs=change_logs,
        )


# ====================================================================
# PHASE 2: FAST LEXICAL GATEKEEPER
# ====================================================================
class TokenStatus(str, Enum):
    PUNCTUATION_NUM = "PUNCTUATION_NUM"
    FOREIGN_TECH = "FOREIGN_TECH"
    VALID = "VALID"
    AMBIGUOUS = "AMBIGUOUS"
    SUSPECT_TYPO = "SUSPECT_TYPO"
    SUGGESTED_FIX = "SUGGESTED_FIX"


class GatekeeperParagraphOutput(BaseModel):
    original_text: str
    normalized_text: str
    corrected_text: str
    is_heading: bool
    is_dialogue: bool
    all_change_logs: List[ChangeLogItemSchema] = Field(default_factory=list)


class FastLexicalGatekeeper:
    _valid_words_set: Set[str] = set()
    _ambiguous_dict: Dict[str, str] = {}
    _deterministic_dict: Dict[str, str] = {}
    _stemmer: Optional["Stemmer"] = None
    _lemmatizer: Optional["Lemmatizer"] = None
    _is_initialized: bool = False

    PUNCT_SET: Set[str] = frozenset({
        ".", ",", "!", "?", ";", ":", '"', "'", "`", "~", "@", "#", "$", "%", "^", "&", "*",
        "(", ")", "-", "_", "=", "+", "[", "]", "{", "}", "\\", "|", "/", "<", ">",
        "؛", "،", "؟", "«", "»", "٪", "٫", "٬", "٭", "؞", "۔", "﷼", "؋", "ـ", "…",
        "“", "”", "‘", "’", "‹", "›", "„", "‟", "⟨", "⟩", "′", "″",
        "–", "—", "―", "‐", "‑", "‒",
        "•", "◦", "▪", "▫", "★", "☆", "✓", "✔", "✕", "✖", "°", "±", "×", "÷", "≠", "≤", "≥",
        "∞", "§", "¶", "©", "®", "™", "€", "£", "¥", "¢",
    })

    EMAIL_URL_ENG_PATTERN = re.compile(
        r"^(https?://\S+|www\.\S+|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|[a-zA-Z0-9_-]+)$"
    )

    def __init__(
        self,
        deterministic_json_path: str = "deterministic_compounds.json",
        ambiguous_json_path: str = "ambiguous_compounds.json",
        context_window_size: int = 3,
        sym_spell: Optional[object] = None,
    ):
        self.context_window_size = context_window_size
        self.sym_spell = sym_spell
        FastLexicalGatekeeper._ensure_initialized(
            deterministic_json_path, ambiguous_json_path
        )

    @classmethod
    def _ensure_initialized(
        cls, deterministic_json_path: str, ambiguous_json_path: str
    ) -> None:
        if cls._is_initialized:
            return

        hazm_words = words_list() if HAZM_AVAILABLE else []
        cls._valid_words_set = {
            w[0] if isinstance(w, (tuple, list)) else str(w) for w in hazm_words
        }

        if os.path.exists(deterministic_json_path):
            with open(deterministic_json_path, "r", encoding="utf-8") as f:
                cls._deterministic_dict = json.load(f)

        if os.path.exists(ambiguous_json_path):
            with open(ambiguous_json_path, "r", encoding="utf-8") as f:
                cls._ambiguous_dict = json.load(f)

        if HAZM_AVAILABLE:
            cls._stemmer = Stemmer()
            cls._lemmatizer = Lemmatizer()
        cls._is_initialized = True

    @classmethod
    def _cached_stem_check(cls, clean_token: str) -> Optional[str]:
        if not HAZM_AVAILABLE or not cls._stemmer or not cls._lemmatizer:
            return None
        stemmed = cls._stemmer.stem(clean_token)
        if stemmed in cls._valid_words_set:
            return stemmed
        lemmatized = cls._lemmatizer.lemmatize(clean_token)
        clean_lemma = lemmatized.split("#")[-1] if "#" in lemmatized else lemmatized
        if clean_lemma in cls._valid_words_set:
            return clean_lemma
        return None

    @classmethod
    def _is_zwnj_compound_valid(cls, token: str) -> bool:
        if "\u200c" not in token:
            return False
        parts = token.split("\u200c")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part in cls._valid_words_set:
                continue
            if cls._cached_stem_check(part):
                continue
            return False
        return True

    @classmethod
    @lru_cache(maxsize=50000)
    def _evaluate_token_core(
        cls, clean_token: str
    ) -> Tuple[TokenStatus, Optional[str], Optional[str]]:
        if not clean_token:
            return TokenStatus.PUNCTUATION_NUM, None, None

        is_punct_num = True
        for char in clean_token:
            if char.isdigit() or char in cls.PUNCT_SET:
                continue
            if unicodedata.category(char)[0] in ("P", "S", "Z"):
                continue
            is_punct_num = False
            break

        if is_punct_num:
            return TokenStatus.PUNCTUATION_NUM, None, None

        if cls.EMAIL_URL_ENG_PATTERN.match(clean_token):
            return TokenStatus.FOREIGN_TECH, None, None

        if clean_token in cls._deterministic_dict:
            suggested = cls._deterministic_dict[clean_token]
            if clean_token != suggested:
                return TokenStatus.SUGGESTED_FIX, None, suggested

        if clean_token in cls._ambiguous_dict:
            return TokenStatus.AMBIGUOUS, None, cls._ambiguous_dict[clean_token]

        if clean_token in cls._valid_words_set:
            return TokenStatus.VALID, clean_token, None

        matched_root = cls._cached_stem_check(clean_token)
        if matched_root:
            return TokenStatus.VALID, matched_root, None

        if cls._is_zwnj_compound_valid(clean_token):
            return TokenStatus.VALID, clean_token, None

        return TokenStatus.SUSPECT_TYPO, None, None

    def get_spelling_suggestions(self, word: str, max_count: int = 6) -> List[str]:
        if not self.sym_spell or not SYMSPELL_AVAILABLE:
            return []
        try:
            suggestions = self.sym_spell.lookup(
                word,
                Verbosity.ALL,
                max_edit_distance=2
            )

            return [item.term for item in suggestions[:max_count]]

        except Exception as e:
            return []

    def _extract_context(
        self, sentence_tokens: List[str], t_idx: int, ngram_len: int, target_str: str
    ) -> ContextInfo:
        start_before = max(0, t_idx - self.context_window_size)
        before_tokens = sentence_tokens[start_before:t_idx]

        end_after = min(len(sentence_tokens), t_idx + ngram_len + self.context_window_size)
        after_tokens = sentence_tokens[t_idx + ngram_len : end_after]

        before_str = " ".join(before_tokens)
        after_str = " ".join(after_tokens)
        full_ctx = f"{before_str} [{target_str}] {after_str}".strip()

        return ContextInfo(
            before=before_str,
            target=target_str,
            after=after_str,
            full_context=full_ctx,
        )

    def _map_norm_span_to_orig_span(
        self, opcodes: List[Tuple[str, int, int, int, int]], j_start: int, j_end: int
    ) -> Tuple[int, int]:
        i_start, i_end = None, None
        for tag, i1, i2, j1, j2 in opcodes:
            if j1 <= j_start < j2:
                i_start = i1 + (j_start - j1) if tag == "equal" else i1
            if j1 < j_end <= j2:
                i_end = i1 + (j_end - j1) if tag == "equal" else i2

        if i_start is None:
            i_start = 0
        if i_end is None:
            i_end = 0
        return i_start, max(i_start, i_end)

    def process_normalized_paragraph(
        self,
        phase1_output: NormalizedParagraph,
        paragraph_idx: int = 1,
    ) -> GatekeeperParagraphOutput:
        all_logs: List[ChangeLogItemSchema] = list(phase1_output.mechanical_change_logs)
        norm_text = phase1_output.normalized_text
        current_char_search_pos = 0

        corrected_sentences_tokens: List[List[str]] = []

        for sentence_tokens in phase1_output.sentence_tokens:
            corrected_sentence_tokens: List[str] = []
            t_idx = 0
            num_tokens = len(sentence_tokens)

            while t_idx < num_tokens:
                matched_compound = False

                for ngram_len in (3, 2):
                    if t_idx + ngram_len <= num_tokens:
                        candidate = " ".join(sentence_tokens[t_idx : t_idx + ngram_len])
                        if candidate in self._deterministic_dict:
                            suggested = self._deterministic_dict[candidate]

                            j_start = norm_text.find(candidate, current_char_search_pos)
                            if j_start != -1:
                                j_end = j_start + len(candidate)
                                current_char_search_pos = j_end
                                i_start, i_end = self._map_norm_span_to_orig_span(
                                    phase1_output.opcodes, j_start, j_end
                                )
                                orig_str = phase1_output.original_text[i_start:i_end]
                            else:
                                i_start, i_end = 0, 0
                                orig_str = candidate

                            context = self._extract_context(
                                sentence_tokens, t_idx, ngram_len, candidate
                            )

                            all_logs.append(
                                ChangeLogItemSchema(
                                    change_type=ChangeType.SUGGESTED_FIX,
                                    category_title="Half-space correction suggestion",
                                    original_segment=orig_str if orig_str else candidate,
                                    modified_segment=suggested,
                                    start_char=i_start,
                                    end_char=i_end,
                                    paragraph_idx=paragraph_idx,
                                    context=context,
                                    suggestions=[suggested],
                                )
                            )

                            for k in range(ngram_len):
                                corrected_sentence_tokens.append(sentence_tokens[t_idx + k])
                            t_idx += ngram_len
                            matched_compound = True
                            break

                if not matched_compound:
                    token = sentence_tokens[t_idx]
                    clean_token = token.strip()
                    status, matched_root, target_pair = self._evaluate_token_core(clean_token)

                    if status == TokenStatus.SUGGESTED_FIX and target_pair:
                        context = self._extract_context(
                            sentence_tokens, t_idx, 1, clean_token
                        )
                        j_start = norm_text.find(token, current_char_search_pos)
                        if j_start != -1:
                            j_end = j_start + len(token)
                            current_char_search_pos = j_end
                            i_start, i_end = self._map_norm_span_to_orig_span(
                                phase1_output.opcodes, j_start, j_end
                            )
                            orig_str = phase1_output.original_text[i_start:i_end]
                        else:
                            i_start, i_end = 0, 0
                            orig_str = token

                        all_logs.append(
                            ChangeLogItemSchema(
                                change_type=ChangeType.SUGGESTED_FIX,
                                category_title="Half-space correction suggestion",
                                original_segment=orig_str,
                                modified_segment=target_pair,
                                start_char=i_start,
                                end_char=i_end,
                                paragraph_idx=paragraph_idx,
                                context=context,
                                suggestions=[target_pair],
                            )
                        )
                        corrected_sentence_tokens.append(token)

                    elif status == TokenStatus.AMBIGUOUS:
                        context = self._extract_context(
                            sentence_tokens, t_idx, 1, clean_token
                        )
                        j_start = norm_text.find(token, current_char_search_pos)
                        if j_start != -1:
                            j_end = j_start + len(token)
                            current_char_search_pos = j_end
                            i_start, i_end = self._map_norm_span_to_orig_span(
                                phase1_output.opcodes, j_start, j_end
                            )
                            orig_str = phase1_output.original_text[i_start:i_end]
                        else:
                            i_start, i_end = 0, 0
                            orig_str = token

                        all_logs.append(
                            ChangeLogItemSchema(
                                change_type=ChangeType.AMBIGUOUS,
                                category_title="Ambiguous compound",
                                original_segment=orig_str,
                                modified_segment=target_pair or "Requires human review",
                                start_char=i_start,
                                end_char=i_end,
                                paragraph_idx=paragraph_idx,
                                context=context,
                                suggestions=[target_pair] if target_pair else [],
                            )
                        )
                        corrected_sentence_tokens.append(token)

                    elif status == TokenStatus.SUSPECT_TYPO:
                        context = self._extract_context(
                            sentence_tokens, t_idx, 1, clean_token
                        )
                        j_start = norm_text.find(token, current_char_search_pos)
                        if j_start != -1:
                            j_end = j_start + len(token)
                            current_char_search_pos = j_end
                            i_start, i_end = self._map_norm_span_to_orig_span(
                                phase1_output.opcodes, j_start, j_end
                            )
                            orig_str = phase1_output.original_text[i_start:i_end]
                        else:
                            i_start, i_end = 0, 0
                            orig_str = token

                        suggestions_list = self.get_spelling_suggestions(clean_token, max_count=4)
                        best_suggestion = suggestions_list[0] if suggestions_list else "Requires review"

                        all_logs.append(
                            ChangeLogItemSchema(
                                change_type=ChangeType.SUSPECT_TYPO,
                                category_title="Suspected typo",
                                original_segment=orig_str,
                                modified_segment=best_suggestion,
                                start_char=i_start,
                                end_char=i_end,
                                paragraph_idx=paragraph_idx,
                                context=context,
                                suggestions=suggestions_list,
                            )
                        )
                        corrected_sentence_tokens.append(token)

                    else:
                        corrected_sentence_tokens.append(token)

                    t_idx += 1

            corrected_sentences_tokens.append(corrected_sentence_tokens)

        corrected_sentences = [
            PersianDetokenizer.detokenize(tokens) for tokens in corrected_sentences_tokens
        ]
        corrected_paragraph_text = " ".join(corrected_sentences)

        return GatekeeperParagraphOutput(
            original_text=phase1_output.original_text,
            normalized_text=phase1_output.normalized_text,
            corrected_text=corrected_paragraph_text,
            is_heading=phase1_output.is_heading,
            is_dialogue=phase1_output.is_dialogue,
            all_change_logs=all_logs,
        )


# ====================================================================
# MASTER PIPELINE (Process Management and JSON Output)
# ====================================================================
class PersianTextPipeline:
    def __init__(
        self,
        deterministic_json_path: str = "deterministic_compounds.json",
        ambiguous_json_path: str = "ambiguous_compounds.json",
        context_window_size: int = 3,
        sym_spell: Optional[object] = None,
        dictionary_path: str = "persian_dictionary.txt"
    ):
        self.cleaner = StructuralCleaner()
        self.normalizer = MechanicalNormalizer()

        if sym_spell is None and SYMSPELL_AVAILABLE:
            sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

            if not os.path.isabs(dictionary_path):
                base_dir = os.path.dirname(os.path.abspath(__file__))
                abs_dictionary_path = os.path.join(base_dir, dictionary_path)
            else:
                abs_dictionary_path = dictionary_path

            if os.path.exists(abs_dictionary_path):
                success = sym_spell.load_dictionary(abs_dictionary_path, term_index=0, count_index=1, encoding="utf-8")
                if not success:
                    print(f"Warning: Failed to load SymSpell dictionary from {abs_dictionary_path}")
            else:
                print(f"Warning: SymSpell dictionary file not found at {abs_dictionary_path}")

        self.gatekeeper = FastLexicalGatekeeper(
            deterministic_json_path=deterministic_json_path,
            ambiguous_json_path=ambiguous_json_path,
            context_window_size=context_window_size,
            sym_spell=sym_spell,
        )

    def process_text(self, raw_text: str) -> ProcessingResult:
        clean_paragraphs = self.cleaner.process(raw_text)

        all_logs: List[ChangeLogItemSchema] = []
        corrected_paragraphs: List[str] = []

        for idx, para in enumerate(clean_paragraphs, start=1):
            norm_para = self.normalizer.process_paragraph(
                raw_text=para.text,
                paragraph_idx=idx,
                is_heading=para.is_heading,
                is_dialogue=para.is_dialogue,
            )

            gate_para = self.gatekeeper.process_normalized_paragraph(
                phase1_output=norm_para,
                paragraph_idx=idx,
            )

            all_logs.extend(gate_para.all_change_logs)
            corrected_paragraphs.append(gate_para.corrected_text)

        full_corrected_text = "\n\n".join(corrected_paragraphs)

        return ProcessingResult(
            original_text=raw_text,
            corrected_text=full_corrected_text,
            total_changes=len(all_logs),
            change_logs=all_logs,
        )

    def process_and_save_json(
        self, raw_text: str, output_filepath: str
    ) -> ProcessingResult:
        result = self.process_text(raw_text)

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2, ensure_ascii=False))

        return result

    @staticmethod
    def apply_llm_corrections(result: ProcessingResult) -> str:
        """
        Apply LLM-approved replacements (or default values) to the original text
        based on precise character indices (reverse order to preserve index positions).
        """
        para_logs: Dict[int, List[ChangeLogItemSchema]] = {}
        for log in result.change_logs:
            para_logs.setdefault(log.paragraph_idx, []).append(log)

        cleaner = StructuralCleaner()
        paragraphs = cleaner.process(result.original_text)
        final_paragraphs: List[str] = []

        for idx, para in enumerate(paragraphs, start=1):
            p_text = para.text
            logs = para_logs.get(idx, [])

            # Sort descending so replacements do not shift previous indices
            logs_sorted = sorted(
                [l for l in logs if l.start_char is not None and l.end_char is not None],
                key=lambda x: (x.start_char, x.end_char),
                reverse=True
            )

            last_processed_start = len(p_text) + 1

            for log in logs_sorted:
                # Skip invalid overlapping indices
                if log.end_char > last_processed_start:
                    continue

                # Select LLM word if available, otherwise default or original word
                if log.llm_choice is not None:
                    replacement = log.llm_choice
                elif log.change_type == ChangeType.MECHANICAL_NORM:
                    replacement = log.modified_segment
                else:
                    replacement = log.original_segment

                # Slice and replace
                p_text = p_text[:log.start_char] + replacement + p_text[log.end_char:]
                last_processed_start = log.start_char

            final_paragraphs.append(p_text)

        return "\n\n".join(final_paragraphs)