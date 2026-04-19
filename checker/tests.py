from django.test import SimpleTestCase

from .services import (
    KetQuaTimKiem,
    danh_gia_rui_ro_trademark,
    tao_de_xuat,
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

    def test_tach_duoc_brand_va_ten_rieng_trong_cung_title(self):
        self.assertCountEqual(tach_tu_khoa_chinh("Benson Boone Nike concert shirt"), ["Nike", "Benson Boone"])

    def test_tach_duoc_nhieu_ip_trong_title_dai(self):
        self.assertEqual(tach_tu_khoa_chinh("Funny Disney Mickey Mouse Shirt"), ["Mickey Mouse", "Disney"])

    def test_tach_duoc_cum_chinh_voi_ten_la(self):
        self.assertEqual(tach_tu_khoa_chinh("Nirvexa premium retro shirt"), ["Nirvexa"])

    def test_khong_ghep_ten_voi_tu_mo_ta_streetwear(self):
        self.assertEqual(tach_tu_khoa_chinh("Benito Style Urban Streetwear Tee"), ["Benito"])

    def test_giu_cum_tm_benito_bowl_va_bo_mo_ta_football_gift(self):
        self.assertEqual(
            tach_tu_khoa_chinh("Benito Bowl Shirt Puerto Rico Football Tee Halftime Fans Gift Multi"),
            ["Benito Bowl"],
        )

    def test_benito_va_benito_bowl_duoc_xem_la_trademark(self):
        for tu_khoa in ("Benito", "Benito Bowl"):
            tom_tat = tao_tom_tat([], {"extract": f"{tu_khoa} clothing brand."})
            bao_cao = danh_gia_rui_ro_trademark(tu_khoa, [], {"extract": f"{tu_khoa} clothing brand."}, tom_tat)
            self.assertGreaterEqual(bao_cao["score"], 65)

    def test_tach_benson_tu_title_merch_dai(self):
        self.assertEqual(
            tach_tu_khoa_chinh(
                "AICase for Benson Merch Friendship Bracelets Inspired by Benson Concert Album Lyrics Inspired Stackable"
            ),
            ["Benson Boone"],
        )

    def test_benson_duoc_xem_la_public_figure_rui_ro_cao(self):
        tom_tat = tao_tom_tat([], {"extract": "Benson Boone is an American singer-songwriter and musician."})
        bao_cao = danh_gia_rui_ro_trademark(
            "Benson Boone",
            [],
            {"extract": "Benson Boone is an American singer-songwriter and musician."},
            tom_tat,
        )
        self.assertGreaterEqual(bao_cao["score"], 70)

    def test_de_xuat_benson_khong_giu_ten_nguoi_noi_tieng(self):
        tom_tat = tao_tom_tat([], {"extract": "Benson Boone is an American singer-songwriter and musician."})
        bao_cao = danh_gia_rui_ro_trademark(
            "Benson Boone",
            [],
            {"extract": "Benson Boone is an American singer-songwriter and musician."},
            tom_tat,
        )
        de_xuat = tao_de_xuat(
            original_term="AICase for Benson Merch Friendship Bracelets Inspired by Benson Concert Album Lyrics Inspired Stackable",
            resolved_term="Benson Boone",
            trademark=bao_cao,
            summary=tom_tat,
        )
        text = " ".join(de_xuat["bypass"]).lower()
        self.assertNotIn("benson", text)
        self.assertNotIn("boone", text)

    def test_josh_allen_la_public_figure_rui_ro_cao_va_de_xuat_khong_lap_ten(self):
        self.assertEqual(tach_tu_khoa_chinh("Josh Allen street wear"), ["Josh Allen"])
        tom_tat = tao_tom_tat([], {"extract": "Josh Allen is an American football quarterback."})
        bao_cao = danh_gia_rui_ro_trademark(
            "Josh Allen",
            [],
            {"extract": "Josh Allen is an American football quarterback."},
            tom_tat,
        )
        self.assertGreaterEqual(bao_cao["score"], 70)
        de_xuat = tao_de_xuat(
            original_term="Josh Allen street wear",
            resolved_term="Josh Allen",
            trademark=bao_cao,
            summary=tom_tat,
        )
        text = " ".join(de_xuat["bypass"]).lower()
        self.assertNotIn("josh", text)
        self.assertNotIn("allen", text)

    def test_tach_title_the_thao_ra_team_brand_va_cau_thu(self):
        self.assertEqual(
            tach_tu_khoa_chinh("Cincinnati Bengals Nike Game Home Team Colour Jersey - Black - Joe Burrow - Mens"),
            ["Cincinnati Bengals", "Joe Burrow", "Nike"],
        )

    def test_robert_kraft_doanh_nhan_la_public_figure_rui_ro_cao(self):
        tom_tat = tao_tom_tat([], {"extract": "Robert Kraft is an American businessman and sports team owner."})
        bao_cao = danh_gia_rui_ro_trademark(
            "Robert Kraft",
            [],
            {"extract": "Robert Kraft is an American businessman and sports team owner."},
            tom_tat,
        )
        rui_ro_nguoi_noi_tieng = next(muc for muc in bao_cao["analyses"] if muc["title"] == "Public figure risk")
        self.assertGreaterEqual(rui_ro_nguoi_noi_tieng["score"], 75)
        self.assertGreaterEqual(bao_cao["score"], 75)

    def test_christian_pulisic_la_van_dong_vien_public_figure_rui_ro_cao(self):
        tom_tat = tao_tom_tat([], {"extract": "Christian Pulisic is an American professional soccer player and athlete."})
        bao_cao = danh_gia_rui_ro_trademark(
            "Christian Pulisic",
            [],
            {"extract": "Christian Pulisic is an American professional soccer player and athlete."},
            tom_tat,
        )
        rui_ro_nguoi_noi_tieng = next(muc for muc in bao_cao["analyses"] if muc["title"] == "Public figure risk")
        self.assertGreaterEqual(rui_ro_nguoi_noi_tieng["score"], 80)
        self.assertGreaterEqual(bao_cao["score"], 80)

    def test_roblox_gift_card_chi_tach_roblox_va_rui_ro_cao(self):
        self.assertEqual(tach_tu_khoa_chinh("Roblox Digital Gift Card - 1,000 Robux"), ["Roblox"])
        tom_tat = tao_tom_tat([], {"extract": "Roblox is an online game platform and game creation system."})
        bao_cao = danh_gia_rui_ro_trademark(
            "Roblox",
            [],
            {"extract": "Roblox is an online game platform and game creation system."},
            tom_tat,
        )
        self.assertGreaterEqual(bao_cao["score"], 80)

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

