from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import update_last_login
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from .models import LichSuKiemTra
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

user_logged_in.disconnect(update_last_login, dispatch_uid="update_last_login")


def tao_admin_mac_dinh() -> None:
    TaiKhoan = get_user_model()
    ten_dang_nhap = "Phamly"
    mat_khau = "Phamlyy0212@"
    try:
        tai_khoan, _ = TaiKhoan.objects.get_or_create(username=ten_dang_nhap)
        tai_khoan.set_password(mat_khau)
        tai_khoan.is_active = True
        tai_khoan.is_staff = True
        tai_khoan.is_superuser = True
        tai_khoan.save()
    except (OperationalError, ProgrammingError):
        # Render co the mo app truoc khi migrate xong.
        return


def la_admin(user) -> bool:
    return user.is_authenticated and user.is_superuser


def dang_nhap(request):
    tao_admin_mac_dinh()

    if request.user.is_authenticated:
        return redirect("dashboard")

    loi = ""
    if request.method == "POST":
        ten_dang_nhap = (request.POST.get("username") or "").strip()
        mat_khau = request.POST.get("password") or ""
        user = authenticate(request, username=ten_dang_nhap, password=mat_khau)
        if user is None:
            loi = "Sai tài khoản hoặc mật khẩu."
        else:
            login(request, user)
            return redirect(request.GET.get("next") or "home")

    return render(request, "login.html", {"error": loi})


def dang_xuat(request):
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    thong_ke = LichSuKiemTra.objects.filter(user=request.user).aggregate(
        tong=Count("id"),
        an_toan=Count("id", filter=Q(co_rui_ro=False)),
        co_rui_ro=Count("id", filter=Q(co_rui_ro=True)),
    )
    lich_su_gan_day = LichSuKiemTra.objects.filter(user=request.user)[:8]
    return render(
        request,
        "dashboard.html",
        {
            "tong_luot_check": thong_ke["tong"] or 0,
            "tu_khoa_an_toan": thong_ke["an_toan"] or 0,
            "tu_khoa_co_rui_ro": thong_ke["co_rui_ro"] or 0,
            "lich_su_gan_day": lich_su_gan_day,
        },
    )


@user_passes_test(la_admin, login_url="login")
def quan_ly_tai_khoan(request):
    TaiKhoan = get_user_model()
    danh_sach_tai_khoan = TaiKhoan.objects.annotate(
        so_lan_check=Count("lich_su_kiem_tra"),
        so_keyword_rui_ro=Count("lich_su_kiem_tra", filter=Q(lich_su_kiem_tra__co_rui_ro=True)),
    ).order_by("-is_superuser", "username")
    return render(request, "accounts.html", {"danh_sach_tai_khoan": danh_sach_tai_khoan})


def luu_lich_su_check(request, bao_cao: dict) -> None:
    if not request.user.is_authenticated:
        return
    muc_rui_ro = bao_cao.get("trademark", {}).get("level", "Thấp")
    diem_rui_ro = int(bao_cao.get("trademark", {}).get("score", 0) or 0)
    try:
        LichSuKiemTra.objects.create(
            user=request.user,
            tu_khoa=bao_cao.get("term") or "",
            tu_khoa_goc=bao_cao.get("original_term") or "",
            diem_rui_ro=diem_rui_ro,
            muc_rui_ro=muc_rui_ro,
            co_rui_ro=diem_rui_ro >= 35,
        )
    except Exception:
        pass


def home(request):
    tu_khoa = ""
    bao_cao = None
    loi = ""
    lich_su = []
    if request.user.is_authenticated:
        lich_su = list(
            LichSuKiemTra.objects.filter(user=request.user)
            .values_list("tu_khoa_goc", flat=True)[:6]
        )

    if request.method == "POST":
        hanh_dong = (request.POST.get("action") or "").strip()
        gia_tri_lich_su = (request.POST.get("history_value") or "").strip()

        if hanh_dong == "delete_history" and gia_tri_lich_su and request.user.is_authenticated:
            LichSuKiemTra.objects.filter(
                Q(tu_khoa_goc__iexact=gia_tri_lich_su) | Q(tu_khoa__iexact=gia_tri_lich_su),
                user=request.user,
            ).delete()
            lich_su = list(
                LichSuKiemTra.objects.filter(user=request.user)
                .values_list("tu_khoa_goc", flat=True)[:6]
            )
        elif hanh_dong == "clear_history" and request.user.is_authenticated:
            LichSuKiemTra.objects.filter(user=request.user).delete()
            lich_su = []
        elif hanh_dong == "search_history" and gia_tri_lich_su and request.user.is_authenticated:
            tu_khoa = gia_tri_lich_su
            try:
                bao_cao = lay_bao_cao_tu_khoa(tu_khoa)
                luu_lich_su_check(request, bao_cao)
            except Exception:
                loi = THONG_BAO_LOI_DU_LIEU
        else:
            tu_khoa = (request.POST.get("keyword") or "").strip()
            if not tu_khoa:
                loi = "Hãy nhập từ cần check."
            else:
                try:
                    bao_cao = lay_bao_cao_tu_khoa(tu_khoa)
                    luu_lich_su_check(request, bao_cao)
                    if request.user.is_authenticated:
                        lich_su = list(
                            LichSuKiemTra.objects.filter(user=request.user)
                            .values_list("tu_khoa_goc", flat=True)[:6]
                        )
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
