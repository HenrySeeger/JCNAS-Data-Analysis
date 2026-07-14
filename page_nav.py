import streamlit as st

pages = {
    "Resources": [
        st.Page("home.py", title="Home"),
        st.Page("graphing.py", title="Graphing"),
    ],
}

pg = st.navigation(pages)
pg.run()