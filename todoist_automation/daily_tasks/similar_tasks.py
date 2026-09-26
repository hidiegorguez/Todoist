import os

import pandas as pd
from cryptography.fernet import Fernet, InvalidToken

from todoist_automation import config


def _get_cipher():
    key = os.getenv("SIMILAR_TASKS_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("SIMILAR_TASKS_ENCRYPTION_KEY is required for the similar-tasks cache")
    try:
        return Fernet(key.encode("ascii"))
    except (UnicodeEncodeError, ValueError) as exc:
        raise ValueError("SIMILAR_TASKS_ENCRYPTION_KEY must be a valid Fernet key") from exc


def _load_cached_similars():
    if not os.path.exists(config.SIMILAR_TASKS_CSV):
        return []

    cipher = _get_cipher()
    similars_df = pd.read_csv(config.SIMILAR_TASKS_CSV)
    similars = []
    legacy_rows = False
    for value in similars_df["similar"].values:
        token = str(value)
        try:
            similars.append(cipher.decrypt(token.encode("utf-8")).decode("utf-8"))
        except InvalidToken:
            if token.startswith("gAAAAA"):
                raise ValueError("Could not decrypt the similar-tasks cache; check its encryption key")
            similars.append(token)
            legacy_rows = True

    if legacy_rows:
        similars_df["similar"] = [cipher.encrypt(value.encode("utf-8")).decode("ascii") for value in similars]
        similars_df.to_csv(config.SIMILAR_TASKS_CSV, index=False)

    return similars


def _write_cached_similars(similars):
    cipher = _get_cipher()
    encrypted = [cipher.encrypt(value.encode("utf-8")).decode("ascii") for value in similars]
    similars_df = pd.DataFrame(encrypted, columns=["similar"])
    os.makedirs(os.path.dirname(config.SIMILAR_TASKS_CSV), exist_ok=True)
    similars_df.to_csv(config.SIMILAR_TASKS_CSV, index=False)


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

    cached_similars = _load_cached_similars()
    similars_blob = [] if weekday == 0 else cached_similars

    if similars:
        for similar in similars:
            if similar not in similars_blob:
                similar_msgs.append(f'- {similar}')
                similars_blob.append(similar)
        _write_cached_similars(similars)

    return similar_msgs
