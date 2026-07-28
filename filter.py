import numpy as np
import pandas as pd
import streamlit as st
import DataObject as d
import matplotlib.pyplot as plt

st.session_state.setdefault("data_objects", [])
st.session_state.setdefault("filter_state", None)
# st.session_state.setdefault("IntFilterTabs", "a")

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
    for i, col in enumerate(st.columns([1, 17], gap = "xxsmall", border = False)):
      with col:
        if i == 0:   
          st.toggle(label = "Inlcude", key = "FilterToggle", value = True, label_visibility = "collapsed")
        else:
          st.markdown(f"<div style='padding-top: 9.5px;'>{"Include" if st.session_state.FilterToggle else "Exclude"}</div>", unsafe_allow_html = True)

    match type(filter_data_object.key_owner(filter_col)[0].dtypes[filter_col]):
      case pd.StringDtype:
        st.text("string")
      case np.dtypes.Int64DType:
        disable_button = True
        # for i, tab in enumerate(st.tabs(tabs = ["Select Bounds", "Individual Values"])):
        #   with tab:
        #     if i == 0:
        #       col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
        #       with col1:
        #         st.markdown("<div style='padding-top: 8px;'>Lower Bound</div>", unsafe_allow_html = True)
        #       with col2:
        #         int_lower = st.number_input(label = "Lower Bound", label_visibility = "collapsed", width = 200, value = None)
        #       with col3:
        #         st.markdown("<div style='padding-top: 8px;'>Upper Bound</div>", unsafe_allow_html = True)
        #       with col4:
        #         int_upper = st.number_input(label = "Upper Bound", label_visibility = "collapsed", width = 200, value = None)
        #       disable_button = int_lower is None and int_upper is None
        #       print(disable_button)
        #     else:
        #       int_area = st.text_area(label = "List Integers:", placeholder = "1, 2, 3, . . .", value = None)
        #       try:
        #         [int(val) for val in int_area.replace(" ", "").split(",")]
        #         disable_button = False
        #       except:
        #         disable_button = True
        # IntFilterBounds, IntFilterList = st.tabs(tabs = ["Select Bounds", "Individual Values"])
        int_tabs = st.segmented_control(label = "int_tabs", options = ["Select Bounds", "Individual Values"], default = "Select Bounds", selection_mode = "single", label_visibility = "collapsed")
        if int_tabs == "Select Bounds":
          col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
          with col1:
            st.markdown("<div style='padding-top: 8px;'>Lower Bound</div>", unsafe_allow_html = True)
          with col2:
            int_lower = st.number_input(label = "Lower Bound", step = 1, label_visibility = "collapsed", width = 200, value = None)
          with col3:
            st.markdown("<div style='padding-top: 8px;'>Upper Bound</div>", unsafe_allow_html = True)
          with col4:
            int_upper = st.number_input(label = "Upper Bound", step = 1, label_visibility = "collapsed", width = 200, value = None)
          disable_button = int_lower is None and int_upper is None
        elif int_tabs == "Individual Values":
          int_area = st.text_area(label = "List Integers:", placeholder = "1, 2, 3, . . .", value = "")
          try:
            a = [int(val) for val in int_area.replace(" ", "").split(",")]
            disable_button = False
          except:
            if "." in int_area:
              st.markdown(":red[Decimals should not be used here, only integers are allowed.]")
            elif int_area not in [None, ""]:
              st.markdown(":red[Only integers are allowed here.]")
            disable_button = True
        # st.text(f"(({int_tabs == "Select Bounds"} and ({int_lower is not None} or {int_upper is not None})) or ({int_tabs == "Individual Values"} and {int_area not in [None, ""]})")
        st.button(label = "Filter", disabled = disable_button)
      case np.dtypes.DateTime64DType:
        st.text("date")

with st.expander(label = "Merging"):
  st.text("stuff")

# with st.expander(label = "Manual Filtering"):
#   manual_dataset = st.selectbox(label = "Select a Data Object", options = ["No Selection", "option2"])
#   filter_code_input = st.text_area(label = "Enter Manual Filtration Code", placeholder = "{\"filter_code\" : ...", disabled = manual_dataset == "No Selection")