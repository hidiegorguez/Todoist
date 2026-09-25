import os

import pandas as pd

from todoist_automation import config


def _jaccard_coef(cadena1, cadena2):
    set_cadena1 = set(cadena1.split())
    set_cadena2 = set(cadena2.split())
    interseccion = len(set_cadena1.intersection(set_cadena2))
    union = len(set_cadena1.union(set_cadena2))
    return interseccion / union


def _are_similar(cadena1, cadena2, umbral=0.5):
    if _jaccard_coef(cadena1, cadena2) >= umbral:
        return f'{cadena1} & {cadena2}'
    return None


def _find_similar_pairs(all_tasks, excluded_project_ids, umbral=0.5):
    project_tasks = [task.content for task in all_tasks if task.project_id not in excluded_project_ids]
    similars = []
    for i in range(len(project_tasks) - 1):
        for j in range(i + 1, len(project_tasks)):
            pair = _are_similar(project_tasks[i], project_tasks[j], umbral=umbral)
            if pair is not None and pair not in config.SIMILAR_TASKS_IGNORED_PAIRS:
                similars.append(pair)
    return similars


def find_new_similar_tasks(all_tasks, weekday, umbral=0.7):
    """Detect newly-similar task pairs, caching already-reported ones in a CSV.

    The cache resets every Monday (weekday == 0).
    """
    similar_msgs = []
    similars = _find_similar_pairs(all_tasks, config.SIMILAR_TASKS_EXCLUDED_PROJECT_IDS, umbral=umbral)

    if weekday == 0:
        similars_blob = []
    elif os.path.exists(config.SIMILAR_TASKS_CSV):
        similars_df = pd.read_csv(config.SIMILAR_TASKS_CSV)
        similars_blob = list(similars_df['similar'].values)
    else:
        similars_blob = []

    if similars:
        for similar in similars:
            if similar not in similars_blob:
                similar_msgs.append(f'- {similar}')
                similars_blob.append(similar)
        similars_df = pd.DataFrame(similars, columns=["similar"])
        os.makedirs(os.path.dirname(config.SIMILAR_TASKS_CSV), exist_ok=True)
        similars_df.to_csv(config.SIMILAR_TASKS_CSV, index=False)

    return similar_msgs
