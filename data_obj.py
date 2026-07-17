import copy
import numpy as np
import pandas as pd
import streamlit as st
import DataObject as do
import matplotlib.pyplot as plt

st.session_state.setdefault("master_data", None)
st.session_state.setdefault("data_objects", [])

st.header("Managing Data Objects")

upload_datasets_expander = st.expander(label = "Upload Datasets")

with upload_datasets_expander:
  def master_data_uploaders_on_change():
    if (st.session_state.applications_entry is not None and st.session_state.responses_entry is not None):
      st.session_state.master_data = do.DataObject("Master", pd.read_csv(st.session_state.applications_entry), pd.read_csv(st.session_state.responses_entry))
    else:
      st.session_state.master_data = None
  
  applications_entry = st.file_uploader(label = "Upload the applications dataset", max_upload_size = 2000, on_change = master_data_uploaders_on_change, key = "applications_entry") 
  responses_entry = st.file_uploader(label = "Upload the responses dataset", max_upload_size = 2000, on_change = master_data_uploaders_on_change, key = "responses_entry")

creation_expander = st.expander(label = "Create a Data Object", key = "DataObjectExpander")

with creation_expander:
  creation_name_input = st.text_input(label = "Name", key = "DataObjectName", placeholder = "Enter data object name", disabled = applications_entry is None or responses_entry is None)
  
  def creation_button_on_click():
    st.session_state.DataObjectName = ""
    if creation_name_input not in [obj.name for obj in st.session_state.data_objects]:
      st.session_state.data_objects.append(do.DataObject.from_dataobject(creation_name_input, st.session_state.master_data))
      st.toast(body = f"DataObject '{creation_name_input}' successfully created")
    else:
      st.toast(body = f"'{creation_name_input}' is the name of an existing DataObject")

  obj_creation_button = st.button(label = "Create Object", disabled = applications_entry is None or responses_entry is None, on_click = creation_button_on_click)

data_view_expander = st.expander("View Datasets", key = "DataViewer")

with data_view_expander:
  def data_viewer_formatting(data):
    if type(data) == str:
      return data
    else:
      return data["name"][:data["name"].rfind(".")]
  
  if st.session_state.master_data is not None:
    data_viewer_selection = st.selectbox(label = "Select a dataset to view", 
                                        options = ["No Selection"] + [data for obj in st.session_state.data_objects + [st.session_state.master_data] for data in [{"name" : f"{obj.name}: applications", "data" : obj.applications}, {"name" : f"{obj.name}: responses", "data" : obj.responses}]],
                                        format_func = data_viewer_formatting, key = "DataViewerSelecter",
                                        disabled = applications_entry is None and responses_entry is None)
    if data_viewer_selection != "No Selection":
      st.dataframe(data_viewer_selection["data"])
  else:
    st.text("Both an applications dataset and a responses dataset are required to be uploaded before any datsetsa can be viewed")