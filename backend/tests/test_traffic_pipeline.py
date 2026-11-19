from ml.traffic_pipeline import ScenarioDataset, ScenarioTrafficService, train_and_evaluate


def test_synthetic_training_is_labelled_and_reproducible() -> None:
    dataset = ScenarioDataset.generate(rows=240, seed=17)
    first = train_and_evaluate(dataset, seed=17)
    second = train_and_evaluate(dataset, seed=17)

    assert first.provenance == "synthetic_scenario"
    assert first.dataset_fingerprint == second.dataset_fingerprint
    assert first.metrics == second.metrics
    assert {m.name for m in first.metrics} == {
        "linear_regression",
        "random_forest",
        "gradient_boosting",
    }
    assert all(m.mae >= 0 and m.rmse >= 0 for m in first.metrics)
    assert all(-1 <= m.r2 <= 1 for m in first.metrics)


def test_prediction_exposes_synthetic_provenance_and_derived_delay() -> None:
    service = ScenarioTrafficService(rows=300, seed=5)
    prediction = service.predict(
        hour=9,
        day_of_week=1,
        weather="rain",
        vehicle_density=0.8,
        road_category="arterial",
        surface="moderate",
        base_travel_time_min=20,
    )

    assert prediction.provenance == "synthetic_scenario_model"
    assert 0 <= prediction.congestion_percent <= 100
    assert prediction.estimated_delay_min >= 0
    assert prediction.expected_travel_time_min >= 20
    assert prediction.model_name in {
        "random_forest",
        "gradient_boosting",
        "linear_regression",
    }
