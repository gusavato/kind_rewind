import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from password import bronze_path, bronze_parquet, bronze_untrack_parquet
from src.utils.functions import get_title_year, get_logger
from src.utils.api import get_tmdb_id, get_data

# Definición de variables temporales
films = []
df_untrack = pd.DataFrame(columns=["File", "Path"])
logger = get_logger(__name__)

for root_path, _, file_list in os.walk(bronze_path):
    for file_name in file_list:
        if file_name.lower().endswith((".mkv", ".avi")):

            # Obtención de TMDB_ID
            logger.info(f"Procesando {file_name}")
            film_title, film_year = get_title_year(file_name)
            tmdb_id = get_tmdb_id(film_title, film_year)

            # Manejo de errores en obtención TMDB_ID
            if tmdb_id == '':
                logger.warning(f"No se ha obtenido TMDB ID para: {file_name}")
                df_untrack = pd.concat(
                    [df_untrack,
                     pd.DataFrame(
                         [{"File": file_name,
                           "Path": root_path}])],
                    ignore_index=True)

                continue

            # Obtención datos API

            logger.info(f"TMDB ID: {tmdb_id}")
            dictio = get_data(tmdb_id)
            dictio["path"] = str(Path(root_path) / file_name)
            dictio["bronze_date"] = datetime.now()
            films.append(dictio)

# Escritura de tabla con la información de la API
pd.DataFrame(films).to_parquet(bronze_parquet, engine="pyarrow")

# Registro de archivos no localizados en la API
if not df_untrack.empty:
    df_untrack.to_parquet(bronze_untrack_parquet, engine="pyarrow")
