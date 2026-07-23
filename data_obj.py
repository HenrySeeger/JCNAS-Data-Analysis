import copy
import numpy as np
import pandas as pd
import streamlit as st
import DataObject as do
from pyproj import Transformer
import matplotlib.pyplot as plt

st.session_state.setdefault("master_data", None)
st.session_state.setdefault("data_objects", [])

OSGB36_to_WGS84_transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy = True) # OSGB -> lat/long

st.header("Managing Data Objects")

with st.expander(label = "Upload Datasets"):
  # If both the applications and responses datasets have been uploaded, create the master DataObject from them.
  # If at least one is missing the master DataObject is set to None.
  def master_data_uploaders_on_change():
    if (st.session_state.applications_entry is not None and st.session_state.responses_entry is not None):
      st.session_state.applications_entry.seek(0)
      st.session_state.responses_entry.seek(0)
      st.session_state.master_data = do.DataObject("Master", pd.read_csv(st.session_state.applications_entry), pd.read_csv(st.session_state.responses_entry))
    else:
      st.session_state.master_data = None
  
  if "applications_entry" not in st.session_state or st.session_state.applications_entry is None: # REMOVE THE KEY FROM THE FILE_UPLOADER, SET A SESSION STATE EQUAL TO ITS OUTPUT
    st.session_state.applications_entry = st.file_uploader(label = "Upload the applications dataset", max_upload_size = 2000) 
    if st.session_state.applications_entry is not None:
      master_data_uploaders_on_change()
      st.rerun()
  else:
    col1, col2 = st.columns(2)
    with col1:
      st.text(f"Applications Dataset: {st.session_state.applications_entry.name}")
    with col2:
      if st.button(label = "Upload New Applications Dataset"):
        st.session_state.applications_entry = None
        master_data_uploaders_on_change()
        st.rerun()

  
  if "responses_entry" not in st.session_state or st.session_state.responses_entry is None: # REMOVE THE KEY FROM THE FILE_UPLOADER, SET A SESSION STATE EQUAL TO ITS OUTPUT
    st.session_state.responses_entry = st.file_uploader(label = "Upload the responses dataset", max_upload_size = 2000)
    if st.session_state.responses_entry is not None:
      master_data_uploaders_on_change()
      st.rerun()
  else:
    col1, col2 = st.columns(2)
    with col1:
      st.text(f"Responses Dataset: {st.session_state.responses_entry.name}")
    with col2:
      if st.button(label = "Upload New Responses Dataset"):
        st.session_state.responses_entry = None
        master_data_uploaders_on_change()

def osbg_letters_to_nums(letters):
  """
  Takes a string of two letters and converts it to positional coordinates based on the British Ordinance Survey National Grid (OSNG)

  Args:
    letters (str):
      Two letters indicating a position in the OSNG (any two letter combintaion, excluding 'I' or 'i').
      The letters should be capitalized, but the function uses `to_upper()`.
  
  Returns:
    set (integer):
      Two integers indicating where in the matrix the given letters are located and returns their position relative to the origin 'SV', where up and right are positive directions.
      The letters are given in the order (Easting, Northing), akin to x and y coordinates.
  """
  twenty_five_letters = [chr(i) for i in list(range(65, 73)) + list(range(74, 91))] # Removes the letter 'I'
  five_letters = [[char for char in twenty_five_letters[i:5 + i]] for i in range(0, 25, 5)] # Converts list of 25 letters to list of lists of 5 letter pair[[A,B,C,D,E],[F,G,H,J,K],...]
  letter_coords = [[first + second for first in five_letters[i//5] for second in five_letters[i%5]] for i in range(25)] # Creates full 5x5 matrix of 5x5 sub-matrices (25x25)
  for i in range(25): # Locates where in the matrix the given letters are located and returns their position relative to the origin 'SV', where up and right are positive directions
    try:
      return letter_coords[i].index(letters) - 10, 19 - i
    except:
      continue

def jcnas_to_osbg(coords):
  """
  Takes a coordinate in OSBG format and converts it to decimal latitude and longitude

  Args:
    coords (str):
      A string formatted "CC ##### #####", where 'C' is a character and '#' is a number.
      Neither character should be an 'I'.
  
  Returns:
    set (float):
      A set containing the decimal latitude and longitude in that order
  """
  prefixes = osbg_letters_to_nums(coords[:2])

  easting = int(f"{prefixes[0]}{coords[coords.index(" ") + 1:coords.rfind(" ")]}")
  northing = int(f"{prefixes[1]}{coords[coords.rfind(" ") + 1:]}")

  lon, lat = OSGB36_to_WGS84_transformer.transform(easting, northing)

  return lat, lon

with st.expander(label = "Create a Data Object"):
  creation_name_input = st.text_input(label = "Name", key = "DataObjectName", placeholder = "Enter data object name", disabled = st.session_state.applications_entry is None or st.session_state.responses_entry is None)
  
  # Creates a new DataObject with deep copies of the the master DataObject's datasets if the provided name isn't already being used.
  # The user is alerted as to the success or failure of creating a new DataObject
  def creation_button_on_click():
    st.session_state.DataObjectName = ""
    if creation_name_input not in [obj.name for obj in st.session_state.data_objects]:
      st.session_state.data_objects.append(do.DataObject.from_dataobject(creation_name_input, st.session_state.master_data))
      st.toast(body = f"DataObject '{creation_name_input}' successfully created")
    else:
      st.toast(body = f"'{creation_name_input}' is the name of an existing DataObject")

  obj_creation_button = st.button(label = "Create Object", disabled = st.session_state.applications_entry is None or st.session_state.responses_entry is None, on_click = creation_button_on_click)

with st.expander(label = "Manage Data Objects"):
  def data_manager_formatting(data):
    return data if type(data) == str else data.name
  data_manager_data_selector = st.selectbox(label = "Select a data object",
                                            options = ["No Selection", "option2"] + st.session_state.data_objects,
                                            format_func = data_manager_formatting,
                                            disabled = st.session_state.applications_entry is None or st.session_state.responses_entry is None)
  
  data_manager_options = st.selectbox(label = "Manage Options",
                                      options = ["No Selection", "Delete", "Rename"],
                                      disabled = st.session_state.applications_entry is None or st.session_state.responses_entry is None or data_manager_data_selector == "No Selection")

  if data_manager_data_selector != "No Selection":
    match data_manager_options:
      case "Delete":
        data_delete_confirmation = st.toggle(label = f"Confirm deletion of {data_manager_data_selector}", value = False)

        def delete_data(data):
          print("temp")
          # Add an st.toast() declaring success or failure
        data_delete_button = st.button(f"Delete {data_manager_data_selector}", disabled = not data_delete_confirmation, on_click = delete_data)
      case "Rename":
        def rename_data(data):
          print("temp")
          # Add an st.toast() declaring success or failure
        data_new_name_text = st.text_input(label = "Enter New Name:")
        if data_new_name_text != "":
          st.text(f"Rename '{data_manager_data_selector}' to '{data_new_name_text}'")
          st.button(label = "Rename")
  else:
    data_manager_options = "No Selection"
    st.text(data_manager_options)


with st.expander(label = "View Datasets"):
  # Lets the user directly view (but not edit) the datasets of any DataObjects created, as well the master DataObject
  # Selecting 'No Selection' closes any open viewer
  # All master datasets must uploaded before this can be used, text will inform the user if they are missing one or more master datasets
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