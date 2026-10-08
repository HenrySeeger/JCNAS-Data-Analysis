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
  tick_input = [float(tick) for tick in tick_input.replace(" ", "").split(",") if tick != ""][:3]
  num_decimals = max([len(str(val)[str(val).index(".") + 1:]) for val in tick_input])
  match entry_type:
    case "Manual":
      return tick_input
    case "Range":
      return [val / 10**num_decimals for val in range(*[int(val * 10**num_decimals) for val in tick_input])]
    case "Log Range":
      return [10**tick for tick in [val / 10**num_decimals for val in range(*[int(val * 10**num_decimals) for val in tick_input])]]

st.header("Graphing")

#* Select a Graph Type Header
for i, col in enumerate(st.columns([3, 11], gap = None)):
  with col:
    if i == 0:
      st.markdown("<div style='padding-top: 5.5px;'>Select a Graph Type:</div>", unsafe_allow_html = True)
    else:
      st.selectbox(label = "Select graph type", options = ["Select a Graph Type", "Bar Plot", "Pie Chart"], label_visibility = "collapsed", key = "GraphTypeSelect", disabled = len(st.session_state.data_objects) == 0)

"" # Adds a vertical space on the page

def select_object_format(num):
  return num if type(num) == str else st.session_state.data_objects[num].name

st.markdown(f"<h3 style='{"color: #646464" if st.session_state.GraphTypeSelect == "Select a Graph Type" else ""};'>Graph Parameters</h3>", unsafe_allow_html = True)

#* Data Object Selector
col1, col2 = st.columns([2, 10], gap = None)
with col1:
  st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px; color: #{"646464" if st.session_state.GraphTypeSelect == "Select a Graph Type" else "ffffff"}'>Data Objects:</div>", unsafe_allow_html = True)
with col2:
  data_object_indices = st.multiselect(label = "Select a Data Object", disabled = st.session_state.GraphTypeSelect == "Select a Graph Type", options = list(range(len(st.session_state.data_objects))), label_visibility = "collapsed", default = None, format_func = select_object_format)

if st.session_state.GraphTypeSelect != "Select a Graph Type":
  #* Independent Variable
  with st.expander(label = "Independent Variable"):
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
      x_col_name = st.selectbox(label = "Select a Column", disabled = len(data_object_indices) == 0, options = ["No Variable Selected"] + sorted(intersection([set(st.session_state.data_objects[index].applications.keys()) | set(st.session_state.data_objects[index].responses.keys()) for index in data_object_indices])), label_visibility = "collapsed")
      x_col = st.session_state.data_objects[data_object_indices[0]].key_owner(x_col_name)[0][x_col_name] if x_col_name != "No Variable Selected" else ""
      #! x_col shouldn't be instantiated here, it should be 

    #* Variable Grouping
    if x_col_name != "No Variable Selected":
      #* Datetime type
      if x_col.dtype == np.dtype("datetime64[us]"):
        col1, col2 = st.columns([1.5, 10.5], gap = None)
        with col1:
          st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Groups:</div>", unsafe_allow_html = True)
        with col2:
          st.selectbox(label = "x_groups", disabled = x_col_name == "No Variable Selected", options = ["No Grouping Selected", "Yearly", "Monthly"], key = "x_groups", accept_new_options = False, label_visibility = "collapsed")
                                                                                                             #! Add in weekly and daily options
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
            case "Monthly":
              current_x_options = [(pd.Timestamp(f"{start_date.year + (i - 1)//12}/{(i - 1) % 12 + 1}/1"), pd.Timestamp(f"{start_date.year + (i - 1)//12}/{(i - 1) % 12 + 1}/{pd.Timestamp(f"{start_date.year + (i - 1)//12}/{(i - 1) % 12 + 1}/1").days_in_month}")) for i in range(start_date.month, 13 + max(end_date.year - start_date.year - 1, 0) * 12 + end_date.month)]
              def current_x_group_items_format(dates):
                return f"{dates[0].year}-{str(dates[0].month).zfill(2)}"
          st.multiselect(label = "current_x_group_items", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0, key = "current_x_group_items", options = current_x_options, label_visibility = "collapsed", format_func = current_x_group_items_format)

      #* Other (list, string, int)
      else:
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
            st.session_state.current_x_group_items = st.session_state.x_groups_dict[st.session_state.current_x_group]
          st.selectbox(label = "current_x_group", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0, key = "current_x_group", options = st.session_state.x_groups, accept_new_options = x_col_name != "No Variable Selected" and x_col.dtype != np.dtypes.ObjectDType, label_visibility = "collapsed", on_change = current_x_group_change)

        col1, col2 = st.columns([2, 10], gap = None)
        with col1:
          st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Group Items:</div>", unsafe_allow_html = True)
        with col2:
          def current_x_group_items_change():
            st.session_state.x_groups_dict[st.session_state.current_x_group] = set(st.session_state.current_x_group_items)
          st.multiselect(label = "current_x_group_items", disabled = x_col_name == "No Variable Selected" or len(st.session_state.x_groups) == 0, key = "current_x_group_items", options = sorted(set(val for val_list in x_col for val in val_list)) if x_col_name != "No Variable Selected" and x_col.dtype == np.dtypes.ObjectDType else [], accept_new_options = x_col_name != "No Variable Selected" and x_col.dtype != np.dtypes.ObjectDType, label_visibility = "collapsed", on_change = current_x_group_items_change)

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

      #* Scale
      col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Scale:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_scale = st.selectbox(label = "x_axis scale", label_visibility = "collapsed", options = ["Linear", "Log", "Symlog"])

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

      #* Scale
      col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Scale:</div>", unsafe_allow_html = True)
      with col2:
        y_axis_scale = st.selectbox(label = "y_axis_scale", label_visibility = "collapsed", options = ["Linear", "Log", "Symlog"])
      with col3:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Y-Axis Lines:</div>", unsafe_allow_html = True)
      with col4:
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
    col1, col2, col3, col4 = st.columns([3.5, 3, 1.75, 3.75], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px; {manual_legend_parameters_label_color};'>Manual Color Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      legend_new_colors_entry_type = st.selectbox(label = "legend_new_colors_entry_type", disabled = not (show_legend and manual_legend_entry_toggle), label_visibility = "collapsed", options = ["Multiple Entry", "Single Entry", "Color Map Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px; {manual_legend_parameters_label_color}'>Fill Colors:</div>", unsafe_allow_html = True)
    with col4:
      if legend_new_colors_entry_type == "Single Entry":
        legend_new_colors = st.color_picker(label = "Legend New Colors", disabled = not (show_legend and manual_legend_entry_toggle), label_visibility = "collapsed", value = None)
      if legend_new_colors_entry_type == "Multiple Entry":
        legend_new_colors = st.multiselect(label = "Legend New Colors", disabled = not (show_legend and manual_legend_entry_toggle), label_visibility = "collapsed", options = [], accept_new_options = True)
      if legend_new_colors_entry_type == "Color Map Entry":
        legend_new_colors = st.text_input(label = "Legend New Colors", disabled = not (show_legend and manual_legend_entry_toggle), label_visibility = "collapsed", value = "")

#* Bar Plot Specific  
if st.session_state.GraphTypeSelect in ["Bar Plot"]:
  with st.expander(label = "Bar Plot Specific"):
    #* Bar Fill Color
    col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      bar_fill_colors_entry_type = st.selectbox(label = "bar__fill_colors_entry_type", label_visibility = "collapsed", options = ["Multiple Entry", "Single Entry", "Color Map Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Fill Colors:</div>", unsafe_allow_html = True)
    with col4:
      if bar_fill_colors_entry_type == "Multiple Entry":
        bar_fill_colors = st.multiselect(label = "Fill Colors", label_visibility = "collapsed", options = [], accept_new_options = True)
      if bar_fill_colors_entry_type == "Single Entry":
        bar_fill_colors = st.color_picker(label = "Fill Colors", label_visibility = "collapsed", value = None)
      if bar_fill_colors_entry_type == "Color Map Entry":
        bar_fill_colors = st.text_input(label = "Fill Colors", label_visibility = "collapsed", value = "")

    #* Bar Edge Color
    col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      bar_edge_colors_entry_type = st.selectbox(label = "bar_edge_colors_entry_type", label_visibility = "collapsed", options = ["Multiple Entry", "Single Entry", "Color Map Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Edge Colors:</div>", unsafe_allow_html = True)
    with col4:
      if bar_edge_colors_entry_type == "Multiple Entry":
        bar_edge_colors = st.multiselect(label = "Edge Colors", label_visibility = "collapsed", options = [], placeholder = "None", accept_new_options = True)
      if bar_edge_colors_entry_type == "Single Entry":
        bar_edge_colors = st.color_picker(label = "Edge Colors", label_visibility = "collapsed", value = None)
      if bar_edge_colors_entry_type == "Color Map Entry":
        bar_edge_colors = st.text_input(label = "Edge Colors", label_visibility = "collapsed", value = "", placeholder = "None")

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
if st.session_state.GraphTypeSelect in ["Pie Chart"]:
  with st.expander(label = "Pie Chart Specific"):
    #* Wedge Fill Color
    col1, col2, col3, col4 = st.columns([2.5, 3.5, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Color Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      wedge_fill_colors_entry_type = st.selectbox(label = "wedge_fill_colors_entry_type", label_visibility = "collapsed", options = ["Multiple Entry", "Single Entry", "Color Map Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Fill Colors:</div>", unsafe_allow_html = True)
    with col4:
      if wedge_fill_colors_entry_type == "Multiple Entry":
        wedge_fill_colors = st.multiselect(label = "Wedge Fill Colors", label_visibility = "collapsed", options = [], accept_new_options = True)
      if wedge_fill_colors_entry_type == "Single Entry":
        wedge_fill_colors = st.color_picker(label = "Wedge Fill Colors", label_visibility = "collapsed", value = None)
      if wedge_fill_colors_entry_type == "Color Map Entry":
        wedge_fill_colors = st.text_input(label = "Wedge Fill Colors", label_visibility = "collapsed", value = "")

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

# Made for formatting graphs made with Plotly
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

#* Graphing
if st.session_state.GraphTypeSelect != "Select a Graph Type" and x_col_name != "No Variable Selected" and (len([i2 for i in st.session_state.x_groups_dict.values() for i2 in i if i2 != ""]) > 0 or (x_col.dtype == np.dtype("datetime64[us]") and len(st.session_state.current_x_group_items) > 0)): #! Make sure to include conditional len(y_groups)
  st.button(label = "Click to Reload Graph")
  
  fig, ax = plt.subplots(1, 1, figsize = (figure_width, figure_height))

  ax.set_title(label = textwrap.fill(figure_title, width = max(len(figure_title), 1) if figure_title_width == None else figure_title_width))
  
  match st.session_state.GraphTypeSelect:
    case "Bar Plot":
      def bar_group_sizes():
        bar_kwargs = {"height" : [], "x" : [], "label" : st.session_state.x_groups_dict, "facecolor" : interpret_colors(bar_fill_colors, len(st.session_state.x_groups_dict), bar_fill_colors_entry_type), "edgecolor" : interpret_colors(bar_edge_colors, len(st.session_state.x_groups_dict), bar_edge_colors_entry_type) if len(bar_edge_colors) > 0 else None}
        match type(st.session_state.data_objects[data_object_indices[0]].key_owner(x_col_name)[0].dtypes[x_col_name]):
          case np.dtypes.ObjectDType:
            bar_kwargs["height"] = [len([col for col in x_col if len(group & set(col)) > 0]) for group in st.session_state.x_groups_dict.values()]
            bar_kwargs["x"] = [float(tick) for tick in bar_tick_marks.replace(" ", "").split(",")] if bar_tick_marks != "" and len(bar_tick_marks.replace(" ", "").split(",")) == len(bar_kwargs["height"]) else range(len(bar_kwargs["height"]))
          case pd.StringDtype:
            bar_kwargs["height"] = [len([col for col in x_col if type(col) != float and re.search("|".join(group), col, flags = re.IGNORECASE)]) if len(group) > 0 else 0 for group in st.session_state.x_groups_dict.values()]
            bar_kwargs["x"] = [float(tick) for tick in bar_tick_marks.replace(" ", "").split(",")] if bar_tick_marks != "" and len(bar_tick_marks.replace(" ", "").split(",")) == len(bar_kwargs["height"]) else range(len(bar_kwargs["height"]))
          case np.dtypes.DateTime64DType:
            start_date = min(x_col)
            end_date = max(x_col)
            match st.session_state.x_groups:
              case "Yearly":
                bar_kwargs["height"] = [sum((pd.Timestamp(f"{year}/01/01") <= x_col) & (x_col <= pd.Timestamp(f"{year}/12/31"))) for year in st.session_state.current_x_group_items]
                bar_kwargs["x"] = [float(tick) for tick in bar_tick_marks.replace(" ", "").split(",")] if bar_tick_marks != "" and len(bar_tick_marks.replace(" ", "").split(",")) == len(bar_kwargs["height"]) else range(len(bar_kwargs["height"]))
                bar_kwargs["label"] = st.session_state.current_x_group_items
                bar_kwargs["facecolor"] = interpret_colors(bar_fill_colors, end_date.year - start_date.year + 1, bar_fill_colors_entry_type)
                bar_kwargs["edgecolor"] = interpret_colors(bar_edge_colors, end_date.year - start_date.year + 1, bar_edge_colors_entry_type) if len(bar_edge_colors) > 0 else None
              case "Monthly":
                bar_kwargs["height"] = [sum((bounds[0] <= x_col) & (x_col <= bounds[1])) for bounds in st.session_state.current_x_group_items]
                bar_kwargs["x"] = [float(tick) for tick in bar_tick_marks.replace(" ", "").split(",")] if bar_tick_marks != "" and len(bar_tick_marks.replace(" ", "").split(",")) == len(bar_kwargs["height"]) else range(len(bar_kwargs["height"]))
                bar_kwargs["label"] = [f"{dates[0].year}-{str(dates[0].month).zfill(2)}" for dates in st.session_state.current_x_group_items]
                bar_kwargs["facecolor"] = interpret_colors(bar_fill_colors, len(st.session_state.current_x_group_items), bar_fill_colors_entry_type)
                bar_kwargs["edgecolor"] = interpret_colors(bar_edge_colors, len(st.session_state.current_x_group_items), bar_edge_colors_entry_type) if len(bar_edge_colors) > 0 else None
        return bar_kwargs
      
      ax.bar(**bar_group_sizes(), width = bar_width, log = False)

    case "Pie Chart":
      def wedge_group_sizes():
        wedge_kwargs = {"x" : [], "labels" : st.session_state.x_groups_dict, "colors" : interpret_colors(wedge_fill_colors, len(st.session_state.x_groups_dict), wedge_fill_colors_entry_type)}
        match type(st.session_state.data_objects[data_object_indices[0]].key_owner(x_col_name)[0].dtypes[x_col_name]):
          case np.dtypes.ObjectDType:
            wedge_kwargs["x"] = [len([col for col in x_col if len(group & set(col)) > 0]) for group in st.session_state.x_groups_dict.values()]
            wedge_kwargs["labels"] = [f"{name}{"\n" if pie_percent_label or pie_number_label else ""}{f"{wedge_kwargs["x"][i] / sum(wedge_kwargs["x"]) * 100:.1f}" + "%" if pie_percent_label else ""}{" " if pie_percent_label and pie_number_label else ""}{"(" + f"{wedge_kwargs["x"][i]:,}" + ")" if pie_number_label else ""}" for i, name in enumerate(st.session_state.x_groups_dict.keys())]
          case pd.StringDtype:
            wedge_kwargs["x"] = [len([col for col in x_col if type(col) != float and re.search("|".join(group), col, flags = re.IGNORECASE)]) if len(group) > 0 else 0 for group in st.session_state.x_groups_dict.values()]
            wedge_kwargs["labels"] = [f"{name}{"\n" if pie_percent_label or pie_number_label else ""}{f"{wedge_kwargs["x"][i] / sum(wedge_kwargs["x"]) * 100:.1f}" + "%" if pie_percent_label else ""}{" " if pie_percent_label and pie_number_label else ""}{"(" + f"{wedge_kwargs["x"][i]:,}" + ")" if pie_number_label else ""}" for i, name in enumerate(st.session_state.x_groups_dict.keys())]
          case np.dtypes.DateTime64DType:
            start_date = min(x_col)
            end_date = max(x_col)
            match st.session_state.x_groups:
              case "Yearly":
                wedge_kwargs["x"] = [sum((pd.Timestamp(f"{year}/01/01") <= x_col) & (x_col <= pd.Timestamp(f"{year}/12/31"))) for year in st.session_state.current_x_group_items]
                wedge_kwargs["labels"] = [f"{year}{"\n" if pie_percent_label or pie_number_label else ""}{f"{wedge_kwargs["x"][i] / sum(wedge_kwargs["x"]) * 100:.1f}" + "%" if pie_percent_label else ""}{" " if pie_percent_label and pie_number_label else ""}{"(" + f"{wedge_kwargs["x"][i]:,}" + ")" if pie_number_label else ""}" for i, year in enumerate(st.session_state.current_x_group_items)]
                wedge_kwargs["colors"] = interpret_colors(wedge_fill_colors, end_date.year - start_date.year + 1, wedge_fill_colors_entry_type)
              case "Monthly":
                wedge_kwargs["x"] = [sum((bounds[0] <= x_col) & (x_col <= bounds[1])) for bounds in st.session_state.current_x_group_items]
                wedge_kwargs["labels"] = [f"{dates[0].year}-{str(dates[0].month).zfill(2)}" for dates in st.session_state.current_x_group_items]
                wedge_kwargs["colors"] = interpret_colors(wedge_fill_colors, len(st.session_state.current_x_group_items), wedge_fill_colors_entry_type)
        return wedge_kwargs

      ax.pie(**wedge_group_sizes(), wedgeprops = {"width" : wedge_width}, textprops = {"fontsize" : pie_label_font_size}, startangle = wedge_starting_angle, counterclock = pie_rotation == "Counterclockwise")

  #* X-Axis Formatting
  if st.session_state.GraphTypeSelect not in ["Pie Chart"]:
    ax.set_xlabel(x_axis_label)
    ax.set_xlim(left = x_axis_left_lim, right = x_axis_right_lim)
    ax.set_xscale(x_axis_scale.lower())
    if x_axis_tick_marks not in ["", None]:
      x_ticks = interpret_ticks(x_axis_tick_marks, x_axis_tick_marks_type)
      ax.set_xticks(x_ticks, labels = None if len(x_axis_tick_labels) == 0 else x_axis_tick_labels[:len(x_ticks)] + [""] * max(len(x_ticks) - len(x_axis_tick_labels), 0))
    if len(x_axis_tick_labels) == 0:
      ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}" if x.is_integer() else f"{x:g}"))

  #* Y-Axis Formatting
  if st.session_state.GraphTypeSelect not in ["Pie Chart"]:
    ax.set_ylabel(y_axis_label)
    ax.set_ylim(bottom = y_axis_bottom_lim, top = y_axis_top_lim)
    ax.set_yscale(y_axis_scale.lower())
    if y_axis_tick_marks not in ["", None]:
      y_ticks = interpret_ticks(y_axis_tick_marks, y_axis_tick_marks_type)
      ax.set_yticks(y_ticks, labels = None if len(y_axis_tick_labels) == 0 else y_axis_tick_labels[:len(y_ticks)] + [""] * max(len(y_ticks) - len(y_axis_tick_labels), 0))
    if len(y_axis_tick_labels) == 0:
      ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{int(y):,}" if y.is_integer() else f"{y:g}"))
    if y_axis_grid_lines:
      ax.grid(axis = 'y')
      ax.set_axisbelow(True)

  if show_legend:
    legend_kwargs = {}

    if legend_xpos != None and legend_ypos != None:
      legend_kwargs["bbox_to_anchor"] = (legend_xpos, legend_ypos)
      legend_kwargs["loc"] = "upper left"

    if manual_legend_entry_toggle:
      legend_kwargs["handles"] = [Line2D([], [], marker = "o", linestyle = "", color = color, label = text) for text, color in zip(legend_new_labels, interpret_colors(legend_new_colors, len(legend_new_labels), legend_new_colors_entry_type))]

    fig.legend(ncols = legend_ncols, **legend_kwargs)
  
  st.pyplot(fig, width = "content")