from janus.utils import money_format


def test_money_format():
    assert money_format(1234.56) == "R$1,234.56"
    assert money_format(1234) == "R$1,234.00"
    assert money_format("not a number") == "not a number"
