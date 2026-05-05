"""
Created on Tue Apr 21 09:29:11 2026

@author: benjamin
"""
import optuna
from optuna.storages import JournalStorage
from optuna.storages.journal import JournalFileBackend
import plotly.graph_objects as go
import os



# Path to the Optuna journal file
file_path = "MagneticSkin_optuna_evolutionary.log"

# Initialize storage
storage_backend = JournalFileBackend(file_path)
storage = JournalStorage(storage_backend)

all_studies = optuna.study.get_all_study_summaries(storage=storage)
studies_names = [s.study_name for s in all_studies]


if len(studies_names) == 0:
    print("No hay estudios en el archivo.")
    exit()

study_name_target = studies_names[0]

# =========================
# Load 
# =========================
try:
    study = optuna.load_study(
        study_name=study_name_target,
        storage=storage
    )

    print(f"Study '{study_name_target}' successfully loaded..")
    print(f"Total number of trials: {len(study.trials)}")

except KeyError:
    print(f"Error: Study '{study_name_target}' was not found.")
    exit()


# Extract Pareto front trials
pareto_trials = study.best_trials
pareto_numbers = set(t.number for t in pareto_trials)

pareto_points = []
dominated_points = []

for t in study.trials:
    if t.values is None:
        continue  

    if t.number in pareto_numbers:
        pareto_points.append(t.values)
    else:
        dominated_points.append(t.values)

print(f"Number of Pareto-optimal points: {len(pareto_points)}")
print(f"Number of dominated points: {len(dominated_points)}")

# =========================
# Visualization
# =========================


fig = go.Figure()


if len(dominated_points) > 0:
    fig.add_trace(go.Scatter3d(
        x=[v[0] for v in dominated_points],
        y=[v[1] for v in dominated_points],
        z=[v[2] for v in dominated_points],
        mode='markers',
        marker=dict(
            size=4,
            color='blue',
            opacity=0.6
        ),
        name='Dominados'
    ))


if len(pareto_points) > 0:
    fig.add_trace(go.Scatter3d(
        x=[v[0] for v in pareto_points],
        y=[v[1] for v in pareto_points],
        z=[v[2] for v in pareto_points],
        mode='markers',
        marker=dict(
            size=6,
            color='yellow',
            opacity=1.0
        ),
        name='Pareto Front'
    ))

# fig.update_layout(
#     title=f"Frente de Pareto: {study_name_target}",
#     scene=dict(
#         xaxis_title='MagnetNumber f_1(d)',
#         yaxis_title='MagnetNumber f_2(d)',
#         zaxis_title='MagneticSensitivity f_3(d)'
#     ),
#     title_x=0.5
# )
fig.update_layout(
    title=f"Frente de Pareto: {study_name_target}",
    scene=dict(
        xaxis_title='MagnetNumber f<sub>1</sub>(d)',
        yaxis_title='MagnetNumber f<sub>2</sub>(d)',
        zaxis_title='MagneticSensitivity f<sub>3</sub>(d)'
    ),
    title_x=0.5
)
output_html = "pareto_front.html"
fig.write_html(output_html)

print(f"\nGráfico exportado en: {os.path.abspath(output_html)}") 