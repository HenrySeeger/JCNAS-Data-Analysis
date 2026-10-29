import re
import math
import textwrap
import numpy as np
import pandas as pd
import DataObject as d
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.ticker as mticker

st.session_state.setdefault("data_objects", [])
st.session_state.setdefault("x_groups_dict", {})
st.session_state.setdefault("y_groups_dict", {})

line_markers_reference_table = {"." : "Point",
                           "," : "Pixel",
                           "o" : "Circle",
                           "v" : "Triangle Down",
                           "^" : "Triangle Up",
                           "<" : "Triangle Left",
                           ">" : "Triangle Right",
                           "1" : "Tri Down",
                           "2" : "Tri Up",
                           "3" : "Tri Left",
                           "4" : "Tri Right",
                           "8" : "Octagon",
                           "s" : "Square",
                           "p" : "Pentagon",
                           "P" : "Plus (Filled)",
                           "*" : "Star",
                           "h" : "Hexagon1",
                           "H" : "Hexagon2",
                           "+" : "Plus",
                           "x" : "X",
                           "X" : "X (Filled)",
                           "D" : "Diamond",
                           "d" : "Thin Diamond",
                           "|" : "Vline",
                           "_" : "Hline",
                           0 : "Tick Left",
                           1 : "Tick right",
                           2 : "Tick Up",
                           3 : "Tick Down",
                           4 : "Caret Left",
                           5 : "Caret Right",
                           6 : "Caret Up",
                           7 : "Caret Down",
                           8 : "Caret Left (Centered at Base)",
                           9 : "Caret Right (Centered at Base)",
                           10 : "Caret Up (Centered at Base)",
                           11 : "Caret Down (Centered at Base)"}

linestyle_reference_table = {"-" : "Solid",
                             ":" : "Dotted",
                             (0, (1, 1)) : "Dense Dots",
                             "--" : "Dashes",
                             (0, (10, 3)) : "Long Dashes",
                             "-." : "Dashes and Dots"}

def interpret_colors(colors, desired_num_colors, entry_type):
  if len(colors) == 0:
    return ([plt.get_cmap("tab10")(i / 10) for i in range(10)] * (1 + desired_num_colors // 10))[:desired_num_colors]

  if entry_type == "Color Map Entry":
    return [plt.get_cmap(colors)(i / desired_num_colors) for i in range(desired_num_colors)]
  else:
    if entry_type == "Single Entry":
      colors = [colors]

    colors = [color # Written colors (e.g. "red", "green", "gold", "thistle", etc)
              if re.match(r"[a-zA-z]+", color) else

              # Hex codes (e.g. "#1bE012"), assumes exactly 6 chars after the '#'
              [int(color[1:][i:i + 2], 16) / 255 for i in range(0, 6, 2)]
              if re.match(r"#\w{6}", color) else

              # RGBA values (e.g. "(200, 150, 80)", "120, 0, 255, 100", etc), RGB values are 0-255, A value is optional and 0-100, '()' are optional
              [1.0 if rgba_val == None else min(int(rgba_val) / (100 if i == 3 else 255), 1.0) for i, rgba_val in enumerate(re.search(r"\(?(?P<r>\d{1,3})\s*,\s*(?P<g>\d{1,3})\s*,\s*(?P<b>\d{1,3})\s*,?\s*(?P<a>\d{1,3})?\)?", color).groups())]

              for color in colors]

    if len(colors) < desired_num_colors:
      colors = (colors * math.ceil(desired_num_colors / len(colors)))

    return colors[:desired_num_colors]

def interpret_ticks(tick_input, entry_type):
  if len(tick_input) == 0:
    return []
  tick_input = [float(tick) for tick in tick_input.replace(" ", "").split(",") if tick != ""]
  num_decimals = max([len(str(val)[str(val).index(".") + 1:]) for val in tick_input])
  match entry_type:
    case "Manual":
      return tick_input
    case "Range":
      return [val / 10**num_decimals for val in range(*[int(val * 10**num_decimals) for val in tick_input[:3]])]
    case "Log Range":
      return [10**tick for tick in [val / 10**num_decimals for val in range(*[int(val * 10**num_decimals) for val in tick_input[:3]])]]

def default_color_selectors(label_name, disabled = False):
  label_color = "color: #959595;" if disabled else ""
  st.markdown(f"<div style='padding-left: 15px; {label_color}'>{label_name}:</div>", unsafe_allow_html = True)
  col1, col2, col3, col4 = st.columns([2.5, 3.25, 1.5, 4.25], gap = None)
  with col1:
    st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px; {label_color}'>Color Entry Type:</div>", unsafe_allow_html = True)
  with col2:
    new_colors_entry_type = st.selectbox(label = f"{label_name}_new_colors_entry_type", disabled = disabled, label_visibility = "collapsed", options = ["Multiple Entry", "Single Entry", "Color Map Entry"])
  with col3:
    st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px; {label_color}'>Colors:</div>", unsafe_allow_html = True)
  with col4:
    if new_colors_entry_type == "Single Entry":
      new_colors = st.color_picker(label = f"{label_name}_New Colors", disabled = disabled, label_visibility = "collapsed", value = None)
    if new_colors_entry_type == "Multiple Entry":
      new_colors = st.multiselect(label = f"{label_name}_New Colors", disabled = disabled, label_visibility = "collapsed", options = [], accept_new_options = True)
    if new_colors_entry_type == "Color Map Entry":
      new_colors = st.text_input(label = f"{label_name}_New Colors", disabled = disabled, label_visibility = "collapsed", value = "")
  return (new_colors_entry_type, new_colors)

st.header("Graphing")

#* Select a Graph Type Header
col1, col2 = st.columns([3, 11])
with col1:
  st.markdown("<div style='padding-top: 5.5px;'>Select a Graph Type:</div>", unsafe_allow_html = True)
with col2:
  st.selectbox(label = "Select graph type", options = ["Select a Graph Type", "Bar Plot", "Pie Chart", "Line Chart"], label_visibility = "collapsed", key = "GraphTypeSelect", disabled = len(st.session_state.data_objects) == 0)

"" # Adds a vertical space on the page

def select_object_format(num):
  return num if type(num) == str else st.session_state.data_objects[num].name

st.markdown(f"<h3 style='{"color: #808080" if st.session_state.GraphTypeSelect == "Select a Graph Type" else ""};'>Graph Parameters</h3>", unsafe_allow_html = True)

#* Data Object Selector
col1, col2 = st.columns([2, 10], gap = None)
with col1:
  st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px; {"color: #808080;" if st.session_state.GraphTypeSelect == "Select a Graph Type" else ""}'>Data Objects:</div>", unsafe_allow_html = True)
with col2:
  data_object_indices = st.multiselect(label = "Select a Data Object", disabled = st.session_state.GraphTypeSelect == "Select a Graph Type", options = list(range(len(st.session_state.data_objects))), label_visibility = "collapsed", default = None, format_func = select_object_format)

if st.session_state.GraphTypeSelect != "Select a Graph Type":
  #* Independent Variable
  with st.expander(label = "Independent Variable (X-Axis)"):
    #* Column Selection
    col1, col2 = st.columns([3, 9], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Independent Variable:</div>", unsafe_allow_html = True)
    with col2:
      def intersection(sets):
        if len(sets) == 0:
          return {}
        rtn = set(sets[0])
        for s in sets[1:]:
          rtn = rtn & s
        return rtn
      x_col_name = st.selectbox(label = "Select a Column", disabled = len(data_object_indices) == 0, options = ["No Variable Selected"] + sorted(intersection([set(st.session_state.data_objects[index].applications.keys()) | set(st.session_state.data_objects[index].responses.keys()) for index in data_object_indices])), key = "x_col_name_select", label_visibility = "collapsed")
      x_col = st.session_state.data_objects[data_object_indices[0]].key_owner(x_col_name)[0][x_col_name] if x_col_name != "No Variable Selected" else ""

    #* Variable Grouping
    if x_col_name != "No Variable Selected":
      match type(x_col.dtype):
        case np.dtypes.DateTime64DType:
          col1, col2 = st.columns([1.5, 10.5], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Groups:</div>", unsafe_allow_html = True)
          with col2:
            st.selectbox(label = "x_groups", disabled = x_col_name == "No Variable Selected", options = ["No Grouping Selected", "Yearly", "Quarterly", "Monthly"], key = "x_groups", accept_new_options = False, label_visibility = "collapsed")

          col1, col2 = st.columns([2, 10], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
          with col2:
            current_x_options = []
            start_date = min(x_col)
            end_date = max(x_col)
            def current_x_group_items_format(year):
              return str(year)
            match st.session_state.x_groups:
              case "Yearly":
                current_x_options = range(start_date.year, end_date.year + 1, 1)
              
              case "Quarterly":
                def quarter_num(month):
                  return (month - 1) // 3 + 1
                current_x_options = [(pd.Timestamp(f"{start_date.year + i // 4}/{(i % 4) * 3 + 1}/1"), pd.Timestamp(f"{start_date.year + i // 4}/{(i % 4 + 1) * 3}/{pd.Timestamp(f"2000/{(i % 4 + 1) * 3}/1").days_in_month}") + pd.Timedelta(value = 8.64 * 10**13 - 1, unit = "nanoseconds")) for i in range(quarter_num(start_date.month) - 1, (end_date.year - start_date.year) * 4 + quarter_num(end_date.month))]
                def current_x_group_items_format(dates):
                  quarter_months_lookup_table = {1 : "Jan-Mar", 2: "Apr-Jun", 3 : "Jul-Sep", 4 : "Oct-Dec"}
                  return f"{dates[0].year} {quarter_months_lookup_table[dates[1].month / 3]}"
              
              case "Monthly":                                                                                                                                                                                                                                # 1 day - 1 nanosecond
                current_x_options = [(pd.Timestamp(f"{start_date.year + i // 12}/{i % 12 + 1}/1"), pd.Timestamp(f"{start_date.year + i // 12}/{i % 12 + 1}/{pd.Timestamp(f"{start_date.year + i // 12}/{i % 12 + 1}/1").days_in_month}") + pd.Timedelta(value = 8.64 * 10**13 - 1, unit = "nanoseconds")) for i in range(start_date.month - 1, (end_date.year - start_date.year) * 12 + end_date.month)]
                def current_x_group_items_format(dates):
                  return f"{dates[0].year}-{str(dates[0].month).zfill(2)}"
            st.multiselect(label = "current_x_group_items", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0, key = "current_x_group_items", options = current_x_options, label_visibility = "collapsed", format_func = current_x_group_items_format)

        case pd.StringDtype:
          #* Create Groups
          col1, col2 = st.columns([1.5, 10.5], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Groups:</div>", unsafe_allow_html = True)
          with col2:
            def x_groups_change():
              st.session_state.x_groups_dict = {key : st.session_state.x_groups_dict[key] if key in st.session_state.x_groups_dict.keys() else set() for key in st.session_state.x_groups}
              if st.session_state.current_x_group not in st.session_state.x_groups_dict:
                st.session_state.current_x_group = None
            st.multiselect(label = "x_groups", disabled = x_col_name == "No Variable Selected", options = None, key = "x_groups", accept_new_options = True, label_visibility = "collapsed", on_change = x_groups_change)

          #* Choose a Group
          col1, col2 = st.columns([2.25, 9.75], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Current Group:</div>", unsafe_allow_html = True)
          with col2:
            def current_x_group_change():
              if st.session_state.current_x_group == None:
                st.session_state.current_x_group_items = []
              else:
                st.session_state.current_x_group_items = st.session_state.x_groups_dict[st.session_state.current_x_group]
            st.selectbox(label = "current_x_group", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0, key = "current_x_group", options = st.session_state.x_groups, index = None, label_visibility = "collapsed", on_change = current_x_group_change)

          #* Add Items to the Group
          col1, col2 = st.columns([2, 10], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
          with col2:
            def current_x_group_items_change():
              if st.session_state.current_x_group in st.session_state.x_groups_dict.keys():
                st.session_state.x_groups_dict[st.session_state.current_x_group] = set(st.session_state.current_x_group_items)
              else:
                st.session_state.current_x_group_items = []
            unique_x_col = list(x_col.unique())
            if np.nan in unique_x_col:
              unique_x_col.remove(np.nan)
            unique_x_col = sorted([val for val in unique_x_col if val not in [vals for group_name in st.session_state.x_groups_dict.keys() if group_name != st.session_state.current_x_group for vals in st.session_state.x_groups_dict[group_name]]])
            st.multiselect(label = "current_x_group_items", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0 or st.session_state.current_x_group == None, key = "current_x_group_items", options = unique_x_col if len(unique_x_col) <= 30 else [], accept_new_options = x_col_name != "No Variable Selected" and len(unique_x_col) > 25, label_visibility = "collapsed", on_change = current_x_group_items_change)
        
        case np.dtypes.ObjectDType:
          col1, col2 = st.columns([1.5, 10.5], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Groups:</div>", unsafe_allow_html = True)
          with col2:
            def x_groups_change():
              st.session_state.x_groups_dict = {key : st.session_state.x_groups_dict[key] if key in st.session_state.x_groups_dict.keys() else set() for key in st.session_state.x_groups}
            st.multiselect(label = "x_groups", disabled = x_col_name == "No Variable Selected", options = None, key = "x_groups", accept_new_options = True, label_visibility = "collapsed", on_change = x_groups_change)

          col1, col2 = st.columns([2.25, 9.75], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Current Group:</div>", unsafe_allow_html = True)
          with col2:
            def current_x_group_change():
              if st.session_state.current_x_group_items == None:
                st.session_state.current_x_group_items = []
              else:
                st.session_state.current_x_group_items = st.session_state.x_groups_dict[st.session_state.current_x_group]
            st.selectbox(label = "current_x_group", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0, key = "current_x_group", index = None, options = st.session_state.x_groups, label_visibility = "collapsed", on_change = current_x_group_change)

          col1, col2 = st.columns([2, 10], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
          with col2:
            def current_x_group_items_change():
              st.session_state.x_groups_dict[st.session_state.current_x_group] = set(st.session_state.current_x_group_items)
            st.multiselect(label = "current_x_group_items", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0 or st.session_state.current_x_group == None, key = "current_x_group_items", options = sorted([val for val in set(val for val_list in x_col for val in val_list) if val not in [vals for group_name in st.session_state.x_groups_dict.keys() if group_name != st.session_state.current_x_group for vals in st.session_state.x_groups_dict[group_name]]]) if x_col_name != "No Variable Selected" else [], label_visibility = "collapsed", on_change = current_x_group_items_change)
        
        case np.dtypes.Int64DType:
          #* Create Groups
          col1, col2 = st.columns([1.5, 10.5], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Groups:</div>", unsafe_allow_html = True)
          with col2:
            def x_groups_change():
              st.session_state.x_groups_dict = {key : st.session_state.x_groups_dict[key] if key in st.session_state.x_groups_dict.keys() else set() for key in st.session_state.x_groups}
              if st.session_state.current_x_group not in st.session_state.x_groups_dict:
                st.session_state.current_x_group = None
            st.multiselect(label = "x_groups", disabled = x_col_name == "No Variable Selected", options = None, key = "x_groups", accept_new_options = True, label_visibility = "collapsed", on_change = x_groups_change)

          #* Choose a Group
          col1, col2 = st.columns([2.25, 9.75], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Current Group:</div>", unsafe_allow_html = True)
          with col2:
            def current_x_group_change():
              if st.session_state.current_x_group_items == None:
                st.session_state.current_x_group_items = []
              else:
                st.session_state.current_x_group_items = st.session_state.x_groups_dict[st.session_state.current_x_group]
            st.selectbox(label = "current_x_group", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0, key = "current_x_group", options = st.session_state.x_groups, index = None, label_visibility = "collapsed", on_change = current_x_group_change)

          #* Add Items to the Group
          col1, col2 = st.columns([2, 10], gap = None)
          with col1:
            st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
          with col2:
            def current_x_group_items_change():
              if st.session_state.current_x_group in st.session_state.x_groups_dict.keys():
                type_cast = int if x_col.dtype == int else float
                st.session_state.x_groups_dict[st.session_state.current_x_group] = [[type_cast(vals[1:vals.index(",")]), type_cast(vals[vals.index(",") + 1:-1])] if type(vals) == str else vals for vals in st.session_state.current_x_group_items]
              else:
                st.session_state.current_x_group_items = []

            st.multiselect(label = "current_x_group_items", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0 or st.session_state.current_x_group == None, key = "current_x_group_items", placeholder = "", options = None, accept_new_options = True, label_visibility = "collapsed", on_change = current_x_group_items_change)

          #* Min/Max Math
          x_dict_vals = sorted([val for vals in st.session_state.x_groups_dict.values() for val in vals])
          min_value = min(x_col)
          max_value = max(x_col)
          index = 0
          while index < len(x_dict_vals) - 1 and len(x_dict_vals) > 1:
            if x_dict_vals[index][1] == x_dict_vals[index + 1][0]:
              x_dict_vals[index] = [x_dict_vals[index][0], x_dict_vals[index + 1][1]]
              x_dict_vals.pop(index + 1)
            else:
              index += 1
          
          if len(x_dict_vals) > 0 and min_value == x_dict_vals[0][0]:
            min_value = x_dict_vals[0][1]
          if len(x_dict_vals) > 0 and max_value == x_dict_vals[-1][1]:
            max_value = x_dict_vals[-1][0]
          
          #* Choose Bounds
          col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5], gap = None)
          with col1:
            st.markdown("<div style='padding-top: 8px;'>Lower Bound</div>", unsafe_allow_html = True)
          with col2:
            if "x_num_upper_bound" in st.session_state:
              if st.session_state.x_num_lower_bound != None:
                int_bound_index = [bound for bound in x_dict_vals if bound[0] <= st.session_state.x_num_lower_bound and st.session_state.x_num_lower_bound < bound[1]] if len(x_dict_vals) > 0 else []
                if len(int_bound_index) > 0:
                  st.session_state.x_num_lower_bound = int_bound_index[0][1]
              elif st.session_state.x_num_upper_bound != None and len(x_dict_vals) > 0:
                for bounds in reversed(x_dict_vals):
                  if st.session_state.x_num_upper_bound > bounds[1]:
                    min_value = bounds[1]
                    break
            st.number_input(label = "x_num_lower_bound", min_value = min_value, max_value = max_value, step = 1 if x_col.dtype == int else 1.0, placeholder = min_value, key = "x_num_lower_bound", label_visibility = "collapsed", width = 215, value = None, disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0 or st.session_state.current_x_group == None or min_value > max_value)
          
          with col3:
            st.markdown("<div style='padding-top: 8px;'>Upper Bound</div>", unsafe_allow_html = True)
          with col4:
            if "x_num_upper_bound" in st.session_state:
              if st.session_state.x_num_upper_bound != None:
                int_bound_index = [bound for bound in x_dict_vals if bound[0] <= st.session_state.x_num_upper_bound and st.session_state.x_num_upper_bound < bound[1]] if len(x_dict_vals) > 0 else []
                if len(int_bound_index) > 0:
                  st.session_state.x_num_upper_bound = int_bound_index[0][0]
              elif st.session_state.x_num_lower_bound != None and len(x_dict_vals) > 0:
                for bounds in x_dict_vals:
                  if st.session_state.x_num_lower_bound < bounds[1]:
                    max_value = bounds[0]
                    break
            st.number_input(label = "x_num_upper_bound", min_value = min_value, max_value = max_value, step = 1 if x_col.dtype == int else 1.0, placeholder = max_value, key = "x_num_upper_bound", label_visibility = "collapsed", width = 215, value = None, disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0 or st.session_state.current_x_group == None or min_value > max_value)

          if not (st.session_state.x_num_lower_bound == None or st.session_state.x_num_upper_bound == None) and st.session_state.x_num_lower_bound > st.session_state.x_num_upper_bound:
            st.markdown("<div style='padding-bottom: 6px; color: red;'>The lower bound must be less than the upper bound</div>", unsafe_allow_html = True)

          #* Add Bounds Button
          def x_num_add_bound_click():
            if str([st.session_state.x_num_lower_bound, st.session_state.x_num_upper_bound]) not in st.session_state.current_x_group_items:
              st.session_state.current_x_group_items = st.session_state.current_x_group_items + [str([st.session_state.x_num_lower_bound, st.session_state.x_num_upper_bound])]
              type_cast = int if x_col.dtype == int else float
              st.session_state.x_groups_dict[st.session_state.current_x_group] = sorted([[type_cast(vals[1:vals.index(",")]), type_cast(vals[vals.index(",") + 1:-1])] for vals in st.session_state.current_x_group_items])
            st.session_state.x_num_lower_bound = None
            st.session_state.x_num_upper_bound = None
          
          st.button(label = "Add Bound", key = "x_num_add_bound", disabled = st.session_state.x_num_lower_bound == None or st.session_state.x_num_upper_bound == None or (st.session_state.x_num_lower_bound > st.session_state.x_num_upper_bound), on_click = x_num_add_bound_click)
          
        case _:
          st.markdown(f"<div style='color: rgb(255, 0, 0); padding-bottom: 8px;'>Variables with type '{x_col.dtype}' are invalid</div>", unsafe_allow_html = True)

  #* Dependent Variable
  if st.session_state.GraphTypeSelect in ["Line Chart"]:
    with st.expander(label = "Dependent Variable (Y-Axis)"):
      #* Create groups (by providing names)
      col1, col2 = st.columns([1.5, 10.5], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Groups:</div>", unsafe_allow_html = True)
      with col2:
        def y_groups_change():
          # st.session_state.y_groups_dict = {key : st.session_state.y_groups_dict[key] if key in st.session_state.y_groups_dict.keys() else [] for key in st.session_state.y_groups}
          st.session_state.y_groups_dict = {key : st.session_state.y_groups_dict[key] if key in st.session_state.y_groups_dict.keys() else ["No Variable Selected", []] for key in st.session_state.y_groups}
          if st.session_state.current_y_group not in st.session_state.y_groups_dict:
            st.session_state.current_y_group = None
        st.multiselect(label = "y_groups", options = None, key = "y_groups", accept_new_options = True, label_visibility = "collapsed", on_change = y_groups_change)

      #* Select a group to add items to
      col1, col2 = st.columns([2.25, 9.75], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Current Group:</div>", unsafe_allow_html = True)
      with col2:
        def current_y_group_change():
          # st.session_state.current_y_group_items = st.session_state.y_groups_dict[st.session_state.current_y_group]
          # st.session_state.y_col_name_select = st.session_state.y_groups_dict[st.session_state.current_y_group]
          if st.session_state.current_y_group != None:
            st.session_state.y_col_name_select = st.session_state.y_groups_dict[st.session_state.current_y_group][0]
            st.session_state.current_y_group_items = st.session_state.y_groups_dict[st.session_state.current_y_group][1]
        st.selectbox(label = "current_y_group" or len(st.session_state.y_groups) == 0, key = "current_y_group", options = st.session_state.y_groups, index = None, label_visibility = "collapsed", on_change = current_y_group_change)

      #* Column Selection
      col1, col2 = st.columns([3, 9], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Dependent Variable:</div>", unsafe_allow_html = True)
      with col2:
        def intersection(sets):
          if len(sets) == 0:
            return {}
          rtn = set(sets[0])
          for s in sets[1:]:
            rtn = rtn & s
          return rtn
        def y_col_name_select_change():
          st.session_state.y_groups_dict[st.session_state.current_y_group] = [st.session_state.y_col_name_select, st.session_state.current_y_group_items]
        y_col_name = st.selectbox(label = "y_col_name_select", key = "y_col_name_select", disabled = st.session_state.current_y_group in [None, ""], options = ["No Variable Selected"] + sorted(intersection([set(st.session_state.data_objects[index].applications.keys()) | set(st.session_state.data_objects[index].responses.keys()) for index in data_object_indices])), label_visibility = "collapsed", on_change = y_col_name_select_change)
        y_col = st.session_state.data_objects[data_object_indices[0]].key_owner(y_col_name)[0][y_col_name] if y_col_name != "No Variable Selected" else ""

      #* Variable Grouping
      try:
        match type(y_col.dtype):
          case np.dtypes.DateTime64DType:
            #* Select a grouping option
            col1, col2 = st.columns([2.25, 9.75], gap = None)
            with col1:
              st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Date Grouping:</div>", unsafe_allow_html = True)
            with col2:
              def date_groups_change():
                st.session_state.current_y_group_items = []
                st.session_state.y_groups_dict[st.session_state.current_y_group] = [y_col_name, st.session_state.current_y_group_items]
              st.selectbox(label = "date_groups", disabled = False, options = ["No Grouping Selected", "Yearly", "Quarterly", "Monthly"], key = "date_groups", accept_new_options = False, label_visibility = "collapsed", on_change = date_groups_change)

            #* Add items to the selected group
            col1, col2 = st.columns([2, 10], gap = None)
            with col1:
              st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
            with col2:
              current_y_options = []
              start_date = min(y_col)
              end_date = max(y_col)
              def current_y_group_items_format(year):
                return str(year)
              match st.session_state.date_groups:
                case "Yearly":
                  current_y_options = range(start_date.year, end_date.year + 1, 1)
                case "Quarterly":
                  def quarter_num(month):
                    return (month - 1) // 3 + 1
                  current_y_options = [(pd.Timestamp(f"{start_date.year + i // 4}/{(i % 4) * 3 + 1}/1"), pd.Timestamp(f"{start_date.year + i // 4}/{(i % 4 + 1) * 3}/{pd.Timestamp(f"2000/{(i % 4 + 1) * 3}/1").days_in_month}") + pd.Timedelta(value = 8.64 * 10**13 - 1, unit = "nanoseconds")) for i in range(quarter_num(start_date.month) - 1, (end_date.year - start_date.year) * 4 + quarter_num(end_date.month))]
                  def current_y_group_items_format(dates):
                    quarter_months_lookup_table = {1 : "Jan-Mar", 2: "Apr-Jun", 3 : "Jul-Sep", 4 : "Oct-Dec"}
                    return f"{dates[0].year} {quarter_months_lookup_table[dates[1].month / 3]}"
                case "Monthly":                                                                                                                                                                                                                                # 1 day - 1 nanosecond
                  current_y_options = [(pd.Timestamp(f"{start_date.year + i // 12}/{i % 12 + 1}/1"), pd.Timestamp(f"{start_date.year + i // 12}/{i % 12 + 1}/{pd.Timestamp(f"{start_date.year + i // 12}/{i % 12 + 1}/1").days_in_month}") + pd.Timedelta(value = 8.64 * 10**13 - 1, unit = "nanoseconds")) for i in range(start_date.month - 1, (end_date.year - start_date.year) * 12 + end_date.month)]
                  def current_y_group_items_format(dates):
                    return f"{dates[0].year}-{str(dates[0].month).zfill(2)}"
              def current_y_group_items_change():
                if st.session_state.current_y_group in st.session_state.y_groups_dict.keys():
                  # st.session_state.y_groups_dict[st.session_state.current_y_group] = [y_col_name] + list(set(st.session_state.current_y_group_items))
                  st.session_state.y_groups_dict[st.session_state.current_y_group] = [y_col_name, st.session_state.current_y_group_items]
              st.multiselect(label = "current_y_group_items", disabled = y_col_name == "No Variable Selected" or len(st.session_state.date_groups) == 0, key = "current_y_group_items", options = current_y_options, label_visibility = "collapsed", format_func = current_y_group_items_format, on_change = current_y_group_items_change)

          case pd.StringDtype:
            #* Add items to the selected group
            col1, col2 = st.columns([2, 10], gap = None)
            with col1:
              st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
            with col2:
              def current_y_group_items_change():
                if st.session_state.current_y_group in st.session_state.y_groups_dict.keys():
                  # st.session_state.y_groups_dict[st.session_state.current_y_group] = [y_col_name] + list(set(st.session_state.current_y_group_items))
                  st.session_state.y_groups_dict[st.session_state.current_y_group] = [y_col_name, st.session_state.current_y_group_items]
                else:
                  st.session_state.current_y_group_items = []
              unique_y_col = list(y_col.unique())
              if np.nan in unique_y_col:
                unique_y_col.remove(np.nan)
              st.multiselect(label = "current_y_group_items", disabled = y_col_name == "No Variable Selected" or len(st.session_state.y_groups) == 0, key = "current_y_group_items", options = unique_y_col if len(unique_y_col) <= 25 else [], accept_new_options = y_col_name != "No Variable Selected" and len(unique_y_col) > 25, label_visibility = "collapsed", on_change = current_y_group_items_change)
            
          case np.dtypes.ObjectDType:
            col1, col2 = st.columns([2, 10], gap = None)
            with col1:
              st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
            with col2:
              def current_y_group_items_change():
                # st.session_state.y_groups_dict[st.session_state.current_y_group] = set(st.session_state.current_y_group_items)
                st.session_state.y_groups_dict[st.session_state.current_y_group] = [y_col_name, st.session_state.current_y_group_items]
              st.multiselect(label = "current_y_group_items", disabled = y_col_name == "No Variable Selected" or len(st.session_state.y_groups) == 0, key = "current_y_group_items", options = sorted(set(val for val_list in y_col for val in val_list)) if y_col_name != "No Variable Selected" else [], label_visibility = "collapsed", on_change = current_y_group_items_change)
            
          case _:
            st.markdown(f"<div style='color: rgb(255, 0, 0); padding-bottom: 8px;'>Variables with type '{y_col.dtype}' are invalid</div>", unsafe_allow_html = True)
      except:
        col1, col2 = st.columns([2, 10], gap = None)
        with col1:
          st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
        with col2:
          st.multiselect(label = "placeholder", disabled = True, options = [], label_visibility = "collapsed")
      # st.text(st.session_state.y_groups_dict)
      # if st.button(label = "button"):
      #   st.text(st.session_state.y_groups_dict)

  #* Figure Layout
  with st.expander(label = "Figure Layout"):
    #* Figure Title
    col1, col2, col3, col4 = st.columns([1, 7, 2, 2], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Title:</div>", unsafe_allow_html = True)
    with col2:
      figure_title = st.text_input(label = "figure title", value = "", label_visibility = "collapsed")
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Title Width:</div>", unsafe_allow_html = True)
    with col4:
      figure_title_width = st.number_input(label = "figure title width", value = None, min_value = 1, step = 1, placeholder = "∞", label_visibility = "collapsed")

    #* Figure Dimensions
    col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Width:</div>", unsafe_allow_html = True)
    with col2:
      figure_width = st.number_input(label = "figure width input", value = 8, step = 1, label_visibility = "collapsed")
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Height:</div>", unsafe_allow_html = True)
    with col4:
      figure_height = st.number_input(label = "figure height input", value = 5, step = 1, label_visibility = "collapsed")

  #* X-Axis
  if st.session_state.GraphTypeSelect not in ["Pie Chart"]:
    with st.expander(label = "X-Axis"):
      #* Variable and Label Selection
      col1, col2 = st.columns([2, 10], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Label:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_label = st.text_input(label = "x_axis_label", label_visibility = "collapsed", placeholder = "Axis Label")

      #* Tick Marks
      col1, col2, col3, col4 = st.columns([2.25, 3.75, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Tick Entry Type:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_tick_marks_type = st.selectbox(label = "x_axis_tick_marks type", disabled = len(data_object_indices) == 0, options = ["Manual", "Range", "Log Range"], label_visibility = "collapsed")
      with col3:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px;'>Tick Marks:</div>", unsafe_allow_html = True)
      with col4:
        x_axis_tick_marks_placeholders = {"Manual" : "0, 1, 2, ...", "Range" : "Start, Stop, Step", "Log Range" : "log(Start), log(Stop), log(Step)"}
        x_axis_tick_marks = st.text_input(label = "x_axis_tick_marks", label_visibility = "collapsed", placeholder = x_axis_tick_marks_placeholders[x_axis_tick_marks_type])

      #* Tick Labels
      col1, col2 = st.columns([2, 10], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Tick labels:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_tick_labels = st.multiselect(label = "x_axis_tick_labels", options = [], label_visibility = "collapsed", accept_new_options = True)

      #* Left/Right Limits
      col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Left Limit:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_left_lim = st.number_input(label = "x_axis left lim", step = 0.1, label_visibility = "collapsed", value = None)
      with col3:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Right Limit:</div>", unsafe_allow_html = True)
      with col4:
        x_axis_right_lim = st.number_input(label = "x_axis right lim", step = 0.1, label_visibility = "collapsed", value = None)

      #* Scale and Thousands Separator
      col1, col2, col3, col4 = st.columns([2, 4, 5, 1], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Scale:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_scale = st.selectbox(label = "x_axis scale", label_visibility = "collapsed", options = ["Linear", "Log", "Symlog"])
      with col3:
        st.markdown(f"<div style='padding-top: 9px; text-align: right; padding-right: 15px;'>Use Thousands Separator Commas:</div>", unsafe_allow_html = True)
      with col4:
        x_thousands_separator = st.toggle(label = "x_thousands_separator", value = True, key = "x_thousands_separator", label_visibility = "collapsed")

  #* Y-Axis
  if st.session_state.GraphTypeSelect not in ["Pie Chart"]:
    with st.expander(label = "Y-Axis"):
      #* Variable and Label Selection
      col1, col2 = st.columns([2, 10], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Label:</div>", unsafe_allow_html = True)
      with col2:
        y_axis_label = st.text_input(label = "y_axis_label", label_visibility = "collapsed", placeholder = "Axis Label")

      #* Tick Marks
      col1, col2, col3, col4 = st.columns([2.25, 3.75, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Tick Entry Type:</div>", unsafe_allow_html = True)
      with col2:
        y_axis_tick_marks_type = st.selectbox(label = "y_axis_tick_marks type", disabled = len(data_object_indices) == 0, options = ["Manual", "Range", "Log Range"], label_visibility = "collapsed")
      with col3:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px;'>Tick Marks:</div>", unsafe_allow_html = True)
      with col4:
        y_axis_tick_marks_placeholders = {"Manual" : "0, 1, 2, ...", "Range" : "Start, Stop, Step", "Log Range" : "log(Start), log(Stop), log(Step)"}
        y_axis_tick_marks = st.text_input(label = "y_axis_tick_marks", label_visibility = "collapsed", placeholder = y_axis_tick_marks_placeholders[y_axis_tick_marks_type])

      #* Tick Labels
      col1, col2 = st.columns([2, 10], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Tick labels:</div>", unsafe_allow_html = True)
      with col2:
        y_axis_tick_labels = st.multiselect(label = "y_axis_tick_labels", options = [], label_visibility = "collapsed", accept_new_options = True)

      #* Left/Right Limits
      col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Lower Limit:</div>", unsafe_allow_html = True)
      with col2:
        y_axis_bottom_lim = st.number_input(label = "y_axis_bottom_lim", step = 0.1, label_visibility = "collapsed", value = None)
      with col3:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Upper Limit:</div>", unsafe_allow_html = True)
      with col4:
        y_axis_top_lim = st.number_input(label = "y_axis_top_lim", step = 0.1, label_visibility = "collapsed", value = None)

      #* Scale and Thousands Separator
      col1, col2, col3, col4 = st.columns([2, 4, 5, 1], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Scale:</div>", unsafe_allow_html = True)
      with col2:
        y_axis_scale = st.selectbox(label = "y_axis_scale", label_visibility = "collapsed", options = ["Linear", "Log", "Symlog"])
      with col3:
        st.markdown(f"<div style='padding-top: 9px; text-align: right; padding-right: 15px;'>Use Thousands Separator Commas:</div>", unsafe_allow_html = True)
      with col4:
        y_thousands_separator = st.toggle(label = "y_thousands_separator", value = True, key = "y_thousands_separator", label_visibility = "collapsed")
      
      #* Y-Axis Grid Lines
      col1, col2 = st.columns([2, 10], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Y-Axis Lines:</div>", unsafe_allow_html = True)
      with col2:
        y_axis_grid_lines = st.toggle(label = "y_axis_grid_lines", value = False, label_visibility = "collapsed")

  #* Legend
  with st.expander(label = "Legend"):
    #* Legend Toggle
    col1, col2, col3, col4 = st.columns([2.5, 2.5, 3.25, 3.75], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 8.5px; text-align: right; padding-right: 15px;'>Enable Legend:</div>", unsafe_allow_html = True)
    with col2:
      show_legend = st.toggle(label = "show legend", value = True, label_visibility = "collapsed")
      legend_parameters_label_color = "" if show_legend else "color: #959595"
    with col3:
      st.markdown(f"<div style='padding-top: 8.5px; text-align: right; padding-right: 15px; {legend_parameters_label_color};'>Number of Columns:</div>", unsafe_allow_html = True)
    with col4:
      legend_ncols = st.number_input(label = "legend ncols", value = 1, min_value = 1, step = 1, disabled = not show_legend, label_visibility = "collapsed")      

    #* Row/Col Dimensions
    col1, col2, col3, col4 = st.columns([2.25, 3.75, 2.25, 3.75], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 8.5px; text-align: right; padding-right: 15px; {legend_parameters_label_color};'>X-Coordinate:</div>", unsafe_allow_html = True)
    with col2:
      legend_xpos = st.number_input(label = "legend xpos", value = None, step = 0.01, disabled = not show_legend, label_visibility = "collapsed")
    with col3:
      st.markdown(f"<div style='padding-top: 8.5px; text-align: right; padding-right: 15px; {legend_parameters_label_color};'>Y-Coordinate:</div>", unsafe_allow_html = True)
    with col4:
      legend_ypos = st.number_input(label = "legend ypos", value = None, step = 0.01, disabled = not show_legend, label_visibility = "collapsed")

    #* Legend Background Colors
    st.markdown(f"<div style='padding-left: 15px;'>Legend Background:</div>", unsafe_allow_html = True)
    col1, col2, col3, col4 = st.columns([2.5, 3.25, 1.5, 4.25], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Color Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      legend_background_colors_entry_type = st.selectbox(label = f"legend background_legend_background_colors_entry_type", label_visibility = "collapsed", options = ["Single Entry", "Manual Single Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Colors:</div>", unsafe_allow_html = True)
    with col4:
      if legend_background_colors_entry_type == "Single Entry":
        legend_background_colors = st.color_picker(label = f"Legend Background New Colors", label_visibility = "collapsed", value = "#ffffff")
      if legend_background_colors_entry_type == "Manual Single Entry":
        legend_background_colors = st.selectbox(label = f"Legend Background New Colors", label_visibility = "collapsed", options = None, accept_new_options = True)

    #* Legend Edge Colors
    st.markdown(f"<div style='padding-left: 15px;'>Legend Edge:</div>", unsafe_allow_html = True)
    col1, col2, col3, col4 = st.columns([2.5, 3.25, 1.5, 4.25], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Color Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      legend_edge_colors_entry_type = st.selectbox(label = f"legend_edge_legend_edge_colors_entry_type", label_visibility = "collapsed", options = ["Single Entry", "Manual Single Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Colors:</div>", unsafe_allow_html = True)
    with col4:
      if legend_edge_colors_entry_type == "Single Entry":
        legend_edge_colors = st.color_picker(label = f"Legend Edge New Colors", label_visibility = "collapsed", value = "#BEBEBE")
      if legend_edge_colors_entry_type == "Manual Single Entry":
        legend_edge_colors = st.selectbpx(label = f"Legend Edge New Colors", label_visibility = "collapsed", options = None, accept_new_options = True)

    # #* Legend Edge Colors
    # legend_edge_colors_entry_type, legend_edge_colors = default_color_selectors("Legend Edge")

    #* New Labels Toggle
    col1, col2 = st.columns([3, 9], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 8.5px; text-align: right; padding-right: 15px; {legend_parameters_label_color};'>Manual Legend Entry:</div>", unsafe_allow_html = True)
    with col2:
      manual_legend_entry_toggle = st.toggle(label = "manual legend entry", value = False, disabled = not show_legend, label_visibility = "collapsed")

    #* Optional Different Legend Labels
    manual_legend_parameters_label_color = "" if show_legend and manual_legend_entry_toggle else "color: #959595"
    col1, col2 = st.columns([2.5, 9.5], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 7.5px; text-align: right; padding-right: 15px; {manual_legend_parameters_label_color};'>Manual Labels:</div>", unsafe_allow_html = True)
    with col2:
      legend_new_labels = st.multiselect(label = "legend new labels", disabled = not (show_legend and manual_legend_entry_toggle), options = None, accept_new_options = True, label_visibility = "collapsed")

    #* Optional Different Legend Colors
    legend_new_colors_entry_type, legend_new_colors = default_color_selectors("New Legend Colors", disabled = not (show_legend and manual_legend_entry_toggle))
    
#* Bar Plot Specific  
if st.session_state.GraphTypeSelect  == "Bar Plot":
  with st.expander(label = "Bar Plot Specific"):
    #* Bar Fill Color
    bar_fill_colors_entry_type, bar_fill_colors = default_color_selectors("Bar Fill Colors")

    #* Bar Edge Color
    bar_edge_colors_entry_type, bar_edge_colors = default_color_selectors("Bar Edge Colors")

   #* Bar Width and Tick Marks
    col1, col2, col3, col4 = st.columns([2, 2.25, 1.75, 6], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Bar Width:</div>", unsafe_allow_html = True)
    with col2:
      bar_width = st.number_input(label = "bar_width", min_value = 0., step = 0.1, value = 0.8, label_visibility = "collapsed")
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px;'>Bar Ticks:</div>", unsafe_allow_html = True)
    with col4:
      bar_tick_marks = st.text_input(label = "bar tick marks", label_visibility = "collapsed", placeholder = "0, 1, 2, ...")

#* Pie Chart Specific
if st.session_state.GraphTypeSelect == "Pie Chart":
  with st.expander(label = "Pie Chart Specific"):
    #* Wedge Fill Color
    wedge_fill_colors_entry_type, wedge_fill_colors = default_color_selectors("Wedge Fill Colors")

    #* Rotation (Direction and Starting Position)
    col1, col2, col3, col4 = st.columns([1.5, 4.5, 2.5, 3.5], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Direction:</div>", unsafe_allow_html = True)
    with col2:
      pie_rotation = st.selectbox(label = "pie_rotation", options = ["Counterclockwise", "Clockwise"], label_visibility = "collapsed")
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Starting Angle:</div>", unsafe_allow_html = True)
    with col4:
      wedge_starting_angle = st.number_input(label = "wedge_starting_angle", min_value = 0.0, max_value = 360.0, step = 1.0, label_visibility = "collapsed")

    #* Label Choices and Wedge Width
    col1, col2, col3, col4, col5, col6 = st.columns([3.25, 0.75, 3.25, 0.75, 2.0, 2], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 9px; text-align: right; padding-right: 15px;'>Label: Include Percent:</div>", unsafe_allow_html = True)
    with col2:
      pie_percent_label = st.toggle(label = "pie_percent_label", value = False, label_visibility = "collapsed")
    with col3:
      st.markdown(f"<div style='padding-top: 9px; text-align: right; padding-right: 15px;'>Label: Include Number:</div>", unsafe_allow_html = True)
    with col4:
      pie_number_label = st.toggle(label = "pie_number_label", value = False, label_visibility = "collapsed")
    with col5:
      st.markdown(f"<div style='padding-top: 8px; text-align: right; padding-right: 15px;'>Wedge Width</div>", unsafe_allow_html = True)
    with col6:
      wedge_width = st.number_input(label = "wedge_width", value = 1., min_value = 0.0, step = 0.01, max_value = 1.0, label_visibility = "collapsed")

    #* Label Font Size
    col1, col2 = st.columns([2.5, 9.5])
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Label: Font Size:</div>", unsafe_allow_html = True)
    with col2:
      pie_label_font_size = st.number_input(label = "pie_label_font_size", value = 10., min_value = 1., step = 1., label_visibility = "collapsed")

#* Line Chart Specific
if st.session_state.GraphTypeSelect == "Line Chart":
  with st.expander(label = "Line Chart Specific"):
    line_colors_entry_type, line_colors = default_color_selectors("Line")

    #* Markers and Line Styles
    col1, col2, col3, col4 = st.columns([1.5, 4.5, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Markers:</div>", unsafe_allow_html = True)
    with col2:
      def line_markers_format(value):
        return line_markers_reference_table[value]
      line_markers = st.multiselect(label = "line_markers", options = line_markers_reference_table.keys(), key = "line_markers", accept_new_options = False, label_visibility = "collapsed", format_func = line_markers_format)
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Line Styles:</div>", unsafe_allow_html = True)
    with col4:
      def line_styles_format(value):
        return linestyle_reference_table[value]
      line_styles = st.multiselect(label = "line_styles", options = linestyle_reference_table.keys(), key = "line_styles", accept_new_options = False, label_visibility = "collapsed", format_func = line_styles_format)

#* Made for formatting graphs made with Plotly
def plt_formatting(fig):
  fig.update_xaxes(showline = True,
                   linewidth = 1,
                   linecolor = "black",
                   mirror = True,
                   title_font_color = "black",
                   tickfont_color = "black",
                   ticks = "outside",
                   ticklen = 6,
                   tickwidth = 1,
                   showgrid = False)
  xmax = max(trace.x.max() for trace in fig.data)
  fig.update_xaxes(range=[0, xmax * 1.05])
  
  fig.update_yaxes(showline = True,
                   linewidth = 1,
                   linecolor = "black",
                   mirror = True,
                   title_font_color = "black",
                   tickfont_color = "black",
                   ticks = "outside",
                   ticklen = 6,
                   tickwidth = 1,
                   showgrid = False,
                   zeroline = False)
  ymax = max(trace.y.max() for trace in fig.data)
  fig.update_yaxes(range=[0, ymax * 1.05])
        
  fig.update_layout(plot_bgcolor = "white",
                    paper_bgcolor = "white",
                    font = {"family" : "Arial",
                            "size" : 16,
                            "color" : "black"},
                    legend = {"bgcolor" : "rgba(255,255,255,0)",
                              "font_color" : "black",
                              "title_font_color" : "black",
                              "borderwidth" : 0},
                    width = 700,
                    height = 500,
                    margin = {"l" : 50, "r" : 20, "t" : 30, "b" : 50})
  fig.update_traces(marker = {"size" : 4})

  return fig

#* Automatically vs Manually Update Graph
col1, col2, col3 = st.columns([3.1, 0.8, 8.1], gap = None)
with col2:
  st.toggle(label = "automatically_update_graph", value = True, key = "automatically_update_graph_toggle", label_visibility = "collapsed")
with col1:
  st.button(label = "Manually Update Graph", key = "manually_update_graph", disabled = st.session_state.automatically_update_graph_toggle)
with col3:
  st.markdown(f"<div style='padding-top: 9.5px; text-align: left; padding-left: 0px;{"" if st.session_state.automatically_update_graph_toggle else " color: rgb(100, 100, 100);"})'>Automatically Update Graph</div>", unsafe_allow_html = True)

#* Graphing
#         Graph should be automatically updated                update graph button pushed                            graph type selected                                  x column selected                                        at least one x group has a value (string, list)                                          x col is a date and a date grouping object has been chosen
if (st.session_state.automatically_update_graph_toggle or st.session_state.manually_update_graph) and st.session_state.GraphTypeSelect != "Select a Graph Type" and x_col_name != "No Variable Selected" and (len([i2 for i in st.session_state.x_groups_dict.values() for i2 in i if i2 != ""]) > 0 or (x_col.dtype == np.dtype("datetime64[us]") and len(st.session_state.current_x_group_items) > 0)) and (True if st.session_state.GraphTypeSelect not in ["Line Chart"] else ({vals[0] != "No Variable Selected" for vals in st.session_state.y_groups_dict.values()} == {True} and True in [len(vals[1]) > 0 for vals in st.session_state.y_groups_dict.values()])): #! Make sure to include conditional len(y_groups)
  fig, ax = plt.subplots(1, 1, figsize = (figure_width, figure_height))

  ax.set_title(label = textwrap.fill(figure_title, width = max(len(figure_title), 1) if figure_title_width == None else figure_title_width))
  
  match st.session_state.GraphTypeSelect:
    case "Bar Plot":
      def bar_group_sizes():
        bar_kwargs = {"height" : [], "x" : [], "label" : st.session_state.x_groups_dict, "facecolor" : interpret_colors(bar_fill_colors, len(st.session_state.x_groups_dict), bar_fill_colors_entry_type), "edgecolor" : interpret_colors(bar_edge_colors, len(st.session_state.x_groups_dict), bar_edge_colors_entry_type) if len(bar_edge_colors) > 0 else None}
        match type(st.session_state.data_objects[data_object_indices[0]].key_owner(x_col_name)[0].dtypes[x_col_name]):
          case np.dtypes.ObjectDType:
            bar_kwargs["height"] = [len([col for col in x_col if len(group & set(col)) > 0]) for group in st.session_state.x_groups_dict.values()]
          case pd.StringDtype:
            bar_kwargs["height"] = [len([col for col in x_col if type(col) != float and re.search("|".join(group), col, flags = re.IGNORECASE)]) if len(group) > 0 else 0 for group in st.session_state.x_groups_dict.values()]
          case np.dtypes.DateTime64DType:
            match st.session_state.x_groups:
              case "Yearly":
                bar_kwargs["height"] = [sum((pd.Timestamp(f"{year}/1/1") <= x_col) & (x_col < pd.Timestamp(f"{year + 1}/1/1"))) for year in st.session_state.current_x_group_items]
                bar_kwargs["label"] = st.session_state.current_x_group_items
              case "Quarterly":
                bar_kwargs["height"] = [sum((bounds[0] <= x_col) & (x_col <= bounds[1])) for bounds in st.session_state.current_x_group_items]
                quarter_months_lookup_table = {1 : "Jan-Mar", 2: "Apr-Jun", 3 : "Jul-Sep", 4 : "Oct-Dec"}
                bar_kwargs["label"] = [f"{dates[0].year} {quarter_months_lookup_table[dates[1].month / 3]}" for dates in st.session_state.current_x_group_items]
              case "Monthly":
                bar_kwargs["height"] = [sum((bounds[0] <= x_col) & (x_col <= bounds[1])) for bounds in st.session_state.current_x_group_items]
                bar_kwargs["label"] = [f"{dates[0].year}-{str(dates[0].month).zfill(2)}" for dates in st.session_state.current_x_group_items]
            bar_kwargs["facecolor"] = interpret_colors(bar_fill_colors, len(st.session_state.current_x_group_items), bar_fill_colors_entry_type)
            bar_kwargs["edgecolor"] = interpret_colors(bar_edge_colors, len(st.session_state.current_x_group_items), bar_edge_colors_entry_type) if len(bar_edge_colors) > 0 else None
          case np.dtypes.Int64DType:
            bar_kwargs["height"] = [sum([sum((bounds[0] <= x_col) & (x_col < bounds[1])) for bounds in group]) for group in st.session_state.x_groups_dict.values()]
        bar_kwargs["x"] = [float(tick) for tick in bar_tick_marks.replace(" ", "").split(",")] if bar_tick_marks != "" and len(bar_tick_marks.replace(" ", "").split(",")) == len(bar_kwargs["height"]) else range(len(bar_kwargs["height"]))

        return bar_kwargs
      
      ax.bar(**bar_group_sizes(), width = bar_width, log = False)

    case "Pie Chart":
      def pie_group_sizes():
        pie_kwargs = {"x" : [], "labels" : st.session_state.x_groups_dict, "colors" : interpret_colors(wedge_fill_colors, len(st.session_state.x_groups_dict), wedge_fill_colors_entry_type)}
        match type(st.session_state.data_objects[data_object_indices[0]].key_owner(x_col_name)[0].dtypes[x_col_name]):
          case np.dtypes.ObjectDType:
            pie_kwargs["x"] = [len([col for col in x_col if len(group & set(col)) > 0]) for group in st.session_state.x_groups_dict.values()]
            pie_kwargs["labels"] = [f"{name}{"\n" if pie_percent_label or pie_number_label else ""}{f"{pie_kwargs["x"][i] / sum(pie_kwargs["x"]) * 100:.1f}" + "%" if pie_percent_label else ""}{" " if pie_percent_label and pie_number_label else ""}{"(" + f"{pie_kwargs["x"][i]:,}" + ")" if pie_number_label else ""}" for i, name in enumerate(st.session_state.x_groups_dict.keys())]
          case pd.StringDtype:
            pie_kwargs["x"] = [len([col for col in x_col if type(col) != float and re.search("|".join(group), col, flags = re.IGNORECASE)]) if len(group) > 0 else 0 for group in st.session_state.x_groups_dict.values()]
            pie_kwargs["labels"] = [f"{name}{"\n" if pie_percent_label or pie_number_label else ""}{f"{pie_kwargs["x"][i] / sum(pie_kwargs["x"]) * 100:.1f}" + "%" if pie_percent_label else ""}{" " if pie_percent_label and pie_number_label else ""}{"(" + f"{pie_kwargs["x"][i]:,}" + ")" if pie_number_label else ""}" for i, name in enumerate(st.session_state.x_groups_dict.keys())]
          case np.dtypes.DateTime64DType:
            match st.session_state.x_groups:
              case "Yearly":
                pie_kwargs["x"] = [sum((pd.Timestamp(f"{year}/1/1") <= x_col) & (x_col < pd.Timestamp(f"{year + 1}/1/1"))) for year in st.session_state.current_x_group_items]
                pie_kwargs["labels"] = [f"{year}{"\n" if pie_percent_label or pie_number_label else ""}{f"{pie_kwargs["x"][i] / sum(pie_kwargs["x"]) * 100:.1f}" + "%" if pie_percent_label else ""}{" " if pie_percent_label and pie_number_label else ""}{"(" + f"{pie_kwargs["x"][i]:,}" + ")" if pie_number_label else ""}" for i, year in enumerate(st.session_state.current_x_group_items)]
              case "Quarterly": #! Add percent and number
                pie_kwargs["x"] = [sum((bounds[0] <= x_col) & (x_col <= bounds[1])) for bounds in st.session_state.current_x_group_items]
                quarter_months_lookup_table = {1 : "Jan-Mar", 2: "Apr-Jun", 3 : "Jul-Sep", 4 : "Oct-Dec"}
                pie_kwargs["labels"] = [f"{dates[0].year} {quarter_months_lookup_table[dates[1].month / 3]}" for dates in st.session_state.current_x_group_items]
              case "Monthly": #! Add percent and number
                pie_kwargs["x"] = [sum((bounds[0] <= x_col) & (x_col <= bounds[1])) for bounds in st.session_state.current_x_group_items]
                pie_kwargs["labels"] = [f"{dates[0].year}-{str(dates[0].month).zfill(2)}" for dates in st.session_state.current_x_group_items]
            pie_kwargs["colors"] = interpret_colors(wedge_fill_colors, len(st.session_state.current_x_group_items), wedge_fill_colors_entry_type)
          case np.dtypes.Int64DType: #! Add percent and number
            pie_kwargs["x"] = [sum([sum((bounds[0] <= x_col) & (x_col < bounds[1])) for bounds in group]) for group in st.session_state.x_groups_dict.values()]
        return pie_kwargs

      ax.pie(**pie_group_sizes(), wedgeprops = {"width" : wedge_width}, textprops = {"fontsize" : pie_label_font_size}, startangle = wedge_starting_angle, counterclock = pie_rotation == "Counterclockwise")

    case "Line Chart":
      line_colors = interpret_colors(line_colors, len(st.session_state.y_groups_dict), line_colors_entry_type)
      for i, group_name in enumerate(st.session_state.y_groups_dict.keys()):
        line_kwargs = {"color" : line_colors[i], "marker" : "" if line_markers == [] else line_markers[i % len(line_markers)], "linestyle" : None if line_styles == [] else line_styles[i % len(line_styles)]}
        
        def line_group_sizes(y_group_col_name: str, y_group_items: set):
          global x_axis_tick_marks_type
          global x_axis_tick_marks
          global x_axis_tick_labels

          x_coords = []
          y_coords = []
          temp_data_object = d.DataObject.from_dataobject("temp", st.session_state.data_objects[data_object_indices[0]])
          x_owner = temp_data_object.key_owner_name(x_col_name)
          y_owner = temp_data_object.key_owner_name(y_group_col_name)
          df = temp_data_object.responses if y_owner == "responses" else temp_data_object.applications

          #* Dependent Variable
          match type(temp_data_object.key_owner(y_group_col_name)[0].dtypes[y_group_col_name]):
            case np.dtypes.ObjectDType:
              df = df[[not y_group_items.isdisjoint(df_val) for df_val in df[y_group_col_name]]]
            case pd.StringDtype:
              df = df[df[y_group_col_name].str.contains("|".join(y_group_items), case = False, na = False)]
            case np.dtypes.DateTime64DType:
              match st.session_state.x_groups:
                case "Yearly":
                  mask = pd.Series(False, index = df.index)
                  for year in y_group_items:
                    mask |= (pd.Timestamp(f"{year}/1/1") <= df[y_group_col_name]) & (df[y_group_col_name] < pd.Timestamp(f"{year + 1}/1/1"))
                  df = df[mask]
                case "Quarterly" | "Monthly":
                  mask = pd.Series(False, index = df.index)
                  for bounds in y_group_items:
                    mask |= (bounds <= df[y_group_col_name]) & (df[y_group_col_name] < bounds)
                  df = df[mask]
            case np.dtypes.Int64DType:
              # pie_kwargs["x"] = [sum([sum((bounds[0] <= x_col) & (x_col < bounds[1])) for bounds in group]) for group in st.session_state.x_groups_dict.values()]
              mask = pd.Series(False, index = df.index)
              for bounds in y_group_items:
                mask |= (bounds <= df[y_group_col_name]) & (df[y_group_col_name] < bounds)
              df = df[mask]
          
          if not ((x_owner in ["both", "applications"] and y_owner in ["both", "applications"]) or (x_owner == "responses" and y_owner == "responses")):
            df = pd.merge(df, temp_data_object.responses if x_owner == "responses" else temp_data_object.applications, on = "application_id", how = "inner")
            df.drop(columns = [key for key in df.keys() if "_y" in key], inplace = True)
            df = df.rename(columns = {key : key.replace("_x", "") for key in df.keys()})
          
          #* Independent Variable
          match type(temp_data_object.key_owner(x_col_name)[0].dtypes[x_col_name]):
            case np.dtypes.ObjectDType:
              y_coords = [len(df[[not set(group).isdisjoint(vals) for vals in df[x_col_name]]]) for group in st.session_state.x_groups_dict.values()]
              x_coords = range(len(st.session_state.x_groups_dict))
              if x_axis_tick_marks in ["", None]:
                x_axis_tick_marks_type = "Manual"
                x_axis_tick_marks = ",".join([str(j) for j in range(len(st.session_state.x_groups_dict))])
                x_axis_tick_labels = st.session_state.x_groups_dict.keys()
              elif len(x_axis_tick_labels) == 0:
                x_axis_tick_labels = [key for i, key in enumerate(st.session_state.x_groups_dict.keys()) if i in interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)]
            
            case pd.StringDtype:
              y_coords = [len(df[[bool(re.search("|".join(group), vals, flags = re.IGNORECASE)) for vals in df[x_col_name]]]) for group in st.session_state.x_groups_dict.values()]
              x_coords = range(len(st.session_state.x_groups_dict))
              if x_axis_tick_marks in ["", None]:
                x_axis_tick_marks_type = "Manual"
                x_axis_tick_marks = ",".join([str(j) for j in range(len(st.session_state.x_groups_dict))])
                x_axis_tick_labels = st.session_state.x_groups_dict.keys()
              elif len(x_axis_tick_labels) == 0:
                x_axis_tick_labels = [key for i, key in enumerate(st.session_state.x_groups_dict.keys()) if i in interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)]
            
            case np.dtypes.DateTime64DType:
              match st.session_state.x_groups:
                case "Yearly":
                  y_coords = [len(df[(pd.Timestamp(f"{year}/1/1") <= df[x_col_name]) & (df[x_col_name] < pd.Timestamp(f"{year + 1}/1/1"))]) for year in st.session_state.current_x_group_items]
                  x_coords = range(len(st.session_state.current_x_group_items))
                  if x_axis_tick_marks in ["", None]:
                    x_axis_tick_marks_type = "Manual"
                    x_axis_tick_marks = ",".join([str(j) for j in range(len(st.session_state.current_x_group_items))])
                    x_axis_tick_labels = st.session_state.current_x_group_items
                  elif len(x_axis_tick_labels) == 0:
                    x_axis_tick_labels = [date for i, date in enumerate(st.session_state.current_x_group_items) if i in interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)]
                  
                case "Quarterly":
                  y_coords = [len(df[(bounds[0] <= df[x_col_name]) & (df[x_col_name] < bounds[1])]) for bounds in st.session_state.current_x_group_items]
                  quarter_months_lookup_table = {1 : "Jan-Mar", 2: "Apr-Jun", 3 : "Jul-Sep", 4 : "Oct-Dec"}
                  x_coords = range(len(st.session_state.current_x_group_items))
                  if x_axis_tick_marks in ["", None]:
                    x_axis_tick_marks_type = "Manual"
                    x_axis_tick_marks = ",".join([str(j) for j in range(len(st.session_state.current_x_group_items))])
                    x_axis_tick_labels = [f"{dates[0].year} {quarter_months_lookup_table[dates[1].month / 3]}" for dates in st.session_state.current_x_group_items]
                  elif len(x_axis_tick_labels) == 0:
                    x_axis_tick_labels = [f"{dates[0].year} {quarter_months_lookup_table[dates[1].month / 3]}" for i, dates in enumerate(st.session_state.current_x_group_items) if i in interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)]
                
                case "Monthly":
                  y_coords = [len(df[(bounds[0] <= df[x_col_name]) & (df[x_col_name] < bounds[1])]) for bounds in st.session_state.current_x_group_items]
                  x_coords = range(len(st.session_state.current_x_group_items))
                  if x_axis_tick_marks in ["", None]:
                    x_axis_tick_marks_type = "Manual"
                    x_axis_tick_marks = ",".join([str(j) for j in range(len(st.session_state.current_x_group_items))])
                    x_axis_tick_labels = [f"{dates[0].year}-{str(dates[0].month).zfill(2)}" for dates in st.session_state.current_x_group_items]
                  elif len(x_axis_tick_labels) == 0:
                    x_axis_tick_labels = [f"{dates[0].year}-{str(dates[0].month).zfill(2)}" for i, dates in enumerate(st.session_state.current_x_group_items) if i in interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)]
            case np.dtypes.Int16DType:
              y_coords = [sum([sum((bounds[0] <= x_col) & (x_col < bounds[1])) for bounds in group]) for group in st.session_state.x_groups_dict.values()]
              x_coords = range(len(st.session_state.x_groups_dict))
              if x_axis_tick_marks in ["", None]:
                x_axis_tick_marks_type = "Manual"
                x_axis_tick_marks = ",".join([str(j) for j in range(len(st.session_state.x_groups_dict))])
                x_axis_tick_labels = st.session_state.x_groups_dict.keys()
              elif len(x_axis_tick_labels) == 0:
                x_axis_tick_labels = [key for i, key in enumerate(st.session_state.x_groups_dict.keys()) if i in interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)]
          return [x_coords, y_coords]

        values = st.session_state.y_groups_dict[group_name]
        ax.plot(*line_group_sizes(values[0], set(values[1])), label = group_name, **line_kwargs)

  #* X-Axis Formatting
  if st.session_state.GraphTypeSelect not in ["Pie Chart"]:
    ax.set_xlabel(x_axis_label)
    ax.set_xlim(left = x_axis_left_lim, right = x_axis_right_lim)
    ax.set_xscale(x_axis_scale.lower())
    if x_axis_tick_marks not in ["", None]:
      x_ticks = interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)
      ax.set_xticks(x_ticks, labels = None if len(x_axis_tick_labels) == 0 else x_axis_tick_labels[:len(x_ticks)] + [""] * max(len(x_ticks) - len(x_axis_tick_labels), 0))
    if len(x_axis_tick_labels) == 0 and x_thousands_separator:
      ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}" if x.is_integer() else f"{x:g}"))

  #* Y-Axis Formatting
  if st.session_state.GraphTypeSelect not in ["Pie Chart"]:
    ax.set_ylabel(y_axis_label)
    ax.set_ylim(bottom = y_axis_bottom_lim, top = y_axis_top_lim)
    ax.set_yscale(y_axis_scale.lower())
    if y_axis_tick_marks not in ["", None]:
      y_ticks = interpret_ticks(y_axis_tick_marks, y_axis_tick_marks_type)
      ax.set_yticks(y_ticks, labels = None if len(y_axis_tick_labels) == 0 else y_axis_tick_labels[:len(y_ticks)] + [""] * max(len(y_ticks) - len(y_axis_tick_labels), 0))
    if len(y_axis_tick_labels) == 0 and y_thousands_separator:
      ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{int(y):,}" if y.is_integer() else f"{y:g}"))
    if y_axis_grid_lines:
      ax.grid(axis = 'y')
      ax.set_axisbelow(True)

  if show_legend:
    legend_kwargs = {}

    if legend_background_colors not in [None, []]:
      legend_kwargs["facecolor"] = interpret_colors(legend_background_colors, 1, legend_background_colors_entry_type)[0]
      if len(legend_kwargs["facecolor"]) == 4 and legend_kwargs["facecolor"][3] == 0:
        legend_kwargs["facecolor"] = "none"

    if legend_edge_colors not in [None, []]:
      legend_kwargs["edgecolor"] = interpret_colors(legend_edge_colors, 1, legend_edge_colors_entry_type)[0]
      if len(legend_kwargs["edgecolor"]) == 4 and legend_kwargs["edgecolor"][3] == 0:
        legend_kwargs["edgecolor"] = "none"

    if legend_xpos != None and legend_ypos != None:
      legend_kwargs["bbox_to_anchor"] = (legend_xpos, legend_ypos)
      legend_kwargs["loc"] = "upper left"

    if manual_legend_entry_toggle:
      legend_kwargs["handles"] = [Line2D([], [], marker = "o", linestyle = "", color = color, label = text) for text, color in zip(legend_new_labels, interpret_colors(legend_new_colors, len(legend_new_labels), legend_new_colors_entry_type))]

    fig.legend(ncols = legend_ncols, **legend_kwargs)
  
  st.pyplot(fig, width = "content")
