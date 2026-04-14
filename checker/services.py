import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urlparse
from urllib.request import Request, urlopen

from django.conf import settings


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

PEOPLE_HINTS = (
    "singer",
    "ca si",
    "musician",
    "rapper",
    "actor",
    "actress",
    "artist",
    "born",
    "sinh nam",
    "footballer",
    "politician",
    "president",
    "prime minister",
    "celebrity",
    "personality",
    "songwriter",
)

TRADEMARK_KEYWORDS = (
    "trademark",
    "registered trademark",
    "brand",
    "company",
    "product",
    "service",
    "official site",
    "app",
    "platform",
    "store",
    "software",
    "logo",
    "retail",
    "manufacturer",
)

POD_RELEVANT_TRADEMARK_CLASSES = {
    16: "poster, lịch, ấn phẩm giấy",
    21: "cốc, ly, đồ gia dụng",
    25: "áo thun, hoodie, sweater, quần áo",
}

POLITICAL_KEYWORDS = (
    "president",
    "prime minister",
    "government",
    "politician",
    "election",
    "campaign",
    "congress",
    "senate",
    "trump",
    "biden",
    "obama",
    "maga",
    "đảng",
    "chính trị",
    "nhà nước",
    "quốc hội",
)

FICTIONAL_CONTEXT_HINTS = (
    "harry potter",
    "hogwarts",
    "wizard",
    "witchcraft",
    "fictional",
    "franchise",
    "character",
    "novel",
    "film",
    "movie",
    "magic",
    "fantasy",
)

FAMOUS_BRAND_KEYWORDS = (
    "coca cola",
    "coca-cola",
    "disney",
    "pikachu",
    "pokemon",
    "marvel",
    "avengers",
    "nike",
    "adidas",
    "gucci",
    "louis vuitton",
    "hello kitty",
    "mcdonald",
    "apple",
    "samsung",
    "spotify",
    "netflix",
    "google",
    "youtube",
    "tiktok",
)

FAMOUS_SLOGANS = {
    "just do it": "Nike",
    "i'm lovin' it": "McDonald's",
    "im lovin it": "McDonald's",
    "think different": "Apple",
    "because you're worth it": "L'Oreal",
}

FAMOUS_PERSON_DISPLAY = {
    "donald trump": "Donald Trump",
    "trump": "Donald Trump",
    "taylor swift": "Taylor Swift",
    "drake": "Drake",
    "eminem": "Eminem",
    "rihanna": "Rihanna",
    "beyonce": "Beyonce",
    "justin bieber": "Justin Bieber",
    "messi": "Lionel Messi",
    "lionel messi": "Lionel Messi",
    "ronaldo": "Cristiano Ronaldo",
    "cristiano ronaldo": "Cristiano Ronaldo",
    "neymar": "Neymar",
    "lebron james": "LeBron James",
    "michael jordan": "Michael Jordan",
    "kobe bryant": "Kobe Bryant",
    "bts": "BTS",
    "blackpink": "BLACKPINK",
    "newjeans": "NewJeans",
    "ive": "IVE",
    "twice": "TWICE",
    "exo": "EXO",
    "seventeen": "SEVENTEEN",
}

FAMOUS_PERSON_KEYWORDS = (
    "bts",
    "blackpink",
    "newjeans",
    "ive",
    "twice",
    "exo",
    "seventeen",
    "donald trump",
    "trump",
    "taylor swift",
    "drake",
    "eminem",
    "rihanna",
    "beyonce",
    "justin bieber",
    "messi",
    "ronaldo",
    "neymar",
    "lebron james",
    "michael jordan",
    "kobe bryant",
    "lionel messi",
    "cristiano ronaldo",
)

IP_BRAND_HINTS = (
    "franchise",
    "character",
    "fictional character",
    "media franchise",
    "entertainment company",
    "theme park",
    "studio",
    "streaming service",
    "toy line",
    "game franchise",
    "consumer products",
    "licensing",
    "licensed",
    "brand",
)

COPYRIGHT_KEYWORDS = (
    "movie",
    "film",
    "tv series",
    "television series",
    "anime",
    "manga",
    "comic",
    "character",
    "fictional character",
    "franchise",
    "game franchise",
    "song",
    "album",
    "lyrics",
    "studio",
    "disney",
    "pokemon",
    "barbie",
    "marvel",
)

POP_CULTURE_KEYWORDS = (
    "kill bill",
    "barbie",
    "barbie girl",
    "pokemon",
    "pikachu",
    "marvel",
    "avengers",
    "disney",
    "harry potter",
    "hogwarts",
    "star wars",
)

POP_CULTURE_CONTEXT = {
    "hogwarts": "Harry Potter",
    "harry potter": "Harry Potter",
    "avengers": "Marvel",
    "pikachu": "Pokemon",
    "pokemon": "Pokemon",
    "barbie": "Barbie",
    "barbie girl": "Barbie",
    "kill bill": "Kill Bill",
    "star wars": "Star Wars",
}

MUSIC_COPYRIGHT_KEYWORDS = (
    "music",
    "song",
    "album",
    "artist",
    "band",
    "k-pop",
    "group",
    "idol",
    "lyrics",
    "single",
)

STRONG_MUSIC_HINTS = (
    "singer",
    "musician",
    "rapper",
    "band",
    "album",
    "lyrics",
    "single",
    "songwriter",
    "record label",
    "discography",
    "k-pop",
)

GENERIC_INPUT_WORDS = {
    "a",
    "an",
    "and",
    "art",
    "brand",
    "cap",
    "classic",
    "cool",
    "cute",
    "design",
    "edition",
    "fan",
    "for",
    "funny",
    "graphic",
    "hat",
    "hoodie",
    "in",
    "inspired",
    "jacket",
    "logo",
    "merch",
    "merchandise",
    "mug",
    "of",
    "official",
    "on",
    "poster",
    "premium",
    "print",
    "quote",
    "retro",
    "shirt",
    "shop",
    "sticker",
    "style",
    "sweater",
    "tee",
    "the",
    "theme",
    "tshirt",
    "t-shirt",
    "vintage",
    "wear",
    "with",
}


@dataclass
class SearchResult:
    title: str
    snippet: str
    link: str
    source: str
    image: str = ""

    @property
    def favicon_url(self) -> str:
        host = urlparse(self.link).netloc
        if not host:
            return ""
        return f"https://www.google.com/s2/favicons?domain={quote_plus(host)}&sz=64"


def fetch_term_report(term: str) -> dict[str, Any]:
    original_term = normalize_space(term)
    candidates = resolve_focus_terms(original_term)
    reports = build_candidate_reports(candidates, original_term)
    primary_report = choose_primary_report(reports, original_term)
    resolved_term = primary_report["term"]
    web_results = primary_report["results"]
    wiki_summary = primary_report["wiki_summary"]
    summary = primary_report["summary"]
    trademark = primary_report["trademark"]
    suggested_fix = build_suggested_fix(
        original_term=original_term,
        resolved_term=resolved_term,
        trademark=trademark,
        summary=summary,
    )
    return {
        "term": resolved_term,
        "original_term": original_term,
        "resolved_from_input": resolved_term != original_term,
        "summary": summary,
        "trademark": trademark,
        "suggested_fix": suggested_fix,
        "results": web_results[:5],
        "wiki_summary": wiki_summary,
        "display_image": choose_display_image(wiki_summary, web_results),
        "used_google_api": has_google_api_credentials(),
        "detected_terms": [report["term"] for report in reports],
        "all_reports": reports,
    }


def fetch_google_like_results(term: str) -> list[SearchResult]:
    if has_google_api_credentials():
        try:
            api_results = fetch_google_custom_search(term)
            if api_results:
                return api_results
        except (HTTPError, URLError, TimeoutError, ValueError):
            pass

    html_results = fetch_google_html_results(term)
    if html_results:
        return html_results

    try:
        return fetch_duckduckgo_results(term)
    except (HTTPError, URLError, TimeoutError, ValueError):
        return []


def resolve_focus_terms(term: str) -> list[str]:
    cleaned = normalize_space(term)
    if not cleaned:
        return []

    quoted = extract_quoted_term(cleaned)
    if quoted:
        return [quoted]

    direct_matches = extract_known_entities_from_input(cleaned)
    if direct_matches:
        return direct_matches

    input_candidates = extract_input_entity_candidates(cleaned)
    if input_candidates:
        return input_candidates

    if len(cleaned.split()) <= 4:
        return [cleaned]

    initial_results = fetch_google_like_results(cleaned)
    inferred = infer_term_from_results(cleaned, initial_results)
    return [inferred or cleaned]


def build_candidate_reports(
    candidates: list[str],
    original_term: str,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = normalize_space(candidate)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)

        results = fetch_google_like_results(cleaned)
        wiki_summary = fetch_wikipedia_summary(cleaned)
        summary = build_summary(results, wiki_summary)
        trademark = assess_trademark_risk(cleaned, results, wiki_summary, summary)
        reports.append(
            {
                "term": cleaned,
                "results": results,
                "wiki_summary": wiki_summary,
                "display_image": choose_display_image(wiki_summary, results),
                "summary": summary,
                "trademark": trademark,
                "suggested_fix": build_suggested_fix(
                    original_term=original_term,
                    resolved_term=cleaned,
                    trademark=trademark,
                    summary=summary,
                ),
            }
        )

    if reports:
        return reports

    fallback_results = fetch_google_like_results(original_term)
    fallback_wiki = fetch_wikipedia_summary(original_term)
    fallback_summary = build_summary(fallback_results, fallback_wiki)
    fallback_trademark = assess_trademark_risk(
        original_term, fallback_results, fallback_wiki, fallback_summary
    )
    return [
        {
            "term": original_term,
            "results": fallback_results,
            "wiki_summary": fallback_wiki,
            "display_image": choose_display_image(fallback_wiki, fallback_results),
            "summary": fallback_summary,
            "trademark": fallback_trademark,
            "suggested_fix": build_suggested_fix(
                original_term=original_term,
                resolved_term=original_term,
                trademark=fallback_trademark,
                summary=fallback_summary,
            ),
        }
    ]


def choose_primary_report(reports: list[dict[str, Any]], original_term: str) -> dict[str, Any]:
    if not reports:
        return {
            "term": original_term,
            "results": [],
            "wiki_summary": {},
            "display_image": "",
            "summary": {"overview": "", "facts": [], "entity_type": "Chưa rõ", "birth_year": "", "top_matches": []},
            "trademark": {
                "score": 0,
                "level": "Thấp",
                "level_class": "low",
                "verdict": "Chưa thấy dấu hiệu trademark mạnh.",
                "is_trademark": "Chưa rõ",
                "consequence": "Nếu sử dụng, rủi ro hiện chưa cao nhưng vẫn nên tra cứu chính thức trước.",
                "is_political": False,
                "reasons": [],
                "search_links": [],
                "official_sources": [],
            },
            "suggested_fix": {"bypass": [], "safe": []},
        }

    return max(
        reports,
        key=lambda report: (
            report["trademark"]["score"],
            len(report["results"]),
            len(report["summary"].get("overview", "")),
        ),
    )


def fetch_google_custom_search(term: str) -> list[SearchResult]:
    params = urlencode(
        {
            "key": settings.GOOGLE_API_KEY,
            "cx": settings.GOOGLE_CSE_ID,
            "q": term,
            "num": 5,
        }
    )
    data = fetch_json(f"https://www.googleapis.com/customsearch/v1?{params}")
    items = data.get("items", [])
    return [
        SearchResult(
            title=item.get("title", "").strip(),
            snippet=item.get("snippet", "").strip(),
            link=item.get("link", "").strip(),
            source="Google Custom Search",
            image=extract_google_result_image(item),
        )
        for item in items
        if item.get("title") and item.get("link")
    ]


def fetch_google_html_results(term: str) -> list[SearchResult]:
    try:
        html = fetch_text(f"https://www.google.com/search?hl=en&q={quote_plus(term)}")
    except (HTTPError, URLError, TimeoutError):
        return []

    blocks = re.findall(r'<div class="g".*?</div></div></div>', html, flags=re.DOTALL)
    results: list[SearchResult] = []
    for block in blocks:
        title_match = re.search(r"<h3.*?>(.*?)</h3>", block, flags=re.DOTALL)
        link_match = re.search(r'<a href="/url\?q=(.*?)&amp;', block, flags=re.DOTALL)
        snippet_match = re.search(r'<div class="VwiC3b.*?">(.*?)</div>', block, flags=re.DOTALL)
        if not title_match or not link_match:
            continue

        title = strip_html(title_match.group(1))
        link = unescape(link_match.group(1))
        snippet = strip_html(snippet_match.group(1)) if snippet_match else ""
        if title and link.startswith("http"):
            results.append(
                SearchResult(
                    title=title,
                    snippet=snippet,
                    link=link,
                    source="Google Search",
                )
            )
        if len(results) >= 5:
            break
    return results


def fetch_duckduckgo_results(term: str) -> list[SearchResult]:
    data = fetch_json(
        "https://api.duckduckgo.com/?"
        + urlencode({"q": term, "format": "json", "no_html": 1, "skip_disambig": 1})
    )
    results: list[SearchResult] = []

    abstract = normalize_space(data.get("AbstractText", ""))
    if abstract:
        results.append(
            SearchResult(
                title=data.get("Heading", term),
                snippet=abstract,
                link=data.get("AbstractURL", f"https://duckduckgo.com/?q={quote_plus(term)}"),
                source="DuckDuckGo Instant Answer",
                image=normalize_duckduckgo_image(data.get("Image", "")),
            )
        )

    for topic in data.get("RelatedTopics", []):
        entries = topic.get("Topics", [topic])
        for entry in entries:
            text = normalize_space(entry.get("Text", ""))
            first_url = entry.get("FirstURL", "")
            if text and first_url:
                results.append(
                    SearchResult(
                        title=text.split(" - ")[0][:90],
                        snippet=text,
                        link=first_url,
                        source="DuckDuckGo",
                    )
                )
            if len(results) >= 5:
                return results
    return results


def fetch_wikipedia_summary(term: str) -> dict[str, str]:
    try:
        search_data = fetch_json(
            "https://en.wikipedia.org/w/api.php?"
            + urlencode(
                {
                    "action": "opensearch",
                    "search": term,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                }
            )
        )
    except (HTTPError, URLError, TimeoutError):
        return {}

    matches = search_data[1] if isinstance(search_data, list) and len(search_data) > 1 else []
    if not matches:
        return {}

    title = matches[0]
    try:
        summary_data = fetch_json(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}"
        )
    except (HTTPError, URLError, TimeoutError):
        return {}

    return {
        "title": summary_data.get("title", ""),
        "extract": normalize_space(summary_data.get("extract", "")),
        "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "image": summary_data.get("thumbnail", {}).get("source", ""),
    }


def build_summary(results: list[SearchResult], wiki_summary: dict[str, str]) -> dict[str, Any]:
    evidence_parts = [wiki_summary.get("extract", "")]
    evidence_parts.extend(result.snippet for result in results if result.snippet)
    evidence_text = f" {' '.join(evidence_parts)} ".lower()

    entity_type = infer_entity_type(evidence_text)
    birth_year = extract_birth_year(evidence_text)
    wiki_overview = wiki_summary.get("extract", "")
    best_result = choose_best_result(results)
    result_overview = best_result.snippet if best_result else first_non_empty([result.snippet for result in results])
    is_ambiguous = is_ambiguous_summary(wiki_overview)

    if wiki_overview and not is_ambiguous:
        overview = translate_text(wiki_overview, target_lang="vi") or wiki_overview
    elif result_overview:
        overview = translate_text(result_overview, target_lang="vi") or result_overview
    elif wiki_overview:
        overview = translate_text(wiki_overview, target_lang="vi") or wiki_overview
    else:
        overview = "Chưa lấy được mô tả rõ ràng cho từ khóa này."
    overview = shorten_text(overview, 220)

    facts: list[str] = []
    if entity_type:
        facts.append(f"Loại: {entity_type}.")
    if birth_year:
        facts.append(f"Năm sinh: {birth_year}.")
    if results:
        facts.append(f"Kết quả tham khảo: {len(results)}.")
    if wiki_summary.get("url"):
        facts.append("Có thêm nguồn Wikipedia.")
    if is_ambiguous:
        facts.append("Từ khóa này có thể đang mang nhiều nghĩa.")

    return {
        "overview": overview,
        "facts": facts,
        "entity_type": entity_type,
        "birth_year": birth_year,
        "top_matches": build_top_matches(results),
    }


def assess_trademark_risk(
    term: str,
    results: list[SearchResult],
    wiki_summary: dict[str, str],
    summary: dict[str, Any],
) -> dict[str, Any]:
    combined_text = " ".join(
        [wiki_summary.get("extract", "")]
        + [result.title for result in results]
        + [result.snippet for result in results]
    ).lower()
    normalized_term = term.lower().strip()
    is_political = phat_hien_tin_hieu_chinh_tri(term, combined_text)
    is_famous_brand = normalized_term in FAMOUS_BRAND_KEYWORDS
    is_famous_person = normalized_term in FAMOUS_PERSON_KEYWORDS
    is_famous_slogan = normalized_term in FAMOUS_SLOGANS
    has_ip_brand_signals = any(keyword in combined_text for keyword in IP_BRAND_HINTS)
    entity_type = summary.get("entity_type")

    reasons: list[str] = []
    score = 0

    if any(keyword in combined_text for keyword in ("registered trademark", "trademark", "®", " tm ")):
        score += 45
        reasons.append("Có nhắc trực tiếp trademark")

    if any(keyword in combined_text for keyword in TRADEMARK_KEYWORDS):
        score += 30
        reasons.append("Tên giống thương hiệu")

    if summary.get("entity_type") == "Con người":
        score -= 25
        reasons.append("Thiên về tên người")

    if len(normalized_term.split()) <= 3 and normalized_term.isascii():
        score += 10

    exact_mentions = sum(1 for result in results if normalized_term in result.title.lower())
    if exact_mentions >= 2:
        score += 15
        reasons.append("Tên xuất hiện lặp lại trong kết quả tìm kiếm")

    if has_ip_brand_signals:
        score += 25
        reasons.append("Có dấu hiệu IP/thương hiệu")

    if is_famous_brand:
        score = max(score, 85)
        reasons.append(f"Trùng thương hiệu {to_display_name(normalized_term)}")

    if is_famous_slogan:
        score = max(score, 88)
        reasons.append(f"Trùng slogan của {FAMOUS_SLOGANS[normalized_term]}")

    if is_famous_person:
        score = max(score, 82)
        reasons.append(f"Trùng public figure {FAMOUS_PERSON_DISPLAY.get(normalized_term, to_display_name(normalized_term))}")

    if is_political:
        score = max(score, 70)
        reasons.append("Liên quan chính trị")

    trademark_classes = extract_trademark_classes(combined_text)
    class_context = build_class_context(trademark_classes)
    if class_context["status"] == "non_relevant" and score > 0:
        score = min(score, 30)
        reasons.append("Trademark không nằm trong class sản phẩm POD của công ty")
    elif class_context["status"] == "relevant" and score > 0:
        score = max(score, 65)
        reasons.append(f"Trademark có class liên quan POD: {class_context['classes_text']}")

    copyright_analysis = assess_copyright_risk(
        term=term,
        combined_text=combined_text,
        is_famous_brand=is_famous_brand,
        has_ip_brand_signals=has_ip_brand_signals,
        is_famous_slogan=is_famous_slogan,
    )
    public_figure_analysis = assess_public_figure_risk(
        term=term,
        combined_text=combined_text,
        is_political=is_political,
        is_famous_person=is_famous_person,
        entity_type=entity_type,
    )

    trademark_analysis = build_analysis_block(
        title="Trademark risk",
        score=score,
        reasons=reasons,
        high_label="Có đăng ký hoặc sử dụng thương hiệu rất mạnh",
        medium_label="Có dấu hiệu liên quan đến thương hiệu",
        low_label=(
            "Trademark không trùng class sản phẩm của công ty"
            if class_context["status"] == "non_relevant"
            else "Chưa thấy dấu hiệu thương hiệu mạnh"
        ),
    )
    context_tags = detect_context_tags(term, combined_text)

    ip_rights_analysis = build_ip_rights_analysis(
        trademark_analysis,
        copyright_analysis,
        public_figure_analysis,
    )
    analyses = [trademark_analysis, copyright_analysis, public_figure_analysis, ip_rights_analysis]
    overall_score = max(analysis["score"] for analysis in analyses)
    overall_reasons = collect_overall_reasons(analyses)
    overall_reason_text = overall_reasons[0] if overall_reasons else ""

    if overall_score >= 70:
        level = "Cao"
        level_class = "high"
        verdict = overall_reason_text or "Có ít nhất một rủi ro mạnh trong 3 nhóm phân tích."
    elif overall_score >= 35:
        level = "Trung bình"
        level_class = "medium"
        verdict = overall_reason_text or "Có rủi ro ở ít nhất một nhóm phân tích."
    else:
        level = "Thấp"
        level_class = "low"
        if all(analysis["score"] <= 15 for analysis in analyses):
            verdict = "Từ khóa an toàn, có thể sử dụng."
        else:
            verdict = overall_reason_text or "Chưa thấy rủi ro mạnh trong 3 nhóm phân tích."

    if trademark_analysis["score"] >= 70:
        is_trademark = "Có khả năng cao"
    elif trademark_analysis["score"] >= 35:
        is_trademark = "Có thể"
    else:
        is_trademark = "Chưa rõ"

    if public_figure_analysis["score"] >= 70 and is_political:
        consequence = (
            "Nếu sử dụng, rủi ro cao: dễ bị từ chối quảng cáo, gỡ nội dung, khóa gian hàng "
            "hoặc phát sinh khiếu nại liên quan chính trị."
        )
    elif overall_score >= 70:
        consequence = (
            "Nếu sử dụng, có thể bị khiếu nại quyền sở hữu trí tuệ, gỡ listing, gỡ nội dung hoặc phát sinh tranh chấp."
        )
    elif overall_score >= 35:
        consequence = "Nếu sử dụng, có nguy cơ bị cảnh báo hoặc bị khiếu nại ở ít nhất một nhóm rủi ro."
    else:
        if all(analysis["score"] <= 15 for analysis in analyses):
            consequence = "Hiện chưa thấy dấu hiệu rủi ro rõ, có thể sử dụng."
        else:
            consequence = "Nếu sử dụng, rủi ro hiện chưa cao nhưng vẫn nên tra cứu chính thức trước."

    return {
        "score": overall_score,
        "level": level,
        "level_class": level_class,
        "verdict": verdict,
        "action_recommendation": build_action_recommendation(level, overall_score, analyses),
        "explanation": build_risk_explanation(term, level, overall_reasons, analyses, summary, class_context),
        "matched_elements": overall_reasons[:3],
        "confidence_level": build_confidence_level(overall_score, overall_reasons, results),
        "advanced_breakdown": build_advanced_breakdown(term, overall_score, analyses, context_tags, class_context),
        "design_safe": build_design_safe_notes(term, overall_score, overall_reasons),
        "trademark_records": [],
        "official_sources": build_official_sources(term),
        "top_label": build_top_label(
            term=term,
            context_tags=context_tags,
            trademark_analysis=trademark_analysis,
            copyright_analysis=copyright_analysis,
            public_figure_analysis=public_figure_analysis,
            is_famous_slogan=is_famous_slogan,
            is_famous_brand=is_famous_brand,
            is_famous_person=is_famous_person,
            is_political=is_political,
        ),
        "is_trademark": is_trademark,
        "consequence": consequence,
        "is_political": is_political,
        "reasons": overall_reasons,
        "analyses": analyses,
        "context_tags": context_tags,
        "search_links": [
            {
                "label": "Google Search",
                "url": f"https://www.google.com/search?q={quote_plus(term)}",
            },
            {
                "label": "USPTO Search",
                "url": f"https://tmsearch.uspto.gov/search/search-results?query={quote_plus(term)}",
            },
        ],
    }


def build_risk_explanation(
    term: str,
    level: str,
    overall_reasons: list[str],
    analyses: list[dict[str, Any]],
    summary: dict[str, Any],
    class_context: dict[str, Any] | None = None,
) -> str:
    strongest = max(analyses, key=lambda item: item["score"])
    reason = overall_reasons[0] if overall_reasons else "chưa thấy tín hiệu rủi ro rõ"
    entity_type = summary.get("entity_type") or "thực thể chưa rõ"
    term_lower = term.lower()
    strongest_title = translate_analysis_title(strongest["title"])
    if class_context and class_context.get("status") == "non_relevant":
        return (
            f"Trademark của '{term}' đang được dữ liệu tìm kiếm nhắc ở {class_context['classes_text']}, "
            "không thuộc nhóm sản phẩm công ty đang bán (Class 16 poster/lịch, Class 21 cốc, Class 25 áo/hoodie/sweater), "
            "nên điểm Trademark được hạ xuống thấp. Tuy nhiên vẫn cần xem riêng Copyright và IP Rights nếu từ khóa là nhân vật, logo, slogan hoặc IP nổi tiếng."
        )

    if "disney" in term_lower:
        return (
            f"Tên '{term}' rủi ro cao vì trùng Disney, một IP/thương hiệu giải trí toàn cầu. "
            "Nếu dùng cho áo/POD, rủi ro nằm ở chữ Disney, lâu đài, nhân vật, princess, chuột tai tròn, "
            "font hoặc style hoạt hình gợi Disney; listing có thể bị gỡ hoặc bị claim nhanh. "
            "Nên đổi sang concept chung như fairy tale, magic castle, enchanted story và tự tạo artwork riêng."
        )
    if "harry potter" in term_lower or "hogwarts" in term_lower:
        return (
            f"Tên '{term}' rủi ro cao vì gắn với IP Harry Potter. "
            "Nếu làm POD, tránh dùng trực tiếp tên Harry Potter/Hogwarts, đũa phép, kính tròn, tia sét, huy hiệu nhà "
            "hoặc bố cục giống franchise. Nên chuyển sang mô tả chung như magic academy, wizard school hoặc fantasy castle."
        )
    if "nike" in term_lower:
        return (
            f"Tên '{term}' rủi ro cao vì trùng thương hiệu Nike. "
            "Nếu dùng trên áo/POD, rủi ro nằm ở chữ Nike, dấu swoosh, slogan, hình giày hoặc phong cách campaign thể thao "
            "gợi Nike. Nên đổi sang mô tả trung tính như sport energy, urban running hoặc active lifestyle."
        )
    if term_lower in FAMOUS_SLOGANS:
        owner = FAMOUS_SLOGANS[term_lower]
        return (
            f"Tên '{term}' rủi ro cao vì là slogan nổi tiếng gắn với {owner}. "
            "Nếu đưa slogan này lên áo, title, tag hoặc mockup bán hàng, rủi ro trademark trực tiếp rất cao; "
            f"nên bỏ câu slogan và đổi sang thông điệp thể thao/tạo động lực không nhắc {owner}."
        )
    if "trump" in term_lower or "chính trị" in " ".join(overall_reasons).lower():
        return (
            f"Tên '{term}' rủi ro cao vì liên quan người thật/chính trị. "
            "Nếu dùng trong title, tag, artwork hoặc quảng cáo, rủi ro chính nằm ở tên/mặt người thật, slogan tranh cử, "
            "năm bầu cử hoặc nội dung ủng hộ/công kích chính trị; dễ bị giới hạn quảng cáo hoặc gỡ nội dung."
        )
    if term_lower in FAMOUS_PERSON_KEYWORDS:
        display_name = FAMOUS_PERSON_DISPLAY.get(term_lower, to_display_name(term_lower))
        return (
            f"Tên '{term}' rủi ro cao vì trùng tên người nổi tiếng {display_name}. "
            "Nếu dùng để bán áo/POD, tránh dùng trực tiếp tên, mặt, chữ ký, lyric, số áo hoặc biệt danh nhận diện; "
            "nên chuyển sang mô tả fan/general concept không nhắc tên thật."
        )

    if level == "Cao":
        return (
            f"Tên '{term}' có rủi ro cao vì {reason}. "
            f"Tín hiệu mạnh nhất nằm ở nhóm {strongest_title} với điểm {strongest['score']}/100. "
            "Nếu dùng cho POD, hãy bỏ phần tên/biểu tượng đang trùng và chuyển sang concept mô tả chung, tự tạo artwork riêng."
        )
    if level == "Trung bình":
        return (
            f"Tên '{term}' có một số tín hiệu cần xem xét vì {reason}. "
            f"Loại thực thể hiện suy ra là {entity_type}. Nên tra cứu thêm trước khi dùng thương mại."
        )
    return (
        f"Tên '{term}' hiện chưa có tín hiệu rủi ro rõ trong dữ liệu đang lấy được. "
        "Có thể dùng ở mức tham khảo; nếu chạy ads hoặc in số lượng lớn thì vẫn nên kiểm tra nguồn chính thức."
    )


def build_official_sources(term: str) -> list[dict[str, str]]:
    encoded = quote_plus(term)
    return [
        {
            "label": "Tra cứu USPTO",
            "url": f"https://tmsearch.uspto.gov/search/search-results?query={encoded}",
        },
        {
            "label": "Tra cứu WIPO",
            "url": f"https://branddb.wipo.int/en/quicksearch?by=brandName&v={encoded}",
        },
    ]


def extract_trademark_classes(text: str) -> list[int]:
    classes: set[int] = set()
    patterns = (
        r"(?:international\s+class|nice\s+class|class|classes|ic)\s*(?:no\.?\s*)?0?(\d{1,3})",
        r"\b0?(16|21|25)\b\s*(?:goods|shirts|hoodies|sweaters|mugs|posters|calendars)",
    )
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            value = match[0] if isinstance(match, tuple) else match
            try:
                class_number = int(value)
            except ValueError:
                continue
            if 1 <= class_number <= 45:
                classes.add(class_number)
    return sorted(classes)


def build_class_context(classes: list[int]) -> dict[str, Any]:
    relevant = [class_number for class_number in classes if class_number in POD_RELEVANT_TRADEMARK_CLASSES]
    classes_text = ", ".join(f"Class {class_number}" for class_number in classes) if classes else "chưa thấy class rõ"
    relevant_text = ", ".join(
        f"Class {class_number} ({POD_RELEVANT_TRADEMARK_CLASSES[class_number]})"
        for class_number in relevant
    )
    pod_classes_text = "Class 16/21/25"

    if relevant:
        return {
            "classes": classes,
            "relevant": relevant,
            "classes_text": classes_text,
            "status": "relevant",
            "message": f"Có trong nhóm sản phẩm công ty: {relevant_text}.",
            "pod_classes_text": pod_classes_text,
        }
    if classes:
        return {
            "classes": classes,
            "relevant": [],
            "classes_text": classes_text,
            "status": "non_relevant",
            "message": f"Không thuộc nhóm sản phẩm công ty ({pod_classes_text}).",
            "pod_classes_text": pod_classes_text,
        }
    return {
        "classes": [],
        "relevant": [],
        "classes_text": classes_text,
        "status": "unknown",
        "message": "Chưa có dữ liệu class chính thức",
        "pod_classes_text": pod_classes_text,
    }


def build_confidence_level(score: int, reasons: list[str], results: list[SearchResult]) -> str:
    if score >= 70 and reasons:
        return "Cao"
    if score >= 35 or results:
        return "Trung bình"
    return "Thấp"


def build_advanced_breakdown(
    term: str,
    overall_score: int,
    analyses: list[dict[str, Any]],
    context_tags: list[str],
    class_context: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    category_conflict = class_context["message"] if class_context else "Chưa thấy class trademark rõ"
    market_sensitivity = "US/EU: cao" if overall_score >= 70 else "US/EU: cần kiểm tra" if overall_score >= 35 else "US/EU: thấp"
    strongest = max(analyses, key=lambda item: item["score"])
    context = ", ".join(context_tags) if context_tags else "Chưa rõ"
    rows = [
        {"label": "Điểm tương đồng", "value": f"{overall_score}%"},
        {"label": "Độ nhạy thị trường", "value": market_sensitivity},
        {"label": "Nguồn rủi ro chính", "value": translate_analysis_title(strongest["title"])},
        {"label": "Ngữ cảnh", "value": context},
    ]
    if not class_context or class_context.get("status") != "unknown":
        rows.insert(1, {"label": "Class POD", "value": category_conflict})
    return rows


def translate_analysis_title(title: str) -> str:
    translations = {
        "Trademark risk": "Trademark",
        "Copyright risk": "Copyright",
        "Public figure risk": "Public Figure",
        "Intellectual Property Rights": "Intellectual Property Rights",
    }
    return translations.get(title, title)


def build_design_safe_notes(term: str, score: int, reasons: list[str]) -> list[str]:
    if score < 35:
        return [
            f"Có thể dùng '{term}' nếu chỉ là mô tả chung, không copy hình/logo có sẵn.",
            "Nếu dùng POD, nên tự vẽ nhân vật hoặc bố cục mới hoàn toàn.",
        ]
    lowered_reasons = " ".join(reasons).lower()
    if "disney" in term.lower() or "disney" in lowered_reasons:
        return [
            "Không dùng chữ Disney trực tiếp trên title, tag hoặc artwork.",
            "Không dùng lâu đài, chuột tai tròn, princess hoặc style quá giống Disney.",
            "Nên chuyển sang concept chung như fairy tale, magic castle, enchanted story.",
            "Tự vẽ nhân vật/bối cảnh mới, tránh màu/font/logo nhận diện của Disney.",
        ]
    if "harry potter" in term.lower() or "hogwarts" in term.lower() or "harry potter" in lowered_reasons:
        return [
            "Không dùng Harry Potter, Hogwarts hoặc tên nhà/trường phép thuật trực tiếp.",
            "Không dùng đũa phép, kính tròn, tia sét, huy hiệu nhà theo bố cục quen thuộc.",
            "Nên chuyển sang concept chung như magic academy, wizard school, fantasy castle.",
            "Tự thiết kế biểu tượng phép thuật mới, không copy artwork/phông chữ của franchise.",
        ]
    if "nike" in term.lower() or "nike" in lowered_reasons:
        return [
            "Không dùng chữ Nike, swoosh hoặc slogan gắn với Nike.",
            "Không copy hình giày, campaign hoặc layout quảng cáo của Nike.",
            "Nên chuyển sang concept chung như sport energy, urban running, active lifestyle.",
            "Dùng biểu tượng tự tạo, tránh đường cong/logo gợi nhớ swoosh.",
        ]
    if "trump" in term.lower() or "chính trị" in lowered_reasons:
        return [
            "Không dùng trực tiếp tên, mặt hoặc khẩu hiệu chính trị.",
            "Tránh slogan tranh cử, năm bầu cử hoặc biểu tượng đảng phái.",
            "Nên chuyển sang chủ đề hài/chính luận trung tính, không nhắc tên người thật.",
            "Nếu chạy ads, nên tránh nội dung công kích hoặc ủng hộ chính trị trực tiếp.",
        ]
    notes = [
        f"Không dùng trực tiếp tên '{term}' trên thiết kế.",
        "Không dùng logo, font, màu nhận diện hoặc hình ảnh chính thức.",
        "Không copy nhân vật, biểu tượng, quote hoặc slogan nổi tiếng.",
        "Nên chuyển sang mô tả chung và tạo nhân vật/bố cục gốc.",
    ]
    if any("chính trị" in reason.lower() for reason in reasons):
        notes.append("Tránh dùng mặt người thật, khẩu hiệu tranh cử hoặc thông điệp chính trị trực tiếp.")
    return notes


def assess_copyright_risk(
    term: str,
    combined_text: str,
    is_famous_brand: bool,
    has_ip_brand_signals: bool,
    is_famous_slogan: bool,
) -> dict[str, Any]:
    normalized_term = term.lower().strip()
    reasons: list[str] = []
    score = 0

    direct_copyright = False
    indirect_copyright = False

    if any(keyword in combined_text for keyword in COPYRIGHT_KEYWORDS):
        score += 45
        direct_copyright = True
        reasons.append("Gắn với phim/IP/nhân vật")
    if phat_hien_tin_hieu_am_nhac(term, combined_text):
        score += 25
        indirect_copyright = True
        reasons.append("Có tín hiệu âm nhạc")
    if has_ip_brand_signals:
        score += 25
        indirect_copyright = True
        reasons.append("Có dấu hiệu IP giải trí")
    if normalized_term in POP_CULTURE_KEYWORDS:
        score = max(score, 80)
        direct_copyright = True
        reasons.append(tao_ly_do_van_hoa_dai_chung(normalized_term))
    if normalized_term in FAMOUS_PERSON_KEYWORDS and normalized_term in ("bts", "blackpink", "newjeans", "twice", "exo", "seventeen"):
        score = max(score, 75)
        direct_copyright = True
        reasons.append(f"Trùng nhóm nhạc {to_display_name(normalized_term)}")
    if is_famous_brand and normalized_term in ("disney", "pokemon", "pikachu", "marvel"):
        score = max(score, 90)
        direct_copyright = True
        reasons.append(f"Trùng IP lớn {to_display_name(normalized_term)}")
    elif is_famous_slogan:
        score = max(score, 40)
        indirect_copyright = True
        reasons.append(f"Gắn campaign của {FAMOUS_SLOGANS[normalized_term]}")
    elif is_famous_brand:
        score = max(score, 35)
        indirect_copyright = True
        reasons.append(f"Gián tiếp qua logo/hình của {to_display_name(normalized_term)}")

    analysis = build_analysis_block(
        title="Copyright risk",
        score=score,
        reasons=reasons,
        high_label="Nguy cơ bản quyền trực tiếp rất cao",
        medium_label="Có dấu hiệu bản quyền gián tiếp",
        low_label="Chưa thấy dấu hiệu bản quyền mạnh",
    )
    if analysis["level"] == "medium" and indirect_copyright and not direct_copyright:
        analysis["detail"] = (
            "Gián tiếp: thường nằm ở logo, thiết kế sản phẩm hoặc hình ảnh quảng cáo."
        )
    elif analysis["level"] == "high" and direct_copyright:
        analysis["detail"] = "Trực tiếp: gắn với nhân vật, phim, franchise hoặc nội dung giải trí nổi tiếng."
    else:
        analysis["detail"] = ""
    return analysis


def assess_public_figure_risk(
    term: str,
    combined_text: str,
    is_political: bool,
    is_famous_person: bool,
    entity_type: str,
) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0
    normalized_term = term.lower().strip()

    if normalized_term in FAMOUS_SLOGANS:
        return build_analysis_block(
            title="Public figure risk",
            score=0,
            reasons=[],
            high_label="Nguy cơ public figure rất cao",
            medium_label="Có dấu hiệu public figure",
            low_label="Chưa thấy dấu hiệu public figure mạnh",
        )

    if entity_type == "Con người":
        score += 35
        reasons.append("Giống tên người thật")
    if is_famous_person:
        score = max(score, 85)
        reasons.append(f"Trùng public figure {FAMOUS_PERSON_DISPLAY.get(normalized_term, to_display_name(normalized_term))}")
    if is_political:
        score = max(score, 92)
        reasons.append("Trùng nhân vật chính trị")
    if any(keyword in combined_text for keyword in ("president", "singer", "actor", "rapper", "footballer")):
        score += 20
        reasons.append("Kết quả mô tả public figure")

    return build_analysis_block(
        title="Public figure risk",
        score=score,
        reasons=reasons,
        high_label="Nguy cơ public figure rất cao",
        medium_label="Có dấu hiệu public figure",
        low_label="Chưa thấy dấu hiệu public figure mạnh",
    )


def build_analysis_block(
    title: str,
    score: int,
    reasons: list[str],
    high_label: str,
    medium_label: str,
    low_label: str,
    consequence: str = "",
) -> dict[str, Any]:
    bounded_score = max(0, min(score, 100))
    if bounded_score >= 70:
        level = "high"
        verdict = high_label
    elif bounded_score >= 35:
        level = "medium"
        verdict = medium_label
    else:
        level = "low"
        verdict = low_label
    return {
        "title": title,
        "score": bounded_score,
        "level": level,
        "verdict": verdict,
        "consequence": consequence,
        "reasons": prioritize_specific_reasons(reasons)[:2],
    }


def build_ip_rights_analysis(*analyses: dict[str, Any]) -> dict[str, Any]:
    score = max((analysis["score"] for analysis in analyses), default=0)
    reasons: list[str] = []
    for analysis in analyses:
        if analysis["score"] >= 35:
            reasons.extend(analysis.get("reasons", []))

    return build_analysis_block(
        title="Intellectual Property Rights",
        score=score,
        reasons=reasons or ["Tổng hợp từ trademark, copyright và public figure"],
        high_label="Có rủi ro quyền sở hữu trí tuệ cao",
        medium_label="Có tín hiệu quyền sở hữu trí tuệ cần kiểm tra",
        low_label="Chưa thấy rủi ro quyền sở hữu trí tuệ rõ",
        consequence=build_ip_rights_consequence(score),
    )


def build_ip_rights_consequence(score: int) -> str:
    if score >= 70:
        return (
            "Hậu quả IPR: TikTok có thể gỡ sản phẩm, ghi violation, khóa vĩnh viễn tài khoản, "
            "đóng băng tiền trong ví. Khi đã dính gậy IPR, tài khoản dễ bị đưa vào blacklist và "
            "các sản phẩm sau này sẽ bị duyệt khắt khe hơn."
        )
    if score >= 35:
        return (
            "Hậu quả IPR: có thể bị cảnh báo, gỡ listing hoặc duyệt chậm hơn. "
            "Nên đổi tên/artwork trước khi đăng để tránh tích lũy violation."
        )
    return "Chưa thấy hậu quả IPR rõ, nhưng vẫn nên tránh copy logo, nhân vật, slogan hoặc hình ảnh có quyền."


def build_action_recommendation(level: str, score: int, analyses: list[dict[str, Any]]) -> str:
    ip_score = next(
        (analysis["score"] for analysis in analyses if analysis["title"] == "Intellectual Property Rights"),
        score,
    )
    if level == "Cao" or ip_score >= 70:
        return "Khuyến nghị: Thay đổi thiết kế/từ khóa hoàn toàn trước khi đăng bán."
    if level == "Trung bình" or ip_score >= 35:
        return "Khuyến nghị: Đổi tên hoặc chỉnh artwork để giảm rủi ro trước khi đăng."
    return "Khuyến nghị: Có thể dùng, nhưng vẫn nên tránh copy logo/hình ảnh/slogan có quyền."


def collect_overall_reasons(analyses: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(analyses, key=lambda item: item["score"], reverse=True)
    reasons: list[str] = []
    for analysis in ordered:
        reasons.extend(analysis.get("reasons", []))
    return prioritize_specific_reasons(reasons)[:3]


def build_suggested_fix(
    original_term: str,
    resolved_term: str,
    trademark: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, list[str]]:
    base = normalize_space(original_term or resolved_term)
    normalized = resolved_term.lower().strip()
    top_label = trademark.get("top_label", "")
    safe: list[str] = []
    bypass: list[str] = []

    if trademark.get("level") == "Thấp":
        safe.append("Có thể giữ nguyên từ khóa hiện tại.")
        safe.append("Nếu dùng thương mại, vẫn nên tra cứu nhanh trước khi in ấn hoặc chạy ads.")
        return {"bypass": [], "safe": safe[:2]}

    if top_label == "Brand":
        safe.extend([
            f"Tránh dùng trực tiếp tên thương hiệu {to_display_name(normalized)}.",
            "Đổi sang mô tả sản phẩm trung tính, không nhắc brand.",
        ])
        bypass.extend(make_safe_brand_variants(base))
    elif top_label == "Slogan":
        owner = FAMOUS_SLOGANS.get(normalized, "brand lớn")
        safe.extend([
            f"Tránh dùng nguyên slogan gắn với {owner}.",
            "Đổi sang câu mới cùng tinh thần nhưng khác cấu trúc.",
        ])
        bypass.extend(make_safe_slogan_variants(base))
    elif top_label == "Public figure" or top_label == "Politics":
        safe.extend([
            f"Tránh dùng trực tiếp tên {resolved_term}.",
            "Bỏ yếu tố người thật hoặc chính trị, đổi sang chủ đề trung tính.",
        ])
        bypass.extend(make_safe_public_figure_variants(base))
    elif top_label in ("Music", "Pop culture", "Copyright"):
        safe.extend([
            f"Tránh dùng trực tiếp tên {resolved_term} nếu đây là IP/nội dung giải trí.",
            "Đổi sang mô tả cảm hứng chung, không nhắc tên tác phẩm/nhân vật.",
        ])
        bypass.extend(make_safe_pop_culture_variants(base))
    else:
        safe.extend([
            "Tránh giữ nguyên từ khóa nếu còn nghi ngờ.",
            "Ưu tiên tên mô tả trung tính, không nhắc brand/người nổi tiếng.",
        ])
        bypass.extend(make_variants(base, ["studio", "wear", "lab", "style"]))

    return {
        "bypass": dedupe_preserve_order([item for item in bypass if item]),
        "safe": dedupe_preserve_order([item for item in safe if item]),
    }


def make_variants(base: str, suffixes: list[str]) -> list[str]:
    root = simplify_term(base)
    variants: list[str] = []
    for suffix in suffixes:
        if not root:
            continue
        variants.append(f"{root} {suffix}".strip())
    return variants[:4]


def make_safe_brand_variants(base: str) -> list[str]:
    core = strip_risky_terms(base)
    if not core:
        return [
            "Classic street wear",
            "Urban motion tee",
            "Everyday sport style",
            "Minimal active shirt",
        ]
    return [
        f"{core} street wear",
        f"{core} urban line",
        f"{core} daily fit",
        f"{core} active style",
    ]


def make_safe_slogan_variants(base: str) -> list[str]:
    core = strip_risky_terms(base)
    if not core or len(core.split()) <= 1:
        return [
            "Make your move",
            "Go for more",
            "Create your path",
            "Rise and move",
        ]
    return [
        f"{core} your move",
        f"{core} for more",
        f"{core} your path",
        f"{core} and rise",
    ]


def make_safe_public_figure_variants(base: str) -> list[str]:
    core = strip_person_terms(base)
    if not core or core == "neutral":
        return [
            "Election theme shirt",
            "Debate quote design",
            "Political humor tee",
            "Campaign style graphic",
        ]
    return [
        f"{core} theme shirt",
        f"{core} quote design",
        f"{core} style graphic",
        f"{core} edition tee",
    ]


def make_safe_pop_culture_variants(base: str) -> list[str]:
    core = strip_risky_terms(base)
    if not core:
        return [
            "Classic adventure tee",
            "Retro fantasy shirt",
            "Animated vibe design",
            "Fiction inspired graphic",
        ]
    return [
        f"{core} inspired graphic",
        f"{core} retro design",
        f"{core} fantasy style",
        f"{core} adventure tee",
    ]


def simplify_term(value: str) -> str:
    cleaned = normalize_space(value)
    if not cleaned:
        return ""
    tokens = [token for token in re.split(r"[\s,_-]+", cleaned) if token]
    stop_words = {"the", "a", "an", "shirt", "tshirt", "t-shirt", "tee"}
    kept = [token for token in tokens if token.lower() not in stop_words]
    return " ".join(kept[:2]) if kept else cleaned


def strip_risky_terms(value: str) -> str:
    cleaned = simplify_term(value)
    risky_phrases = (
        list(FAMOUS_BRAND_KEYWORDS)
        + list(FAMOUS_PERSON_KEYWORDS)
        + list(FAMOUS_SLOGANS.keys())
        + list(POP_CULTURE_KEYWORDS)
    )
    risky_tokens = {
        token
        for phrase in risky_phrases
        for token in phrase.lower().replace("'", " ").split()
    }
    kept = [token for token in cleaned.replace("'", " ").split() if token.lower() not in risky_tokens]
    return " ".join(kept).strip()


def strip_person_terms(value: str) -> str:
    cleaned = simplify_term(value)
    person_tokens = {"donald", "trump", "taylor", "swift", "ronaldo", "messi", "bts"}
    kept = [token for token in cleaned.split() if token.lower() not in person_tokens]
    return " ".join(kept) or "neutral"


def build_top_label(
    term: str,
    context_tags: list[str],
    trademark_analysis: dict[str, Any],
    copyright_analysis: dict[str, Any],
    public_figure_analysis: dict[str, Any],
    is_famous_slogan: bool,
    is_famous_brand: bool,
    is_famous_person: bool,
    is_political: bool,
) -> str:
    normalized_term = term.lower().strip()
    if is_political:
        return "Politics"
    if is_famous_slogan:
        return "Slogan"
    if public_figure_analysis["score"] >= max(trademark_analysis["score"], copyright_analysis["score"]) and (
        is_famous_person or public_figure_analysis["score"] >= 35
    ):
        return "Public figure"
    if copyright_analysis["score"] >= max(trademark_analysis["score"], public_figure_analysis["score"]):
        if normalized_term in POP_CULTURE_KEYWORDS:
            return "Pop culture"
        if "Music" in context_tags:
            return "Music"
        return "Copyright"
    if is_famous_brand or trademark_analysis["score"] >= 35:
        return "Brand"
    if context_tags:
        return context_tags[0]
    return "Review"


def detect_context_tags(term: str, combined_text: str) -> list[str]:
    normalized_term = term.lower().strip()
    tags: list[str] = []
    if any(keyword in combined_text for keyword in ("movie", "film", "tv series")) or normalized_term in POP_CULTURE_KEYWORDS:
        tags.append("Phim / văn hóa đại chúng")
    if any(keyword in combined_text for keyword in ("meme", "viral", "internet culture")):
        tags.append("Meme / văn hóa mạng")
    if phat_hien_tin_hieu_chinh_tri(term, combined_text):
        tags.append("Politics")
    if phat_hien_tin_hieu_am_nhac(term, combined_text):
        tags.append("Music")
    return tags


def phat_hien_tin_hieu_chinh_tri(term: str, combined_text: str) -> bool:
    normalized_term = term.lower().strip()
    if normalized_term in POP_CULTURE_KEYWORDS:
        return False
    if any(hint in combined_text for hint in FICTIONAL_CONTEXT_HINTS):
        return False
    return contains_phrase(combined_text, POLITICAL_KEYWORDS)


def phat_hien_tin_hieu_am_nhac(term: str, combined_text: str) -> bool:
    normalized_term = term.lower().strip()
    if normalized_term not in FAMOUS_PERSON_KEYWORDS and normalized_term not in POP_CULTURE_KEYWORDS:
        if not contains_phrase(combined_text, STRONG_MUSIC_HINTS):
            return False
    if contains_phrase(combined_text, ("rabbit", "animal", "mammal", "species", "pet")):
        return False
    return True


def tao_ly_do_van_hoa_dai_chung(normalized_term: str) -> str:
    display_name = to_display_name(normalized_term)
    context = POP_CULTURE_CONTEXT.get(normalized_term, "")
    if context and context.lower() != normalized_term:
        return f"Trùng IP/nhân vật {display_name} trong {context}"
    return f"Trùng IP văn hóa đại chúng {display_name}"


def prioritize_specific_reasons(reasons: list[str]) -> list[str]:
    reasons = merge_related_ip_reasons(reasons)
    specific_markers = ("Trùng", "Liên quan", "Slogan", "Có copyright gián tiếp")
    ordered = sorted(
        reasons,
        key=lambda reason: (
            0 if reason.startswith(specific_markers) else 1,
            len(reason),
        ),
    )
    seen: set[str] = set()
    result: list[str] = []
    for reason in ordered:
        if reason in seen:
            continue
        seen.add(reason)
        result.append(reason)
    return result


def merge_related_ip_reasons(reasons: list[str]) -> list[str]:
    normalized_reasons = list(reasons)
    for brand in FAMOUS_BRAND_KEYWORDS:
        display = to_display_name(brand)
        related = [
            reason
            for reason in normalized_reasons
            if display.lower() in reason.lower()
            and any(marker in reason for marker in ("Trùng IP", "Trùng thương hiệu", "IP văn hóa"))
        ]
        if len(related) < 2:
            continue
        generic_noise = {
            "Có tín hiệu âm nhạc",
            "Tên giống thương hiệu",
            "Có dấu hiệu IP/thương hiệu",
            "Tên xuất hiện lặp lại trong kết quả tìm kiếm",
        }
        normalized_reasons = [
            reason
            for reason in normalized_reasons
            if reason not in related and reason not in generic_noise
        ]
        normalized_reasons.append(f"Trùng IP/thương hiệu lớn {display}")
    for person in FAMOUS_PERSON_KEYWORDS:
        display = FAMOUS_PERSON_DISPLAY.get(person, to_display_name(person))
        related = [
            reason
            for reason in normalized_reasons
            if display.lower() in reason.lower()
            and any(marker in reason for marker in ("Trùng nhóm nhạc", "Trùng public figure", "Có tín hiệu âm nhạc"))
        ]
        if person in {"donald trump", "trump", "biden", "obama"}:
            political_related = [
                reason
                for reason in normalized_reasons
                if reason in {"Liên quan chính trị", "Trùng nhân vật chính trị"}
                or (display.lower() in reason.lower() and "public figure" in reason.lower())
            ]
            if len(political_related) >= 2:
                normalized_reasons = [
                    reason
                    for reason in normalized_reasons
                    if reason not in political_related
                    and reason not in {"Có tín hiệu âm nhạc", "Thiên về tên người", "Giống tên người thật"}
                ]
                normalized_reasons.append(f"Trùng nhân vật chính trị/public figure {display}")
                continue
        if len(related) < 2:
            continue
        if person in {"bts", "blackpink", "newjeans", "ive", "twice", "exo", "seventeen"}:
            normalized_reasons = [
                reason
                for reason in normalized_reasons
                if reason not in related
                and reason not in {"Có tín hiệu âm nhạc", "Thiên về tên người", "Giống tên người thật"}
            ]
            normalized_reasons.append(f"Trùng nhóm nhạc/public figure {display}")
        else:
            normalized_reasons = [
                reason
                for reason in normalized_reasons
                if reason not in related
                and reason not in {"Có tín hiệu âm nhạc", "Thiên về tên người", "Giống tên người thật"}
            ]
            normalized_reasons.append(f"Trùng public figure {display}")
    return normalized_reasons


def infer_entity_type(evidence_text: str) -> str:
    compact = normalize_space(remove_accents(evidence_text.lower()))
    if contains_phrase(compact, PEOPLE_HINTS):
        return "Con người"
    if contains_phrase(compact, ("company", "brand", "startup", "corporation", "business")):
        return "Công ty hoặc brand"
    if contains_phrase(compact, ("software", "application", "platform", "service", "tool")):
        return "Sản phẩm hoặc dịch vụ số"
    return "Chưa rõ"


def extract_birth_year(evidence_text: str) -> str:
    compact = remove_accents(evidence_text.lower())
    patterns = (
        r"\bborn\s+in\s+(\d{4})\b",
        r"\bborn\s+(\d{4})\b",
        r"\((?:born\s+)?(\d{4})[-\u2013]",
        r"\bsinh nam\s+(\d{4})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, compact)
        if match:
            return match.group(1)
    return ""


def fetch_json(url: str) -> Any:
    return json.loads(fetch_text(url))


def fetch_text(url: str) -> str:
    request = Request(url, headers=DEFAULT_HEADERS)
    with urlopen(request, timeout=10) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def strip_html(raw_html: str) -> str:
    text = re.sub(r"<.*?>", " ", raw_html)
    return normalize_space(unescape(text))


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def remove_accents(value: str) -> str:
    source = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    target = "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
    return value.translate(str.maketrans(source, target))


def first_non_empty(values: list[str]) -> str:
    for value in values:
        cleaned = normalize_space(value)
        if cleaned:
            return cleaned
    return ""


def choose_best_result(results: list[SearchResult]) -> SearchResult | None:
    scored_results = []
    for result in results:
        snippet = normalize_space(result.snippet)
        if not snippet:
            continue
        score = len(snippet)
        lowered = f"{result.title} {snippet}".lower()
        if "may refer to" in lowered:
            score -= 200
        if any(keyword in lowered for keyword in PEOPLE_HINTS):
            score += 40
        if any(keyword in lowered for keyword in ("company", "brand", "product", "service")):
            score += 25
        scored_results.append((score, result))

    if not scored_results:
        return None
    scored_results.sort(key=lambda item: item[0], reverse=True)
    return scored_results[0][1]


def infer_term_from_results(original_term: str, results: list[SearchResult]) -> str:
    candidates: dict[str, int] = {}
    original_lower = original_term.lower()

    for result in results[:5]:
        for candidate in split_title_candidates(result.title):
            cleaned = cleanup_candidate(candidate)
            if not cleaned:
                continue
            lowered = cleaned.lower()
            score = 0
            if lowered in original_lower:
                score += 40
            if len(cleaned.split()) <= 5:
                score += 15
            if lowered in result.snippet.lower():
                score += 20
            if any(char.isupper() for char in cleaned):
                score += 10
            candidates[cleaned] = max(candidates.get(cleaned, 0), score)

    if not candidates:
        return ""
    return max(candidates.items(), key=lambda item: item[1])[0]


def split_title_candidates(title: str) -> list[str]:
    separators = (" - ", " | ", " – ", ": ")
    parts = [title]
    for separator in separators:
        next_parts: list[str] = []
        for part in parts:
            next_parts.extend(part.split(separator))
        parts = next_parts
    return [part.strip() for part in parts if part.strip()]


def cleanup_candidate(value: str) -> str:
    cleaned = normalize_space(re.sub(r"\s*\([^)]*\)", "", value))
    cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cleaned)
    if not cleaned:
        return ""
    if len(cleaned.split()) > 6:
        return ""
    generic_phrases = {
        "wikipedia",
        "official site",
        "official website",
        "search results",
        "home",
        "news",
    }
    if cleaned.lower() in generic_phrases:
        return ""
    return cleaned


def extract_quoted_term(text: str) -> str:
    match = re.search(r'"([^"]+)"', text) or re.search(r"'([^']+)'", text)
    if match:
        return normalize_space(match.group(1))
    return ""


def extract_known_entities_from_input(text: str) -> list[str]:
    compact = normalize_space(remove_accents(text.lower()))
    candidates = sorted(
        set(FAMOUS_PERSON_KEYWORDS + FAMOUS_BRAND_KEYWORDS + tuple(FAMOUS_SLOGANS.keys()) + POP_CULTURE_KEYWORDS),
        key=lambda item: len(item),
        reverse=True,
    )
    matches: list[str] = []
    for candidate in candidates:
        if contains_phrase(compact, (candidate,)):
            matches.append(to_display_name(candidate))
    matches = dedupe_preserve_order(matches)
    return remove_substring_duplicates(matches)


def extract_input_entity_candidates(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9'&.-]*", normalize_space(text))
    if not tokens:
        return []

    meaningful = [token for token in tokens if token.lower() not in GENERIC_INPUT_WORDS]
    if not meaningful:
        return []

    candidates: list[str] = []
    max_window = min(3, len(meaningful))
    for window in range(max_window, 0, -1):
        for start in range(0, len(meaningful) - window + 1):
            chunk = meaningful[start : start + window]
            candidate = normalize_space(" ".join(chunk))
            if not candidate:
                continue
            if candidate.lower() in GENERIC_INPUT_WORDS:
                continue
            if len(candidate) <= 2:
                continue
            candidates.append(candidate)

    candidates = dedupe_preserve_order([to_display_name(candidate) for candidate in candidates])
    return remove_substring_duplicates(candidates[:3])


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def remove_substring_duplicates(values: list[str]) -> list[str]:
    kept: list[str] = []
    lowered_values = [value.lower() for value in values]
    for index, value in enumerate(values):
        lowered = lowered_values[index]
        is_substring = False
        for other_index, other in enumerate(lowered_values):
            if index == other_index:
                continue
            if lowered != other and lowered in other:
                is_substring = True
                break
        if not is_substring:
            kept.append(value)
    return kept


def to_display_name(value: str) -> str:
    special_names = {
        "coca cola": "Coca-Cola",
        "coca-cola": "Coca-Cola",
        "bts": "BTS",
        "blackpink": "BLACKPINK",
        "newjeans": "NewJeans",
        "ive": "IVE",
        "twice": "TWICE",
        "exo": "EXO",
        "seventeen": "SEVENTEEN",
        "disney": "Disney",
        "pikachu": "Pikachu",
        "pokemon": "Pokemon",
        "marvel": "Marvel",
        "avengers": "Avengers",
        "harry potter": "Harry Potter",
        "hogwarts": "Hogwarts",
        "nike": "Nike",
        "adidas": "Adidas",
        "gucci": "Gucci",
        "louis vuitton": "Louis Vuitton",
        "hello kitty": "Hello Kitty",
        "mcdonald": "McDonald",
        "apple": "Apple",
        "samsung": "Samsung",
        "spotify": "Spotify",
        "netflix": "Netflix",
        "google": "Google",
        "youtube": "YouTube",
        "tiktok": "TikTok",
        "donald trump": "Donald Trump",
        "trump": "Trump",
        "taylor swift": "Taylor Swift",
        "drake": "Drake",
        "eminem": "Eminem",
        "rihanna": "Rihanna",
        "beyonce": "Beyonce",
        "justin bieber": "Justin Bieber",
        "messi": "Messi",
        "ronaldo": "Ronaldo",
        "neymar": "Neymar",
        "lebron james": "LeBron James",
        "lionel messi": "Lionel Messi",
        "cristiano ronaldo": "Cristiano Ronaldo",
        "michael jordan": "Michael Jordan",
        "kobe bryant": "Kobe Bryant",
    }
    return special_names.get(value.lower(), value.title())


def build_top_matches(results: list[SearchResult]) -> list[str]:
    matches: list[str] = []
    for result in results[:2]:
        title = normalize_space(result.title)
        snippet = normalize_space(result.snippet)
        if title and snippet:
            matches.append(f"{title}: {shorten_text(snippet, 90)}")
        elif title:
            matches.append(title)
    return matches


def is_ambiguous_summary(text: str) -> bool:
    compact = normalize_space(text).lower()
    ambiguous_markers = (
        "may refer to",
        "can refer to",
        "refer to",
        "có thể đề cập đến",
        "có thể là",
    )
    return any(marker in compact for marker in ambiguous_markers)


def has_google_api_credentials() -> bool:
    api_key = (settings.GOOGLE_API_KEY or "").strip()
    cse_id = (settings.GOOGLE_CSE_ID or "").strip()
    invalid_values = {"", "YOUR_GOOGLE_API_KEY", "YOUR_CX", "YOUR_GOOGLE_CSE_ID"}
    return api_key not in invalid_values and cse_id not in invalid_values


def contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    for phrase in phrases:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        if re.search(pattern, text):
            return True
    return False


def translate_text(text: str, target_lang: str = "vi") -> str:
    cleaned = normalize_space(text)
    if not cleaned:
        return ""

    try:
        data = fetch_json(
            "https://translate.googleapis.com/translate_a/single?"
            + urlencode(
                {
                    "client": "gtx",
                    "sl": "auto",
                    "tl": target_lang,
                    "dt": "t",
                    "q": cleaned,
                }
            )
        )
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return ""

    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        return ""

    translated_parts: list[str] = []
    for item in data[0]:
        if isinstance(item, list) and item:
            translated_parts.append(item[0])
    return normalize_space("".join(translated_parts))


def shorten_text(text: str, limit: int) -> str:
    cleaned = normalize_space(text)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[:limit].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."


def choose_display_image(wiki_summary: dict[str, str], results: list[SearchResult]) -> str:
    image = normalize_space(wiki_summary.get("image", ""))
    if image:
        return image
    for result in results:
        if normalize_space(result.image):
            return result.image
    return ""


def extract_google_result_image(item: dict[str, Any]) -> str:
    pagemap = item.get("pagemap", {})
    thumbnails = pagemap.get("cse_thumbnail", [])
    if thumbnails:
        src = normalize_space(thumbnails[0].get("src", ""))
        if src:
            return src
    metatags = pagemap.get("metatags", [])
    for tag in metatags:
        for key in ("og:image", "twitter:image"):
            value = normalize_space(tag.get(key, ""))
            if value:
                return value
    return ""


def normalize_duckduckgo_image(value: str) -> str:
    image = normalize_space(value)
    if not image:
        return ""
    if image.startswith("//"):
        return f"https:{image}"
    if image.startswith("/"):
        return f"https://duckduckgo.com{image}"
    return image
