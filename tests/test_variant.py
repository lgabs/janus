from janus.variant import Variant


def test_variant_initialization():
    variant = Variant(name="A", impressions=1000, conversions=100, revenue=10000)
    assert variant.name == "A"
    assert variant.impressions == 1000
    assert variant.conversions == 100
    assert variant.revenue == 10000
