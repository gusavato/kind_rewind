import streamlit as st
import pandas as pd
from streamlit import session_state
from unidecode import unidecode
from pathlib import Path

# CONSTANTES
ROOT = Path.cwd()
FILMS_PARQUET = ROOT / "data" / "films.parquet"
ACTORS_PARQUET = ROOT / "data" / "actors.parquet"


# Funciones
# Botones
def next_movie(f_list):
    if session_state.idx == len(f_list) - 1:
        st.session_state.idx = 0

    else:
        st.session_state.idx += 1
    st.session_state.box = f_list[st.session_state.idx]


def prev_movie(f_list):
    if session_state.idx == 0:
        st.session_state.idx = len(f_list) - 1
    else:
        st.session_state.idx -= 1
    st.session_state.box = f_list[st.session_state.idx]


# Sincronización índices
def sync_idx(f_list):
    box_select = st.session_state.box
    st.session_state.idx = f_list.index(box_select)


# Funciones fila

def fila(label, value):
    st.markdown(
        f"""
        <div style="
            display:grid;
            grid-template-columns: 160px auto;
            align-items:baseline;
            margin-bottom:6px;
        ">
            <span style="font-size:20px; font-weight:600;">
                {label}
            </span>
            <span style="font-size:20px; color:#b82c16;">
                {value}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


def actor_row(img_url, actor_name):
    st.markdown(
        f"""
        <div style="
            display:grid;
            grid-template-columns: 70px auto;
            align-items:center;
            gap:14px;
            margin-bottom:10px;
            padding:8px;
            border-radius:10px;
        ">
            <img src="{img_url}"
                 style="
                    width:60px;
                    height:60px;
                    object-fit:cover;
                    border-radius:50%;
                 " />
            <span style="
                font-size:20px;
                font-weight:600;
            ">
                {actor_name}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Resetear filtros
def reset_filtros(f_list):
    st.session_state.genero = []
    st.session_state.search = ""
    st.session_state.search_select = "Titulo"

    st.session_state.duracion = (
        f_list.Duracion.min(),
        f_list.Duracion.max()
    )
    st.session_state.nota = (
        0,
        10
    )
    st.session_state.slider = (
        f_list.Year.min(),
        f_list.Year.max()
    )

    st.session_state.idx = 0

# Configuración página
st.set_page_config(layout='wide')

# Carga de dataframe
films = pd.read_parquet(FILMS_PARQUET, engine='pyarrow').sort_values(by=['ID'], ascending=False)
films['Titulo_unidecode'] = films.Titulo.apply(lambda x: unidecode(x))
films['Director_unidecode'] = films.Director.apply(
    lambda x: [unidecode(i).lower() for i in x])
actors = pd.read_parquet(ACTORS_PARQUET, engine='pyarrow')
actors['Nombre_unicode'] = actors.Nombre.apply(lambda x: unidecode(x))

# Sidebar
warning_placeholder = st.sidebar.empty()
box_placeholder = st.sidebar.empty()
genero_placeholder = st.sidebar.empty()

with genero_placeholder:
    st.sidebar.multiselect(
        'Género',
        options=films.Genero.explode().sort_values().unique(),
        key='genero')

st.sidebar.text_input('Búsqueda', key='search')
st.sidebar.radio(label='Opción', horizontal=True, options=[
    'Titulo', 'Reparto', 'Director'],
                 key='search_select')

with st.sidebar.expander('Mas filtros', expanded=True):
    st.slider(label='Valoración', min_value=0,
              max_value=10, key='nota')

    st.slider(label='Año', min_value=films.Year.min(),
              max_value=films.Year.max(), key='slider',
              value=[films.Year.min(), films.Year.max()])

    st.slider(label='Duración', min_value=films.Duracion.min(),
              max_value=films.Duracion.max(), key='duracion',
              value=[films.Duracion.min(), films.Duracion.max()])

# Filtrado dataframe
films_filtrado = films.copy()

if st.session_state.genero:
    films_filtrado = films_filtrado[
        (films_filtrado['Genero']
        .apply(
            lambda lista: any(g in lista for g in st.session_state.genero)
        )
        )
    ]

# Filtros expander
min_dur, max_dur = st.session_state.duracion
min_nota, max_nota = st.session_state.nota
min_year, max_year = st.session_state.slider

films_filtrado = films_filtrado[
    films_filtrado['Duracion'].between(min_dur, max_dur)
    & films_filtrado['TMDB_rate'].between(min_nota, max_nota)
    & films_filtrado['Year'].between(min_year, max_year)
]

# Filtros search
if session_state.search != '':
    if session_state.search_select == 'Titulo':
        films_filtrado = films_filtrado[
            (films_filtrado['Titulo_unidecode'].str.lower().str.contains(session_state.search.lower()))
        ]
    elif  session_state.search_select == 'Director':
        films_filtrado = films_filtrado[
            (films['Director_unidecode'].apply(lambda x: any(session_state.search.lower() in i for i in x)))
        ]
    elif session_state.search_select == 'Reparto':
        id_actor = actors[
            actors.Nombre_unicode.str.lower().str.contains(session_state.search.lower())]['Id'].to_list()

        films_filtrado = films_filtrado[
            (films_filtrado['Reparto'].apply(lambda x: any(item in id_actor for item in x)))
        ]

if films_filtrado.empty:
    films_filtrado = films.copy()
    warning_placeholder.write("❌ No hay películas con los filtros seleccionados")

film_list = films_filtrado.sort_values("ID", ascending=False)['Titulo'].to_list()

# Inicialización de variables de sesión
st.session_state.setdefault('idx', 0)
if st.session_state.idx >= len(film_list):
    st.session_state.idx = 0

# Actualizar selectbox titulo
select = box_placeholder.selectbox(
    "Titulo",
    options=film_list,
    on_change=sync_idx,
    key='box',
    args=(film_list,)
)

select_film = films.loc[films.Titulo == select, :].iloc[0].to_dict()
st.sidebar.button("🎛️ Inicializar filtros", on_click= reset_filtros, args=(films,))
st.sidebar.write(f"{films_filtrado.shape[0]} películas")

# Página Principal
col_01, col_02, col_03 = st.columns(
    spec=[0.20, 0.40, 0.40],
    gap='medium',
    vertical_alignment='top')

with col_01:
    st.image(select_film['Poster'], width=500)

with col_02:
    col_021, col_022, col_023 = st.columns([0.3, 0.3, 0.4],
                                           vertical_alignment="center")
    with col_021:
        st.button("⬅️ Anterior", on_click=prev_movie, args=(film_list,))

    with col_022:
        st.button("Siguiente ➡️", on_click=next_movie, args=(film_list,))

    st.markdown(
        f"""
        <h1 style='font-size: 50px; color: #b82c16;'>{st.session_state.box}</h1>
        """,
        unsafe_allow_html=True)
    st.markdown(select_film["Tag_Line"])
    directors = ", ".join(select_film['Director'])
    paises = ", ".join(select_film['Pais'])
    generos = ", ".join(select_film['Genero'])
    fila("Director:", directors)
    fila("Año:", select_film['Year'])
    fila("Duración:", str(select_film['Duracion']) + " min")
    fila("Título Original:", select_film['Titulo_Original'])
    fila("Pais", paises)
    fila("Género", generos)

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
        st.metric("TMDB rate:", f"{select_film['TMDB_rate']}", border=True)

    with col_112:
        st.metric(label="COD", value=f"{select_film['COD']}", border=True)
    with col_113:
        st.link_button(
            "![imdb](https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg) **IMDb**",
            f"https://www.imdb.com/title/{select_film['IMDB_id']}/",
            type="tertiary"
        )

st.divider()

col_11, col_12 = st.columns([0.5, 0.5])

with col_11:
    st.markdown(
        f"""
            <h1 style='font-size: 40px;'>Reparto</h1>
            """,
        unsafe_allow_html=True)
    col_111, col_112 = st.columns(2, vertical_alignment="top")
    with col_111:
        for actor_id in select_film['Reparto'][:4]:
            actor_row(actors.loc[actors.Id == actor_id, "Foto"].values[0],
                      actors.loc[actors.Id == actor_id, "Nombre"].values[0])
    with col_112:
        for actor_id in select_film['Reparto'][4:8]:
            actor_row(actors.loc[actors.Id == actor_id, "Foto"].values[0],
                      actors.loc[actors.Id == actor_id, "Nombre"].values[0])

with col_12:
    try:
        st.video(select_film['Video'], format='rb')
    except:
        pass
