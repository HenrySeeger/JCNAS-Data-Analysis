import re
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import DataObject as d
import matplotlib.pyplot as plt

st.session_state.setdefault("data_objects", [])
st.session_state.setdefault("filter_state", None)
st.session_state.setdefault("ReplaceNoneToggle", False)

st.header("Filtering, Replacing, & Merging")

#* Action DataObject Selection
col1, col2, col3 = st.columns([3, 7, 2])
with col1:
  st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Select a Data Object:</div>", unsafe_allow_html = True)
with col2:
  def clean_select_format(num):
    return num if type(num) == str else st.session_state.data_objects[num].name
  action_data_object_index = st.selectbox(label = "Select a Data Object", options = ["Select a Data Object"] + list(range(len(st.session_state.data_objects))), key = "ActionDataObject", format_func = clean_select_format, label_visibility = "collapsed")

#* Cleaning Section
with st.expander(label = "Cleaning"):
  #* Data Object Column Selector
  col1, col2, col3 = st.columns([2.62, 6.74, 1.64])
  with col1:
    st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Select a Column:</div>", unsafe_allow_html = True)
  with col2:
    options = ["Select a Column"] + ([] if action_data_object_index == "Select a Data Object" else sorted(set(list(st.session_state.data_objects[action_data_object_index].applications.keys()) + list(st.session_state.data_objects[action_data_object_index].responses.keys()))))
    cleaning_col = st.selectbox(label = "Select a Column", options = options, label_visibility = "collapsed", key = "CleaningColumn", disabled = action_data_object_index == "Select a Data Object")
  
  if cleaning_col != "Select a Column":
    tab_duplicates, tab_filter, tab_remove_col = st.tabs(["Remove Duplicates", "Filter Entries", "Remove a Column"])

    #* Remove Duplicates
    with tab_duplicates:

      def remove_duplicates():
        d.action_code_interpreter(action_data_object_index, {"action_code" : "drop_duplicates","column" : cleaning_col})
        st.session_state.CleaningColumn = "Select a Column"
        st.toast(body = f"Successfully removed duplicate values")
      st.button(label = "Remove Duplicates", on_click = remove_duplicates)

    #* Filter Values
    with tab_filter:
      #* Inclusion/Exclusion & None Inclusion toggles
      if cleaning_col not in [None, "Select a Column"]:
        for i, col in enumerate(st.columns([1, 6.5, 1, 9.5], gap = "xxsmall", border = False)):
          with col:
            if i == 0:
              st.toggle(label = "Inlcude", key = "FilterInclusionToggle", value = False, label_visibility = "collapsed")
            elif i == 1:
              st.markdown(f"<div style='padding-top: 9.5px;'>{"Keep" if st.session_state.FilterInclusionToggle else "Remove"} Selected Bounds/Values</div>", unsafe_allow_html = True)
            elif i == 2:
              st.toggle(label = "Inlcude", key = "FilterNoneToggle", value = False, label_visibility = "collapsed")
            else:
              st.markdown(f"<div style='padding-top: 9.5px;'>{"Remove" if st.session_state.FilterNoneToggle else "Keep"} Empty Values</div>", unsafe_allow_html = True)

        #* Filter Button Logic Controls
        disable_filter_button = True
        filter_function = None
        filter_function_kwargs = None

        #* Variable Type Selection filt
        match type(st.session_state.data_objects[action_data_object_index].key_owner(cleaning_col)[0].dtypes[cleaning_col]):
          #* String Variable Type
          case pd.StringDtype | np.dtypes.ObjectDType:
            is_str = type(st.session_state.data_objects[action_data_object_index].key_owner(cleaning_col)[0].dtypes[cleaning_col]) == pd.StringDtype
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
                  st.toggle(label = "OrGating", key = "FilterOrGateToggle", value = True, label_visibility = "collapsed")
                else:
                  st.markdown(f"<div style='padding-top: 9.5px;'>{"Or" if st.session_state.FilterOrGateToggle else "And"}-Gate</div>", unsafe_allow_html = True)

            standard_filters_table = {"description" : []}

            string_selections = st.multiselect(label = "List Text:", options = standard_filters_table[cleaning_col] if cleaning_col in standard_filters_table.keys() else None, accept_new_options = True, key = "FilterStringSelections")

            filter_function_kwargs = {"action_code" : "filter_string" if is_str else "filter_list_string",
                                      "column" : cleaning_col,
                                      "include_values" : st.session_state.FilterInclusionToggle,
                                      "remove_none" : st.session_state.FilterNoneToggle,
                                      "string_values" : string_selections,
                                      "exact_string" : st.session_state.FilterExactStringToggle,
                                      "case_sensitive" : st.session_state.FilterCaseSensitiveToggle,
                                      "or_gate" : st.session_state.FilterOrGateToggle}
            def filter():
              d.action_code_interpreter(action_data_object_index, filter_function_kwargs)
              st.session_state.FilterStringSelections = []
              st.toast(body = f"'{st.session_state.data_objects[action_data_object_index].name}' successfully filtered")
            st.button(label = "Filter", on_click = filter)

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

                                              # trying to filter without selected values (None-values included)                                            trying to filter with a lower_bound greater than the upper bound
              disable_filter_button = (int_lower_bound is None and int_upper_bound is None and not st.session_state.FilterNoneToggle) or (int_lower_bound is not None and int_upper_bound is not None and int_lower_bound > int_upper_bound)
              filter_function_kwargs = {"action_code" : "filter_int_bound",
                                        "column" : cleaning_col,
                                        "include_values" : st.session_state.FilterInclusionToggle,
                                        "remove_none" : st.session_state.FilterNoneToggle,
                                        "int_lower_bound" : int_lower_bound,
                                        "int_upper_bound" : int_upper_bound}

              def filter():
                d.action_code_interpreter(action_data_object_index, filter_function_kwargs)
                st.session_state.FilterIntLowerBound = None
                st.session_state.FilterIntUpperBound = None
                st.toast(body = f"'{st.session_state.data_objects[action_data_object_index].name}' successfully filtered")
              st.button(label = "Filter", disabled = disable_filter_button, on_click = filter)

            #* List of Integers
            elif int_tabs == "Individual Values":
              int_selections = st.multiselect(label = "List Integers:", options = None, accept_new_options = True, key = "FilterIntSelections")

              try:
                                     # trying to filter without selected values (None-values included)                
                disable_filter_button = int_selections == [] and not st.session_state.FilterNoneToggle
                filter_function_kwargs = {"action_code" : "filter_int_values",
                                          "dataset" : st.session_state.data_objects[action_data_object_index].key_owner_name(cleaning_col),
                                          "column" : cleaning_col,
                                          "include_values" : st.session_state.FilterInclusionToggle,
                                          "remove_none" : st.session_state.FilterNoneToggle,
                                          "int_values" : [int(num) for num in int_selections]}
              except:
                if len([i for i in int_selections if "." in i]):
                  st.markdown(":red[Decimals should not be used, only integers are allowed.]")
                elif int_selections not in [None, []]:
                  st.markdown(":red[Only integers are allowed.]")
                disable_filter_button = True

              def filter():
                d.action_code_interpreter(action_data_object_index, filter_function_kwargs)
                st.session_state.FilterIntSelections = []
                st.toast(body = f"'{st.session_state.data_objects[action_data_object_index].name}' successfully filtered")
              st.button(label = "Filter", disabled = disable_filter_button, on_click = filter)
            
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

                      #                             trying to filter without selected values (None-values included)                                           trying to filter with an earlier date later than the later date
              disable_filter_button = (date_earlier_bound is None and date_later_bound is None and not st.session_state.FilterNoneToggle) or (date_earlier_bound is not None and date_later_bound is not None and date_earlier_bound > date_later_bound)
              filter_function_kwargs = {"action_code" : "filter_date_bound",
                                        "column" : cleaning_col,
                                        "include_values" : st.session_state.FilterInclusionToggle,
                                        "remove_none" : st.session_state.FilterNoneToggle,
                                        "date_earlier_bound" : date_earlier_bound,
                                        "date_later_bound" : date_later_bound}

              def filter():
                d.action_code_interpreter(action_data_object_index, filter_function_kwargs)
                st.session_state.FilterDateEarlierBound = None
                st.session_state.FilterDateLaterBound = None
                st.toast(body = f"'{st.session_state.data_objects[action_data_object_index].name}' successfully filtered")
              st.button(label = "Filter", disabled = disable_filter_button, on_click = filter)

          #* List of Dates
            elif date_tabs == "Individual Dates":
              date_selections = st.multiselect(label = "List Dates:", options = None, accept_new_options = True, placeholder = "YYYY/MM/DD", key = "FilterDateSelections")

              try:
                for date in date_selections:
                  if not (re.match(r"\d{2}(?:\d{2})?[/-]\d{1,2}[/-]\d{1,2}", date)):
                    raise()
                disable_filter_button = date_selections == [] and not st.session_state.FilterNoneToggle
                filter_function_kwargs = {"action_code" : "filter_date_values",
                                          "column" : cleaning_col,
                                          "include_values" : st.session_state.FilterInclusionToggle,
                                          "remove_none" : st.session_state.FilterNoneToggle,
                                          "date_values" : [pd.Timestamp(date) for date in date_selections]}
              except:
                st.markdown(":red[Only dates ('YYYY/MM/DD') are allowed.]")
                disable_filter_button = True

              def filter():
                d.action_code_interpreter(action_data_object_index, filter_function_kwargs)
                st.session_state.FilterDateSelections = []
                st.toast(body = f"'{st.session_state.data_objects[action_data_object_index].name}' successfully filtered")
              st.button(label = "Filter", disabled = disable_filter_button, on_click = filter)

    #* Delete a Column
    with tab_remove_col:
      data_delete_confirmation = st.toggle(label = f"Confirm removal of {cleaning_col}", value = False)

      def remove_column():
        d.action_code_interpreter(action_data_object_index, {"action_code" : "deletion","column" : cleaning_col})
        st.session_state.CleaningColumn = "Select a Column"
        st.toast(body = f"Successfully removed '{cleaning_col}' from '{st.session_state.data_objects[action_data_object_index].name}'")
      st.button(label = f"Remove '{cleaning_col}' from '{st.session_state.data_objects[action_data_object_index].name}'", disabled = not data_delete_confirmation, on_click = remove_column)

#* Replacement Section
with st.expander(label = "Replacing"):
  #* Data Object Column Selector
  col1, col2, col3 = st.columns([2.62, 6.74, 1.64])
  with col1:
    st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Select a Column:</div>", unsafe_allow_html = True)
  with col2:
    options = ["Select a Column"] + ([] if action_data_object_index == "Select a Data Object" else sorted(set(list(st.session_state.data_objects[action_data_object_index].applications.keys()) + list(st.session_state.data_objects[action_data_object_index].responses.keys()))))
    replace_col = st.selectbox(label = "Select a Column", options = options, label_visibility = "collapsed", key = "ReplaceColumn", disabled = action_data_object_index == "Select a Data Object")

  if replace_col not in [None, "Select a Column"]:
    #* None Replacement Toggle & Removal Toggle
    col1, col2, col3, col4 = st.columns([1, 3.76 if st.session_state.ReplaceNoneToggle else 2.5, 1, 12.24 if st.session_state.ReplaceNoneToggle else 13.5], gap = "xxsmall", border = False)
    with col1:
        st.toggle(label = "label", key = "ReplaceNoneToggle", value = False, label_visibility = "collapsed")
    with col2:
        st.markdown(f"<div style='padding-top: 9.5px;'>{"Entries" if not st.session_state.ReplaceNoneToggle else "Empty Entries"}</div>", unsafe_allow_html = True)
    with col3:
        st.toggle(label = "Inlcude", key = "ReplaceInclusionToggle", value = True, label_visibility = "collapsed")
    with col4:
        st.markdown(f"<div style='padding-top: 9.5px;'>Replace {"" if st.session_state.ReplaceInclusionToggle else "Non-"}Selected Bounds/Values</div>", unsafe_allow_html = True)
      
    #* Variable Type Selection 
    match type(st.session_state.data_objects[action_data_object_index].key_owner(replace_col)[0].dtypes[replace_col]):
      #* String Variable Type
      case pd.StringDtype:
        col1, col2 = st.columns([1, 17], gap = "xxsmall")
        with col1:
          st.toggle(label = "label", key = "ReplaceCaseSensitiveToggle", value = True, label_visibility = "collapsed")
        with col2:
          st.markdown(f"<div style='padding-top: 9.5px;'>Case {"Sensitive" if st.session_state.ReplaceCaseSensitiveToggle else "Insensitive"}</div>", unsafe_allow_html = True)

        col1, col2 = st.columns([1, 1], gap = "xxsmall", border = False)
        with col1:
          string_selections_target = st.multiselect(label = "List Text to be Replaced:", disabled = st.session_state.ReplaceNoneToggle, options = None, accept_new_options = True, key = "ReplaceStringSelectionsTarget")
        with col2:
          string_selections_new = st.multiselect(label = "List New Text:", options = None, accept_new_options = True, key = "ReplaceStringSelectionsNew")

                             #         trying to replace entries without target selections             trying to replace without new selections                 trying to replace entries without an equal number of target and new selections                 trying to replace empty entries without exactly 1 target selection
        disable_replace_button = (not st.session_state.ReplaceNoneToggle and string_selections_target == []) or (string_selections_new == []) or (not st.session_state.ReplaceInclusionToggle and len(string_selections_target) != 1) or (not st.session_state.ReplaceNoneToggle and len(string_selections_target) != len(string_selections_new)) or (st.session_state.ReplaceNoneToggle and len(string_selections_new) != 1)
        replace_function_kwargs = {"action_code" : "replace_string",
                                   "column" : replace_col,
                                   "replace_selected" : st.session_state.ReplaceInclusionToggle,
                                   "replace_none" : st.session_state.ReplaceNoneToggle,
                                   "case_sensitive" : st.session_state.ReplaceCaseSensitiveToggle,
                                   "target_values" : string_selections_target, 
                                   "new_values" : string_selections_new}
        
        def replace():
          d.action_code_interpreter(action_data_object_index, replace_function_kwargs)
          st.session_state.ReplaceStringSelectionsTarget = []
          st.session_state.ReplaceStringSelectionsNew = []
          st.toast(body = f"Successfully replaced entries in '{st.session_state.data_objects[action_data_object_index].name}'")
        st.button(label = "Filter", disabled = disable_replace_button, on_click = replace)

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

                    #                                  trying to replace entries without either bound entered                     trying to replace entries without a new value
          disable_replace_button = (not st.session_state.ReplaceNoneToggle and int_lower_bound == None and int_upper_bound == None) or (int_new_bound is None)
          replace_function_kwargs = {"action_code" : "replace_int_bound",
                                     "column" : replace_col,
                                     "replace_selected" : st.session_state.ReplaceInclusionToggle,
                                     "replace_none" : st.session_state.ReplaceNoneToggle,
                                     "lower_bound" : int_lower_bound,
                                     "upper_bound" : int_upper_bound,
                                     "new_values" : int_new_bound}

          def replace():
            d.action_code_interpreter(action_data_object_index, replace_function_kwargs)
            st.session_state.ReplaceIntLowerBound = None
            st.session_state.ReplaceIntUpperBound = None
            st.session_state.ReplaceIntBoundNew = None
            st.toast(body = f"Successfully replaced entries in '{st.session_state.data_objects[action_data_object_index].name}'")
          st.button(label = "Filter", disabled = disable_replace_button, on_click = replace)

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
            replace_function_kwargs = {"action_code" : "replace_int_values",
                                       "column" : replace_col,
                                       "replace_selected" : st.session_state.ReplaceInclusionToggle,
                                       "replace_none" : st.session_state.ReplaceNoneToggle,
                                       "target_values" : [int(num) for num in int_selections_target],
                                       "new_values" : [int(num) for num in int_selections_new]}
          except:
            if len([i for i in int_selections_target if "." in i]) > 0 or len([i for i in int_selections_new if "." in i]):
              st.markdown(":red[Decimals should not be used, only integers are allowed.]")
            elif int_selections_target not in [None, []] or int_selections_new not in [None, []]:
              st.markdown(":red[Only integers are allowed.]")
            disable_replace_button = True

          def replace():
            d.action_code_interpreter(action_data_object_index, replace_function_kwargs)
            st.session_state.ReplaceIntSelectionsTarget = []
            st.session_state.ReplaceIntSelectionsNew = []
            st.toast(body = f"Successfully replaced entries in '{st.session_state.data_objects[action_data_object_index].name}'")
          st.button(label = "Filter", disabled = disable_replace_button, on_click = replace)

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
          replace_function_kwargs = {"action_code" : "replace_date_bound", 
                                     "dataset" : st.session_state.data_objects[action_data_object_index].key_owner_name(replace_col),
                                     "column" : replace_col,
                                     "include_values" : st.session_state.ReplaceInclusionToggle,
                                     "replace_none" : st.session_state.ReplaceNoneToggle,
                                     "earlier_bound" : pd.Timestamp(date_earlier_bound),
                                     "later_bound" : pd.Timestamp(date_earlier_bound),
                                     "new_bound" : pd.Timestamp(date_new_bound)}

          def replace():
            d.action_code_interpreter(action_data_object_index, replace_function_kwargs)
            st.session_state.ReplaceDateEarlierBound = None
            st.session_state.ReplaceDateLaterBound = None
            st.session_state.ReplaceDateBoundNew = None
            st.toast(body = f"Successfully replaced entries in '{st.session_state.data_objects[action_data_object_index].name}' ")
          st.button(label = "Filter", disabled = disable_replace_button, on_click = replace)

      #* List of Dates
        elif date_tabs == "Individual Dates":
          for i, col in enumerate(st.columns([1, 1], gap = "xxsmall", border = False)):
            with col:
              if i == 0:
                date_selections_target = st.multiselect(label = f"List Dates to be Replaced:", disabled = st.session_state.ReplaceNoneToggle, options = None, accept_new_options = True, placeholder = "YYYY/MM/DD", key = "ReplaceDateAreaTarget")
              elif i == 1:
                date_selections_new = st.multiselect(label = "List New Dates:", options = None, accept_new_options = True, placeholder = "YYYY/MM/DD", key = "ReplaceDateAreaNew")

          try:
            for target, new in zip(date_selections_target, date_selections_new):
              if not (re.match(r"\d{2}(?:\d{2})?[/-]\d{1,2}[/-]\d{1,2}", target) or re.match(r"\d{2}(?:\d{2})?[/-]\d{1,2}[/-]\d{1,2}", new)):
                raise()
#                                                trying to replace entries without target dates          trying to replace entries without new values              trying to replace entries without an equal number of target and new selections              
            disable_replace_button = (not st.session_state.ReplaceNoneToggle and date_selections_target == []) or (date_selections_new == []) or (not st.session_state.ReplaceInclusionToggle and len(date_selections_target) != 1) or (not st.session_state.ReplaceNoneToggle and len(date_selections_target) != len(date_selections_new))
            replace_function_kwargs = {"action_code" : "replace_int_values",
                                       "column" : replace_col,
                                       "include_values" : st.session_state.ReplaceInclusionToggle,
                                       "replace_none" : st.session_state.ReplaceNoneToggle,
                                       "int_target_values" : [pd.Timestamp(date) for date in date_selections_target],
                                       "int_new_values" : [pd.Timestamp(date) for date in date_selections_new]}
          except:
            st.markdown(":red[Only dates ('YYYY/MM/DD') are allowed.]")
            disable_replace_button = True

          def replace():
            d.action_code_interpreter(action_data_object_index, replace_function_kwargs)
            st.session_state.ReplaceDateAreaTarget = []
            st.session_state.ReplaceDateAreaNew = []
            st.toast(body = f"Successfully replaced entries in '{st.session_state.data_objects[action_data_object_index].name}'")
          st.button(label = "Filter", disabled = disable_replace_button, on_click = replace)

with st.expander(label = "Merging"):
  st.text("Coming in v2.0")

with st.expander(label = "View Datasets"):
  def data_viewer_formatting(data):
    return data if type(data) == str else data["name"]
  
  if st.session_state.master_data is not None:
    data_viewer_selection = st.selectbox(label = "Select a dataset to view",
                                         options = ["No Selection"] + [data for obj in st.session_state.data_objects + [st.session_state.master_data] for data in [{"name" : f"{obj.name}: applications", "data" : obj.applications}, {"name" : f"{obj.name}: responses", "data" : obj.responses}]],
                                         format_func = data_viewer_formatting, key = "DataViewerSelecter",
                                         disabled = st.session_state.applications_entry is None and st.session_state.responses_entry is None)
    if data_viewer_selection != "No Selection":
      st.dataframe(data_viewer_selection["data"])
  else:
    st.text("Both an applications dataset and a responses dataset are required to be uploaded before any dataset can be viewed")

if action_data_object_index != "Select a Data Object" and len(st.session_state.data_objects[action_data_object_index].action_history):
  with st.expander(label = "View Dataset History", expanded = True):
    if st.button(label = "Undo", disabled = not (action_data_object_index != "Select a Data Object" and len(st.session_state.data_objects[action_data_object_index].action_history))):
      d.undo(action_data_object_index)
    st.text(" - " + str(st.session_state.data_objects[action_data_object_index].action_history)[1:-1].replace("}, ", "\n - ").replace("{", "").replace("}", "").replace("'", ""))