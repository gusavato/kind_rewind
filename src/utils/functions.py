import re
import unicodedata
import logging
import os
import shutil
import pandas as pd
import numpy as np

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Verde
        logging.WARNING: "\033[33m",  # Amarillo
        logging.ERROR: "\033[31m",    # Rojo
        logging.CRITICAL: "\033[41m", # Fondo rojo
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()

        formatter = ColorFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger



def get_title_year(file_name:str) -> tuple[str, str]:
    """
    Función que recoge el nombre del archivo y devuelve título y año
    :param file_name: Nombre del archivo
    :return film_title: Título del film
    :return film_title: Año del film
    """
    # Patrones regex
    year_regex = r"\b(19\d{2}|20\d{2})\b"
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

def get_index_films(df: pd.DataFrame):
    index_dict = df.groupby("COD_LETTER").agg("COD_INDEX").max().to_dict()
    index = df.ID.max()
    if index is np.nan:
        index = 0
    return index_dict, index

def assign_index(cod_letter: str, index_dict: dict):

    try:
        cod_index = index_dict[cod_letter] + 1
        index_dict[cod_letter] += 1
    except KeyError:
        cod_index = 1
        index_dict[cod_letter] = 1

    return cod_index, index_dict