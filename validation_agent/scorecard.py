# -*- coding: utf-8 -*-
from typing import Dict, List
from .section_parser import split_sections, word_count, has_markdown_or_html

def compute_score(text: str, profile: dict) -> Dict:
    prof = profile["profile"]
    glob = profile["global"]
    min_words = prof.get("min_words_per_section", 0)
    sections_cfg = prof["sections"]
    expected_titles = [x["title"] for x in sections_cfg]

    # формат
    critical_broken = has_markdown_or_html(text)

    sections_found = split_sections(text, expected_titles)
    score = 0.0
    breakdown = []

    # секции: присутствие и качество
    for sec in sections_cfg:
        title = sec["title"]
        presence = sec.get("presence", 0.0)
        quality = sec.get("quality", 0.0)
        body = sections_found.get(title, "")
        present_ok = 1.0 if body else 0.0
        quality_ok = 1.0 if (body and word_count(body) >= min_words) else 0.0
        pts = presence * present_ok + quality * quality_ok
        score += pts
        breakdown.append({
            "section": title,
            "present": bool(present_ok),
            "quality_ok": bool(quality_ok),
            "words": word_count(body) if body else 0,
            "points": pts
        })

    # extra критерии
    extra_pts = 0.0
    extras = prof.get("extra", {})
    if extras.get("known_companies") and "🏢" in "".join(sections_found.keys()):
        extra_pts += extras["known_companies"]
    if extras.get("industry_binding"):
        # эвристика: в тексте встречается слово "отрасл" или упоминание конкретной отрасли от бизнес-контекста
        if "отрасл" in text.lower():
            extra_pts += extras["industry_binding"]
    if extras.get("status_binding"):
        # для совместимости: ищем ключевые слова статуса
        if any(w in text.lower() for w in ["сотрудник", "партнер", "контрагент", "контрагентом"]):
            extra_pts += extras["status_binding"]
    if extras.get("news_2_2_2"):
        # примитивная проверка: найдены три блока "Политика", "Экономика", "Фондовый рынок"
        key_ok = all(k in text for k in ["Политика:", "Экономика:", "Фондовый рынок:"])
        if key_ok:
            extra_pts += extras["news_2_2_2"]

    score += extra_pts

    # global критерии
    global_pts = 0.0
    tone_points = glob.get("tone_professional", {}).get("points", 0.0)
    fmt_points = glob.get("formatting_headers", {}).get("points", 0.0)
    if fmt_points:
        # считая, что наличие ожидаемых заголовков уже даёт очки
        global_pts += fmt_points
    if tone_points:
        # упрощённо: если нет просторечных оборотов — даём очки (эвристика)
        if not any(w in text.lower() for w in ["эээ", "ну", "типа"]):
            global_pts += tone_points

    # критический критерий
    if glob.get("no_markdown_html", {}).get("critical", False) and has_markdown_or_html(text):
        # критический провал — можно жёстко занулить
        final = max(0.0, score + global_pts - 5.0)
        return {
            "score": round(final, 2),
            "critical": True,
            "reason": "Обнаружены HTML/Markdown конструкции",
            "breakdown": breakdown,
            "extras": round(extra_pts, 2),
            "global": round(global_pts, 2)
        }

    final = round(score + global_pts, 2)
    return {
        "score": final,
        "critical": False,
        "breakdown": breakdown,
        "extras": round(extra_pts, 2),
        "global": round(global_pts, 2)
    }
