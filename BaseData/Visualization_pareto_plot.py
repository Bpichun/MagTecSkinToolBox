"""
Created on Tue May 4 09:29:11 2026

@author: benjamin
"""

import optuna
from optuna.storages import JournalStorage
from optuna.storages.journal import JournalFileBackend
import plotly.graph_objects as go
import os
import logging
from typing import List, Tuple


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_study_from_file(file_path: str, study_name: str = None) -> optuna.study.Study:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    storage = JournalStorage(JournalFileBackend(file_path))
    studies = optuna.study.get_all_study_summaries(storage=storage)

    if not studies:
        raise ValueError("No studies found in the log file.")

    if study_name is None:
        study_name = studies[0].study_name
        logging.info(f"No study specified. Using: {study_name}")

    try:
        study = optuna.load_study(study_name=study_name, storage=storage)
    except KeyError:
        raise ValueError(f"Study '{study_name}' not found.")

    logging.info(f"Loaded study: {study_name}")
    logging.info(f"Total trials: {len(study.trials)}")

    return study


def extract_pareto_points(study: optuna.study.Study) -> Tuple[List[List[float]], List[List[float]]]:
    pareto_trials = study.best_trials
    pareto_ids = {t.number for t in pareto_trials}

    pareto_points = []
    dominated_points = []

    for trial in study.trials:
        if trial.values is None:
            continue

        if not isinstance(trial.values, (list, tuple)):
            logging.warning(f"Invalid trial values in trial {trial.number}")
            continue

        if trial.number in pareto_ids:
            pareto_points.append(trial.values)
        else:
            dominated_points.append(trial.values)

    if not pareto_points:
        raise ValueError("No Pareto-optimal points found.")

    dim = len(pareto_points[0])
    if dim < 2:
        raise ValueError("Multi-objective study must have at least 2 objectives.")

    logging.info(f"Pareto points: {len(pareto_points)}")
    logging.info(f"Dominated points: {len(dominated_points)}")

    return pareto_points, dominated_points


def plot_pareto(pareto_points, dominated_points, study_name: str, output_file: str):
    dim = len(pareto_points[0])

    fig = go.Figure()

    def split(points):
        return list(zip(*points)) if points else ([], [], [])

    if dim == 2:
        if dominated_points:
            x, y = zip(*dominated_points)
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='markers',
                marker=dict(size=5, color='blue', opacity=0.6),
                name='Dominated'
            ))

        if pareto_points:
            x, y = zip(*pareto_points)
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='markers',
                marker=dict(size=7, color='red'),
                name='Pareto Front'
            ))

        fig.update_layout(
            title=f"Pareto Front: {study_name}",
            xaxis_title='Objective 1',
            yaxis_title='Objective 2'
        )

    elif dim == 3:
        if dominated_points:
            x, y, z = zip(*dominated_points)
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=z,
                mode='markers',
                marker=dict(size=4, color='blue', opacity=0.6),
                name='Dominated'
            ))

        if pareto_points:
            x, y, z = zip(*pareto_points)
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=z,
                mode='markers',
                marker=dict(size=6, color='yellow'),
                name='Pareto Front'
            ))

        fig.update_layout(
            title=f"Pareto Front: {study_name}",
            scene=dict(
                xaxis_title='Objective 1',
                yaxis_title='Objective 2',
                zaxis_title='Objective 3'
            )
        )

    else:
        raise NotImplementedError("Visualization only supports 2D or 3D.")

    fig.write_html(output_file)
    logging.info(f"Plot saved to: {os.path.abspath(output_file)}")


def main():
    file_path = "SensorFinger_10_optuna_evolutionary.log"

    try:
        study = load_study_from_file(file_path)
        pareto_points, dominated_points = extract_pareto_points(study)
        plot_pareto(pareto_points, dominated_points, study.study_name, "pareto_front.html")

    except Exception as e:
        logging.error(f"Execution failed: {e}")


if __name__ == "__main__":
    main()