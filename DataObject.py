import re
import copy
import pandas as pd
import streamlit as st

st.session_state.setdefault("FilterInclusionToggle", None)
st.session_state.setdefault("FilterNoneToggle", None)

def datesToDatetime(df, sample_size = 10, threshold = 3):
  for key in df.keys():
    if type(df[key].dtype) == pd.StringDtype:
      sample = df[key].dropna().iloc[:sample_size]
      if len(sample) == 0:
        continue
      # if "date" in key:
      #   print(sample)
      converted = pd.to_datetime(sample, format = "%Y-%m-%d", errors = "coerce")
      success_rate = converted.notna().mean()
      # print(f"{key} : {success_rate}")
      if success_rate >= threshold / sample_size:
        df[key] = pd.to_datetime(df[key], format = "%Y-%m-%d", errors = "coerce")
      else: #! Delete this part once we get the real datasets form the website, this just handles different formatting from my/your dataset construction
        converted = pd.to_datetime(sample, format = "%m/%d/%Y", errors = "coerce")
        success_rate = converted.notna().mean()
        # print(f"{key} : {success_rate}")
        if success_rate >= threshold / sample_size:
          df[key] = pd.to_datetime(df[key], format = "%m/%d/%Y", errors = "coerce")
  return df

class DataObject:
  def __init__(self, name, applications, responses):
    self.name = name
    self.applications = datesToDatetime(applications)
    self.responses = datesToDatetime(responses)
    self.filter_history = [] # Each element in the list is {"filter_code" : filter_code, "dataset" : dataset, "column" : column, "include_values" : include_values, "include_None" : include_none} + additional kwargs
  
  @classmethod
  def from_dataobject(self, name: str, dataobject):
    return self(name, copy.deepcopy(dataobject.applications), copy.deepcopy(dataobject.responses))

  def key_owner(self, key) -> list:
    """
    Takes a key and produces the owner of the key. Checks the applications dataset first.

    Args:
      key (Any): The key to be matched to a dataset
    
    Returns:
      list (pandas.DataFrame): The owner(s) dataset, the applicatiosn dataset will be first if both datasets are owners
    """
    owners = []
    if key in self.applications:
      owners.append(self.applications)
    if key in self.responses:
      owners.append(self.responses)

    if len(owners) == 0:
      raise KeyError(f"'{key}' is not a key in either the applications or responses dataset")
    return owners

  def key_owner_name(self, key) -> str:
    """
    Takes a key and produces the name of the owner(s) of the key.

    Args:
      key (Any): The key to be matched to a dataset
    
    Returns:
      str: The name of the owner dataset, produces "Both" if both are the owners
    """
    match (key in self.applications, key in self.responses):
      case (True, True):
        return "Both"
      case (True, False):
        return "applications"
      case (False, True):
        return "responses"
      case _:
        raise KeyError(f"'{key}' is not a key in either the applications or responses dataset")

  def filter_owner(self, key, mask): #! There may be an issue regarding the changes to key_owner_name(), specifically with the addition of "Both"
    if self.key_owner_name(key) == "applications":
      pre_filter_applications = self.applications
      self.applications = self.applications[mask]
      removed = set(pre_filter_applications["application_id"]) - set(self.applications["application_id"])
      self.responses = self.responses[~self.responses["application_id"].isin(removed)]
    else:
      pre_filter_responses = self.responses
      self.responses = self.responses[mask]
      removed = set(pre_filter_responses["application_id"]) - set(self.responses["application_id"])
      self.applications = self.applications[~self.applications["application_id"].isin(removed)]
    # print(self.filter_history)
  
  def remove_from_owner(self, key, list_strings_target):
    if key in self.applications:
      self.applications = self.applications[~self.applications[key].isin(list_strings_target)]
    if key in self.responses:
      self.responses = self.responses[~self.responses[key].isin(list_strings_target)]
  
  def add_action_history(self, filter_code: str, dataset, column, **kwargs) -> None:
    """
    Updates the DataObject's filtration history. It also updates the other datasets that weren't directly filtered

    Args:
      dataset (str): The name of the dataset used (applications, responses, etc).
      column (any): The name of the column the filter was applied to. Likely a string.
      **kwargs: Any keyword arguments relevent to the method of filtration. Each method will have its own standard format.
    """
    self.filter_history.append({"filter_code" : filter_code, "dataset" : dataset, "column" : column} | kwargs)
  
  def undo(self) -> list:
    """
    Removes the last (most recent) recorded filtration action from the list and returns it

    Args:
      None:
    
    Returns:
      list:
        [filter_type (str), [arg1, arg2, etc]]
    """
    filter_removed = self.filter_history[-1]
    self.filter_history.pop()
    return filter_removed
  
  def filtration_actions_string(self) -> str:
    """
    Produces a string representing the recorded filtration actions. The produced string is formatted: "filter_type (arg1, arg2, etc) | filter_type (arg1, arg2, etc) | ..."

    Args:
      None:

    Returns:
      str:
        String representation of the filtration actions recorded in the list
    """
    return str(self.filter_history)[1:-1]


def string_replace(replace_data_object_index, replace_col, *args):
  obj = st.session_state.data_objects[replace_data_object_index]
  st.session_state.ReplaceStringAreaTarget = ""
  st.session_state.ReplaceStringAreaNew = ""
  string_area_target, string_area_new = args
  list_strings_target = string_area_target.split("|")
  list_strings_new = string_area_new.split("|")

  for dataset in obj.key_owner(replace_col):
    column = obj.key_owner(replace_col)[0][replace_col]
    if st.session_state.ReplaceNoneToggle:
      if st.session_state.ReplaceRemoveToggle:
        dataset = dataset.fillna(value = {column : list_strings_new[0]})
      else:
        dataset = dataset.dropna(subset = column)
    else:
      if st.session_state.ReplaceRemoveToggle:
        dataset.replace(to_replace = list_strings_target, value = list_strings_new, inplace = True)
      else:
        # dataset = dataset[~dataset[replace_col].isin([list_strings_target])]
        # dataset = dataset[dataset[replace_col] != list_strings_target[0]]
        obj.remove_from_owner(replace_col, list_strings_target)

  match (st.session_state.ReplaceNoneToggle, st.session_state.ReplaceRemoveToggle):
    case (True, True):
      st.toast(body = f"Empty entries successfully replaced with '{list_strings_new[0]}' in {obj.name}'")
    case (True, False):
      st.toast(body = f"Empty entries successfully from {obj.name}'")
    case (False, True):
      st.toast(body = f"Successfully replaced the selected values in {replace_col} in {obj.name}'")
    case (False, False):
      st.toast(body = f"Successfully removed the chosen entries from {obj.name}'")


def string_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.FilterStringArea = ""
  string_area, = args
  list_strings = []
  mask = pd.Series(False, index = column.index)

  for string in string_area.split("|"):
    list_strings.append(string.strip())

  if st.session_state.FilterInclusionToggle: # A True value indicates inclusivity
    if st.session_state.FilterExactStringToggle: # True indicates filtering for the exact string(s), false allows for strings containing a target string
      if st.session_state.FilterCaseSensitivityToggle: # True indicates case-sensitivity, False insensitivity
        mask |= column.isin(list_strings)
      else:
        mask |= column.str.lower().isin([string.lower() for string in list_strings])
    else:
      mask |= column.str.contains("|".join(map(re.escape, list_strings)), case = st.session_state.FilterCaseSensitivityToggle, na = False)
  else:
    if st.session_state.FilterExactStringToggle:
      if st.session_state.FilterCaseSensitivityToggle:
        mask |= ~column.isin(list_strings)
      else:
        mask |= ~column.str.lower().isin([string.lower() for string in list_strings])
    else:
      mask |= ~column.str.contains("|".join(map(re.escape, list_strings)), case = st.session_state.FilterCaseSensitivityToggle, na = False)

  if st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")

def int_bounds_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.IntLowerBound = None
  st.session_state.IntUpperBound = None
  int_lower_bound, int_upper_bound = args

  if st.session_state.FilterInclusionToggle:
    mask = pd.Series(True, index = column.index)
    if int_upper_bound:
      mask &= column <= int_upper_bound
    if int_lower_bound:
      mask &= column >= int_lower_bound
  else:
    mask = pd.Series(False, index = column.index)
    if int_upper_bound:
      mask |= column > int_upper_bound
    if int_lower_bound:
      mask |= column < int_lower_bound

  if st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")

def int_values_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.IntArea = ""
  int_area, = args
  int_values = [int(num) for num in int_area.replace(" ", "").split(",")]
  mask = pd.Series(False, index = column.index)

  if st.session_state.FilterInclusionToggle:
    mask |= column.isin(int_values)
  else:
    mask |= ~column.isin(int_values)

  if st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")

def date_bounds_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.DateEarlierBound = None
  st.session_state.DateLaterBound = None
  date_earlier_bound, date_later_bound = args

  if date_earlier_bound:
    date_earlier_timestamp = pd.Timestamp(f"{str(date_earlier_bound.year).zfill(4)}-{str(date_earlier_bound.month).zfill(2)}-{str(date_earlier_bound.day).zfill(2)}")
  if date_later_bound:
    date_later_timestamp = pd.Timestamp(f"{str(date_later_bound.year).zfill(4)}-{str(date_later_bound.month).zfill(2)}-{str(date_later_bound.day).zfill(2)}") + pd.Timedelta(days = 1)

  if st.session_state.FilterInclusionToggle:
    mask = pd.Series(True, index = column.index)
    if date_earlier_bound:
      mask &= column >= date_earlier_timestamp
    if date_later_bound:
      mask &= column < date_later_timestamp
  else:
    mask = pd.Series(False, index = column.index)
    if date_earlier_bound:
      mask |= column < date_earlier_timestamp
    if date_later_bound:
      mask |= column >= date_later_timestamp
  if st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")

def date_values_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.DateArea = ""
  date_area, = args
  date_values = [pd.Timestamp(date) for date in date_area.replace(" ", "").replace("\n", "").split(",")]
  mask = pd.Series(False, index = column.index)

  if st.session_state.FilterInclusionToggle:
    mask |= column.isin(date_values)
  else:
    mask |= ~column.isin(date_values)

  if st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")