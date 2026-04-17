from django.shortcuts import render

from .services import lay_bao_cao_tu_khoa

THONG_BAO_LOI_DU_LIEU = "Không lấy được dữ liệu từ nguồn bên ngoài. Vui lòng thử lại."

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
                bao_cao = lay_bao_cao_tu_khoa(tu_khoa)
            except Exception:
                loi = THONG_BAO_LOI_DU_LIEU
        else:
            tu_khoa = (request.POST.get("keyword") or "").strip()
            if not tu_khoa:
                loi = "Hãy nhập từ cần check."
            else:
                try:
                    bao_cao = lay_bao_cao_tu_khoa(tu_khoa)
                    lich_su_moi = [tu_khoa] + [muc for muc in lich_su if muc.lower() != tu_khoa.lower()]
                    request.session["search_history"] = lich_su_moi[:6]
                    lich_su = request.session["search_history"]
                except Exception:
                    loi = THONG_BAO_LOI_DU_LIEU

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
