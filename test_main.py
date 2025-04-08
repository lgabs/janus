import pytest
from fastapi.testclient import TestClient
from main import app, WebsiteExperiment, Variant

# Create a test client for the FastAPI app
client = TestClient(app)


# Test the home endpoint
@pytest.mark.asyncio
def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "Janus: Bayesian A/B Testing App" in response.text


# Test the health check endpoint
@pytest.mark.asyncio
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# Test the WebsiteExperiment class
@pytest.mark.asyncio
def test_website_experiment():
    variants = [
        Variant(name="A", impressions=1000, conversions=100, revenue=1000.0),
        Variant(name="B", impressions=1000, conversions=150, revenue=1500.0),
    ]
    experiment = WebsiteExperiment(variants=variants, baseline_variant="A")
    experiment.run(show=False)
    assert len(experiment.conversion_results) == 2
    assert len(experiment.arpu_results) == 2
    assert len(experiment.revenue_per_sale_results) == 2


@pytest.mark.asyncio
def test_run_conversion_experiment():
    variants = [
        Variant(name="A", impressions=1000, conversions=100, revenue=1000.0),
        Variant(name="B", impressions=1000, conversions=150, revenue=1500.0),
    ]
    experiment = WebsiteExperiment(variants=variants, baseline_variant="A")
    experiment.run_conversion_experiment(show=False)
    assert len(experiment.conversion_results) == 2


@pytest.mark.asyncio
def test_run_arpu_experiment():
    variants = [
        Variant(name="A", impressions=1000, conversions=100, revenue=1000.0),
        Variant(name="B", impressions=1000, conversions=150, revenue=1500.0),
    ]
    experiment = WebsiteExperiment(variants=variants, baseline_variant="A")
    experiment.run_arpu_experiment(show=False)
    assert len(experiment.arpu_results) == 2


@pytest.mark.asyncio
def test_run_revenue_per_sale_experiment():
    variants = [
        Variant(name="A", impressions=1000, conversions=100, revenue=1000.0),
        Variant(name="B", impressions=1000, conversions=150, revenue=1500.0),
    ]
    experiment = WebsiteExperiment(variants=variants, baseline_variant="A")
    experiment.run_revenue_per_sale_experiment(show=False)
    assert len(experiment.revenue_per_sale_results) == 2


@pytest.mark.asyncio
def test_compile_full_data():
    variants = [
        Variant(name="A", impressions=1000, conversions=100, revenue=1000.0),
        Variant(name="B", impressions=1000, conversions=150, revenue=1500.0),
    ]
    experiment = WebsiteExperiment(variants=variants, baseline_variant="A")
    experiment.run(show=False)
    compiled_data = experiment.compile_full_data()
    assert len(compiled_data) == 2


@pytest.mark.asyncio
def test_get_reports():
    variants = [
        Variant(name="A", impressions=1000, conversions=100, revenue=1000.0),
        Variant(name="B", impressions=1000, conversions=150, revenue=1500.0),
    ]
    experiment = WebsiteExperiment(variants=variants, baseline_variant="A")
    experiment.run(show=False)
    (
        df_summary,
        df_conv,
        df_arpu,
        df_rev_per_sale,
        conv_dist,
        arpu_dist,
        rev_per_sale_dist,
    ) = experiment.get_reports()
    assert not df_summary.empty
    assert not df_conv.empty
    assert not df_arpu.empty
    assert not df_rev_per_sale.empty
    assert conv_dist is not None
    assert arpu_dist is not None
    assert rev_per_sale_dist is not None
