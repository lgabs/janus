import streamlit as st
import pandas as pd


def save_results_in_session_state(experiment, control_label, treatment_label):
    st.session_state.experiment_results = experiment.results
    st.session_state.treatment_stats = pd.DataFrame.from_dict(
        experiment.results[treatment_label]["statistics"]
    )
    st.session_state.control_stats = pd.DataFrame.from_dict(
        experiment.results[control_label]["statistics"]
    )


def explain_metrics():
    st.write(
        """
    - **chance_to_beat**: chance that the variant is better than the other.
    - **expected_loss**: a measure of the risk you're assuming if you stay with this variant. The lower the risk, the best (e.g: 0.10 in conversion means that your risk of staying with the variant compared to the other is to lose 10% p.p. 0.10 for arpu is a risk of loosing $0.10 per user.)
    - **lift**: the observed relative difference compared to the other variant for each metric.
    - **diff**: the observed absolute difference compared to the other variant for each metric.
    """
    )
