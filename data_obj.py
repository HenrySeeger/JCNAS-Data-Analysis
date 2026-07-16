import copy
import numpy as np
import pandas as pd
import streamlit as st
import DataObject as do
import matplotlib.pyplot as plt

st.session_state.setdefault("app_data_master", {"name" : None, "data" : None})
st.session_state.setdefault("res_data_master", {"name" : None, "data" : None})
st.session_state.setdefault("data_objects", {})

st.header("Managing Data Objects")

upload_datasets_expander = st.expander(label = "Upload Datasets")

with upload_datasets_expander:
  applications_entry = st.file_uploader(label = "Upload the applications dataset", max_upload_size = 2000)
  if applications_entry is not None and st.session_state.app_data_master["name"] is not applications_entry.name:
      st.session_state.app_data_master["name"] = applications_entry.name
      st.session_state.app_data_master["data"] = pd.read_csv(applications_entry)
  
  responses_entry = st.file_uploader(label = "Upload the responses dataset", max_upload_size = 2000)
  if responses_entry is not None and st.session_state.res_data_master["name"] is not responses_entry.name:
      st.session_state.res_data_master["name"] = responses_entry.name
      st.session_state.res_data_master["data"] = pd.read_csv(responses_entry)

creation_expander = st.expander(label = "Create a Data Object", key = "DataObjectExpander")

with creation_expander:
  creation_name_input = st.text_input(label = "Name", key = "DataObjectName", placeholder = "Enter data object name", disabled = applications_entry is None or responses_entry is None)
  
  def creation_button_on_click():
    if creation_name_input not in st.session_state.data_objects.keys():
      st.session_state.data_objects[creation_name_input] = do.DataObject(creation_name_input, copy.deepcopy(st.session_state.app_data_master), copy.deepcopy(st.session_state.res_data_master))

  st.button(label = "Create Object", disabled = applications_entry is None or responses_entry is None, on_click = creation_button_on_click)

data_view_expander = st.expander("View Datasets", key = "DataViewer")

with data_view_expander:
  def data_viewer_formatting(data):
    if type(data) == str:
      return data
    else:
      return data["name"][:data["name"].rfind(".")]
  
  data_viewer_selection = st.selectbox(label = "Select a dataset to view", options = ["No Selection"] + [data for data in [st.session_state.app_data_master, st.session_state.res_data_master] if data["name"] is not None], format_func = data_viewer_formatting, key = "DataViewerSelecter", disabled = applications_entry is None and responses_entry is None)
  if data_viewer_selection != "No Selection":
    st.dataframe(data_viewer_selection["data"])