from django.test import SimpleTestCase

from .services import (
    KetQuaTimKiem,
    danh_gia_rui_ro_trademark,
    trich_xuat_nam_sinh,
    suy_luan_tu_khoa_tu_ket_qua,
    nen_uu_tien_tu_khoa_suy_luan,
    tach_tu_khoa_chinh,
    tao_tom_tat,
)


class KiemThuDichVu(SimpleTestCase):
    def test_lay_nam_sinh_tu_doan_tieu_su(self):
        doan_van = "Taylor Swift is an American singer-songwriter born 1989 in Pennsylvania."
        self.assertEqual(trich_xuat_nam_sinh(doan_van), "1989")

    def test_ten_nguoi_noi_tieng_co_rui_ro_su_dung_cao(self):
        tom_tat = tao_tom_tat(
            [],
            {"extract": "Taylor Swift is an American singer-songwriter born 1989."},
        )
        bao_cao = danh_gia_rui_ro_trademark(
            "Taylor Swift",
            [],
            {"extract": "Taylor Swift is an American singer-songwriter born 1989."},
            tom_tat,
        )
        self.assertGreaterEqual(bao_cao["score"], 65)

    def test_tu_khoa_thuong_hieu_lam_tang_rui_ro_trademark(self):
        tom_tat = tao_tom_tat(
            [],
            {"extract": "Spotify is a music streaming service and technology company."},
        )
        bao_cao = danh_gia_rui_ro_trademark(
            "Spotify",
            [],
            {"extract": "Spotify is a music streaming service and technology company."},
            tom_tat,
        )
        self.assertGreaterEqual(bao_cao["score"], 35)

    def test_tach_tu_khoa_chinh_tim_duoc_coca_cola_trong_title_dai(self):
        self.assertEqual(tach_tu_khoa_chinh("Coca Cola Vintage Shirt"), ["Coca-Cola"])

    def test_tach_tu_khoa_chinh_tim_duoc_harry_potter_trong_title_dai(self):
        self.assertEqual(tach_tu_khoa_chinh("Harry Potter Hogwarts Shirt"), ["Harry Potter", "Hogwarts"])

    def test_tach_duoc_cum_chinh_voi_ten_la(self):
        self.assertEqual(tach_tu_khoa_chinh("Nirvexa premium retro shirt"), ["Nirvexa"])

    def test_uu_tien_ten_day_du_khi_google_goi_y_ro(self):
        ket_qua = [
            KetQuaTimKiem(
                title="Benson Boone - Official Website",
                snippet="Benson Boone is an American singer-songwriter.",
                link="https://example.com",
                source="Example",
            )
        ]
        ten_suy_ra = suy_luan_tu_khoa_tu_ket_qua("Benson", ket_qua)
        self.assertEqual(ten_suy_ra, "Benson Boone")
        self.assertTrue(nen_uu_tien_tu_khoa_suy_luan("Benson", ten_suy_ra))

    def test_ca_si_tim_tu_google_phai_la_rui_ro_cao(self):
        tom_tat = tao_tom_tat(
            [],
            {"extract": "Benson Boone is an American singer-songwriter and musician."},
        )
        bao_cao = danh_gia_rui_ro_trademark(
            "Benson Boone",
            [],
            {"extract": "Benson Boone is an American singer-songwriter and musician."},
            tom_tat,
        )
        rui_ro_nguoi_noi_tieng = next(muc for muc in bao_cao["analyses"] if muc["title"] == "Public figure risk")
        self.assertGreaterEqual(rui_ro_nguoi_noi_tieng["score"], 70)
        self.assertGreaterEqual(bao_cao["score"], 70)

    def test_hogwarts_khong_bi_xep_nham_la_chinh_tri(self):
        tom_tat = tao_tom_tat(
            [],
            {"extract": "Hogwarts is a fictional boarding school of magic in the Harry Potter franchise."},
        )
        bao_cao = danh_gia_rui_ro_trademark(
            "Hogwarts",
            [],
            {"extract": "Hogwarts is a fictional boarding school of magic in the Harry Potter franchise."},
            tom_tat,
        )
        self.assertFalse(bao_cao["is_political"])
        rui_ro_nguoi_noi_tieng = next(muc for muc in bao_cao["analyses"] if muc["title"] == "Public figure risk")
        self.assertEqual(rui_ro_nguoi_noi_tieng["score"], 0)

    def test_rabbit_khong_bi_xep_nham_la_am_nhac(self):
        tom_tat = tao_tom_tat(
            [],
            {"extract": "Rabbit is a small mammal often kept as a pet and found in many species around the world."},
        )
        bao_cao = danh_gia_rui_ro_trademark(
            "Rabbit",
            [],
            {"extract": "Rabbit is a small mammal often kept as a pet and found in many species around the world."},
            tom_tat,
        )
        rui_ro_ban_quyen = next(muc for muc in bao_cao["analyses"] if muc["title"] == "Copyright risk")
        self.assertEqual(rui_ro_ban_quyen["score"], 0)

