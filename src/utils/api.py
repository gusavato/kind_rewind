import requests
from datetime import datetime
from password import TOKEN
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

headers = {"accept": "application/json", "Authorization": f"Bearer {TOKEN}"}
base_path = Path(__file__).resolve().parent
path_actors = base_path / r"../../data/actors.parquet"

def get_tmdb_id(title: str, year: str) -> str:
    """Función que devuelve el identificador de TMDB para un título"""

    format_title = title.replace(' ', '%20')

    url = f"https://api.themoviedb.org/3/search/movie?query={format_title}&include_adult=false&language=ES&page=1&year={year}"

    response = requests.get(url, headers=headers).json()
    try:
        return response['results'][0]['id']

    except (KeyError, TypeError, ValueError, IndexError):
        logger.error(f"No se ha obtenido ID para: {title}")
        return ''

def get_details_tmdb(tmdb_id):
    """Función que devuelve los detalles de la película"""

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?language=es-ES"

    response = requests.get(url, headers=headers).json()

    dictio = dict()
    dictio['Titulo'] = response['title']
    dictio['Titulo_Original'] = response['original_title']
    try:
        dictio['Year'] = datetime.strptime(
            response['release_date'], '%Y-%m-%d').year
    except (KeyError, TypeError, ValueError):
        dictio['Year'] = 0
    dictio['Duracion'] = response['runtime']
    dictio['Tag_Line'] = response['tagline']
    dictio['Sinopsis'] = response['overview']
    dictio['Genero'] = [gen['name'] for gen in response['genres']]
    dictio['TMDB_rate'] = response['vote_average']
    try:
        dictio['Poster'] = 'https://image.tmdb.org/t/p/w400' + \
            response['poster_path']
    except (KeyError, TypeError, ValueError):
        dictio['Poster'] = ''
    dictio['Productoras'] = [prod['name']
                             for prod in response['production_companies']]
    dictio['Pais'] = [country['iso_3166_1']
                      for country in response['production_countries']]
    try:
        dictio['Fecha_Estreno'] = datetime.strptime(
            response['release_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
    except (KeyError, TypeError, ValueError):
        dictio['Fecha_Estreno'] = '01-01-1900'
    dictio['TMDB_id'] = response['id']
    dictio['IMDB_id'] = response['imdb_id']

    return dictio


def get_cast(tmdb_id):
    """Función que retorna los 8 primeros actores de una película"""

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?language=es-ES"

    response = requests.get(url, headers=headers).json()

    lst = []

    for i in range(min(8, len(response['cast']))):
        dictio = dict()
        dictio['Id'] = response['cast'][i]['id']
        dictio['Nombre'] = response['cast'][i]['name']
        try:
            dictio['Foto'] = 'https://image.tmdb.org/t/p/w200' + \
                response['cast'][i]['profile_path']
        except (KeyError, TypeError, ValueError):
            dictio['Foto'] = ''
        lst.append(dictio)

    df = pd.DataFrame(lst)
    actors = pd.read_parquet(path_actors)
    actors = pd.concat(
        [actors, df], axis=0).drop_duplicates().reset_index(drop=True)
    actors.to_parquet(path_actors, engine='pyarrow')

    return df


def get_director_writer(tmdb_id):

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?language=es-ES"

    response = requests.get(url, headers=headers).json()
    dictio = dict()
    try:
        df = pd.DataFrame(response['crew'])

        dictio['Director'] = df[df.job == 'Director']['name'].to_list()
        dictio['Guion'] = df[df.job == 'Screenplay']['name'].to_list()
    except AttributeError:
        logger.warning("No se tiene registro director / guion")
        dictio['Director'] = ''
        dictio['Guion'] = ''

    return dictio


def get_video(tmdb_id,titulo):

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?language=es-ES"

    response = requests.get(url, headers=headers).json()

    try:
        video = 'https://www.youtube.com/watch?v=' + \
            response['results'][0]['key']
    except (KeyError, TypeError, ValueError, IndexError):
        logger.warning(f"No se ha obtenido video para: {titulo}")
        return ''

    return video


def get_data(tmdb_id):
    """
    Función que une toda la información extraída de la API
    """

    dictio = get_details_tmdb(tmdb_id)
    try:
        dictio['Reparto'] = get_cast(tmdb_id)['Id'].to_list()
    except (KeyError, TypeError, ValueError):
        dictio['Reparto'] = []
    dictio = {**dictio, **get_director_writer(tmdb_id), 'Video': get_video(tmdb_id,dictio['Titulo'])}

    return dictio