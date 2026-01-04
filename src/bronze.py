import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from password import bronze_path, bronze_parquet, bronze_untrack_parquet, bronze_srt_parquet
from src.utils.functions import get_title_year, get_logger
from src.utils.api import get_tmdb_id, get_data

# Definición de variables temporales
films = []
untrack = []
# df_untrack = pd.DataFrame(columns=["File", "Path"])
# df_srt = pd.DataFrame(columns=["Film", "Subtitle", "Path"])
subtitles = []
logger = get_logger(__name__)

for root_path, _, file_list in os.walk(bronze_path):
    for file_name in file_list:
        if file_name.lower().endswith((".mkv", ".avi")):

            # Obtención de TMDB_ID
            logger.info(f"Procesando {file_name}")
            film_title, film_year = get_title_year(file_name)
            tmdb_id = get_tmdb_id(film_title, film_year)

            # Manejo de errores en obtención TMDB_ID
            # Registro en untrack
            if tmdb_id == '':
                logger.warning(f"No se ha obtenido TMDB ID para: {file_name}")
                dictio_untrack = {
                    "File": file_name,
                    "Path": str(Path(root_path) / file_name)
                }
                untrack.append(dictio_untrack)

                continue

            # Obtención datos API
            logger.info(f"TMDB ID: {tmdb_id}")
            dictio = get_data(tmdb_id)
            dictio["path"] = str(Path(root_path) / file_name)
            dictio["bronze_date"] = datetime.now()
            films.append(dictio)

            # Registro de subtítulos para .avi
            if file_name.lower().endswith(".avi"):
                for root_path_srt, dir_names, file_list_srt in os.walk(root_path):
                    dir_names.clear() # Evita entrar en subcarpetas
                    for file_name_srt in file_list_srt:
                        if file_name_srt.lower().endswith(".srt"):
                            dictio_srt = {
                                "Film": dictio["Titulo"],
                                "Subtitle": file_name_srt,
                                "Path": str(Path(root_path_srt) / file_name_srt)
                            }
                            subtitles.append(dictio_srt)


# Escritura de tabla con la información de la API
pd.DataFrame(films).to_parquet(bronze_parquet, engine="pyarrow")

# Registro de subtítulos
if subtitles:
    pd.DataFrame(subtitles).to_parquet(bronze_srt_parquet, engine="pyarrow")

# Registro de archivos no localizados en la API
if untrack:
    pd.DataFrame(untrack).to_parquet(bronze_untrack_parquet, engine="pyarrow")
