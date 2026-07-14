import streamlit as st

pages = [st.Page("home.py", title = "Home"),
         st.Page("data_obj.py", title = "Data Objects Creation and Management"),
         st.Page("graphing.py", title = "Graphing"),
         st.Page("stats.py", title = "Statistics"),
         st.Page("faq.py", title = "FAQ")]

pg = st.navigation(pages)
pg.run()