import copy
import pandas as pd

def datesToDatetime(df, sample_size = 10, threshold = 3):
  for key in df.keys():
    if type(df[key].dtype) == pd.StringDtype:
      sample = df[key].dropna().iloc[:sample_size]
      if len(sample) == 0:
        continue
      converted = pd.to_datetime(sample, format = "%Y-%m-%d", errors = "coerce")
      success_rate = converted.notna().mean()
      if success_rate >= threshold / sample_size:
        df[key] = pd.to_datetime(df[key], format = "%Y-%m-%d", errors = "coerce")
  return df

class DataObject:
  def __init__(self, name, applications, responses):
    self.name = name
    self.applications = datesToDatetime(applications)
    self.responses = datesToDatetime(responses)
    self.filter_history = [] # Each element{"filter_code":filtration_type_code, "dataset":dataset, "column":column, "arg1":arg1, "arg2":arg2, etc}
  
  @classmethod
  def from_dataobject(self, name: str, dataobject):
    return self(name, copy.deepcopy(dataobject.applications), copy.deepcopy(dataobject.responses))

  def key_owner(self, key) -> list:
    """
    Takes a key and produces the owner of the key. Checks the applications dataset first.

    Args:
      key (Any): The key to be matched to a dataset
    
    Returns:
      pandas.DataFrame: The owner dataset
    """
    if key in self.applications:
      return self.applications
    elif key in self.responses:
      return self.responses
    else:
      raise KeyError(f"'{key}' is not a key in either the applications or responses dataset")

  def key_owner_name(self, key) -> list:
    """
    Takes a key and produces the owner of the key. Checks the applications dataset first.

    Args:
      key (Any): The key to be matched to a dataset
    
    Returns:
      pandas.DataFrame: The owner dataset
    """
    if key in self.applications:
      return "applications"
    elif key in self.responses:
      return "responses"
    else:
      raise KeyError(f"'{key}' is not a key in either the applications or responses dataset")

  def filter_owner(self, key, mask, *args, **kwargs): # NEED TO FILTER OTHER DATASET AS WELL, FILTER HISTORY
    self.filter_history.append({"filter_code" : args[0], "dataset" : args[1], "column" : args[2]} | kwargs)
    if self.key_owner_name(key) == "applications":
      self.applications = self.applications[mask]
    else:
      self.responses = self.responses[mask]
    print(self.filter_history)

  
  def add_filter_history(self, dataset: str, column: any, **kwargs) -> None:
    """
    Updates the DataObject's filtration history. It also updates the other datasets that weren't directly filtered

    Args:
      dataset (str): The name of the dataset used (applications, responses, etc).
      column (any): The name of the column the filter was applied to. Likely a string.
      **kwargs: Any keyword arguments relevent to the method of filtration. Each method will have its own standard format.
    """
    # match dataset:
    #   case "applications":
    #     self.responses = pd.merge(self.applications, self.responses)
    #   case "responses":
    #     self.applications = pd.merge(self.applications, self.responses)

    filter = {"dataset" : dataset, "column" : column}
    for key, val in kwargs.items():
      filter[key] = val
    self.filter_history.append(filter)
  
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
    string = ""
    for action in self.filter_history:
      string.append(str(action).replace("'","")[1:-1] + "\n")
    return string[:-1]