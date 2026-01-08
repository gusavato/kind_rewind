import re
import unicodedata
import logging
import os
import shutil

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

def move_file_to_silver(title: str, source_path: str, silver_path: str):
    if not os.path.isfile(source_path):
        raise FileNotFoundError(f"No existe el archivo: {source_path}")

    folder_name = sanitize_folder_name(title)
    destination_dir = os.path.join(silver_path, folder_name)

    os.makedirs(destination_dir, exist_ok=True)

    destination_path = os.path.join(
        destination_dir,
        os.path.basename(source_path)
    )

    shutil.move(source_path, destination_path)

    return destination_path
