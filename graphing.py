import re
import math
import textwrap
import numpy as np
import pandas as pd
import DataObject as d
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

st.session_state.setdefault("data_objects", [])

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

st.header("Graphing")

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
  st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px; color: #{"646464" if st.session_state.GraphTypeSelect == "Select a Graph Type" else "ffffff"}'>Data Objects:</div>", unsafe_allow_html = True) #Remove|<span style = 'color: red;'><u>Replace</u></span>
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
    col1, col2 = st.columns([1.5, 10.5], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Grouping:</div>", unsafe_allow_html = True)
    with col2:
      active = x_col_name != "No Variable Selected"
      groups = st.multiselect(label = "Select column groups", disabled = x_col_name == "No Variable Selected", options = sorted(set(val for val_list in x_col for val in val_list)) if active and x_col.dtype == np.dtypes.ObjectDType else [], accept_new_options = active and x_col.dtype != np.dtypes.ObjectDType, label_visibility = "collapsed")

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
      figure_title_width = st.number_input(label = "figure title width", value = None, step = 1, label_visibility = "collapsed")

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
        x_col_name = st.selectbox(label = "x-axis tick marks type", disabled = len(data_object_indices) == 0, options = ["Manual", "Range", "Log Range"], label_visibility = "collapsed")
      with col3:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px;'>Tick Marks:</div>", unsafe_allow_html = True) #Remove|<span style = 'color: red;'><u>Replace</u></span>
      with col4:
        x_axis_tick_marks = st.text_input(label = "x-axis tick marks", label_visibility = "collapsed", placeholder = "0, 2, 4, ...")

      #* Left/Right Limits
      col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Left Limit:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_left_lim = st.number_input(label = "x_axis left lim", label_visibility = "collapsed", value = None)
      with col3:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Right Limit:</div>", unsafe_allow_html = True)
      with col4:
        x_axis_right_lim = st.number_input(label = "x_axis right lim", label_visibility = "collapsed", value = None)

      #* Scale
      col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
      with col1:
        st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Scale:</div>", unsafe_allow_html = True)
      with col2:
        x_axis_scale = st.selectbox(label = "x_axis scale", label_visibility = "collapsed", options = ["linear", "log", "symlog"])
      # with col3:
      #   st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Right Limit:</div>", unsafe_allow_html = True)
      # with col4:
      #   x_axis_right_lim = st.number_input(label = "x_axis right lim", label_visibility = "collapsed", value = None)

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
      legend_new_colors_entry_type = st.selectbox(label = "legend_new_colors_entry_type", disabled = not (show_legend and manual_legend_entry_toggle), label_visibility = "collapsed", options = ["Single Entry", "Multiple Entry", "Color Map Entry"])
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
  with st.expander(label = "Bar Plot-Specific"):
    #* Bin Fill Color
    col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      bin_fill_colors_entry_type = st.selectbox(label = "bin__fill_colors_entry_type", label_visibility = "collapsed", options = ["Single Entry", "Multiple Entry", "Color Map Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Fill Color:</div>", unsafe_allow_html = True)
    with col4:
      if bin_fill_colors_entry_type == "Single Entry":
        bin_fill_colors = st.color_picker(label = "Fill Colors", label_visibility = "collapsed", value = None)
      if bin_fill_colors_entry_type == "Multiple Entry":
        bin_fill_colors = st.multiselect(label = "Fill Colors", label_visibility = "collapsed", options = [], accept_new_options = True)
      if bin_fill_colors_entry_type == "Color Map Entry":
        bin_fill_colors = st.text_input(label = "Fill Colors", label_visibility = "collapsed", value = None)

    #* Bin Edge Color
    col1, col2, col3, col4 = st.columns([2, 4, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      bin_edge_colors_entry_type = st.selectbox(label = "bin_edge_colors_entry_type", label_visibility = "collapsed", options = ["Single Entry", "Multiple Entry", "Color Map Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Edge Color:</div>", unsafe_allow_html = True)
    with col4:
      if bin_edge_colors_entry_type == "Single Entry":
        bin_edge_colors = st.color_picker(label = "Edge Colors", label_visibility = "collapsed", value = None)
      if bin_edge_colors_entry_type == "Multiple Entry":
        bin_edge_colors = st.multiselect(label = "Edge Colors", label_visibility = "collapsed", options = [], accept_new_options = True)
      if bin_edge_colors_entry_type == "Color Map Entry":
        bin_edge_colors = st.text_input(label = "Edge Colors", label_visibility = "collapsed", value = None)

#* Pie Chart Specific
if st.session_state.GraphTypeSelect in ["Pie Chart"]:
  with st.expander(label = "Pie Chart-Specific"):
    #* Wedge Fill Color
    col1, col2, col3, col4 = st.columns([2.5, 3.5, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Color Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      wedge_fill_colors_entry_type = st.selectbox(label = "wedge_fill_colors_entry_type", label_visibility = "collapsed", options = ["Multiple Entry", "Single Entry", "Color Map Entry"])
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Fill Colors:</div>", unsafe_allow_html = True)
    with col4:
      if wedge_fill_colors_entry_type == "Single Entry":
        wedge_fill_colors = st.color_picker(label = "Wedge Fill Colors", label_visibility = "collapsed", value = None)
      if wedge_fill_colors_entry_type == "Multiple Entry":
        wedge_fill_colors = st.multiselect(label = "Wedge Fill Colors", label_visibility = "collapsed", options = [], accept_new_options = True)
      if wedge_fill_colors_entry_type == "Color Map Entry":
        wedge_fill_colors = st.text_input(label = "Wedge Fill Colors", label_visibility = "collapsed", value = "")

    #* Wedge Width (Central Gap)
    col1, col2= st.columns([2.5, 9.5], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Wedge Width</div>", unsafe_allow_html = True)
    with col2:
      wedge_width = st.number_input(label = "wedge_width", value = 1., min_value = 0.0, step = 0.01, max_value = 1.0, label_visibility = "collapsed")


# Made for formatting a plotly graph
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
if st.session_state.GraphTypeSelect != "Select a Graph Type" and x_col_name != "No Variable Selected" and len(groups) > 0:
  st.button(label = "Click to Reload Graph")
  
  fig, ax = plt.subplots(1, 1, figsize = (figure_width, figure_height))

  ax.set_title(label = textwrap.fill(figure_title, width = max(len(figure_title), 1) if figure_title_width == None else figure_title_width))
  
  match st.session_state.GraphTypeSelect:
    case "Bar Plot":
      st.text("Bar Plot")

    case "Pie Chart":
      ax.pie([len([col for col in x_col if group in col]) for group in groups], labels = groups, wedgeprops = {"width" : wedge_width}, colors = interpret_colors(wedge_fill_colors, len(groups), wedge_fill_colors_entry_type))

  if show_legend:
    legend_kwargs = {}
    if legend_xpos != None and legend_ypos != None:
      legend_kwargs["bbox_to_anchor"] = (legend_xpos, legend_ypos)
      legend_kwargs["loc"] = "upper left"
    if manual_legend_entry_toggle:
      legend_kwargs["handles"] = [Line2D([], [], marker = "o", linestyle = "", color = color, label = text) for text, color in zip(legend_new_labels, interpret_colors(legend_new_colors, len(legend_new_labels), legend_new_colors_entry_type))]
    fig.legend(ncols = legend_ncols, **legend_kwargs)
  
  st.pyplot(fig, width = "content")