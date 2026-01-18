import streamlit as st
import pandas as pd
from unidecode import unidecode
from password import FILMS_PARQUET, ACTORS_PARQUET

# Configuración página
st.set_page_config(layout='wide')

# Cargamos df
films = pd.read_parquet(FILMS_PARQUET, engine='pyarrow').sort_values(by=['ID'], ascending=False)
films['Titulo_unidecode'] = films.Titulo.apply(lambda x: unidecode(x))
films['Director_unidecode'] = films.Director.apply(
    lambda x: [unidecode(i).lower() for i in x])
actors = pd.read_parquet(ACTORS_PARQUET, engine='pyarrow')
actors['Nombre_unicode'] = actors.Nombre.apply(lambda x: unidecode(x))


film_list = films.sort_values(['ID'],ascending=False)['Titulo']
select = st.sidebar.selectbox(
    'Título',
    options=film_list,
    key='box')

select_film = films.loc[films.Titulo == select,:].iloc[0].to_dict()

# Página Principal
col_01, col_02, col_03 = st.columns(
    spec = [0.2,0.5,0.3],
    gap = 'medium',
    vertical_alignment= 'top')

with col_01:
    st.image(select_film['Poster'], width=500)

with col_02:
    st.markdown(
        f"""
        <h1 style='font-size: 50px; color: #b82c16;'>{st.session_state.box}</h1>
        """,
        unsafe_allow_html=True)
    st.markdown(select_film["Tag_Line"])
    directors = ", ".join(select_film['Director'])
    st.markdown(f"Director: {directors}")


# st.text(select)
# st.text(select_film['Titulo_unidecode'].to_string())
# st.text(select_film['ID'].to_string())
# st.text(select_film['COD'].to_string())
