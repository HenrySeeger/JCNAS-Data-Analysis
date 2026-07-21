import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.title("Cleaning, Filtering, & Merging")

with st.expander(label = "Cleaning"):
  cleaning_file_column, cleaning_col_column = st.columns(2)
  with cleaning_file_column:
    cleaning_file = st.selectbox(label = "Select a File", options = ["Select a File", "option2"], label_visibility = "collapsed")
  with cleaning_col_column:
    cleaning_col = st.selectbox(label = "Select a Column", options = ["Select a Column", "option2"], label_visibility = "collapsed", disabled = cleaning_file == "Select a File")
  
  if cleaning_col != "Select a Column":
    tab_duplicates, tab_replace, tab_remove_col = st.tabs(["Remove Duplicates", "Replace/Remove Applications", "Remove a Column"])

    with tab_duplicates:
      st.button(label = "Remove Duplicates")
    
    with tab_replace:
      st.checkbox(label = "Check the box to replace NaN and None values")
      st.checkbox(label = "Check the box to remove rows with the indicated value instead of replacing them")
      st.button(label = "Replace Value")
    
    with tab_remove_col:
      data_delete_confirmation = st.toggle(label = f"Confirm removal of {cleaning_col}", value = False)
      # data_delete_button = st.button(f"Delete {data_manager_data_selector}", disabled = not data_delete_confirmation, on_click = delete_data)
      st.button(f"Remove '{cleaning_col}' from '{cleaning_file}'", disabled = not data_delete_confirmation)

with st.expander(label = "Filtering"):
  st.text("stuff")

with st.expander(label = "Merging"):
  st.text("stuff")