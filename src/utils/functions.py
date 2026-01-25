import re
import unicodedata
import os
import shutil
import pandas as pd
from password import FILMS_PARQUET
from src.utils.api import get_data

def get_title_year(file_name:str) -> tuple[str, str]:
    """
    Función que recoge el nombre del archivo y devuelve título y año
    :param file_name: Nombre del archivo
    :return film_title: Título del film
    :return film_title: Año del film
    """
    # Patrones regex
    year_regex = r"\((19\d{2}|20\d{2})\)"
    title_regex = r"^(.*?)(?=[\(\[])"

    try:
        film_year = re.findall(year_regex, file_name)[0]
    except IndexError:
        film_year = ''

    try:
        film_title = re.findall(title_regex, file_name)[0]
        film_title = film_title.replace('.',' ').strip()
    except IndexError:
        film_title = ''

    return film_title, film_year


def sanitize_folder_name(name: str) -> str:
    if not name:
        return "UNKNOWN"

    # Normaliza acentos (á → a, ñ → n, etc.)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Elimina caracteres no permitidos
    name = re.sub(r'[<>:"/\\|?*\[\]()]', '', name)

    # Espacios múltiples → uno solo
    name = re.sub(r'\s+', ' ', name).strip()

    return name

def move_file_to_silver(title: str,cod:str, source_path: str, silver_path: str):
    if not os.path.isfile(source_path):
        raise FileNotFoundError(f"No existe el archivo: {source_path}")

    title_name = sanitize_folder_name(title)
    folder_name = cod + '_' + title_name
    destination_dir = os.path.join(silver_path, folder_name)

    os.makedirs(destination_dir, exist_ok=True)

    destination_path = os.path.join(
        destination_dir,
        os.path.basename(source_path)
    )

    shutil.move(source_path, destination_path)

    return destination_dir

def remove_acentos(text: str) -> str:
    trans = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return text.translate(trans)


def create_cod_letter(title: str) -> str:
    if not title:
        return "#"

    cod_letter = title[0].upper()
    cod_letter = remove_acentos(cod_letter)
    cod_letter = re.sub(r"[^a-zA-Z]", "#", cod_letter)

    return cod_letter

def first_missing_id(s):
    s = set(s)
    i = 1
    while i in s:
        i += 1
    return i

def get_index_films(df: pd.DataFrame):
    index_dict = \
    df.groupby("COD_LETTER")["COD_INDEX"].apply(list).to_dict()
    index = df['ID'].to_list()
    return index_dict, index

def assign_index(cod_letter: str, index_dict: dict):

    try:
        cod_index = first_missing_id(index_dict[cod_letter])
        index_dict[cod_letter].append(cod_index)
    except KeyError:
        cod_index = 1
        index_dict[cod_letter] = [1]

    return cod_index, index_dict

def update_film(cod: str, tmdb_id: int, logger):
    films = pd.read_parquet(FILMS_PARQUET, engine="pyarrow")
    old_folder = films[films['COD']==cod]['folder'].iloc[0]
    dictio = get_data(tmdb_id)
    cod_letter = create_cod_letter(dictio["Titulo"])
    if cod_letter != films[films['COD']==cod]['COD_LETTER'].iloc[0]:
        logger.error("COD_LETTER no coincide. No se procede a la actualización")
        logger.info(f"COD a actualizar {cod} vs COD_LETTER update {cod_letter}")
        return None
    logger.info(f"Se va a actualizar {films[films['COD']==cod]['Titulo'].iloc[0]} por {dictio['Titulo']}")
    mask = films["COD"] == cod
    films.loc[mask, dictio.keys()] = pd.DataFrame([dictio], index=films.index[mask])
    films.loc[mask, "folder"] = (
            films["COD_LETTER"]
            + films["COD_INDEX"].astype("string").str.zfill(4)
            + "_"
            + films["Titulo"]
    )
    films.to_parquet(FILMS_PARQUET, engine="pyarrow")
    logger.info("Actualizado FILMS_PARQUET")
    logger.info(f"Actualizar nombre de carpeta {old_folder} por {films[films['COD']==cod]['folder'].iloc[0]}")
    return None