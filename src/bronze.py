import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from password import (BRONZE_PATH, SILVER_PATH, BRONZE_PARQUET,
                      BRONZE_UNTRACK_PARQUET, BRONZE_SRT_PARQUET)
from src.utils.functions import get_title_year, get_logger, move_file_to_silver
from src.utils.api import get_tmdb_id, get_data

# Inicio logger
logger = get_logger(__name__)

# Definición de variables temporales
films = []
untrack = []
subtitles = []

for root_path, _, file_list in os.walk(BRONZE_PATH):
    for file_name in file_list:
        if file_name.lower().endswith((".mkv", ".avi")):

            # Obtención de TMDB_ID
            film_title, film_year = get_title_year(file_name)
            tmdb_id = get_tmdb_id(film_title, film_year)

            # Manejo de errores en obtención TMDB_ID
            # Registro en untrack
            if tmdb_id == '':
                logger.warning(f"No se ha obtenido TMDB ID para: {file_name}")
                dictio_untrack = {
                    "File": file_name,
                    "Path": str(Path(root_path) / file_name),
                    "Date" : datetime.now()
                }
                untrack.append(dictio_untrack)

                continue

            # Obtención datos API
            dictio = get_data(tmdb_id)
            dictio["bronze_path"] = str(Path(root_path) / file_name)
            dictio["bronze_date"] = datetime.now()
            films.append(dictio)

            # Registro de subtítulos para .avi
            if file_name.lower().endswith(".avi"):
                for root_path_srt, dir_names, file_list_srt in os.walk(root_path):
                    dir_names.clear() # Evita entrar en sub carpetas
                    for file_name_srt in file_list_srt:
                        if file_name_srt.lower().endswith(".srt"):
                            dictio_srt = {
                                "Film": dictio["Titulo"],
                                "Subtitle": file_name_srt,
                                "Path": str(Path(root_path_srt) / file_name_srt)
                            }
                            subtitles.append(dictio_srt)


# Escritura de tabla con la información de la API
if films:
    df_films = pd.DataFrame(films)
    df_films.to_parquet(BRONZE_PARQUET, engine="pyarrow")
    # Bronze --> Silver
    # Archivos
    for i, row in df_films.iterrows():
        film_silver_folder = move_file_to_silver(
            title=row["Titulo"],
            source_path=row["bronze_path"],
            silver_path=SILVER_PATH
        )
        df_films.loc[i,"silver_folder"] = film_silver_folder
        logger.info(f"BRONZE --> SILVER: {row['TMDB_id']} - {row['Titulo']}")
    df_films.to_parquet(BRONZE_PARQUET, engine="pyarrow")
# Registro de subtítulos
if subtitles:
    pd.DataFrame(subtitles).to_parquet(BRONZE_SRT_PARQUET, engine="pyarrow")
    # Bronze --> Silver
    # Subtítulos
    for _,row in pd.DataFrame(subtitles).iterrows():
        move_file_to_silver(
            title=row["Film"],
            source_path=row["Path"],
            silver_path=SILVER_PATH
        )
    logger.info("BRONZE --> SILVER: Subtítulos")

# Registro de archivos no localizados en la API
if untrack:
    pd.DataFrame(untrack).to_parquet(BRONZE_UNTRACK_PARQUET, engine="pyarrow")
    logger.warning("No se han movido los siguientes ficheros")
    for f in untrack:
        print(f['Film'])