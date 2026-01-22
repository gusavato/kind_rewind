import streamlit as st

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