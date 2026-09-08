import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.session_state.setdefault("data_objects", [])

st.header("Graphing")

for i, col in enumerate(st.columns([3, 11], gap = None)):
  with col:
    if i == 0:
      st.markdown("<div style='padding-top: 5.5px;'>Select a Graph Type:</div>", unsafe_allow_html = True)
    else:
      st.selectbox(label = "Select graph type", options = ["Select a Graph Type", "Bar Plot"], label_visibility = "collapsed", key = "GraphTypeSelect", disabled = len(st.session_state.data_objects) == 0)

"" # Adds a vertical space on the page

def select_object_format(num):
      return num if type(num) == str else st.session_state.data_objects[num].name

if st.session_state.GraphTypeSelect != "Select a Graph Type":
  st.subheader(body = "Graph Parameters")

  #* Data Object Selector
  col1, col2 = st.columns([2, 10], gap = None)
  with col1:
    st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15.0px;'>Data Objects:</div>", unsafe_allow_html = True) #Remove|<span style = 'color: red;'><u>Replace</u></span>
  with col2:
    data_object_index = st.multiselect(label = "Select an X-Axis Data Object", options = list(range(len(st.session_state.data_objects))), label_visibility = "collapsed", default = None, format_func = select_object_format)
  
  #* Variable and Label Selection
  with st.expander(label = "x-axis"):
    col1, col2, col3, col4 = st.columns([2, 4, 1.25, 4.75], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Variable:</div>", unsafe_allow_html = True)
    with col2:
      def intersection(sets):
        if len(sets) == 0:
          return {}
        rtn = set(sets[0])
        for s in sets[1:]:
          rtn = rtn & s
        return rtn
      x_axis_column = st.selectbox(label = "Select an X-Axis Column", disabled = len(data_object_index) == 0, options = ["No Variable Selected"] + sorted(intersection([set(st.session_state.data_objects[index].applications.keys()) | set(st.session_state.data_objects[index].responses.keys()) for index in data_object_index])), label_visibility = "collapsed")
    with col3:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Label:</div>", unsafe_allow_html = True)
    with col4:
      x_axis_label = st.text_input(label = "x_axis_label", label_visibility = "collapsed", placeholder = "Axis Label")

    #* Tick Marks
    col1, col2, col3, col4 = st.columns([2.25, 3.75, 2, 4], gap = None)
    with col1:
      st.markdown(f"<div style='padding-top: 6.5px; text-align: right; padding-right: 15px;'>Tick Entry Type:</div>", unsafe_allow_html = True)
    with col2:
      x_axis_column = st.selectbox(label = "x-axis tick marks type", disabled = len(data_object_index) == 0, options = ["Manual", "Range", "Log Range"], label_visibility = "collapsed")
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


match st.session_state.GraphTypeSelect:
  case "Bar Plot":
    st.text("Bar Plot")