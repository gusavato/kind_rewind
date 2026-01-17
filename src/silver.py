import pandas as pd
from password import BRONZE_PARQUET, FILMS_PARQUET
from src.utils.functions import get_logger, create_cod_letter, get_index_films, assign_index

# Inicio logger
logger = get_logger(__name__)

# Carga tabla bronze para transformación silver
df_silver = pd.read_parquet(BRONZE_PARQUET, engine="pyarrow")

# Creación de campos
df_silver = create_cod_letter(df_silver)

# Obtención de índices
df_index = pd.read_parquet(FILMS_PARQUET, engine="pyarrow")[["ID","COD_LETTER","COD_INDEX"]]
index_dict, index = get_index_films(df_index)
df_silver = assign_index(df_silver,index_dict,index)



