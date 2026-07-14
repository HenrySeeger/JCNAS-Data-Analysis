import pandas as pd

class DataObject:
  def __init__(self, name, applications, responses):
    self.name = name
    self.applications = applications
    self.responses = responses
    self.filter_history = [] # [[filter_type, [arg1, arg2, etc]], [filter_type, [arg1, arg2]]]
  
  def key_owner(self, key) -> list:
    """
    Takes a key and produces a list of all the contained datasets with the owner in the 0 index position. Checks the applications dataset first.

    Args:
      key (Any): The key to be matched to a dataset
    
    Returns:
      list (pandas.DataFrame): A list with the owner dataset in the first position
    """
    if key in self.applications:
      return [self.applications, self.responses]
    elif key in self.responses:
      return [self.responses, self.applications]
    else:
      raise KeyError(f"'{key}' is not a key in either the applications or responses dataset")
  

  def add_filter_history(self, filter_type: str, *args) -> None:
    self.filter_history.append([filter_type, args])
  
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
      string.append(f"{action[0]} ({str(action[1])[1:-1]}) | ")
    return string[:-3]