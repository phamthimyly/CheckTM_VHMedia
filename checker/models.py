from django.conf import settings
from django.db import models


class LichSuKiemTra(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lich_su_kiem_tra")
    tu_khoa = models.CharField(max_length=255)
    tu_khoa_goc = models.CharField(max_length=255, blank=True)
    diem_rui_ro = models.PositiveSmallIntegerField(default=0)
    muc_rui_ro = models.CharField(max_length=20, default="Thấp")
    co_rui_ro = models.BooleanField(default=False)
    thoi_gian = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-thoi_gian"]

    def __str__(self) -> str:
        return f"{self.tu_khoa} - {self.muc_rui_ro}"
