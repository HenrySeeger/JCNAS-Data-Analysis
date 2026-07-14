import numpy as np
import pandas as pd
import streamlit as st
import DataObject as do
import matplotlib.pyplot as plt

st.header("Managing Data Objects")

upload_datasets_expander = st.expander(label = "Upload Datasets")

with upload_datasets_expander:
  applications_entry = st.file_uploader(label = "Upload the applications dataset")
  if applications_entry is not None:
    st.text(f"Applications Dataset Source: {applications_entry.name}")
  responses_entry = st.file_uploader(label = "Upload the responses dataset")
  if responses_entry is not None:
    st.text(f"Responses Dataset Source: {responses_entry.name}")

creation_expander = st.expander(label = "Create a Data Object", key = "DataObjectExpander")

with creation_expander:
  st.text_input(label = "Name", key = "DataObjectName", placeholder = "Enter data object name", disabled = applications_entry is None or responses_entry is None)
  st.button(label = "Create Object", disabled = applications_entry is None or responses_entry is None)