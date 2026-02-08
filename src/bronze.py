import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from password import (BRONZE_PATH, GOLD_PATH, BRONZE_PARQUET,
                      BRONZE_UNTRACK_PARQUET, BRONZE_SRT_PARQUET, FILMS_PARQUET, STORAGE)
from src.utils.functions import get_title_year, move_file_to_silver, create_cod_letter, get_index_films, \
    assign_index, first_missing_id
from src.utils.api import get_tmdb_id, get_data
from src.utils.logger import get_logger

# Inicio logger
logger = get_logger(__name__)

# Definición de variables temporales
films = []
untrack = []
subtitles = []

# Obtención de índices
df_index = pd.read_parquet(FILMS_PARQUET, engine="pyarrow")[["ID", "COD_LETTER", "COD_INDEX"]]
index_dict, index = get_index_films(df_index)
tmdb_id_list = pd.read_parquet(FILMS_PARQUET, engine="pyarrow")['TMDB_id'].to_list()

for root_path, _, file_list in os.walk(BRONZE_PATH):
    for file_name in file_list:
        if file_name.lower().endswith((".mkv", ".avi")):

            # Obtención de TMDB_ID
            film_title, film_year = get_title_year(file_name)
            tmdb_id = get_tmdb_id(film_title, film_year)

            # Manejo de errores en obtención TMDB_ID
            # Registro en untrack
            if tmdb_id == '':
                logger.error(f"No se ha obtenido TMDB ID para: {file_name}")
                dictio_untrack = {
                    "File": file_name,
                    "Path": str(Path(root_path) / file_name),
                    "Date" : datetime.now()
                }
                untrack.append(dictio_untrack)

                continue

            # Obtención datos API
            dictio = get_data(tmdb_id)

            # Comprobación TMDB_id
            if dictio['TMDB_id'] in tmdb_id_list:
                logger.error(f"{dictio['Titulo']} ya existe en films.parquet")
                dictio_untrack = {
                    "File": file_name,
                    "Path": str(Path(root_path) / file_name),
                    "Date": datetime.now()
                }
                untrack.append(dictio_untrack)

                continue

            # Ubicaciones
            dictio["bronze_path"] = str(Path(root_path) / file_name)
            dictio["add_date"] = datetime.today().date()

            # Generación de índices
            dictio["COD_LETTER"] = create_cod_letter(dictio['Titulo'])
            dictio["COD_INDEX"], index_dict = assign_index(dictio["COD_LETTER"], index_dict)
            dictio['ID'] = first_missing_id(index)
            index.append(first_missing_id(index))
            dictio["COD"] = dictio['COD_LETTER'] + str(dictio['COD_INDEX']).zfill(4)

            # Agregamos a films
            films.append(dictio)
            logger.info(f"{dictio['Titulo']} procesada")

            # Registro de subtítulos para .avi
            if file_name.lower().endswith(".avi"):
                for root_path_srt, dir_names, file_list_srt in os.walk(root_path):
                    dir_names.clear() # Evita entrar en sub carpetas
                    for file_name_srt in file_list_srt:
                        if file_name_srt.lower().endswith(".srt"):
                            dictio_srt = {
                                "Film": dictio["Titulo"],
                                "Subtitle": file_name_srt,
                                "Path": str(Path(root_path_srt) / file_name_srt),
                                "COD" : dictio['COD']
                            }
                            subtitles.append(dictio_srt)

# # Escritura de tabla con la información de la API
if films:
    df_films = pd.DataFrame(films)
    df_films.to_parquet(BRONZE_PARQUET, engine="pyarrow")
    # Bronze --> Silver
    # Archivos
    for i, row in df_films.iterrows():
        film_gold_folder = move_file_to_silver(
            title=row["Titulo"],
            cod = row['COD'],
            source_path=row["bronze_path"],
            silver_path=GOLD_PATH
        )
        df_films.loc[i,"gold_folder"] = film_gold_folder
        logger.info(f"BRONZE --> GOLD: {row['COD']} - {row['Titulo']} - {row['TMDB_id']}")
    df_films.to_parquet(BRONZE_PARQUET, engine="pyarrow")

# # Registro de subtítulos
if subtitles:
    pd.DataFrame(subtitles).to_parquet(BRONZE_SRT_PARQUET, engine="pyarrow")
    # Bronze --> Silver
    # Subtítulos
    for _,row in pd.DataFrame(subtitles).iterrows():
        move_file_to_silver(
            title=row["Film"],
            cod = row['COD'],
            source_path=row["Path"],
            silver_path=GOLD_PATH
        )
    logger.info("BRONZE --> GOLD: Subtítulos")

# Registro de archivos no localizados en la API
if untrack:
    pd.DataFrame(untrack).to_parquet(BRONZE_UNTRACK_PARQUET, engine="pyarrow")
    logger.warning("No se han movido los siguientes ficheros")
    for f in untrack:
        print(f['File'])

# Tabla final
if films:
    columns = ['ID', 'COD', 'Titulo', 'Titulo_Original', 'Year', 'Duracion', 'Tag_Line', 'Sinopsis',
               'Genero', 'TMDB_rate', 'Poster', 'Productoras', 'Pais', 'Fecha_Estreno',
               'TMDB_id', 'IMDB_id', 'Reparto', 'Director', 'Guion', 'Video',
               'add_date', 'COD_LETTER', 'COD_INDEX',
               'gold_folder']

    df_gold = pd.read_parquet(FILMS_PARQUET, engine="pyarrow")
    df_bronze = pd.read_parquet(BRONZE_PARQUET, engine="pyarrow")
    df_bronze = df_bronze[columns]

    # Nuevas columnas
    df_bronze['Storage'] = STORAGE['H']
    df_bronze['Vista'] = False
    df_bronze['folder'] = df_bronze['gold_folder'].str.split("\\").str[-1]
    df_bronze.drop(columns=['gold_folder'], inplace=True)

    df_gold = pd.concat([df_gold, df_bronze],ignore_index=True)

    df_gold.to_parquet(FILMS_PARQUET, engine="pyarrow")
    text = "FILMS PARQUET ACTUALIZADO"
    logger.info(f"{text:-^100}")