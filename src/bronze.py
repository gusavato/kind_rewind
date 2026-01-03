import os
import pandas as pd
from password import bronze_path
from src.utils.functions import get_title_year, get_logger
from src.utils.api import get_tmdb_id, get_data

films = []
logger = get_logger(__name__)

for root_path, _, file_list in os.walk(bronze_path):
    for file_name in file_list:
        if file_name.lower().endswith((".mkv",".avi")):
            logger.info(f"Procesando {file_name}")
            film_title, film_year = get_title_year(file_name)
            tmdb_id = get_tmdb_id(film_title, film_year)
            if tmdb_id == '':
                logger.warning(f"No se ha obtenido TMDB ID para: {file_name}")
                continue
            logger.info(f"TMDB ID: {tmdb_id}")
            films.append(get_data(tmdb_id))

pd.DataFrame(films).to_parquet("films_bronze.parquet",engine="pyarrow")







