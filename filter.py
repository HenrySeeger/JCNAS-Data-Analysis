import datetime
import numpy as np
import pandas as pd
import streamlit as st
import DataObject as d
import matplotlib.pyplot as plt

st.session_state.setdefault("data_objects", [])
st.session_state.setdefault("filter_state", None)
st.session_state.setdefault("ReplaceNoneToggle", False)

st.header("Cleaning, Filtering, & Merging")

#* Cleaning Section
with st.expander(label = "Cleaning"):
  cleaning_data_object_column, cleaning_col_column = st.columns(2)

  #* Data Object Selector
  with cleaning_data_object_column:
    def clean_select_format(num):
      return num if type(num) == str else st.session_state.data_objects[num].name
    cleaning_data_object_index = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + list(range(len(st.session_state.data_objects))), key = "CleaningDataObject", format_func = clean_select_format, label_visibility = "collapsed")

  #* Data Object Column Selector
  with cleaning_col_column:
    options = ["Select a Column"] + ([] if cleaning_data_object_index == "Select a Data Object" else sorted(set(list(st.session_state.data_objects[cleaning_data_object_index].applications.keys()) + list(st.session_state.data_objects[cleaning_data_object_index].responses.keys()))))
    cleaning_col = st.selectbox(label = "Select a Column", options = options, label_visibility = "collapsed", key = "CleaningColumn", disabled = cleaning_data_object_index == "Select a Data Object")
  
  if cleaning_col != "Select a Column":
    tab_duplicates, tab_filter, tab_remove_col = st.tabs(["Remove Duplicates", "Filter Entries", "Remove a Column"])

    #* Remove Duplicates
    with tab_duplicates:

      def remove_duplicates():
        global cleaning_col
        match (cleaning_col in st.session_state.data_objects[cleaning_data_object_index].applications.keys(), cleaning_col in st.session_state.data_objects[cleaning_data_object_index].responses.keys()):
          case (True, False): # column in applications dataset
            initial = len(st.session_state.data_objects[cleaning_data_object_index].applications)
            st.session_state.data_objects[cleaning_data_object_index].applications.drop_duplicates(subset = cleaning_col, inplace = True)
            st.toast(body = f"Successfully removed {initial - len(st.session_state.data_objects[cleaning_data_object_index].applications)} duplicate values")
            st.session_state.data_objects[cleaning_data_object_index].add_action_history("duplicates", "applications", cleaning_col)
          case (False, True): # column in responses dataset
            initial = len(st.session_state.data_objects[cleaning_data_object_index].responses)
            st.session_state.data_objects[cleaning_data_object_index].responses.drop_duplicates(subset = cleaning_col, inplace = True)
            st.toast(body = f"Successfully removed {initial - len(st.session_state.data_objects[cleaning_data_object_index].responses)} duplicate values")
            st.session_state.data_objects[cleaning_data_object_index].add_action_history("duplicates", "responses", cleaning_col)
          case (True, True): # column in both datasets
            st.session_state.data_objects[cleaning_data_object_index].applications.drop_duplicates(subset = cleaning_col, inplace = True)
            st.session_state.data_objects[cleaning_data_object_index].responses.drop_duplicates(subset = cleaning_col, inplace = True)
            st.toast(body = f"Successfully removed duplicate values")
            st.session_state.data_objects[cleaning_data_object_index].add_action_history("duplicates", "both", cleaning_col)
        cleaning_col = "Select a Column"

      st.button(label = "Remove Duplicates", on_click = remove_duplicates)

    #* Filter Values replace
    with tab_filter:
      #* Inclusion/Exclusion & None Inclusion toggles
      if cleaning_col not in [None, "Select a Column"]:
        for i, col in enumerate(st.columns([1, 6.5, 1, 9.5], gap = "xxsmall", border = False)):
          with col:
            if i == 0:
              st.toggle(label = "Inlcude", key = "FilterInclusionToggle", value = True, label_visibility = "collapsed")
            elif i == 1: #! Figure out why this None check needs to happen
              st.markdown(f"<div style='padding-top: 9.5px;'>{"Include" if st.session_state.FilterInclusionToggle or st.session_state.FilterInclusionToggle is None else "Exclude"} Selected Bounds/Values</div>", unsafe_allow_html = True)
            elif i == 2:
              st.toggle(label = "Inlcude", key = "FilterNoneToggle", value = False, label_visibility = "collapsed")
            else:
              st.markdown(f"<div style='padding-top: 9.5px;'>{"Remove" if st.session_state.FilterNoneToggle else "Keep"} Empty Values</div>", unsafe_allow_html = True)

        #* Filter Button Logic Controls
        disable_filter_button = True
        filter_function = None
        filter_function_args = None

        #* Variable Type Selection filt
        match type(st.session_state.data_objects[cleaning_data_object_index].key_owner(cleaning_col)[0].dtypes[cleaning_col]):

          #* String Variable Type
          case pd.StringDtype:
            for i, col in enumerate(st.columns([1, 6.5, 1, 5, 1, 3.5], gap = "xxsmall", border = False)):
              with col:
                if i == 0:
                  st.toggle(label = "Inlcude", key = "FilterExactStringToggle", value = True, label_visibility = "collapsed")
                elif i == 1:
                  st.markdown(f"<div style='padding-top: 9.5px;'>{"Matches Exact" if st.session_state.FilterExactStringToggle else "Contains"} Text</div>", unsafe_allow_html = True)
                elif i == 2:
                  st.toggle(label = "CaseSensitivity", key = "FilterCaseSensitiveToggle", value = True, label_visibility = "collapsed")
                elif i == 3:
                  st.markdown(f"<div style='padding-top: 9.5px;'>Case {"Sensitive" if st.session_state.FilterCaseSensitiveToggle else "Insensitive"}</div>", unsafe_allow_html = True)
                elif i == 4:
                  st.toggle(label = "AndGating", key = "FilterOrGateToggle", value = False, label_visibility = "collapsed")
                else:
                  st.markdown(f"<div style='padding-top: 9.5px;'>{"And" if st.session_state.FilterOrGateToggle else "Or"}-Gate</div>", unsafe_allow_html = True)

            string_selections = st.multiselect(label = "List Text:", options = None, accept_new_options = True, key = "FilterStringSelections")

#                                    trying to filter without selected values (None-values included)
            disable_filter_button = string_selections == [] and not st.session_state.FilterNoneToggle
            filter_function = d.string_filter
            filter_function_args = ((cleaning_data_object_index, cleaning_col, string_selections),
                                    ("filter_string", st.session_state.data_objects[cleaning_data_object_index].key_owner_name(cleaning_col), cleaning_col),
                                    {"include_values" : st.session_state.FilterInclusionToggle,
                                     "include_none" : st.session_state.FilterNoneToggle,
                                     "string_values" : string_selections,
                                     "exact_string" : st.session_state.FilterExactStringToggle,
                                     "case_sensitive" : st.session_state.FilterCaseSensitiveToggle,
                                     "and_gate" : st.session_state.FilterOrGateToggle})

          #* Integer Variable Type
          case np.dtypes.Int64DType:
            int_tabs = st.segmented_control(label = "filter_int_tabs", options = ["Select Bounds", "Individual Values"], default = "Select Bounds", selection_mode = "single", label_visibility = "collapsed")

            #* Lower and Upper Bounds
            if int_tabs == "Select Bounds":
              col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
              with col1:
                st.markdown("<div style='padding-top: 8px;'>Lower Bound</div>", unsafe_allow_html = True)
              with col2:
                int_lower_bound = st.number_input(label = "Lower Bound", step = 1, label_visibility = "collapsed", key = "FilterIntLowerBound", width = 200, value = None)
              with col3:
                st.markdown("<div style='padding-top: 8px;'>Upper Bound</div>", unsafe_allow_html = True)
              with col4:
                int_upper_bound = st.number_input(label = "Upper Bound", step = 1, label_visibility = "collapsed", key = "FilterIntUpperBound", width = 200, value = None)

              if int_lower_bound is not None and int_upper_bound is not None and int_lower_bound > int_upper_bound:
                st.markdown(":red[The lower bound must not be greater than the upper bound.]")

#                                                trying to filter without selected values (None-values included)                                            trying to filter with a lower_bound greater than the upper bound
              disable_filter_button = (int_lower_bound is None and int_upper_bound is None and not st.session_state.FilterNoneToggle) or (int_lower_bound is not None and int_upper_bound is not None and int_lower_bound > int_upper_bound)
              filter_function = d.int_bounds_filter
              filter_function_args = ((cleaning_data_object_index, cleaning_col, int_lower_bound, int_upper_bound),
                                      ("filter_int_bound", st.session_state.data_objects[cleaning_data_object_index].key_owner_name(cleaning_col), cleaning_col), 
                                      {"include_values" : st.session_state.FilterInclusionToggle,
                                      "include_none" : st.session_state.FilterNoneToggle,
                                      "int_lower_bound" : int_lower_bound,
                                      "int_upper_bound" : int_upper_bound})

            #* List of Integers
            elif int_tabs == "Individual Values":
              int_selections = st.multiselect(label = "List Integers:", options = None, accept_new_options = True, key = "FilterIntSelections")

              try:
#                                       trying to filter without selected values (None-values included)                
                disable_filter_button = int_selections == [] and not st.session_state.FilterNoneToggle
                filter_function = d.int_values_filter
                filter_function_args = ((cleaning_data_object_index, cleaning_col, int_selections),
                                        ("filter_int_values", st.session_state.data_objects[cleaning_data_object_index].key_owner_name(cleaning_col), cleaning_col),
                                        {"include_values" : st.session_state.FilterInclusionToggle,
                                        "include_none" : st.session_state.FilterNoneToggle,
                                        "int_values" : [int(num) for num in int_selections]})
              except:
                if len([i for i in int_selections if "." in i]):
                  st.markdown(":red[Decimals should not be used, only integers are allowed.]")
                elif int_selections not in [None, []]:
                  st.markdown(":red[Only integers are allowed.]")
                disable_filter_button = True

          #* DateTime Variable Type
          case np.dtypes.DateTime64DType:
            date_tabs = st.segmented_control(label = "filter_date_tabs", options = ["Select Date Bounds", "Individual Dates"], default = "Select Date Bounds", selection_mode = "single", label_visibility = "collapsed")

            #* Earlier and Later Bounds
            if date_tabs == "Select Date Bounds":
              col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
              with col1:
                st.markdown("<div style='padding-top: 8px;'>Earlier Date</div>", unsafe_allow_html = True)
              with col2:
                date_earlier_bound = st.date_input(label = "Earlier Date", label_visibility = "collapsed", key = "FilterDateEarlierBound", width = 200, value = None)
              with col3:
                st.markdown("<div style='padding-top: 8px;'>Later Date</div>", unsafe_allow_html = True)
              with col4:
                date_later_bound = st.date_input(label = "Later Date", label_visibility = "collapsed", key = "FilterDateLaterBound", width = 200, value = None)

              if date_earlier_bound is not None and date_later_bound is not None and date_earlier_bound >= date_later_bound:
                st.markdown(":red[The lower bound must not be greater than the upper bound.]")

#                                                   trying to filter without selected values (None-values included)                                           trying to filter with an earlier date later than the later date
              disable_filter_button = (date_earlier_bound is None and date_later_bound is None and not st.session_state.FilterNoneToggle) or (date_earlier_bound is not None and date_later_bound is not None and date_earlier_bound > date_later_bound)
              filter_function = d.date_bounds_filter
              filter_function_args = ((cleaning_data_object_index, cleaning_col, date_earlier_bound, date_later_bound),
                                      ("filter_date_bound", st.session_state.data_objects[cleaning_data_object_index].key_owner_name(cleaning_col), cleaning_col), 
                                      {"include_values" : st.session_state.FilterInclusionToggle,
                                      "include_none" : st.session_state.FilterNoneToggle,
                                      "date_earlier_bound" : date_earlier_bound,
                                      "date_later_bound" : date_later_bound})

          #* List of Dates
            elif date_tabs == "Individual Dates":
              date_selections = st.multiselect(label = "List Dates:", options = None, accept_new_options = True, placeholder = "YYYY/MM/DD", key = "FilterDateSelections")

              try:
                disable_filter_button = date_selections == [] and not st.session_state.FilterNoneToggle
                filter_function = d.date_values_filter
                filter_function_args = ((cleaning_data_object_index, cleaning_col, date_selections),
                                        ("filter_date_values", st.session_state.data_objects[cleaning_data_object_index].key_owner_name(cleaning_col), cleaning_col),
                                        {"include_values" : st.session_state.FilterInclusionToggle,
                                        "include_none" : st.session_state.FilterNoneToggle,
                                        "date_values" : [pd.Timestamp(date) for date in date_selections]})
              except:
                st.markdown(":red[Only dates ('YYYY-MM-DD') are allowed.]")
                disable_filter_button = True

        def filter_on_click(*args):
          """
            Updates the DataObject's action history. It also updates the other datasets that weren't directly filtered

            Args:
              arg1 (tuple): Used for the action     | cleaning_data_object_index, cleaning_col, any additonal arguments necessray for the action
              arg2 (tuple): Used for action history | filter_code, dataset, column
              arg3  (dict): Used for action history | Any keyword arguments specific to the method of action
              """
          filter_function(*args[0])
          st.session_state.data_objects[cleaning_data_object_index].add_action_history(*args[1], **args[2])

        st.button(label = "Filter", disabled = disable_filter_button, on_click = filter_on_click, args = filter_function_args)

    #* Delete a Column
    with tab_remove_col:
      data_delete_confirmation = st.toggle(label = f"Confirm removal of {cleaning_col}", value = False)

      def delete_column():
        global cleaning_col
        if cleaning_col in st.session_state.data_objects[cleaning_data_object_index].applications.keys():
          st.session_state.data_objects[cleaning_data_object_index].applications.drop(columns = cleaning_col, inplace = True)
        if cleaning_col in st.session_state.data_objects[cleaning_data_object_index].responses.keys():
          st.session_state.data_objects[cleaning_data_object_index].responses.drop(columns = cleaning_col, inplace = True)

        st.session_state.data_objects[cleaning_data_object_index].add_action_history("deletion", "both", cleaning_col)
        st.toast(body = f"Successfully removed '{cleaning_col}' from '{st.session_state.data_objects[cleaning_data_object_index].name}'")
        cleaning_col = "Select a Column"

      st.button(f"Remove '{cleaning_col}' from '{st.session_state.data_objects[cleaning_data_object_index].name}'", on_click = delete_column, disabled = not data_delete_confirmation)

#* Replacement Expander Section
with st.expander(label = "Replacing"):
  replace_data_object_column, replace_col_column = st.columns(2)

  #* Data Object Selector
  with replace_data_object_column:
    def replace_select_format(num):
      return num if type(num) == str else st.session_state.data_objects[num].name
    # replace_data_object = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + st.session_state.data_objects, format_func = replace_select_format, label_visibility = "collapsed")
    replace_data_object_index = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + list(range(len(st.session_state.data_objects))), key = "ReplaceDataObject", format_func = replace_select_format, label_visibility = "collapsed")

  #* Data Object Column Selector
  with replace_col_column:
    options = ["Select a Column"] + ([] if replace_data_object_index == "Select a Data Object" else sorted(set(list(st.session_state.data_objects[replace_data_object_index].applications.keys()) + list(st.session_state.data_objects[replace_data_object_index].responses.keys()))))
    replace_col = st.selectbox(label = "Select a Column", options = options, label_visibility = "collapsed", key = "ReplaceColumn", disabled = replace_data_object_index == "Select a Data Object")

  if replace_col not in [None, "Select a Column"]:
    #* None Replacement Toggle & Removal Toggle
    for i, col in enumerate(st.columns([1, 3.76 if st.session_state.ReplaceNoneToggle else 2.5, 1, 12.24 if st.session_state.ReplaceNoneToggle else 13.5], gap = "xxsmall", border = False)):
      with col:
        if i == 0:
          st.toggle(label = "label", key = "ReplaceNoneToggle", value = False, label_visibility = "collapsed")
        elif i == 1:
          st.markdown(f"<div style='padding-top: 9.5px;'>{"Entries" if not st.session_state.ReplaceNoneToggle else "Empty Entries"}</div>", unsafe_allow_html = True)
        elif i == 2:
          st.toggle(label = "Inlcude", key = "ReplaceInclusionToggle", value = True, label_visibility = "collapsed")
        else:
          st.markdown(f"<div style='padding-top: 9.5px;'>{"Include" if st.session_state.ReplaceInclusionToggle else "Exclude"} Selected Bounds/Values</div>", unsafe_allow_html = True)

    disable_replace_button = True
    replace_function = None
    replace_function_args = None
      
    #* Variable Type Selection 
    match type(st.session_state.data_objects[replace_data_object_index].key_owner(replace_col)[0].dtypes[replace_col]):

      #* String Variable Type
      case pd.StringDtype:

        for i, col in enumerate(st.columns([1, 17], gap = "xxsmall", border = False)):
          with col:
            if i == 0:
              st.toggle(label = "label", key = "ReplaceCaseSensitiveToggle", value = True, label_visibility = "collapsed")
            else:
              st.markdown(f"<div style='padding-top: 9.5px;'>Case {"Sensitive" if st.session_state.ReplaceCaseSensitivityToggle else "Insensitive"}</div>", unsafe_allow_html = True)

        for i, col in enumerate(st.columns([1, 1], gap = "xxsmall", border = False)):
          with col:
            if i == 0:
              string_selections_target = st.multiselect(label = f"List Text to be Replaced:", disabled = st.session_state.ReplaceNoneToggle, options = None, accept_new_options = True, key = "ReplaceStringSelectionsTarget")
            elif i == 1:
              string_selections_new = st.multiselect(label = "List New Text:", options = None, accept_new_options = True, key = "ReplaceStringSelectionsNew")

#                                      trying to replace entries without target selections             trying to replace without new selections                 trying to replace entries without an equal number of target and new selections                 trying to replace empty entries without exactly 1 target selection
        disable_replace_button = (not st.session_state.ReplaceNoneToggle and string_selections_target == []) or (string_selections_new == []) or (not st.session_state.ReplaceInclusionToggle and len(string_selections_target) != 1) or (not st.session_state.ReplaceNoneToggle and len(string_selections_target) != len(string_selections_new)) or (st.session_state.ReplaceNoneToggle and len(string_selections_new) != 1)
        replace_function = d.values_replace
        replace_function_args = ((replace_data_object_index, replace_col, string_selections_target, string_selections_new),
                                 ("replace_string", st.session_state.data_objects[replace_data_object_index].key_owner_name(replace_col), replace_col),
                                 {"replace_none" : st.session_state.ReplaceNoneToggle,
                                  "string_target_values" : string_selections_target, 
                                  "string_new_values" : string_selections_new})

      #* Integer Variable Type
      case np.dtypes.Int64DType:
        replace_int_tabs = st.segmented_control(label = "replace_int_tabs", options = ["Select Bounds", "Individual Values"], default = "Select Bounds", selection_mode = "single", label_visibility = "collapsed")

        #* Lower and Upper Bounds
        if replace_int_tabs == "Select Bounds":
          col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 9.5px; color: rgb({"100, 100, 100" if st.session_state.ReplaceNoneToggle else "255, 255, 255"});'>Lower Bound</div>", unsafe_allow_html = True) #Remove|<span style = 'color: red;'><u>Replace</u></span>
            st.markdown(f"<div style='padding-top: 30px; color: rgb({"100, 100, 100" if st.session_state.ReplaceNoneToggle else "255, 255, 255"});'>Upper Bound</div>", unsafe_allow_html = True)
          with col2:
            int_lower_bound = st.number_input(label = "Lower Bound", step = 1, disabled = st.session_state.ReplaceNoneToggle, label_visibility = "collapsed", key = "ReplaceIntLowerBound", width = 200, value = None)
            int_upper_bound = st.number_input(label = "Upper Bound", step = 1, disabled = st.session_state.ReplaceNoneToggle, label_visibility = "collapsed", key = "ReplaceIntUpperBound", width = 200, value = None)
          with col3:
            st.markdown(f"<div style='padding-top: 9.5px;'>New Integer</div>", unsafe_allow_html = True)
          with col4:
            int_new_bound = st.number_input(label = "New Integer:", step = 1, label_visibility = "collapsed", key = "ReplaceIntBoundNew", width = 200, value = None)

          if int_lower_bound is not None and int_upper_bound is not None and int_lower_bound > int_upper_bound:
            st.markdown(":red[The lower bound must be less than the upper bound.]")

#                                                      trying to replace entries without either bound entered                       trying to replace entries without a new value
          disable_replace_button = (not st.session_state.ReplaceNoneToggle and int_lower_bound == None and int_upper_bound == None) or (int_new_bound is None)
          replace_function = d.bounds_replace
          replace_function_args = ((replace_data_object_index, replace_col, int_lower_bound, int_upper_bound, int_new_bound),
                                  ("replace_int_bound", st.session_state.data_objects[replace_data_object_index].key_owner_name(replace_col), replace_col), 
                                  {"replace_none" : st.session_state.ReplaceNoneToggle,
                                  "include_values" : st.session_state.ReplaceInclusionToggle,
                                  "int_lower_bound" : int_lower_bound,
                                  "int_upper_bound" : int_upper_bound,
                                  "int_new_values" : int_new_bound})

        #* List of Integers
        elif replace_int_tabs == "Individual Values":
          for i, col in enumerate(st.columns([1, 1], gap = "xxsmall", border = False)):
            with col:
              if i == 0:
                int_selections_target = st.multiselect(label = f"List Integers to be Replaced:", disabled = st.session_state.ReplaceNoneToggle, options = None, accept_new_options = True, key = "ReplaceIntSelectionsTarget")
              elif i == 1:
                int_selections_new = st.multiselect(label = "List New Integers:", options = None, accept_new_options = True, key = "ReplaceIntSelectionsNew")

          try:
#                                                 trying to replace entries without target integers       trying to replace entries without new values              trying to replace entries without an equal number of target and new selections
            disable_replace_button = (not st.session_state.ReplaceNoneToggle and int_selections_target == []) or (int_selections_new == []) or (not st.session_state.ReplaceInclusionToggle and len(int_selections_target) != 1) or (not st.session_state.ReplaceNoneToggle and len(int_selections_target) != len(int_selections_new))
            replace_function = d.values_replace
            replace_function_args = ((replace_data_object_index, replace_col, [int(num) for num in int_selections_target], [int(num) for num in int_selections_new]),
                                    ("replace_int_values", st.session_state.data_objects[replace_data_object_index].key_owner_name(replace_col), replace_col),
                                    {"replace_none" : st.session_state.ReplaceNoneToggle,
                                     "int_target_values" : [int(num) for num in int_selections_target],
                                     "int_new_values" : [int(num) for num in int_selections_new]})
          except:
            if len([i for i in int_selections_target if "." in i]) > 0 or len([i for i in int_selections_new if "." in i]):
              st.markdown(":red[Decimals should not be used, only integers are allowed.]")
            elif int_selections_target not in [None, []] or int_selections_new not in [None, []]:
              st.markdown(":red[Only integers are allowed.]")
            disable_replace_button = True

      #* DateTime Variable Type
      case np.dtypes.DateTime64DType:
        date_tabs = st.segmented_control(label = "replace_date_tabs", options = ["Select Date Bounds", "Individual Dates"], default = "Select Date Bounds", selection_mode = "single", label_visibility = "collapsed")    
          
        #* Earlier and Later Bounds
        if date_tabs == "Select Date Bounds":
          col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 9.5px; color: rgb({"100, 100, 100" if st.session_state.ReplaceNoneToggle else "255, 255, 255"});'>Earlier Date</div>", unsafe_allow_html = True)
            st.markdown(f"<div style='padding-top: 30px; color: rgb({"100, 100, 100" if st.session_state.ReplaceNoneToggle else "255, 255, 255"});'>Later Date</div>", unsafe_allow_html = True)
          with col2:
            date_earlier_bound = st.date_input(label = "Earlier Date", label_visibility = "collapsed", disabled = st.session_state.ReplaceNoneToggle, key = "ReplaceDateEarlierBound", width = 200, value = None)
            date_later_bound = st.date_input(label = "Later Date", label_visibility = "collapsed", disabled = st.session_state.ReplaceNoneToggle, key = "ReplaceDateLaterBound", width = 200, value = None)
          with col3:
            st.markdown(f"<div style='padding-top: 9.5px;'>New Date</div>", unsafe_allow_html = True)
          with col4:
            date_new_bound = st.date_input(label = "List a New Date", label_visibility = "collapsed", key = "ReplaceDateBoundNew", width = 200, value = None)

          if date_earlier_bound is not None and date_later_bound is not None and date_earlier_bound >= date_later_bound:
            st.markdown(":red[The lower bound must be less than the upper bound.]")

#                                                      trying to replace entries without either bound entered                             trying to replace entries without a new value
          disable_replace_button = (not st.session_state.ReplaceNoneToggle and date_earlier_bound == None and date_later_bound == None) or (date_new_bound is None)
          replace_function = d.bounds_replace
          replace_function_args = ((replace_data_object_index, replace_col, pd.Timestamp(date_earlier_bound), pd.Timestamp(date_later_bound) + pd.Timedelta(days = 1)),
                                  ("replace_date_bound", st.session_state.data_objects[replace_data_object_index].key_owner_name(replace_col), replace_col), 
                                  {"replace_none" : st.session_state.ReplaceNoneToggle,
                                   "include_values" : st.session_state.ReplaceInclusionToggle,
                                   "date_earlier_bound" : date_earlier_bound,
                                   "date_later_bound" : pd.Timestamp(date_earlier_bound),
                                   "date_new_values" : pd.Timestamp(date_later_bound) + pd.Timedelta(days = 1)})

      #* List of Dates
        elif date_tabs == "Individual Dates":
          for i, col in enumerate(st.columns([1, 1], gap = "xxsmall", border = False)):
            with col:
              if i == 0:
                date_selections_target = st.multiselect(label = f"List Dates to be Replaced:", disabled = st.session_state.ReplaceNoneToggle, options = None, accept_new_options = True, placeholder = "YYYY/MM/DD", key = "ReplaceDateAreaTarget")
              elif i == 1:
                date_selections_new = st.multiselect(label = "List New Dates:", options = None, accept_new_options = True, placeholder = "YYYY/MM/DD", key = "ReplaceDateAreaNew")

          try:
#                                                trying to replace entries without target dates          trying to replace entries without new values              trying to replace entries without an equal number of target and new selections              
            disable_replace_button = (not st.session_state.ReplaceNoneToggle and date_selections_target == []) or (date_selections_new == []) or (not st.session_state.ReplaceInclusionToggle and len(date_selections_target) != 1) or (not st.session_state.ReplaceNoneToggle and len(date_selections_target) != len(date_selections_new))
            replace_function = d.values_replace
            replace_function_args = ((replace_data_object_index, replace_col, [pd.Timestamp(date) for date in date_selections_target], [pd.Timestamp(date) for date in date_selections_new]),
                                    ("replace_int_values", st.session_state.data_objects[replace_data_object_index].key_owner_name(replace_col), replace_col),
                                    {"replace_none" : st.session_state.ReplaceNoneToggle,
                                     "int_target_values" : [pd.Timestamp(date) for date in date_selections_target],
                                     "int_new_values" : [pd.Timestamp(date) for date in date_selections_new]})
          except:
            st.markdown(":red[Only dates ('YYYY/MM/DD') are allowed.]")
            disable_replace_button = True

    def replace_on_click(*args):
      """
        Updates the DataObject's action history (which includes cleaning).
      
        Args:
          arg1 (tuple): Used for the action     | replace_data_object_index, replace_col, any additonal arguments necessray for the action
          arg2 (tuple): Used for action history | action_code, dataset, column, include_values, include_none
          arg3  (dict): Used for action history | Any keyword arguments specific to the method of filtration
      """
      replace_function(*args[0])
      st.session_state.data_objects[replace_data_object_index].add_action_history(*args[1], **args[2])

    st.button(label = f"Replace Value(s)", disabled = disable_replace_button, on_click = replace_on_click, args = replace_function_args)

with st.expander(label = "Merging"):
  st.text("stuff")

# with st.expander(label = "Manual Filtering"):
#   manual_dataset = st.selectbox(label = "Select a Data Object", options = ["No Selection", "option2"])
#   filter_code_input = st.text_area(label = "Enter Manual Filtration Code", placeholder = "{\"filter_code\" : ...", disabled = manual_dataset == "No Selection")