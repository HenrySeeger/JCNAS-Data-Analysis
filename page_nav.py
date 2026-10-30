import streamlit as st
import streamlit_analytics2 as sa2

pages = [st.Page("data_obj.py", title = "Managing Data Objects"),
        st.Page("filter.py", title = "Filtering, Replacing, & Merging"),
        st.Page("graphing.py", title = "Graphing"),
        st.Page("stats.py", title = "Statistics"),
        st.Page("faq.py", title = "How to Use & FAQs")]

pg = st.navigation(pages)

with sa2.track():
  pg.run()