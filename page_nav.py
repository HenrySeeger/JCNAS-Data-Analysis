import streamlit as st

pages = [#st.Page("home.py", title = "Home"),
         st.Page("data_obj.py", title = "Managing Data Objects"),
         st.Page("filter.py", title = "Cleaning, Filtering, & Merging"),
         st.Page("graphing.py", title = "Graphing"),
         st.Page("stats.py", title = "Statistics"),
         st.Page("faq.py", title = "How to Use & FAQs")]

pg = st.navigation(pages)#, position="top")
pg.run()