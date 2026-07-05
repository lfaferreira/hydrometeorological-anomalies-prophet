from src.evaluation.sensitivity import run_interval_width_sensitivity

EVENTS = [
    {"name": "Evento A", "region": "rmr", "start_date": "2020-02-01", "end_date": "2020-02-01", "source": "teste"},
]


def test_run_interval_width_sensitivity_returns_one_row_per_width(tiny_prophet_df):
    result = run_interval_width_sensitivity(
        train=tiny_prophet_df, full_df=tiny_prophet_df, known_events=EVENTS, widths=[0.8, 0.95]
    )

    assert list(result["interval_width"]) == [0.8, 0.95]
    assert {"precision", "recall", "f1", "false_positive_rate", "n_anomalies"}.issubset(result.columns)
    # intervalo mais largo (0.95) deve gerar não mais anomalias que o mais estreito (0.8)
    n_anomalies_by_width = result.set_index("interval_width")["n_anomalies"]
    assert n_anomalies_by_width[0.95] <= n_anomalies_by_width[0.8]
