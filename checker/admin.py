from django.contrib import admin

from .models import LichSuKiemTra


@admin.register(LichSuKiemTra)
class QuanLyLichSuKiemTra(admin.ModelAdmin):
    list_display = ("tu_khoa", "user", "muc_rui_ro", "diem_rui_ro", "co_rui_ro", "thoi_gian")
    list_filter = ("co_rui_ro", "muc_rui_ro", "thoi_gian")
    search_fields = ("tu_khoa", "tu_khoa_goc", "user__username")
