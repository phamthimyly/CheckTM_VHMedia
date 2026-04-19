import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urlparse
from urllib.request import Request, urlopen

from django.conf import settings


TIEU_DE_MAC_DINH = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

GOI_Y_CON_NGUOI = (
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

GOI_Y_NGUOI_CONG_CHUNG = (
    "singer",
    "singer-songwriter",
    "songwriter",
    "musician",
    "rapper",
    "recording artist",
    "music artist",
    "actor",
    "actress",
    "footballer",
    "athlete",
    "politician",
    "president",
    "youtuber",
    "influencer",
    "celebrity",
    "public figure",
)

TU_KHOA_THUONG_HIEU = (
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

CLASS_TRADEMARK_POD_LIEN_QUAN = {
    16: "poster, lịch, ấn phẩm giấy",
    21: "cốc, ly, đồ gia dụng",
    25: "áo thun, hoodie, sweater, quần áo",
}

TU_KHOA_CHINH_TRI = (
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

GOI_Y_NGU_CANH_HU_CAU = (
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

TU_KHOA_THUONG_HIEU_LON = (
    "coca cola",
    "coca-cola",
    "disney",
    "pikachu",
    "pokemon",
    "mickey mouse",
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

SLOGAN_NOI_TIENG = {
    "just do it": "Nike",
    "i'm lovin' it": "McDonald's",
    "im lovin it": "McDonald's",
    "think different": "Apple",
    "because you're worth it": "L'Oreal",
}

TEN_HIEN_THI_NGUOI_NOI_TIENG = {
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

TU_KHOA_NGUOI_NOI_TIENG = (
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

GOI_Y_IP_THUONG_HIEU = (
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

TU_KHOA_BAN_QUYEN = (
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

TU_KHOA_VAN_HOA_DAI_CHUNG = (
    "kill bill",
    "barbie",
    "barbie girl",
    "pokemon",
    "pikachu",
    "mickey mouse",
    "mickey",
    "marvel",
    "avengers",
    "disney",
    "harry potter",
    "hogwarts",
    "star wars",
    "batman",
    "superman",
    "snoopy",
    "minions",
)

NGU_CANH_VAN_HOA_DAI_CHUNG = {
    "hogwarts": "Harry Potter",
    "harry potter": "Harry Potter",
    "avengers": "Marvel",
    "pikachu": "Pokemon",
    "pokemon": "Pokemon",
    "mickey": "Disney",
    "mickey mouse": "Disney",
    "barbie": "Barbie",
    "barbie girl": "Barbie",
    "kill bill": "Kill Bill",
    "star wars": "Star Wars",
}

TU_KHOA_BAN_QUYEN_AM_NHAC = (
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

GOI_Y_AM_NHAC_MANH = (
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

TU_CHUNG_DAU_VAO = {
    "a",
    "an",
    "and",
    "art",
    "brand",
    "cap",
    "classic",
    "cool",
    "concert",
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
    "tour",
    "tshirt",
    "t-shirt",
    "vintage",
    "wear",
    "with",
}


@dataclass
class KetQuaTimKiem:
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


def lay_bao_cao_tu_khoa(term: str) -> dict[str, Any]:
    tu_khoa_goc = chuan_hoa_khoang_trang(term)
    tu_khoa_ung_vien = tach_tu_khoa_chinh(tu_khoa_goc)
    cac_bao_cao = tao_bao_cao_ung_vien(tu_khoa_ung_vien, tu_khoa_goc)
    bao_cao_chinh = chon_bao_cao_chinh(cac_bao_cao, tu_khoa_goc)
    tu_khoa_da_chon = bao_cao_chinh["term"]
    ket_qua_web = bao_cao_chinh["results"]
    tom_tat_wiki = bao_cao_chinh["wiki_summary"]
    tom_tat = bao_cao_chinh["summary"]
    danh_gia = bao_cao_chinh["trademark"]
    de_xuat = tao_de_xuat(
        original_term=tu_khoa_goc,
        resolved_term=tu_khoa_da_chon,
        trademark=danh_gia,
        summary=tom_tat,
    )
    return {
        "term": tu_khoa_da_chon,
        "original_term": tu_khoa_goc,
        "resolved_from_input": tu_khoa_da_chon != tu_khoa_goc,
        "summary": tom_tat,
        "trademark": danh_gia,
        "suggested_fix": de_xuat,
        "results": ket_qua_web[:5],
        "wiki_summary": tom_tat_wiki,
        "display_image": chon_anh_hien_thi(tom_tat_wiki, ket_qua_web),
        "used_google_api": co_cau_hinh_google_api(),
        "detected_terms": [bao_cao["term"] for bao_cao in cac_bao_cao],
        "all_reports": cac_bao_cao,
    }


def lay_ket_qua_tim_kiem(term: str) -> list[KetQuaTimKiem]:
    if co_cau_hinh_google_api():
        try:
            api_results = lay_ket_qua_google_api(term)
            if api_results:
                return api_results
        except (HTTPError, URLError, TimeoutError, ValueError):
            pass

    html_results = lay_ket_qua_google_html(term)
    if html_results:
        return html_results

    try:
        return lay_ket_qua_duckduckgo(term)
    except (HTTPError, URLError, TimeoutError, ValueError):
        return []


def tach_tu_khoa_chinh(term: str) -> list[str]:
    cleaned = chuan_hoa_khoang_trang(term)
    if not cleaned:
        return []

    quoted = trich_xuat_tu_trong_ngoac(cleaned)
    if quoted:
        return [quoted]

    direct_matches = trich_xuat_thuc_the_da_biet(cleaned)

    if len(cleaned.split()) <= 2:
        ket_qua_ban_dau = lay_ket_qua_tim_kiem(cleaned)
        ten_day_du = suy_luan_tu_khoa_tu_ket_qua(cleaned, ket_qua_ban_dau)
        if nen_uu_tien_tu_khoa_suy_luan(cleaned, ten_day_du):
            return [ten_day_du]
        return [cleaned]

    phan_chua_biet = bo_cum_da_biet_khoi_cau(cleaned, direct_matches)
    input_candidates = trich_xuat_ung_vien_dau_vao(phan_chua_biet)
    candidates = loc_ung_vien_check([*direct_matches, *input_candidates])
    if candidates:
        return candidates

    if len(cleaned.split()) <= 4:
        return [cleaned]

    initial_results = lay_ket_qua_tim_kiem(cleaned)
    inferred = suy_luan_tu_khoa_tu_ket_qua(cleaned, initial_results)
    return [inferred or cleaned]


def tao_bao_cao_ung_vien(
    candidates: list[str],
    original_term: str,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = chuan_hoa_khoang_trang(candidate)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)

        results = lay_ket_qua_tim_kiem(cleaned)
        wiki_summary = lay_tom_tat_wikipedia(cleaned)
        summary = tao_tom_tat(results, wiki_summary)
        trademark = danh_gia_rui_ro_trademark(cleaned, results, wiki_summary, summary)
        reports.append(
            {
                "term": cleaned,
                "results": results,
                "wiki_summary": wiki_summary,
                "display_image": chon_anh_hien_thi(wiki_summary, results),
                "summary": summary,
                "trademark": trademark,
                "suggested_fix": tao_de_xuat(
                    original_term=original_term,
                    resolved_term=cleaned,
                    trademark=trademark,
                    summary=summary,
                ),
            }
        )

    if reports:
        return reports

    fallback_results = lay_ket_qua_tim_kiem(original_term)
    fallback_wiki = lay_tom_tat_wikipedia(original_term)
    fallback_summary = tao_tom_tat(fallback_results, fallback_wiki)
    fallback_trademark = danh_gia_rui_ro_trademark(
        original_term, fallback_results, fallback_wiki, fallback_summary
    )
    return [
        {
            "term": original_term,
            "results": fallback_results,
            "wiki_summary": fallback_wiki,
            "display_image": chon_anh_hien_thi(fallback_wiki, fallback_results),
            "summary": fallback_summary,
            "trademark": fallback_trademark,
            "suggested_fix": tao_de_xuat(
                original_term=original_term,
                resolved_term=original_term,
                trademark=fallback_trademark,
                summary=fallback_summary,
            ),
        }
    ]


def chon_bao_cao_chinh(reports: list[dict[str, Any]], original_term: str) -> dict[str, Any]:
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


def lay_ket_qua_google_api(term: str) -> list[KetQuaTimKiem]:
    params = urlencode(
        {
            "key": settings.GOOGLE_API_KEY,
            "cx": settings.GOOGLE_CSE_ID,
            "q": term,
            "num": 5,
        }
    )
    data = lay_json(f"https://www.googleapis.com/customsearch/v1?{params}")
    items = data.get("items", [])
    return [
        KetQuaTimKiem(
            title=item.get("title", "").strip(),
            snippet=item.get("snippet", "").strip(),
            link=item.get("link", "").strip(),
            source="Google Custom Search",
            image=trich_xuat_anh_google(item),
        )
        for item in items
        if item.get("title") and item.get("link")
    ]


def lay_ket_qua_google_html(term: str) -> list[KetQuaTimKiem]:
    try:
        html = lay_text(f"https://www.google.com/search?hl=en&q={quote_plus(term)}")
    except (HTTPError, URLError, TimeoutError):
        return []

    blocks = re.findall(r'<div class="g".*?</div></div></div>', html, flags=re.DOTALL)
    results: list[KetQuaTimKiem] = []
    for block in blocks:
        title_match = re.search(r"<h3.*?>(.*?)</h3>", block, flags=re.DOTALL)
        link_match = re.search(r'<a href="/url\?q=(.*?)&amp;', block, flags=re.DOTALL)
        snippet_match = re.search(r'<div class="VwiC3b.*?">(.*?)</div>', block, flags=re.DOTALL)
        if not title_match or not link_match:
            continue

        title = bo_html(title_match.group(1))
        link = unescape(link_match.group(1))
        snippet = bo_html(snippet_match.group(1)) if snippet_match else ""
        if title and link.startswith("http"):
            results.append(
                KetQuaTimKiem(
                    title=title,
                    snippet=snippet,
                    link=link,
                    source="Google Search",
                )
            )
        if len(results) >= 5:
            break
    return results


def lay_ket_qua_duckduckgo(term: str) -> list[KetQuaTimKiem]:
    data = lay_json(
        "https://api.duckduckgo.com/?"
        + urlencode({"q": term, "format": "json", "no_html": 1, "skip_disambig": 1})
    )
    results: list[KetQuaTimKiem] = []

    abstract = chuan_hoa_khoang_trang(data.get("AbstractText", ""))
    if abstract:
        results.append(
            KetQuaTimKiem(
                title=data.get("Heading", term),
                snippet=abstract,
                link=data.get("AbstractURL", f"https://duckduckgo.com/?q={quote_plus(term)}"),
                source="DuckDuckGo Instant Answer",
                image=chuan_hoa_anh_duckduckgo(data.get("Image", "")),
            )
        )

    for topic in data.get("RelatedTopics", []):
        entries = topic.get("Topics", [topic])
        for entry in entries:
            text = chuan_hoa_khoang_trang(entry.get("Text", ""))
            first_url = entry.get("FirstURL", "")
            if text and first_url:
                results.append(
                    KetQuaTimKiem(
                        title=text.split(" - ")[0][:90],
                        snippet=text,
                        link=first_url,
                        source="DuckDuckGo",
                    )
                )
            if len(results) >= 5:
                return results
    return results


def lay_tom_tat_wikipedia(term: str) -> dict[str, str]:
    try:
        search_data = lay_json(
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
        summary_data = lay_json(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}"
        )
    except (HTTPError, URLError, TimeoutError):
        return {}

    return {
        "title": summary_data.get("title", ""),
        "extract": chuan_hoa_khoang_trang(summary_data.get("extract", "")),
        "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "image": summary_data.get("thumbnail", {}).get("source", ""),
    }


def tao_tom_tat(results: list[KetQuaTimKiem], wiki_summary: dict[str, str]) -> dict[str, Any]:
    cac_doan_du_lieu = [wiki_summary.get("extract", "")]
    cac_doan_du_lieu.extend(result.snippet for result in results if result.snippet)
    van_ban_doi_chieu = f" {' '.join(cac_doan_du_lieu)} ".lower()

    loai_thuc_the = suy_luan_loai_thuc_the(van_ban_doi_chieu)
    nam_sinh = trich_xuat_nam_sinh(van_ban_doi_chieu)
    mo_ta_wiki = wiki_summary.get("extract", "")
    ket_qua_tot_nhat = chon_ket_qua_tot_nhat(results)
    mo_ta_tu_ket_qua = ket_qua_tot_nhat.snippet if ket_qua_tot_nhat else lay_gia_tri_dau_tien([result.snippet for result in results])
    bi_nhieu_nghia = tom_tat_nhieu_nghia(mo_ta_wiki)

    if mo_ta_wiki and not bi_nhieu_nghia:
        overview = dich_van_ban(mo_ta_wiki, target_lang="vi") or mo_ta_wiki
    elif mo_ta_tu_ket_qua:
        overview = dich_van_ban(mo_ta_tu_ket_qua, target_lang="vi") or mo_ta_tu_ket_qua
    elif mo_ta_wiki:
        overview = dich_van_ban(mo_ta_wiki, target_lang="vi") or mo_ta_wiki
    else:
        overview = "Chưa lấy được mô tả rõ ràng cho từ khóa này."
    overview = rut_gon_van_ban(overview, 220)

    thong_tin_ngan: list[str] = []
    if loai_thuc_the:
        thong_tin_ngan.append(f"Loại: {loai_thuc_the}.")
    if nam_sinh:
        thong_tin_ngan.append(f"Năm sinh: {nam_sinh}.")
    if results:
        thong_tin_ngan.append(f"Kết quả tham khảo: {len(results)}.")
    if wiki_summary.get("url"):
        thong_tin_ngan.append("Có thêm nguồn Wikipedia.")
    if bi_nhieu_nghia:
        thong_tin_ngan.append("Từ khóa này có thể đang mang nhiều nghĩa.")

    return {
        "overview": overview,
        "facts": thong_tin_ngan,
        "entity_type": loai_thuc_the,
        "birth_year": nam_sinh,
        "top_matches": tao_ket_qua_trung_khop(results),
    }


def danh_gia_rui_ro_trademark(
    term: str,
    results: list[KetQuaTimKiem],
    wiki_summary: dict[str, str],
    summary: dict[str, Any],
) -> dict[str, Any]:
    van_ban_gop = " ".join(
        [wiki_summary.get("extract", "")]
        + [result.title for result in results]
        + [result.snippet for result in results]
    ).lower()
    tu_khoa_chuan = term.lower().strip()
    co_tin_hieu_chinh_tri = phat_hien_tin_hieu_chinh_tri(term, van_ban_gop)
    la_thuong_hieu_lon = tu_khoa_chuan in TU_KHOA_THUONG_HIEU_LON
    la_nguoi_noi_tieng = tu_khoa_chuan in TU_KHOA_NGUOI_NOI_TIENG
    la_slogan_noi_tieng = tu_khoa_chuan in SLOGAN_NOI_TIENG
    co_tin_hieu_ip_brand = any(keyword in van_ban_gop for keyword in GOI_Y_IP_THUONG_HIEU)
    loai_thuc_the = summary.get("entity_type")

    ly_do: list[str] = []
    diem = 0

    if any(keyword in van_ban_gop for keyword in ("registered trademark", "trademark", "®", " tm ")):
        diem += 45
        ly_do.append("Có nhắc trực tiếp trademark")

    if any(keyword in van_ban_gop for keyword in TU_KHOA_THUONG_HIEU):
        diem += 30
        ly_do.append("Tên giống thương hiệu")

    if summary.get("entity_type") == "Con người":
        diem -= 25
        ly_do.append("Thiên về tên người")

    if len(tu_khoa_chuan.split()) <= 3 and tu_khoa_chuan.isascii():
        diem += 10

    so_lan_nhac_ten = sum(1 for result in results if tu_khoa_chuan in result.title.lower())
    if so_lan_nhac_ten >= 2:
        diem += 15
        ly_do.append("Tên xuất hiện lặp lại trong kết quả tìm kiếm")

    if co_tin_hieu_ip_brand:
        diem += 25
        ly_do.append("Có dấu hiệu IP/thương hiệu")

    if la_thuong_hieu_lon:
        diem = max(diem, 85)
        ly_do.append(f"Trùng thương hiệu {tao_ten_hien_thi(tu_khoa_chuan)}")

    if la_slogan_noi_tieng:
        diem = max(diem, 88)
        ly_do.append(f"Trùng slogan của {SLOGAN_NOI_TIENG[tu_khoa_chuan]}")

    if la_nguoi_noi_tieng:
        diem = max(diem, 82)
        ly_do.append(f"Trùng public figure {TEN_HIEN_THI_NGUOI_NOI_TIENG.get(tu_khoa_chuan, tao_ten_hien_thi(tu_khoa_chuan))}")

    if co_tin_hieu_chinh_tri:
        diem = max(diem, 70)
        ly_do.append("Liên quan chính trị")

    cac_class_trademark = trich_xuat_class_trademark(van_ban_gop)
    ngu_canh_class = tao_ngu_canh_class(cac_class_trademark)
    if ngu_canh_class["status"] == "non_relevant" and diem > 0:
        diem = min(diem, 30)
        ly_do.append("Trademark không nằm trong class sản phẩm POD của công ty")
    elif ngu_canh_class["status"] == "relevant" and diem > 0:
        diem = max(diem, 65)
        ly_do.append(f"Trademark có class liên quan POD: {ngu_canh_class['classes_text']}")

    phan_tich_ban_quyen = danh_gia_rui_ro_ban_quyen(
        term=term,
        combined_text=van_ban_gop,
        is_famous_brand=la_thuong_hieu_lon,
        has_ip_brand_signals=co_tin_hieu_ip_brand,
        is_famous_slogan=la_slogan_noi_tieng,
    )
    phan_tich_nguoi_noi_tieng = danh_gia_rui_ro_nguoi_noi_tieng(
        term=term,
        combined_text=van_ban_gop,
        is_political=co_tin_hieu_chinh_tri,
        is_famous_person=la_nguoi_noi_tieng,
        entity_type=loai_thuc_the,
    )

    phan_tich_trademark = tao_khoi_phan_tich(
        title="Trademark risk",
        score=diem,
        reasons=ly_do,
        high_label="Có đăng ký hoặc sử dụng thương hiệu rất mạnh",
        medium_label="Có dấu hiệu liên quan đến thương hiệu",
        low_label=(
            "Trademark không trùng class sản phẩm của công ty"
            if ngu_canh_class["status"] == "non_relevant"
            else "Chưa thấy dấu hiệu thương hiệu mạnh"
        ),
    )
    nhan_ngu_canh = phat_hien_nhan_ngu_canh(term, van_ban_gop)

    phan_tich_quyen_so_huu_tri_tue = tao_phan_tich_quyen_so_huu_tri_tue(
        phan_tich_trademark,
        phan_tich_ban_quyen,
        phan_tich_nguoi_noi_tieng,
    )
    cac_phan_tich = [phan_tich_trademark, phan_tich_ban_quyen, phan_tich_nguoi_noi_tieng, phan_tich_quyen_so_huu_tri_tue]
    diem_tong = max(phan_tich["score"] for phan_tich in cac_phan_tich)
    ly_do_tong = gom_ly_do_tong(cac_phan_tich)
    ly_do_chinh = ly_do_tong[0] if ly_do_tong else ""

    if diem_tong >= 70:
        level = "Cao"
        level_class = "high"
        verdict = ly_do_chinh or "Có ít nhất một rủi ro mạnh trong 3 nhóm phân tích."
    elif diem_tong >= 35:
        level = "Trung bình"
        level_class = "medium"
        verdict = ly_do_chinh or "Có rủi ro ở ít nhất một nhóm phân tích."
    else:
        level = "Thấp"
        level_class = "low"
        if all(phan_tich["score"] <= 15 for phan_tich in cac_phan_tich):
            verdict = "Từ khóa an toàn, có thể sử dụng."
        else:
            verdict = ly_do_chinh or "Chưa thấy rủi ro mạnh trong 3 nhóm phân tích."

    if phan_tich_trademark["score"] >= 70:
        is_trademark = "Có khả năng cao"
    elif phan_tich_trademark["score"] >= 35:
        is_trademark = "Có thể"
    else:
        is_trademark = "Chưa rõ"

    if phan_tich_nguoi_noi_tieng["score"] >= 70 and co_tin_hieu_chinh_tri:
        consequence = (
            "Nếu sử dụng, rủi ro cao: dễ bị từ chối quảng cáo, gỡ nội dung, khóa gian hàng "
            "hoặc phát sinh khiếu nại liên quan chính trị."
        )
    elif diem_tong >= 70:
        consequence = (
            "Nếu sử dụng, có thể bị khiếu nại quyền sở hữu trí tuệ, gỡ listing, gỡ nội dung hoặc phát sinh tranh chấp."
        )
    elif diem_tong >= 35:
        consequence = "Nếu sử dụng, có nguy cơ bị cảnh báo hoặc bị khiếu nại ở ít nhất một nhóm rủi ro."
    else:
        if all(phan_tich["score"] <= 15 for phan_tich in cac_phan_tich):
            consequence = "Hiện chưa thấy dấu hiệu rủi ro rõ, có thể sử dụng."
        else:
            consequence = "Nếu sử dụng, rủi ro hiện chưa cao nhưng vẫn nên tra cứu chính thức trước."

    return {
        "score": diem_tong,
        "level": level,
        "level_class": level_class,
        "verdict": verdict,
        "action_recommendation": tao_khuyen_nghi_hanh_dong(level, diem_tong, cac_phan_tich),
        "explanation": tao_giai_thich_rui_ro(term, level, ly_do_tong, cac_phan_tich, summary, ngu_canh_class),
        "matched_elements": ly_do_tong[:3],
        "confidence_level": tao_muc_tin_cay(diem_tong, ly_do_tong, results),
        "advanced_breakdown": tao_phan_tich_chi_tiet(term, diem_tong, cac_phan_tich, nhan_ngu_canh, ngu_canh_class),
        "design_safe": tao_ghi_chu_an_toan_thiet_ke(term, diem_tong, ly_do_tong),
        "trademark_records": [],
        "official_sources": tao_nguon_tra_cuu_chinh_thuc(term),
        "top_label": tao_nhan_chinh(
            term=term,
            context_tags=nhan_ngu_canh,
            trademark_analysis=phan_tich_trademark,
            copyright_analysis=phan_tich_ban_quyen,
            public_figure_analysis=phan_tich_nguoi_noi_tieng,
            is_famous_slogan=la_slogan_noi_tieng,
            is_famous_brand=la_thuong_hieu_lon,
            is_famous_person=la_nguoi_noi_tieng,
            is_political=co_tin_hieu_chinh_tri,
        ),
        "is_trademark": is_trademark,
        "consequence": consequence,
        "is_political": co_tin_hieu_chinh_tri,
        "reasons": ly_do_tong,
        "analyses": cac_phan_tich,
        "context_tags": nhan_ngu_canh,
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


def tao_giai_thich_rui_ro(
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
    strongest_title = dich_ten_nhom_phan_tich(strongest["title"])
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
    if term_lower in SLOGAN_NOI_TIENG:
        owner = SLOGAN_NOI_TIENG[term_lower]
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
    if term_lower in TU_KHOA_NGUOI_NOI_TIENG:
        display_name = TEN_HIEN_THI_NGUOI_NOI_TIENG.get(term_lower, tao_ten_hien_thi(term_lower))
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


def tao_nguon_tra_cuu_chinh_thuc(term: str) -> list[dict[str, str]]:
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


def trich_xuat_class_trademark(text: str) -> list[int]:
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


def tao_ngu_canh_class(classes: list[int]) -> dict[str, Any]:
    relevant = [class_number for class_number in classes if class_number in CLASS_TRADEMARK_POD_LIEN_QUAN]
    classes_text = ", ".join(f"Class {class_number}" for class_number in classes) if classes else "chưa thấy class rõ"
    relevant_text = ", ".join(
        f"Class {class_number} ({CLASS_TRADEMARK_POD_LIEN_QUAN[class_number]})"
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


def tao_muc_tin_cay(score: int, reasons: list[str], results: list[KetQuaTimKiem]) -> str:
    if score >= 70 and reasons:
        return "Cao"
    if score >= 35 or results:
        return "Trung bình"
    return "Thấp"


def tao_phan_tich_chi_tiet(
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
        {"label": "Nguồn rủi ro chính", "value": dich_ten_nhom_phan_tich(strongest["title"])},
        {"label": "Ngữ cảnh", "value": context},
    ]
    if not class_context or class_context.get("status") != "unknown":
        rows.insert(1, {"label": "Class POD", "value": category_conflict})
    return rows


def dich_ten_nhom_phan_tich(title: str) -> str:
    translations = {
        "Trademark risk": "Trademark",
        "Copyright risk": "Copyright",
        "Public figure risk": "Public Figure",
        "Intellectual Property Rights": "Intellectual Property Rights",
    }
    return translations.get(title, title)


def tao_ghi_chu_an_toan_thiet_ke(term: str, score: int, reasons: list[str]) -> list[str]:
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


def danh_gia_rui_ro_ban_quyen(
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

    if any(keyword in combined_text for keyword in TU_KHOA_BAN_QUYEN):
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
    if normalized_term in TU_KHOA_VAN_HOA_DAI_CHUNG:
        score = max(score, 80)
        direct_copyright = True
        reasons.append(tao_ly_do_van_hoa_dai_chung(normalized_term))
    if normalized_term in TU_KHOA_NGUOI_NOI_TIENG and normalized_term in ("bts", "blackpink", "newjeans", "twice", "exo", "seventeen"):
        score = max(score, 75)
        direct_copyright = True
        reasons.append(f"Trùng nhóm nhạc {tao_ten_hien_thi(normalized_term)}")
    if is_famous_brand and normalized_term in ("disney", "pokemon", "pikachu", "marvel"):
        score = max(score, 90)
        direct_copyright = True
        reasons.append(f"Trùng IP lớn {tao_ten_hien_thi(normalized_term)}")
    elif is_famous_slogan:
        score = max(score, 40)
        indirect_copyright = True
        reasons.append(f"Gắn campaign của {SLOGAN_NOI_TIENG[normalized_term]}")
    elif is_famous_brand:
        score = max(score, 35)
        indirect_copyright = True
        reasons.append(f"Gián tiếp qua logo/hình của {tao_ten_hien_thi(normalized_term)}")

    analysis = tao_khoi_phan_tich(
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


def danh_gia_rui_ro_nguoi_noi_tieng(
    term: str,
    combined_text: str,
    is_political: bool,
    is_famous_person: bool,
    entity_type: str,
) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0
    normalized_term = term.lower().strip()

    if normalized_term in SLOGAN_NOI_TIENG:
        return tao_khoi_phan_tich(
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
        reasons.append(f"Trùng public figure {TEN_HIEN_THI_NGUOI_NOI_TIENG.get(normalized_term, tao_ten_hien_thi(normalized_term))}")
    if is_political:
        score = max(score, 92)
        reasons.append("Trùng nhân vật chính trị")
    if co_chua_cum_tu(combined_text, GOI_Y_NGUOI_CONG_CHUNG):
        score = max(score, 75)
        reasons.append(f"Kết quả mô tả {term} là người nổi tiếng/public figure")

    return tao_khoi_phan_tich(
        title="Public figure risk",
        score=score,
        reasons=reasons,
        high_label="Nguy cơ public figure rất cao",
        medium_label="Có dấu hiệu public figure",
        low_label="Chưa thấy dấu hiệu public figure mạnh",
    )


def tao_khoi_phan_tich(
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
        "reasons": uu_tien_ly_do_cu_the(reasons)[:2],
    }


def tao_phan_tich_quyen_so_huu_tri_tue(*analyses: dict[str, Any]) -> dict[str, Any]:
    score = max((analysis["score"] for analysis in analyses), default=0)
    reasons: list[str] = []
    for analysis in analyses:
        if analysis["score"] >= 35:
            reasons.extend(analysis.get("reasons", []))

    return tao_khoi_phan_tich(
        title="Intellectual Property Rights",
        score=score,
        reasons=reasons or ["Tổng hợp từ trademark, copyright và public figure"],
        high_label="Có rủi ro quyền sở hữu trí tuệ cao",
        medium_label="Có tín hiệu quyền sở hữu trí tuệ cần kiểm tra",
        low_label="Chưa thấy rủi ro quyền sở hữu trí tuệ rõ",
        consequence=tao_hau_qua_quyen_so_huu_tri_tue(score),
    )


def tao_hau_qua_quyen_so_huu_tri_tue(score: int) -> str:
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


def tao_khuyen_nghi_hanh_dong(level: str, score: int, analyses: list[dict[str, Any]]) -> str:
    ip_score = next(
        (analysis["score"] for analysis in analyses if analysis["title"] == "Intellectual Property Rights"),
        score,
    )
    if level == "Cao" or ip_score >= 70:
        return "Khuyến nghị: Thay đổi thiết kế/từ khóa hoàn toàn trước khi đăng bán."
    if level == "Trung bình" or ip_score >= 35:
        return "Khuyến nghị: Đổi tên hoặc chỉnh artwork để giảm rủi ro trước khi đăng."
    return "Khuyến nghị: Có thể dùng, nhưng vẫn nên tránh copy logo/hình ảnh/slogan có quyền."


def gom_ly_do_tong(analyses: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(analyses, key=lambda item: item["score"], reverse=True)
    reasons: list[str] = []
    for analysis in ordered:
        reasons.extend(analysis.get("reasons", []))
    return uu_tien_ly_do_cu_the(reasons)[:3]


def tao_de_xuat(
    original_term: str,
    resolved_term: str,
    trademark: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, list[str]]:
    base = chuan_hoa_khoang_trang(original_term or resolved_term)
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
            f"Tránh dùng trực tiếp tên thương hiệu {tao_ten_hien_thi(normalized)}.",
            "Đổi sang mô tả sản phẩm trung tính, không nhắc brand.",
        ])
        bypass.extend(tao_bien_the_thuong_hieu_an_toan(base))
    elif top_label == "Slogan":
        owner = SLOGAN_NOI_TIENG.get(normalized, "brand lớn")
        safe.extend([
            f"Tránh dùng nguyên slogan gắn với {owner}.",
            "Đổi sang câu mới cùng tinh thần nhưng khác cấu trúc.",
        ])
        bypass.extend(tao_bien_the_slogan_an_toan(base))
    elif top_label == "Public figure" or top_label == "Politics":
        safe.extend([
            f"Tránh dùng trực tiếp tên {resolved_term}.",
            "Bỏ yếu tố người thật hoặc chính trị, đổi sang chủ đề trung tính.",
        ])
        bypass.extend(tao_bien_the_nguoi_noi_tieng_an_toan(base))
    elif top_label in ("Music", "Pop culture", "Copyright"):
        safe.extend([
            f"Tránh dùng trực tiếp tên {resolved_term} nếu đây là IP/nội dung giải trí.",
            "Đổi sang mô tả cảm hứng chung, không nhắc tên tác phẩm/nhân vật.",
        ])
        bypass.extend(tao_bien_the_van_hoa_dai_chung_an_toan(base))
    else:
        safe.extend([
            "Tránh giữ nguyên từ khóa nếu còn nghi ngờ.",
            "Ưu tiên tên mô tả trung tính, không nhắc brand/người nổi tiếng.",
        ])
        bypass.extend(tao_bien_the(base, ["studio", "wear", "lab", "style"]))

    return {
        "bypass": loai_trung_giu_thu_tu([item for item in bypass if item]),
        "safe": loai_trung_giu_thu_tu([item for item in safe if item]),
    }


def tao_bien_the(base: str, suffixes: list[str]) -> list[str]:
    root = don_gian_hoa_tu_khoa(base)
    variants: list[str] = []
    for suffix in suffixes:
        if not root:
            continue
        variants.append(f"{root} {suffix}".strip())
    return variants[:4]


def tao_bien_the_thuong_hieu_an_toan(base: str) -> list[str]:
    core = bo_tu_rui_ro(base)
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


def tao_bien_the_slogan_an_toan(base: str) -> list[str]:
    core = bo_tu_rui_ro(base)
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


def tao_bien_the_nguoi_noi_tieng_an_toan(base: str) -> list[str]:
    core = bo_tu_nguoi_noi_tieng(base)
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


def tao_bien_the_van_hoa_dai_chung_an_toan(base: str) -> list[str]:
    core = bo_tu_rui_ro(base)
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


def don_gian_hoa_tu_khoa(value: str) -> str:
    cleaned = chuan_hoa_khoang_trang(value)
    if not cleaned:
        return ""
    tokens = [token for token in re.split(r"[\s,_-]+", cleaned) if token]
    stop_words = {"the", "a", "an", "shirt", "tshirt", "t-shirt", "tee"}
    kept = [token for token in tokens if token.lower() not in stop_words]
    return " ".join(kept[:2]) if kept else cleaned


def bo_tu_rui_ro(value: str) -> str:
    cleaned = don_gian_hoa_tu_khoa(value)
    risky_phrases = (
        list(TU_KHOA_THUONG_HIEU_LON)
        + list(TU_KHOA_NGUOI_NOI_TIENG)
        + list(SLOGAN_NOI_TIENG.keys())
        + list(TU_KHOA_VAN_HOA_DAI_CHUNG)
    )
    risky_tokens = {
        token
        for phrase in risky_phrases
        for token in phrase.lower().replace("'", " ").split()
    }
    kept = [token for token in cleaned.replace("'", " ").split() if token.lower() not in risky_tokens]
    return " ".join(kept).strip()


def bo_tu_nguoi_noi_tieng(value: str) -> str:
    cleaned = don_gian_hoa_tu_khoa(value)
    person_tokens = {"donald", "trump", "taylor", "swift", "ronaldo", "messi", "bts"}
    kept = [token for token in cleaned.split() if token.lower() not in person_tokens]
    return " ".join(kept) or "neutral"


def tao_nhan_chinh(
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
        if normalized_term in TU_KHOA_VAN_HOA_DAI_CHUNG:
            return "Pop culture"
        if "Music" in context_tags:
            return "Music"
        return "Copyright"
    if is_famous_brand or trademark_analysis["score"] >= 35:
        return "Brand"
    if context_tags:
        return context_tags[0]
    return "Review"


def phat_hien_nhan_ngu_canh(term: str, combined_text: str) -> list[str]:
    normalized_term = term.lower().strip()
    tags: list[str] = []
    if any(keyword in combined_text for keyword in ("movie", "film", "tv series")) or normalized_term in TU_KHOA_VAN_HOA_DAI_CHUNG:
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
    if normalized_term in TU_KHOA_VAN_HOA_DAI_CHUNG:
        return False
    if any(hint in combined_text for hint in GOI_Y_NGU_CANH_HU_CAU):
        return False
    return co_chua_cum_tu(combined_text, TU_KHOA_CHINH_TRI)


def phat_hien_tin_hieu_am_nhac(term: str, combined_text: str) -> bool:
    normalized_term = term.lower().strip()
    if normalized_term not in TU_KHOA_NGUOI_NOI_TIENG and normalized_term not in TU_KHOA_VAN_HOA_DAI_CHUNG:
        if not co_chua_cum_tu(combined_text, GOI_Y_AM_NHAC_MANH):
            return False
    if co_chua_cum_tu(combined_text, ("rabbit", "animal", "mammal", "species", "pet")):
        return False
    return True


def tao_ly_do_van_hoa_dai_chung(normalized_term: str) -> str:
    display_name = tao_ten_hien_thi(normalized_term)
    context = NGU_CANH_VAN_HOA_DAI_CHUNG.get(normalized_term, "")
    if context and context.lower() != normalized_term:
        return f"Trùng IP/nhân vật {display_name} trong {context}"
    return f"Trùng IP văn hóa đại chúng {display_name}"


def uu_tien_ly_do_cu_the(reasons: list[str]) -> list[str]:
    reasons = gop_ly_do_ip_lien_quan(reasons)
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


def gop_ly_do_ip_lien_quan(reasons: list[str]) -> list[str]:
    normalized_reasons = list(reasons)
    for brand in TU_KHOA_THUONG_HIEU_LON:
        display = tao_ten_hien_thi(brand)
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
    for person in TU_KHOA_NGUOI_NOI_TIENG:
        display = TEN_HIEN_THI_NGUOI_NOI_TIENG.get(person, tao_ten_hien_thi(person))
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


def suy_luan_loai_thuc_the(evidence_text: str) -> str:
    compact = chuan_hoa_khoang_trang(bo_dau_tieng_viet(evidence_text.lower()))
    if co_chua_cum_tu(compact, GOI_Y_CON_NGUOI):
        return "Con người"
    if co_chua_cum_tu(compact, ("company", "brand", "startup", "corporation", "business")):
        return "Công ty hoặc brand"
    if co_chua_cum_tu(compact, ("software", "application", "platform", "service", "tool")):
        return "Sản phẩm hoặc dịch vụ số"
    return "Chưa rõ"


def trich_xuat_nam_sinh(evidence_text: str) -> str:
    compact = bo_dau_tieng_viet(evidence_text.lower())
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


def lay_json(url: str) -> Any:
    return json.loads(lay_text(url))


def lay_text(url: str) -> str:
    request = Request(url, headers=TIEU_DE_MAC_DINH)
    with urlopen(request, timeout=10) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def bo_html(raw_html: str) -> str:
    text = re.sub(r"<.*?>", " ", raw_html)
    return chuan_hoa_khoang_trang(unescape(text))


def chuan_hoa_khoang_trang(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def bo_dau_tieng_viet(value: str) -> str:
    source = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    target = "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
    return value.translate(str.maketrans(source, target))


def lay_gia_tri_dau_tien(values: list[str]) -> str:
    for value in values:
        cleaned = chuan_hoa_khoang_trang(value)
        if cleaned:
            return cleaned
    return ""


def chon_ket_qua_tot_nhat(results: list[KetQuaTimKiem]) -> KetQuaTimKiem | None:
    scored_results = []
    for result in results:
        snippet = chuan_hoa_khoang_trang(result.snippet)
        if not snippet:
            continue
        score = len(snippet)
        lowered = f"{result.title} {snippet}".lower()
        if "may refer to" in lowered:
            score -= 200
        if any(keyword in lowered for keyword in GOI_Y_CON_NGUOI):
            score += 40
        if any(keyword in lowered for keyword in ("company", "brand", "product", "service")):
            score += 25
        scored_results.append((score, result))

    if not scored_results:
        return None
    scored_results.sort(key=lambda item: item[0], reverse=True)
    return scored_results[0][1]


def suy_luan_tu_khoa_tu_ket_qua(original_term: str, results: list[KetQuaTimKiem]) -> str:
    candidates: dict[str, int] = {}
    original_lower = original_term.lower()

    for result in results[:5]:
        for candidate in tach_ung_vien_tu_tieu_de(result.title):
            cleaned = lam_sach_ung_vien(candidate)
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


def nen_uu_tien_tu_khoa_suy_luan(original_term: str, inferred_term: str) -> bool:
    original = chuan_hoa_khoang_trang(original_term)
    inferred = lam_sach_ung_vien(inferred_term)
    if not original or not inferred:
        return False

    original_lower = original.lower()
    inferred_lower = inferred.lower()
    if inferred_lower == original_lower:
        return False
    if len(inferred.split()) <= len(original.split()):
        return False
    if not co_chua_cum_tu(inferred_lower, (original_lower,)):
        return False
    if len(inferred.split()) > 4:
        return False
    return True


def tach_ung_vien_tu_tieu_de(title: str) -> list[str]:
    separators = (" - ", " | ", " – ", ": ")
    parts = [title]
    for separator in separators:
        next_parts: list[str] = []
        for part in parts:
            next_parts.extend(part.split(separator))
        parts = next_parts
    return [part.strip() for part in parts if part.strip()]


def lam_sach_ung_vien(value: str) -> str:
    cleaned = chuan_hoa_khoang_trang(re.sub(r"\s*\([^)]*\)", "", value))
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


def trich_xuat_tu_trong_ngoac(text: str) -> str:
    match = re.search(r'"([^"]+)"', text) or re.search(r"'([^']+)'", text)
    if match:
        return chuan_hoa_khoang_trang(match.group(1))
    return ""


def trich_xuat_thuc_the_da_biet(text: str) -> list[str]:
    compact = chuan_hoa_khoang_trang(bo_dau_tieng_viet(text.lower()))
    candidates = sorted(
        set(TU_KHOA_NGUOI_NOI_TIENG + TU_KHOA_THUONG_HIEU_LON + tuple(SLOGAN_NOI_TIENG.keys()) + TU_KHOA_VAN_HOA_DAI_CHUNG),
        key=lambda item: len(item),
        reverse=True,
    )
    matches: list[str] = []
    for candidate in candidates:
        if co_chua_cum_tu(compact, (candidate,)):
            matches.append(tao_ten_hien_thi(candidate))
    matches = loai_trung_giu_thu_tu(matches)
    return bo_cum_con_bi_trung(matches)


def trich_xuat_ung_vien_dau_vao(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9'&.-]*", chuan_hoa_khoang_trang(text))
    if not tokens:
        return []

    meaningful = [token for token in tokens if token.lower() not in TU_CHUNG_DAU_VAO]
    if not meaningful:
        return []

    candidates: list[str] = []
    max_window = min(2, len(meaningful))
    for window in range(max_window, 0, -1):
        for start in range(0, len(meaningful) - window + 1):
            chunk = meaningful[start : start + window]
            candidate = chuan_hoa_khoang_trang(" ".join(chunk))
            if not candidate:
                continue
            if candidate.lower() in TU_CHUNG_DAU_VAO:
                continue
            if len(candidate) <= 2:
                continue
            candidates.append(candidate)

    candidates = loai_trung_giu_thu_tu([tao_ten_hien_thi(candidate) for candidate in candidates])
    return bo_cum_con_bi_trung(candidates[:3])


def bo_cum_da_biet_khoi_cau(text: str, known_terms: list[str]) -> str:
    cleaned = chuan_hoa_khoang_trang(text)
    for term in sorted(known_terms, key=len, reverse=True):
        if not term:
            continue
        cleaned = re.sub(rf"\b{re.escape(term)}\b", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(rf"\b{re.escape(term.replace('-', ' '))}\b", " ", cleaned, flags=re.IGNORECASE)
    return chuan_hoa_khoang_trang(cleaned)


def loc_ung_vien_check(values: list[str], limit: int = 5) -> list[str]:
    values = [chuan_hoa_khoang_trang(value) for value in values if chuan_hoa_khoang_trang(value)]
    values = loai_trung_giu_thu_tu(values)
    kept: list[str] = []
    for value in values:
        lowered = value.lower()
        if lowered in TU_CHUNG_DAU_VAO or len(lowered) <= 2:
            continue
        la_cum_rui_ro_da_biet = bo_dau_tieng_viet(lowered) in set(
            TU_KHOA_NGUOI_NOI_TIENG
            + TU_KHOA_THUONG_HIEU_LON
            + tuple(SLOGAN_NOI_TIENG.keys())
            + TU_KHOA_VAN_HOA_DAI_CHUNG
        )
        bi_bao_phu = any(lowered != other.lower() and lowered in other.lower() for other in kept)
        if bi_bao_phu and not la_cum_rui_ro_da_biet:
            continue
        kept.append(value)
        if len(kept) >= limit:
            break
    return kept


def loai_trung_giu_thu_tu(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def bo_cum_con_bi_trung(values: list[str]) -> list[str]:
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


def tao_ten_hien_thi(value: str) -> str:
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
        "mickey": "Mickey Mouse",
        "mickey mouse": "Mickey Mouse",
        "marvel": "Marvel",
        "avengers": "Avengers",
        "harry potter": "Harry Potter",
        "hogwarts": "Hogwarts",
        "nike": "Nike",
        "adidas": "Adidas",
        "gucci": "Gucci",
        "louis vuitton": "Louis Vuitton",
        "hello kitty": "Hello Kitty",
        "batman": "Batman",
        "superman": "Superman",
        "snoopy": "Snoopy",
        "minions": "Minions",
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


def tao_ket_qua_trung_khop(results: list[KetQuaTimKiem]) -> list[str]:
    matches: list[str] = []
    for result in results[:2]:
        title = chuan_hoa_khoang_trang(result.title)
        snippet = chuan_hoa_khoang_trang(result.snippet)
        if title and snippet:
            matches.append(f"{title}: {rut_gon_van_ban(snippet, 90)}")
        elif title:
            matches.append(title)
    return matches


def tom_tat_nhieu_nghia(text: str) -> bool:
    compact = chuan_hoa_khoang_trang(text).lower()
    ambiguous_markers = (
        "may refer to",
        "can refer to",
        "refer to",
        "có thể đề cập đến",
        "có thể là",
    )
    return any(marker in compact for marker in ambiguous_markers)


def co_cau_hinh_google_api() -> bool:
    api_key = (settings.GOOGLE_API_KEY or "").strip()
    cse_id = (settings.GOOGLE_CSE_ID or "").strip()
    invalid_values = {"", "YOUR_GOOGLE_API_KEY", "YOUR_CX", "YOUR_GOOGLE_CSE_ID"}
    return api_key not in invalid_values and cse_id not in invalid_values


def co_chua_cum_tu(text: str, phrases: tuple[str, ...]) -> bool:
    for phrase in phrases:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        if re.search(pattern, text):
            return True
    return False


def dich_van_ban(text: str, target_lang: str = "vi") -> str:
    cleaned = chuan_hoa_khoang_trang(text)
    if not cleaned:
        return ""

    try:
        data = lay_json(
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
    return chuan_hoa_khoang_trang("".join(translated_parts))


def rut_gon_van_ban(text: str, limit: int) -> str:
    cleaned = chuan_hoa_khoang_trang(text)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[:limit].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."


def chon_anh_hien_thi(wiki_summary: dict[str, str], results: list[KetQuaTimKiem]) -> str:
    image = chuan_hoa_khoang_trang(wiki_summary.get("image", ""))
    if image:
        return image
    for result in results:
        if chuan_hoa_khoang_trang(result.image):
            return result.image
    return ""


def trich_xuat_anh_google(item: dict[str, Any]) -> str:
    pagemap = item.get("pagemap", {})
    thumbnails = pagemap.get("cse_thumbnail", [])
    if thumbnails:
        src = chuan_hoa_khoang_trang(thumbnails[0].get("src", ""))
        if src:
            return src
    metatags = pagemap.get("metatags", [])
    for tag in metatags:
        for key in ("og:image", "twitter:image"):
            value = chuan_hoa_khoang_trang(tag.get(key, ""))
            if value:
                return value
    return ""


def chuan_hoa_anh_duckduckgo(value: str) -> str:
    image = chuan_hoa_khoang_trang(value)
    if not image:
        return ""
    if image.startswith("//"):
        return f"https:{image}"
    if image.startswith("/"):
        return f"https://duckduckgo.com{image}"
    return image

