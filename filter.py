import datetime
import numpy as np
import pandas as pd
import streamlit as st
import DataObject as d
import matplotlib.pyplot as plt

st.session_state.setdefault("data_objects", [])
st.session_state.setdefault("filter_state", None)

st.header("Cleaning, Filtering, & Merging")

#* Cleaning Section
with st.expander(label = "Cleaning"):
  cleaning_data_object_column, cleaning_col_column = st.columns(2)
  with cleaning_data_object_column:
    def clean_select_format(num):
      return num if type(num) == str else st.session_state.data_objects[num].name
    cleaning_data_object_index = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + list(range(len(st.session_state.data_objects))), key = "CleaningDataObject", format_func = clean_select_format, label_visibility = "collapsed")
  with cleaning_col_column:
    options = ["Select a Column"] + ([] if cleaning_data_object_index == "Select a Data Object" else sorted(set(list(st.session_state.data_objects[cleaning_data_object_index].applications.keys()) + list(st.session_state.data_objects[cleaning_data_object_index].responses.keys()))))
    cleaning_col = st.selectbox(label = "Select a Column", options = options, label_visibility = "collapsed", key = "CleaningColumn", disabled = cleaning_data_object_index == "Select a Data Object")
  
  if cleaning_col != "Select a Column":
    tab_duplicates, tab_replace, tab_remove_col = st.tabs(["Remove Duplicates", "Replace/Remove Applications", "Remove a Column"])

    #* Remove Duplicates
    with tab_duplicates:

      def remove_duplicates():
        global cleaning_col
        match (cleaning_col in st.session_state.data_objects[cleaning_data_object_index].applications.keys(), cleaning_col in st.session_state.data_objects[cleaning_data_object_index].responses.keys()):
          case (True, False): # column in applications dataset
            initial = len(st.session_state.data_objects[cleaning_data_object_index].applications)
            st.session_state.data_objects[cleaning_data_object_index].applications.drop_duplicates(subset = cleaning_col, inplace = True)
            st.toast(body = f"Successfully removed {initial - len(st.session_state.data_objects[cleaning_data_object_index].applications)} duplicate values")
            st.session_state.data_objects[cleaning_data_object_index].add_filter_history("duplicates", "applications", cleaning_col, True, True)
          case (False, True): # column in responses dataset
            initial = len(st.session_state.data_objects[cleaning_data_object_index].responses)
            st.session_state.data_objects[cleaning_data_object_index].responses.drop_duplicates(subset = cleaning_col, inplace = True)
            st.toast(body = f"Successfully removed {initial - len(st.session_state.data_objects[cleaning_data_object_index].responses)} duplicate values")
            st.session_state.data_objects[cleaning_data_object_index].add_filter_history("duplicates", "responses", cleaning_col, True, True)
          case (True, True): # column in both datasets
            st.session_state.data_objects[cleaning_data_object_index].applications.drop_duplicates(subset = cleaning_col, inplace = True)
            st.session_state.data_objects[cleaning_data_object_index].responses.drop_duplicates(subset = cleaning_col, inplace = True)
            st.toast(body = f"Successfully removed duplicate values")
            st.session_state.data_objects[cleaning_data_object_index].add_filter_history("duplicates", "both", cleaning_col, True, True)
        cleaning_col = "Select a Column"

      st.button(label = "Remove Duplicates", on_click = remove_duplicates)

    #* Replace Values
    with tab_replace:
      st.checkbox(label = "Check the box to replace NaN and None values")
      st.checkbox(label = "Check the box to remove rows with the indicated value instead of replacing them")
      st.button(label = "Replace Value")

    #* Delete a Column
    with tab_remove_col:
      data_delete_confirmation = st.toggle(label = f"Confirm removal of {cleaning_col}", value = False)

      def delete_column():
        global cleaning_col
        if cleaning_col in st.session_state.data_objects[cleaning_data_object_index].applications.keys():
          st.session_state.data_objects[cleaning_data_object_index].applications.drop(columns = cleaning_col, inplace = True)
        if cleaning_col in st.session_state.data_objects[cleaning_data_object_index].responses.keys():
          st.session_state.data_objects[cleaning_data_object_index].responses.drop(columns = cleaning_col, inplace = True)

        st.session_state.data_objects[cleaning_data_object_index].add_filter_history("deletion", "both", cleaning_col, True, True)
        st.toast(body = f"Successfully removed '{"address"}' from '{st.session_state.data_objects[cleaning_data_object_index].name}'")
        cleaning_col = "Select a Column"

      st.button(f"Remove '{cleaning_col}' from '{st.session_state.data_objects[cleaning_data_object_index].name}'", on_click = delete_column, disabled = not data_delete_confirmation)

#* Filtration Expander Section
with st.expander(label = "Filtering"):
  filter_data_object_column, filter_col_column = st.columns(2)

  #* Data Object Selector
  with filter_data_object_column:
    def filter_select_format(num):
      return num if type(num) == str else st.session_state.data_objects[num].name
    # filter_data_object = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + st.session_state.data_objects, format_func = filter_select_format, label_visibility = "collapsed")
    filter_data_object_index = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + list(range(len(st.session_state.data_objects))), key = "FilterDataObject", format_func = filter_select_format, label_visibility = "collapsed")

  #* Data Object Column Selector 
  with filter_col_column:
    options = ["Select a Column"] + ([] if filter_data_object_index == "Select a Data Object" else sorted(set(list(st.session_state.data_objects[filter_data_object_index].applications.keys()) + list(st.session_state.data_objects[filter_data_object_index].responses.keys()))))
    filter_col = st.selectbox(label = "Select a Column", options = options, label_visibility = "collapsed", key = "FilterColumn", disabled = filter_data_object_index == "Select a Data Object")

  #* Inclusion/Exclusion & None Inclusion toggles
  if filter_col not in [None, "Select a Column"]:
    for i, col in enumerate(st.columns([1, 6.5, 1, 9.5], gap = "xxsmall", border = False)):
      with col:
        if i == 0:
          st.toggle(label = "Inlcude", key = "FilterInclusionToggle", value = True, label_visibility = "collapsed")
        elif i == 1:
          st.markdown(f"<div style='padding-top: 9.5px;'>{"Include" if st.session_state.FilterInclusionToggle else "Exclude"} Selected Bounds/Values</div>", unsafe_allow_html = True)
        elif i == 2:
          st.toggle(label = "Inlcude", key = "FilterNoneToggle", value = True, label_visibility = "collapsed")
        else:
          st.markdown(f"<div style='padding-top: 9.5px;'>{"Keep" if st.session_state.FilterNoneToggle else "Remove"} Empty Values</div>", unsafe_allow_html = True)

    #* Filter Button Logic Controls
    disable_button = True
    filter_function = None
    filter_function_args = None

    #* Variable Type Selection 
    match type(st.session_state.data_objects[filter_data_object_index].key_owner(filter_col).dtypes[filter_col]):

      #* String Variable Type
      case pd.StringDtype:
        for i, col in enumerate(st.columns([1, 6.5, 1, 9.5], gap = "xxsmall", border = False)):
          with col:
            if i == 0:
              st.toggle(label = "Inlcude", key = "FilterExactStringToggle", value = True, label_visibility = "collapsed")
            elif i == 1:
              st.markdown(f"<div style='padding-top: 9.5px;'>{"Is Exact" if st.session_state.FilterExactStringToggle else "Contains"} Word(s)</div>", unsafe_allow_html = True)
            elif i == 2:
              st.toggle(label = "Inlcude", key = "FilterCaseSensitivityToggle", value = True, label_visibility = "collapsed")
            else:
              st.markdown(f"<div style='padding-top: 9.5px;'>Case {"Sensitive" if st.session_state.FilterCaseSensitivityToggle else "Insensitive"}</div>", unsafe_allow_html = True)

        string_area = st.text_area(label = "List String(s):", placeholder = "Green|Efficient|Energy", value = "", key = "FilterStringArea")

        disable_button = string_area == ""
        filter_function = d.string_filter
        filter_function_args = ((filter_data_object_index, filter_col, string_area),
                                ("string", st.session_state.data_objects[filter_data_object_index].key_owner_name(filter_col), filter_col, st.session_state.FilterInclusionToggle, st.session_state.FilterNoneToggle),
                                {"string_values" : string_area.split("|")})

      #* Integer Variable Type
      case np.dtypes.Int64DType:
        int_tabs = st.segmented_control(label = "int_tabs", options = ["Select Bounds", "Individual Values"], default = "Select Bounds", selection_mode = "single", label_visibility = "collapsed")

        #* Lower and Upper Bounds
        if int_tabs == "Select Bounds":
          col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
          with col1:
            st.markdown("<div style='padding-top: 8px;'>Lower Bound</div>", unsafe_allow_html = True)
          with col2:
            int_lower_bound = st.number_input(label = "Lower Bound", step = 1, label_visibility = "collapsed", key = "IntLowerBound", width = 200, value = None)
          with col3:
            st.markdown("<div style='padding-top: 8px;'>Upper Bound</div>", unsafe_allow_html = True)
          with col4:
            int_upper_bound = st.number_input(label = "Upper Bound", step = 1, label_visibility = "collapsed", key = "IntUpperBound", width = 200, value = None)

          disable_button = int_lower_bound is None and int_upper_bound is None
          if int_lower_bound is not None and int_upper_bound is not None and int_lower_bound >= int_upper_bound:
            st.markdown(":red[The lower bound must be less than the upper bound.]")

          filter_function = d.int_bounds_filter
          filter_function_args = ((filter_data_object_index, filter_col, int_lower_bound, int_upper_bound),
                                  ("int_bound", st.session_state.data_objects[filter_data_object_index].key_owner_name(filter_col), filter_col, st.session_state.FilterInclusionToggle, st.session_state.FilterNoneToggle), 
                                  {"int_lower_bound" : int_lower_bound, "int_upper_bound" : int_upper_bound})

        #* List of Integers
        elif int_tabs == "Individual Values":
          int_area = st.text_area(label = "List Integers:", placeholder = "1, 2, 3, . . .", value = "", key = "IntArea")
          try:
            disable_button = False
            filter_function = d.int_values_filter
            filter_function_args = ((filter_data_object_index, filter_col, int_area),
                                  ("int_values", st.session_state.data_objects[filter_data_object_index].key_owner_name(filter_col), filter_col, st.session_state.FilterInclusionToggle, st.session_state.FilterNoneToggle),
                                  {"int_values" : [int(num) for num in int_area.replace(" ", "").replace("\n", "").split(",")]})
          except:
            if "." in int_area:
              st.markdown(":red[Decimals should not be used here, only integers are allowed.]")
            elif int_area not in [None, ""]:
              st.markdown(":red[Only integers are allowed here.]")

            disable_button = True

      #* DateTime Variable Type
      case np.dtypes.DateTime64DType:
        date_tabs = st.segmented_control(label = "date_tabs", options = ["Select Date Bounds", "Individual Dates"], default = "Select Date Bounds", selection_mode = "single", label_visibility = "collapsed")
        
        #* Earlier and Later Bounds
        if date_tabs == "Select Date Bounds":
          col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
          with col1:
            st.markdown("<div style='padding-top: 8px;'>Earlier Date</div>", unsafe_allow_html = True)
          with col2:
            date_earlier_bound = st.date_input(label = "Earlier Date", label_visibility = "collapsed", key = "DateEarlierBound", width = 200, value = None)
          with col3:
            st.markdown("<div style='padding-top: 8px;'>Later Date</div>", unsafe_allow_html = True)
          with col4:
            date_later_bound = st.date_input(label = "Later Date", label_visibility = "collapsed", key = "DateLaterBound", width = 200, value = None)

          disable_button = date_earlier_bound is None and date_later_bound is None
          if date_earlier_bound is not None and date_later_bound is not None and date_earlier_bound >= date_later_bound:
            st.markdown(":red[The lower bound must be less than the upper bound.]")

          filter_function = d.date_bounds_filter
          filter_function_args = ((filter_data_object_index, filter_col, date_earlier_bound, date_later_bound),
                                  ("date_bound", st.session_state.data_objects[filter_data_object_index].key_owner_name(filter_col), filter_col, st.session_state.FilterInclusionToggle, st.session_state.FilterNoneToggle), 
                                  {"date_earlier_bound" : date_earlier_bound, "date_later_bound" : date_later_bound})

      #* List of Dates
        elif date_tabs == "Individual Dates":
          date_area = st.text_area(label = "List Dates:", placeholder = "YYYY/MM/DD, 2026/08/10, 2025/03/12, . . .", value = "", key = "DateArea")
          try:
            disable_button = False
            filter_function = d.date_values_filter
            filter_function_args = ((filter_data_object_index, filter_col, date_area),
                                    ("date_values", st.session_state.data_objects[filter_data_object_index].key_owner_name(filter_col), filter_col, st.session_state.FilterInclusionToggle, st.session_state.FilterNoneToggle),
                                    {"date_values" : [pd.Timestamp(date) for date in date_area.replace(" ", "").replace("\n", "").split(",")]})
          except:
            st.markdown(":red[Only dates ('YYYY-MM-DD') are allowed here.]")

            disable_button = True

    def filter_on_click(*args):
      """
        Updates the DataObject's filtration history. It also updates the other datasets that weren't directly filtered
      
        Args:
          arg1 (tuple): Used for the filtration     | filter_data_object_index, filter_col, any additonal arguments necessray for the filtration
          arg2 (tuple): Used for filtration history | filter_code, dataset, column, include_values, include_none
          arg3  (dict): Used for filtration history | Any keyword arguments specific to the method of filtration
          """
      filter_function(*args[0])
      st.session_state.data_objects[filter_data_object_index].add_filter_history(*args[1], **args[2])

    st.button(label = "Filter", disabled = disable_button, on_click = filter_on_click, args = filter_function_args)

with st.expander(label = "Merging"):
  st.text("stuff")

# with st.expander(label = "Manual Filtering"):
#   manual_dataset = st.selectbox(label = "Select a Data Object", options = ["No Selection", "option2"])
#   filter_code_input = st.text_area(label = "Enter Manual Filtration Code", placeholder = "{\"filter_code\" : ...", disabled = manual_dataset == "No Selection")