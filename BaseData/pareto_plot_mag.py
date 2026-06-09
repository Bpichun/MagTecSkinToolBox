import optuna
from optuna.storages import JournalStorage
from optuna.storages.journal import JournalFileBackend
from optuna.visualization import plot_pareto_front
import os


file_path = "SensorFinger_0_optuna_evolutionary_testnuevo14mb.log" 

storage_backend = JournalFileBackend(file_path)
storage = JournalStorage(storage_backend)
all_studies = optuna.study.get_all_study_summaries(storage=storage)
studies_names = [s.study_name for s in all_studies]
print(f"Estudios encontrados en el archivo: {studies_names}")
study_name_target = studies_names[0]

try:
    study = optuna.load_study(
        study_name=study_name_target,
        storage=storage
    )
    print(f"Estudio '{study_name_target}' cargado exitosamente.")
    print(f"Número total de trials: {len(study.trials)}")
    
    pareto_trials = study.best_trials
    print(f"Puntos en el frente de Pareto: {len(pareto_trials)}")

except KeyError:
    print(f"Error: El estudio '{study_name_target}' no se encontró en el archivo.")
    study = None


if study is not None:
    print(study.metric_names)
    fig = plot_pareto_front(
        study,
        target_names=["Objetivo 1", "Objetivo 2"], 
        include_dominated_trials=True
    )

    fig.update_layout(
        title_text=f"Frente de Pareto: {study_name_target}",
        title_x=0.5
    )

    output_html = "pareto_front.html"
    fig.write_html(output_html)
    print(f"\nGráfico exportado exitosamente a: {os.path.abspath(output_html)}")







# #sqlite
# import optuna
# from optuna.visualization import plot_pareto_front
# import os
# import sys

# db_path = "/home/benjamin/Repos/MagTecSkinToolBox/Applications/OptimizationResults/MagneticSkin/MagneticSkin_optuna_evolutionary.db"

# if not os.path.exists(db_path):
#     sys.exit(1)

# storage_url = f"sqlite:///{db_path}"

# # Obtener estudios
# all_studies = optuna.study.get_all_study_summaries(storage=storage_url)
# study_names = [s.study_name for s in all_studies]

# print(f"Estudios encontrados en la DB: {study_names}")

# if not study_names:
#     sys.exit(1)

# study_name_target = study_names[0]

# study = optuna.load_study(
#     study_name=study_name_target,
#     storage=storage_url
# )
# print(f"Número total de trials: {len(study.trials)}")

# fig = plot_pareto_front(
#     study,
#     include_dominated_trials=True
# )

# output_html = "pareto_front.html"
# fig.write_html(output_html)

# print(f"✔ Gráfico exportado a: {os.path.abspath(output_html)}")
    
    
