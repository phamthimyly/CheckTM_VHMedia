from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import update_last_login
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

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

DA_CHAY_MIGRATE_TU_DONG = False


def dam_bao_database_san_sang() -> None:
    global DA_CHAY_MIGRATE_TU_DONG
    if DA_CHAY_MIGRATE_TU_DONG:
        return
    try:
        call_command("migrate", interactive=False, verbosity=0)
        DA_CHAY_MIGRATE_TU_DONG = True
    except Exception:
        return


def lay_lich_su_session(request) -> list[dict]:
    return request.session.get("lich_su_check", [])


def lay_ten_lich_su_session(request) -> list[str]:
    return [
        item.get("tu_khoa_goc") or item.get("tu_khoa")
        for item in lay_lich_su_session(request)[:6]
        if item.get("tu_khoa_goc") or item.get("tu_khoa")
    ]


def luu_lich_su_session(request, bao_cao: dict, diem_rui_ro: int, muc_rui_ro: str) -> None:
    if not request.user.is_authenticated:
        return
    tu_khoa = bao_cao.get("term") or ""
    tu_khoa_goc = bao_cao.get("original_term") or tu_khoa
    ban_ghi = {
        "tu_khoa": tu_khoa,
        "tu_khoa_goc": tu_khoa_goc,
        "diem_rui_ro": diem_rui_ro,
        "muc_rui_ro": muc_rui_ro,
        "co_rui_ro": diem_rui_ro >= 35,
        "thoi_gian_hien_thi": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
    }
    lich_su = [
        item
        for item in lay_lich_su_session(request)
        if (item.get("tu_khoa_goc") or item.get("tu_khoa") or "").lower() != tu_khoa_goc.lower()
    ]
    request.session["lich_su_check"] = [ban_ghi, *lich_su][:20]
    request.session.modified = True


def xoa_lich_su_session(request, gia_tri: str) -> None:
    gia_tri = gia_tri.lower()
    request.session["lich_su_check"] = [
        item
        for item in lay_lich_su_session(request)
        if (item.get("tu_khoa_goc") or item.get("tu_khoa") or "").lower() != gia_tri
    ]
    request.session.modified = True


def xoa_toan_bo_lich_su_session(request) -> None:
    request.session["lich_su_check"] = []
    request.session.modified = True


def tao_admin_mac_dinh() -> None:
    dam_bao_database_san_sang()
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
        return redirect("home")

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
    lich_su_check = lay_lich_su_session(request)
    logout(request)
    if lich_su_check:
        request.session["lich_su_check"] = lich_su_check
        request.session.modified = True
    return redirect("home")


@login_required
def dashboard(request):
    dam_bao_database_san_sang()
    lich_su_session = lay_lich_su_session(request)
    try:
        thong_ke = LichSuKiemTra.objects.filter(user=request.user).aggregate(
            tong=Count("id"),
            an_toan=Count("id", filter=Q(co_rui_ro=False)),
            co_rui_ro=Count("id", filter=Q(co_rui_ro=True)),
        )
        lich_su_db = list(
            LichSuKiemTra.objects.filter(user=request.user)
            .values("tu_khoa", "muc_rui_ro", "diem_rui_ro", "co_rui_ro", "thoi_gian")
        )
        for item in lich_su_db:
            item["thoi_gian_hien_thi"] = timezone.localtime(item["thoi_gian"]).strftime("%d/%m/%Y %H:%M")
    except (OperationalError, ProgrammingError):
        thong_ke = {"tong": 0, "an_toan": 0, "co_rui_ro": 0}
        lich_su_db = []

    if thong_ke["tong"] or not lich_su_session:
        tong_luot_check = thong_ke["tong"] or 0
        tu_khoa_an_toan = thong_ke["an_toan"] or 0
        tu_khoa_co_rui_ro = thong_ke["co_rui_ro"] or 0
        lich_su_gan_day = lich_su_db
    else:
        tong_luot_check = len(lich_su_session)
        tu_khoa_an_toan = sum(1 for item in lich_su_session if not item.get("co_rui_ro"))
        tu_khoa_co_rui_ro = sum(1 for item in lich_su_session if item.get("co_rui_ro"))
        lich_su_gan_day = lich_su_session

    return render(
        request,
        "dashboard.html",
        {
            "tong_luot_check": tong_luot_check,
            "tu_khoa_an_toan": tu_khoa_an_toan,
            "tu_khoa_co_rui_ro": tu_khoa_co_rui_ro,
            "lich_su_gan_day": lich_su_gan_day,
        },
    )


@user_passes_test(la_admin, login_url="login")
def quan_ly_tai_khoan(request):
    dam_bao_database_san_sang()
    TaiKhoan = get_user_model()
    loi = ""
    thanh_cong = ""

    if request.method == "POST":
        ten_dang_nhap = (request.POST.get("username") or "").strip()
        mat_khau = request.POST.get("password") or ""
        la_quan_tri = request.POST.get("is_admin") == "on"
        if not ten_dang_nhap or not mat_khau:
            loi = "Hay nhap day du tai khoan va mat khau."
        elif TaiKhoan.objects.filter(username=ten_dang_nhap).exists():
            loi = "Tai khoan nay da ton tai."
        else:
            tai_khoan = TaiKhoan.objects.create_user(username=ten_dang_nhap, password=mat_khau)
            tai_khoan.is_active = True
            tai_khoan.is_staff = la_quan_tri
            tai_khoan.is_superuser = la_quan_tri
            tai_khoan.save()
            thanh_cong = f"Da tao tai khoan {ten_dang_nhap}."

    danh_sach_tai_khoan = TaiKhoan.objects.annotate(
        so_lan_check=Count("lich_su_kiem_tra"),
        so_keyword_rui_ro=Count("lich_su_kiem_tra", filter=Q(lich_su_kiem_tra__co_rui_ro=True)),
    ).order_by("-is_superuser", "username")
    return render(
        request,
        "accounts.html",
        {
            "danh_sach_tai_khoan": danh_sach_tai_khoan,
            "loi": loi,
            "thanh_cong": thanh_cong,
        },
    )


def luu_lich_su_check(request, bao_cao: dict) -> None:
    if not request.user.is_authenticated:
        return
    dam_bao_database_san_sang()
    muc_rui_ro = bao_cao.get("trademark", {}).get("level", "Thấp")
    diem_rui_ro = int(bao_cao.get("trademark", {}).get("score", 0) or 0)
    luu_lich_su_session(request, bao_cao, diem_rui_ro, muc_rui_ro)
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


@login_required
def home(request):
    tu_khoa = ""
    bao_cao = None
    loi = ""
    lich_su = []
    if request.user.is_authenticated:
        try:
            lich_su = list(
                LichSuKiemTra.objects.filter(user=request.user)
                .values_list("tu_khoa_goc", flat=True)[:6]
            )
        except (OperationalError, ProgrammingError):
            lich_su = []
        if not lich_su:
            lich_su = lay_ten_lich_su_session(request)

    if request.method == "POST":
        hanh_dong = (request.POST.get("action") or "").strip()
        gia_tri_lich_su = (request.POST.get("history_value") or "").strip()

        if hanh_dong == "delete_history" and gia_tri_lich_su and request.user.is_authenticated:
            try:
                LichSuKiemTra.objects.filter(
                    Q(tu_khoa_goc__iexact=gia_tri_lich_su) | Q(tu_khoa__iexact=gia_tri_lich_su),
                    user=request.user,
                ).delete()
            except (OperationalError, ProgrammingError):
                pass
            xoa_lich_su_session(request, gia_tri_lich_su)
            try:
                lich_su = list(
                    LichSuKiemTra.objects.filter(user=request.user)
                    .values_list("tu_khoa_goc", flat=True)[:6]
                )
            except (OperationalError, ProgrammingError):
                lich_su = []
            if not lich_su:
                lich_su = lay_ten_lich_su_session(request)
        elif hanh_dong == "clear_history" and request.user.is_authenticated:
            try:
                LichSuKiemTra.objects.filter(user=request.user).delete()
            except (OperationalError, ProgrammingError):
                pass
            xoa_toan_bo_lich_su_session(request)
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
                        try:
                            lich_su = list(
                                LichSuKiemTra.objects.filter(user=request.user)
                                .values_list("tu_khoa_goc", flat=True)[:6]
                            )
                        except (OperationalError, ProgrammingError):
                            lich_su = []
                        if not lich_su:
                            lich_su = lay_ten_lich_su_session(request)
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
