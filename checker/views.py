from django.shortcuts import render

from .services import fetch_term_report

GOI_Y_TU_KHOA = [
    "Disney",
    "Nike",
    "Pokemon",
    "Donald Trump",
    "Taylor Swift",
    "Spotify",
]


def home(request):
    tu_khoa = ""
    bao_cao = None
    loi = ""
    lich_su = request.session.get("search_history", [])

    if request.method == "POST":
        hanh_dong = (request.POST.get("action") or "").strip()
        gia_tri_lich_su = (request.POST.get("history_value") or "").strip()

        if hanh_dong == "delete_history" and gia_tri_lich_su:
            lich_su = [muc for muc in lich_su if muc.lower() != gia_tri_lich_su.lower()]
            request.session["search_history"] = lich_su
        elif hanh_dong == "clear_history":
            lich_su = []
            request.session["search_history"] = lich_su
        elif hanh_dong == "search_history" and gia_tri_lich_su:
            tu_khoa = gia_tri_lich_su
            try:
                bao_cao = fetch_term_report(tu_khoa)
            except Exception as exc:
                loi = (
                    "Không lấy được dữ liệu từ nguồn bên ngoài. "
                    "Kiểm tra Internet hoặc cấu hình Google API. "
                    f"Chi tiết kỹ thuật: {exc}"
                )
        else:
            tu_khoa = (request.POST.get("keyword") or "").strip()
            if not tu_khoa:
                error = "Hãy nhập từ cần check."
            else:
                try:
                    bao_cao = fetch_term_report(tu_khoa)
                    lich_su_moi = [tu_khoa] + [muc for muc in lich_su if muc.lower() != tu_khoa.lower()]
                    request.session["search_history"] = lich_su_moi[:6]
                    lich_su = request.session["search_history"]
                except Exception as exc:
                    loi = (
                        "Không lấy được dữ liệu từ nguồn bên ngoài. "
                        "Kiểm tra Internet hoặc cấu hình Google API. "
                        f"Chi tiết kỹ thuật: {exc}"
                    )

    return render(
        request,
        "index.html",
        {
            "keyword": tu_khoa,
            "report": bao_cao,
            "error": loi,
            "history": lich_su,
            "suggested_keywords": GOI_Y_TU_KHOA,
        },
    )
