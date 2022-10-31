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

