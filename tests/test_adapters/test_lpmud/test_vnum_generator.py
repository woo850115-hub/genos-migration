"""Tests for VNUM generator."""

from genos.adapters.lpmud.vnum_generator import VnumGenerator


class TestVnumGenerator:
    def test_deterministic(self):
        gen = VnumGenerator()
        v1 = gen.path_to_vnum("/방/관도/hwab0324")
        v2 = gen.path_to_vnum("/방/관도/hwab0324")
        assert v1 == v2

    def test_different_paths_different_vnums(self):
        gen = VnumGenerator()
        v1 = gen.path_to_vnum("/방/관도/hwab0324")
        v2 = gen.path_to_vnum("/방/관도/hwab0304")
        assert v1 != v2

    def test_positive_31bit(self):
        gen = VnumGenerator()
        v = gen.path_to_vnum("/방/장백성/c0065")
        assert v > 0
        assert v < 2**31

    def test_strips_c_extension(self):
        gen = VnumGenerator()
        v1 = gen.path_to_vnum("/방/관도/hwab0324.c")
        v2 = gen.path_to_vnum("/방/관도/hwab0324")
        assert v1 == v2

    def test_strips_leading_slash(self):
        gen = VnumGenerator()
        v1 = gen.path_to_vnum("/방/관도/hwab0324")
        v2 = gen.path_to_vnum("방/관도/hwab0324")
        assert v1 == v2

    def test_path_map(self):
        gen = VnumGenerator()
        path = "/방/관도/hwab0324"
        v = gen.path_to_vnum(path)
        pm = gen.get_path_map()
        # path_map stores normalized (no leading /) path
        assert pm[v] == "방/관도/hwab0324"

    def test_zone_id(self):
        gen = VnumGenerator()
        z1 = gen.zone_id("방/관도")
        z2 = gen.zone_id("방/곤륜산")
        assert z1 != z2
        assert isinstance(z1, int)

    def test_collision_resolution(self):
        """If two paths hash to the same value, collision is resolved."""
        gen = VnumGenerator()
        # We can't easily force a collision, but we verify the mechanism
        # by checking that all generated vnums are unique
        paths = [f"/방/test/room{i}" for i in range(100)]
        vnums = [gen.path_to_vnum(p) for p in paths]
        assert len(set(vnums)) == 100
