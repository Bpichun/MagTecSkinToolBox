import optuna
from optuna.storages import JournalStorage
from optuna.storages.journal import JournalFileBackend
import plotly.graph_objects as go
import os

# =========================
# Cargar almacenamiento
# =========================
# file_path = "MagneticSkin_optuna_evolutionary.log"


file_path = "MagneticSkin_optuna_evolutionary_10000_1_dividid_ensors.log"

storage_backend = JournalFileBackend(file_path)
storage = JournalStorage(storage_backend)

# Obtener estudios disponibles
all_studies = optuna.study.get_all_study_summaries(storage=storage)
studies_names = [s.study_name for s in all_studies]

print(f"Estudios encontrados en el archivo: {studies_names}")

if len(studies_names) == 0:
    print("No hay estudios en el archivo.")
    exit()

study_name_target = studies_names[0]

# =========================
# Cargar estudio
# =========================
try:
    study = optuna.load_study(
        study_name=study_name_target,
        storage=storage
    )

    print(f"Estudio '{study_name_target}' cargado exitosamente.")
    print(f"Número total de trials: {len(study.trials)}")

except KeyError:
    print(f"Error: El estudio '{study_name_target}' no se encontró.")
    exit()

# =========================
# Separar Pareto vs dominados
# =========================
pareto_trials = study.best_trials
pareto_numbers = set(t.number for t in pareto_trials)

pareto_points = []
dominated_points = []

for t in study.trials:
    if t.values is None:
        continue  # evitar trials incompletos

    if t.number in pareto_numbers:
        pareto_points.append(t.values)
    else:
        dominated_points.append(t.values)

print(f"Puntos en el frente de Pareto: {len(pareto_points)}")
print(f"Puntos dominados: {len(dominated_points)}")


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

fig.update_layout(
    title=f"Frente de Pareto: {study_name_target}",
    scene=dict(
        xaxis_title='Objetivo 1',
        yaxis_title='Objetivo 2',
        zaxis_title='Objetivo 3'
    ),
    title_x=0.5
)

output_html = "pareto_front.html"
fig.write_html(output_html)

print(f"\nGráfico exportado en: {os.path.abspath(output_html)}") 