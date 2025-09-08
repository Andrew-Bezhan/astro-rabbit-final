# -*- coding: utf-8 -*-
import re
from typing import Dict, List

def split_sections(text: str, expected_titles: List[str]) -> Dict[str, str]:
    # режем по точному совпадению строки заголовка
    sections, current, buf = {}, None, []
    lines = text.splitlines()
    titles = set(t.strip() for t in expected_titles)
    for ln in lines:
        if ln.strip() in titles:
            if current:
                sections[current] = "\n".join(buf).strip()
                buf = []
            current = ln.strip()
        else:
            if current:
                buf.append(ln)
    if current:
        sections[current] = "\n".join(buf).strip()
    return sections

def word_count(s: str) -> int:
    return len(re.findall(r"\w+", s, flags=re.UNICODE))

def has_markdown_or_html(s: str) -> bool:
    if re.search(r"[#*_`]{1,}", s): return True
    if re.search(r"<[^>]+>", s): return True
    return False
