import numpy as np
import pandas as pd
import streamlit as st
import DataObject as d
import matplotlib.pyplot as plt

st.session_state.setdefault("data_objects", [])

st.header("Cleaning, Filtering, & Merging")

with st.expander(label = "Cleaning"):
  cleaning_data_object_column, cleaning_col_column = st.columns(2)
  with cleaning_data_object_column:
    cleaning_data_object = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object", "option2"], label_visibility = "collapsed")
  with cleaning_col_column:
    cleaning_col = st.selectbox(label = "Select a Column", options = ["Select a Column", "option2"], label_visibility = "collapsed", disabled = cleaning_data_object == "Select a Data Object")
  
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
      st.button(f"Remove '{cleaning_col}' from '{cleaning_data_object}'", disabled = not data_delete_confirmation)

with st.expander(label = "Filtering"):
  filter_data_object_column, filter_col_column = st.columns(2)
  with filter_data_object_column:
    def filter_select_format(data):
      return data if type(data) == str else data.name
    filter_data_object = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + st.session_state.data_objects, format_func = filter_select_format, label_visibility = "collapsed")

  with filter_col_column:
    options = ["Select a Column"] + ([] if filter_data_object == "Select a Data Object" else sorted(set(list(filter_data_object.applications.keys()) + list(filter_data_object.responses.keys()))))
    filter_col = st.selectbox(label = "Select a Column", options = options, label_visibility = "collapsed", disabled = filter_data_object == "Select a Data Object")

  if filter_col not in [None, "Select a Column"]:
    col_var_type = type(filter_data_object.key_owner(filter_col)[0].dtypes[filter_col])
    if col_var_type == pd.StringDtype:
      st.text("string")
    elif col_var_type == np.dtypes.Int64DType:
      st.text("int")
    elif col_var_type == np.dtypes.DateTime64DType:
      st.text("date")

with st.expander(label = "Merging"):
  st.text("stuff")

# with st.expander(label = "Manual Filtering"):
#   manual_dataset = st.selectbox(label = "Select a Data Object", options = ["No Selection", "option2"])
#   filter_code_input = st.text_area(label = "Enter Manual Filtration Code", placeholder = "{\"filter_code\" : ...", disabled = manual_dataset == "No Selection")