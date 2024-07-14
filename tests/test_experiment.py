import pytest
from janus.experiment import WebsiteExperiment
from janus.variant import Variant


@pytest.fixture
def variants():
    return [
        Variant(name="A", impressions=1000, conversions=100, revenue=10000),
        Variant(name="B", impressions=2000, conversions=200, revenue=20000),
    ]


@pytest.fixture
def experiment(variants):
    return WebsiteExperiment(variants, baseline_variant="A")


def test_initialization(experiment, variants):
    assert experiment.variants == variants
    assert experiment.baseline_variant == "A"


def test_run_conversion_experiment(experiment):
    experiment.run_conversion_experiment()
    assert hasattr(experiment, "conversion_results")
    assert experiment.conversion_results is not None


def test_run_arpu_experiment(experiment):
    experiment.run_arpu_experiment()
    assert hasattr(experiment, "arpu_results")
    assert experiment.arpu_results is not None


def test_get_reports(experiment):
    experiment.run_conversion_experiment()
    experiment.run_arpu_experiment()
    summary, conv, arpu = experiment.get_reports()
    assert not summary.empty
    assert not conv.empty
    assert not arpu.empty


def test_print_reports(experiment, capsys):
    experiment.run_conversion_experiment()
    experiment.run_arpu_experiment()
    experiment.print_reports()
    captured = capsys.readouterr()
    assert "Summary" in captured.out
    assert "Conversion Stats" in captured.out
    assert "ARPU Stats" in captured.out
