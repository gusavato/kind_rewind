import streamlit as st
import pandas as pd
from streamlit import session_state
from unidecode import unidecode
from password import FILMS_PARQUET, ACTORS_PARQUET
from src.utils.visor_functions import fila, actor_row

# Configuración página
st.set_page_config(layout='wide')

# Inicialización de variables
if "idx" not in st.session_state:
    st.session_state.idx = 0

# Funciones
# Botones
def next_movie():
    if session_state.idx == len(film_list)-1:
        st.session_state.idx = 0

    else:
        st.session_state.idx += 1
    st.session_state.box = film_list[st.session_state.idx]

def prev_movie():
    if session_state.idx == 0:
        st.session_state.idx = len(film_list)-1
    else:
        st.session_state.idx -= 1
    st.session_state.box = film_list[st.session_state.idx]

def sync_idx():
    box_select = st.session_state.box
    st.session_state.idx = film_list.index(box_select)

# Cargamos df
films = pd.read_parquet(FILMS_PARQUET, engine='pyarrow').sort_values(by=['ID'], ascending=False)
films['Titulo_unidecode'] = films.Titulo.apply(lambda x: unidecode(x))
films['Director_unidecode'] = films.Director.apply(
    lambda x: [unidecode(i).lower() for i in x])
actors = pd.read_parquet(ACTORS_PARQUET, engine='pyarrow')
actors['Nombre_unicode'] = actors.Nombre.apply(lambda x: unidecode(x))


film_list = films.sort_values(['ID'],ascending=False)['Titulo'].to_list()



select = st.sidebar.selectbox(
    'Título',
    options=film_list,
    on_change= sync_idx,
    key='box')

select_film = films.loc[films.Titulo == select,:].iloc[0].to_dict()
st.sidebar.write(st.session_state.idx)
# Página Principal
col_01, col_02, col_03 = st.columns(
    spec = [0.20,0.40,0.40],
    gap = 'medium',
    vertical_alignment= 'top')

with col_01:
    st.image(select_film['Poster'], width=500)

with col_02:
    col_021, col_022, col_023 = st.columns([0.3,0.3,0.4],
                                           vertical_alignment="center")
    with col_021:
        st.button("⬅️ Anterior", on_click=prev_movie)

    with col_022:
        st.button("Siguiente ➡️", on_click=next_movie)

    st.markdown(
        f"""
        <h1 style='font-size: 50px; color: #b82c16;'>{st.session_state.box}</h1>
        """,
        unsafe_allow_html=True)
    st.markdown(select_film["Tag_Line"])
    directors = ", ".join(select_film['Director'])
    paises = ", ".join(select_film['Pais'])
    generos = ", ".join(select_film['Genero'])
    fila("Director:",directors)
    fila("Año:", select_film['Year'])
    fila("Duración:", str(select_film['Duracion']) + " min")
    fila("Título Original:", select_film['Titulo_Original'])
    fila("Pais", paises)
    fila("Género",generos)

with col_03:
    st.markdown(f"""
                <h3 style='font-size: 25px; color: #f55742;'>Sinopsis</h3>
                """,
                unsafe_allow_html=True)

    st.markdown(f"""
                <div style='font-size: 18px; '>{select_film['Sinopsis']}</div>
                """,
                unsafe_allow_html=True)
    col_111, col_112, col_113 = st.columns(3, vertical_alignment="center")
    with col_111:
        st.metric("TMDB rate:", f"**{select_film['TMDB_rate']}**", border=True)

    with col_112:
        st.metric(label="COD", value=f"**{select_film['COD']}**", border=True)
    with col_113:
        st.link_button(
            "![imdb](https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg) **IMDb**",
            f"https://www.imdb.com/title/{select_film['IMDB_id']}/",
            type="tertiary"
        )


st.divider()

col_11, col_12 = st.columns([0.5,0.5])

with col_11:
    st.markdown(
        f"""
            <h1 style='font-size: 40px;'>Reparto</h1>
            """,
        unsafe_allow_html=True)
    col_111, col_112 = st.columns(2, vertical_alignment="top")
    with col_111:
        for actor_id in select_film['Reparto'][:4]:
            actor_row(actors.loc[actors.Id == actor_id,"Foto"].values[0],
                      actors.loc[actors.Id == actor_id,"Nombre"].values[0])
    with col_112:
        for actor_id in select_film['Reparto'][4:8]:
            actor_row(actors.loc[actors.Id == actor_id,"Foto"].values[0],
                      actors.loc[actors.Id == actor_id,"Nombre"].values[0])

with col_12:
    try:
        st.video(select_film['Video'],format = 'rb')
    except:
        pass
