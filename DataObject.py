import re
import sys
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
    self.action_history = [] # Each element in the list is {"filter_code" : filter_code, "dataset" : dataset, "column" : column, "include_values" : include_values, "include_None" : include_none} + additional kwargs
  
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
      str: The name of the owner dataset, produces "both" if both are the owners
    """
    match (key in self.applications, key in self.responses):
      case (True, True):
        return "both"
      case (True, False):
        return "applications"
      case (False, True):
        return "responses"
      case _:
        raise KeyError(f"'{key}' is not a key in either the applications or responses dataset")

  def filter_owner(self, key, mask):
    if self.key_owner_name(key) in ["applications", "both"]:
      pre_filter_applications = self.applications
      self.applications = self.applications[mask]
      removed = set(pre_filter_applications["application_id"]) - set(self.applications["application_id"])
      self.responses = self.responses[~self.responses["application_id"].isin(removed)]
    else:
      pre_filter_responses = self.responses
      self.responses = self.responses[mask]
      removed = set(pre_filter_responses["application_id"]) - set(self.responses["application_id"])
      self.applications = self.applications[~self.applications["application_id"].isin(removed)]
  
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
    self.action_history.append({"filter_code" : filter_code, "dataset" : dataset, "column" : column} | kwargs)
  
  def undo(self) -> list:
    """
    Removes the last (most recent) recorded filtration action from the list and returns it

    Args:
      None:
    
    Returns:
      list:
        [filter_type (str), [arg1, arg2, etc]]
    """
    filter_removed = self.action_history[-1]
    self.action_history.pop()
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
    return str(self.action_history)[1:-1]


def string_values_replace(replace_data_object_index, replace_col, *args):
  obj = st.session_state.data_objects[replace_data_object_index]
  st.session_state.ReplaceStringSelectionsTarget = []
  st.session_state.ReplaceStringSelectionsNew = []
  list_target, list_new = args

  for dataset in obj.key_owner(replace_col):
    match (st.session_state.ReplaceNoneToggle, st.session_state.ReplaceInclusionToggle, st.session_state.ReplaceCaseSensitiveToggle):
      case (True, True, True) | (True, True, False):
        dataset.fillna(value = {replace_col : list_new[0]}, inplace = True)
      case (True, False, True) | (True, False, False):
        dataset.loc[dataset[replace_col] is not None, replace_col] = list_new[0]
      case (False, True, True):
        dataset.replace(to_replace = {replace_col : {target : new for target, new in zip(list_target, list_new)}}, inplace = True)
      case (False, True, False):
        for target, new in zip(list_target, list_new):
          dataset[replace_col] = dataset[replace_col].str.replace(target, new, case = False)
      case (False, False, True):
        dataset.loc[~dataset[replace_col].isin(list_target), replace_col] = list_new[0]
      case (False, False, False):
        dataset.loc[~dataset[replace_col].str.lower().isin(list_target), replace_col] = list_new[0]

  st.toast(body = f"Successfully replaced entries in '{obj.name}'")

def values_replace(replace_data_object_index, replace_col, *args): #* Int and Date
  obj = st.session_state.data_objects[replace_data_object_index]
  st.session_state.ReplaceIntSelectionsTarget = []
  st.session_state.ReplaceIntSelectionsNew = []
  st.session_state.ReplaceDateSelectionsTarget = []
  st.session_state.ReplaceDateSelectionsNew = []
  list_target, list_new = args

  for dataset in obj.key_owner(replace_col):
    match (st.session_state.ReplaceNoneToggle, st.session_state.ReplaceInclusionToggle):
      case (True, True):
        dataset.fillna(value = {replace_col : list_new[0]}, inplace = True)
      case (True, False):
        dataset.loc[dataset[replace_col] is not None, replace_col] = list_new[0]
      case (False, True):
        dataset.replace(to_replace = {replace_col : {target : new for target, new in zip(list_target, list_new)}}, inplace = True)
      case (False, False):
        dataset.loc[~dataset[replace_col].isin(list_target), replace_col] = list_new[0]

  st.toast(body = f"Successfully replaced entries in '{obj.name}'")

def bounds_replace(replace_data_object_index, replace_col, *args):
  obj = st.session_state.data_objects[replace_data_object_index]
  st.session_state.ReplaceIntLowerBound = None
  st.session_state.ReplaceIntUpperBound = None
  st.session_state.ReplaceIntNewBound = None
  st.session_state.ReplaceDateEarlierBound = None
  st.session_state.ReplaceDateLaterBound = None
  st.session_state.ReplaceDateNewBound = None
  lower_bound, upper_bound, replace_bound = args

  for dataset in obj.key_owner(replace_col):
    match(st.session_state.ReplaceNoneToggle, st.session_state.ReplaceInclusionToggle):
      case (True, True): # Replace empty entries
        dataset.fillna(value = {replace_col : replace_bound})
      case (True, False): # Replace non-empty entries
        dataset.loc[dataset[replace_col] != None] = replace_bound
      case (False, True): # Replace bounded entries
        dataset.loc[(True if lower_bound is None else lower_bound <= dataset[replace_col]) & 
                    (True if upper_bound is None else upper_bound >= dataset[replace_col]), replace_col] = replace_bound
      case (False, False): # Replace entries outside the bounds
        dataset.loc[(True if lower_bound is None else lower_bound > dataset[replace_col]) |
                    (True if upper_bound is None else upper_bound < dataset[replace_col]), replace_col] = replace_bound

  st.toast(body = f"Successfully replaced entries in '{obj.name}'")


def string_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.FilterStringSelections = []
  list_strings, = args
  mask = pd.Series(False, index = column.index)

  if len(list_strings) != 0:
    if not st.session_state.FilterOrGateToggle:
      match (st.session_state.FilterExactStringToggle, st.session_state.FilterCaseSensitiveToggle):
        case (True, True):
          for string in list_strings:
            mask |= column.isin(string)
        case (True, False):
          for string in list_strings:
            mask |= column.str.lower().isin(string.lower())
        case (False, True) | (False, False):
          for string in list_strings:
            mask |= column.str.contains(string, case = st.session_state.FilterCaseSensitiveToggle, na = False)

      if not st.session_state.FilterInclusionToggle:
        mask = ~mask

    else:
      match (st.session_state.FilterInclusionToggle, st.session_state.FilterExactStringToggle, st.session_state.FilterCaseSensitiveToggle):
        case (True, True, True):
          mask |= column.isin(list_strings)
        case (True, True, False):
          mask |= column.str.lower().isin([string.lower() for string in list_strings])
        case (True, False, True) | (True, False, False):
          mask |= column.str.contains("|".join(list_strings), case = st.session_state.FilterCaseSensitiveToggle, na = False)
        case (False, True, True):
          mask |= ~column.isin(list_strings)
        case (False, True, False):
          mask |= ~column.str.lower().isin([string.lower() for string in list_strings])
        case (False, False, True) | (False, False, False):
          mask |= ~column.str.contains("|".join(list_strings), case = st.session_state.FilterCaseSensitiveToggle, na = False)
      
  if not st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")

def int_bounds_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.FilterIntLowerBound = None
  st.session_state.FilterIntUpperBound = None
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

  if not st.session_state.FilterNoneToggle:
    mask |= column.isna()      

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")

def int_values_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.FilterIntSelections = []
  int_selections, = args
  int_selections = [int(num) for num in int_selections]
  mask = pd.Series(False, index = column.index)

  if st.session_state.FilterInclusionToggle:
    mask |= column.isin(int_selections)
  else:
    mask |= ~column.isin(int_selections)

  if not st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")

def date_bounds_filter(filter_data_object_index, filter_col, *args):
  dataset = st.session_state.data_objects[filter_data_object_index]
  column = dataset.key_owner(filter_col)[0][filter_col]
  st.session_state.FilterDateEarlierBound = None
  st.session_state.FilterDateLaterBound = None
  date_earlier_bound, date_later_bound = args

  if date_earlier_bound:
    date_earlier_timestamp = pd.Timestamp(date_earlier_bound)
  if date_later_bound:
    date_later_timestamp = pd.Timestamp(date_later_bound) + pd.Timedelta(days = 1)

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
  st.session_state.FilterDateSelections = []
  date_area, = args
  date_area = [pd.Timestamp(date) for date in date_area]
  mask = pd.Series(False, index = column.index)

  if st.session_state.FilterInclusionToggle:
    mask |= column.isin(date_area)
  else:
    mask |= ~column.isin(date_area)

  if st.session_state.FilterNoneToggle:
    mask |= column.isna()

  dataset.filter_owner(filter_col, mask)
  st.toast(body = f"'{dataset.name}' successfully filtered")


def period_or_date_to_charities(df):
  def normalize_period(col):
    col = col.fillna("")
    col = col.str.strip()

    # HTML entities that appear in the source
    col = col.str.replace(r"&amp;", "&", regex = True)
    col = col.str.replace(r"&#039;", "'", regex = True)

    # Normalize whitespace
    col = col.str.replace(r"\s+", " ", regex = True)

    # Common inconsistencies or apparent OCR errors
    col = col.str.replace(r"\bCl(\d)", r"C1\1", regex = True)     # Cl9  -> C19
    col = col.str.replace(r"\bl(\d{3})", r"1\1", regex = True)    # l851 -> 1851
    col = col.str.replace(r"\bI(\d{3})", r"1\1", regex = True)    # I800 -> 1800
    col = col.str.replace(r"\b(\d{3})O\b", r"\g<1>0", regex = True)  # 184O -> 1840
    col = col.str.replace(r"\b(\d{4}s*[-–]\s*\d{1,3})O\b", r"\g<1>0", regex = True)  # 185O-6O -> 1850-60
    col = col.str.replace(r"\bC\s+(\d{1,2})", r"C\1", regex = True, flags=re.I) # C 17 -> C17

    return col

  def expand_year_range(range_text):
    start_text, end_text = re.split(r"\s*[-–]\s*", range_text)

    end_is_bc = "bc" in end_text
    start_is_bc = "bc" in start_text or end_is_bc

    start_text = start_text.replace("bc", "")
    end_text = end_text.replace("bc", "")

    start = int(start_text) * (-1 if start_is_bc else 1)
    end = int(end_text) * (-1 if end_is_bc else 1)

    if len(end_text) < len(start_text):
      end = int(start_text[:len(start_text) - len(end_text)] + end_text)

    return [start, end]

  def cent_to_range(century, is_bc):
    if is_bc:
      century[1] *= -1
    match century[0]:
      case "early":
        century = [century[1], century[1] + 33]
      case "mid":
        century = [century[1] + 33, century[1] + 66]
      case "late":
        century = [century[1] + 66, century[1] + 99]
      case "early-mid":
        century = [century[1] + 17, century[1] + 50]
      case "mid-late":
        century = [century[1] + 50, century[1] + 83]
      case "":
        century = [century[1], century[1] + 99]
    if is_bc:
      century[0] *= -1
      century[1] *= -1
    return century

  df['period_or_date'] = normalize_period(df['period_or_date'])

  patterns = {"range" : r"\b(?:ad|bc)?\d{2,4}(?:ad|bc)?\s*[-–]\s*(?:ad|bc)?\d{1,4}\s*(?:ad|bc)?\b",
              "approx" : r"\b(?:c\.?|circa|about)\s*\d{3,4}(?:|ad|bc)?\b",
              "decade" : r"\bc?(\d{3,4}s)\b",
              "century" : r"(?<![-\d.])\b(?P<qualifier>early[-\s]*mid|mid[-\s]*late|early|mid|late|)\s*(?P<century>c?\s*\d{1,2}c?(?:st|nd|rd|th)?c?|\d{1,2}(?:st|nd|rd|th)\s+centur(?:y|ies))\s*-?\s*(?P<period>bc)?\b",
              "year" : r"\b(?<!-)\d{3,4}\b(?!\s*-\s*\d)",
              "other" : r"media?eval|pre[\s-]?media?eval|georgian|victorian|edwardian|anglo[\s-]?saxon|iron[\s-]?age|neolithic|prehistoric|roman|modern|bronze[\s-]?age|post[\s-]?war|middle[\s-]?ages?|norman"}#|archaeolog(?:ical|y)"}

  # Create DataFrame of extracted text
  merged_df = pd.DataFrame({"period_or_date" : df["period_or_date"]} | {key : df["period_or_date"].str.findall(value, re.IGNORECASE) for key, value in patterns.items()})

  # Standardizes the century column qualifiers and converts year text to an int which is the first year of the century (e.g. ["Early Mid", "C18"] -> ["early-mid", 1700])
  merged_df["century"] = merged_df["century"].map(lambda centuries: [[re.sub(r"[\s-]+", "-", century[0].lower()), (1 if century[2] == "" else -1) * (int(re.search(r"\d{1,2}", century[1]).group()) * 100 - 100)] for century in centuries])

  # Removes any version of 'ad' (as in 'AD or 'BC') from the ranges
  merged_df["range"] = merged_df["range"].map(lambda ranges: [range.lower().replace("ad", "").replace(" ", "") for range in ranges])

  # Put into the 'range' column        range text -> int range                               decade text -> int range                                   century+qualifier text -> int range
  merged_df["range"] = [[expand_year_range(range) for range in ranges] + [[int(decade[:-1]), int(decade[:-2]) * 10 + 9] for decade in decades] + [cent_to_range(century, century[1] < 0) for century in centuries] for ranges, decades, centuries in zip(merged_df["range"], merged_df["decade"], merged_df["century"])]
  merged_df.drop(columns = ["decade"], inplace = True)
  merged_df.drop(columns = ["century"], inplace = True)

  # Puts approximations into years and uses sets (briefly) to ensure there aren't duplicates
  merged_df["year"] = [list(set([int(year) for year in years] + [(-1 if "bc" in approx.lower() else 1) * int(re.search(r"\d{3,4}", approx)[0]) for approx in approxes])) for years, approxes in zip(merged_df["year"], merged_df["approx"])]
  merged_df.drop(columns = ["approx"], inplace = True)

  # Replace all ' ' with '-' in the 'other' column
  merged_df["other"] = merged_df["other"].map(lambda others: [other.lower().replace(" ", "-") for other in others])

  charity_bounds = pd.DataFrame({"charity" : ["spab", "georgian", "victorian", "c20"],
                                 "bounds"  : [[-sys.maxsize - 1, 1720], [1715, 1840], [1837, 1914], [1913, sys.maxsize]]})

  time_period_reference_table = {"neolithic" : ["spab"],
                                 "iron-age" : ["spab"],
                                 "bronze-age" : ["spab"],
                                 "prehistoric" : ["spab"],
                                 "roman" : ["spab"],
                                 "pre-medieval" : ["spab"],
                                 "pre-mediaeval" : ["spab"],
                                 "medieval" : ["spab"],
                                 "mediaeval" : ["spab"],
                                 "norman" : ["spab"],
                                 "middle-ages" : ["spab"],
                                 "anglo-saxon" : ["spab"],
                                 "georgian" : ["georgian"],
                                 "victorian" : ["victorian"],
                                 "edwardian" : ["victorian"],
                                 "postwar" : ["c20"],
                                 "post-war" : ["c20"],
                                 "modern" : ["c20"]}

  for charity, bounds in zip(charity_bounds["charity"], charity_bounds["bounds"]):
    merged_df[charity] = [[charity] if [range for range in ranges if range[0] < bounds[1] and range[1] > bounds[0]] or
                                       [year for year in years if bounds[0] < year and year < bounds[1]] or
                                       [other for other in others if charity in time_period_reference_table[other.lower()]] else []
                          for ranges, years, others in zip(merged_df["range"], merged_df["year"], merged_df["other"])]

  df["charities"] = [s + g + v + c for g, s, v, c in zip(merged_df["spab"], merged_df["georgian"], merged_df["victorian"], merged_df["c20"])]

def green_keywords(df):
  green_terms_table = {"climate_change_adaptation" : r"climate[-\s]resilience|climate[-\s]adaptation|adaptation[-\s]measures|resilience[-\s]measures|future[-\s]proofing|flood[-\s]resilience|flood[-\s]resistance|overheating[-\s]mitigation|thermal[-\s]comfort|sustainable[-\s]drainage|rainwater[-\s]management|surface[-\s]water[-\s]management|water[-\s]efficiency|drought[-\s]resilience|green[-\s]infrastructure|biodiversity[-\s]enhancement|nature[-\s]based[-\s]solutions",
                       "energy_efficiency" : r"energy[-\s]efficiency[-\s]improvements|thermal[-\s]upgrade|fabric[-\s]first[-\s]approach|building[-\s]fabric[-\s]improvements|insulation|secondary[-\s]glazing|draught[-\s]proofing|airtightness|heat[-\s]loss[-\s]reduction|thermal[-\s]performance|u[-\s]value|building[-\s]performance|energy[-\s]demand[-\s]reduction|retrofit|sensitive[-\s]retrofit|deep[-\s]retrofit|whole[-\s]building[-\s]retrofit",
                       "decarbonisation" : r"decarboni[sz]ation|net[-\s]zero|low[-\s]carbon|zero[-\s]carbon|carbon[-\s]reduction|carbon[-\s]emissions|operational[-\s]carbon|embodied[-\s]carbon|whole[-\s]life[-\s]carbon|carbon[-\s]footprint|carbon[-\s]savings|carbon[-\s]neutral|carbon[-\s]assessment",
                       "renewable_energy" : r"solar[-\s]pv|solar[-\s]panels|solar[-\s]slates|solar[-\s]roof[-\s]tiles|air[-\s]source[-\s]heat[-\s]pump|ground[-\s]source[-\s]heat[-\s]pump|heat[-\s]network|renewable[-\s]energy|low[-\s]carbon[-\s]heating|clean[-\s]energy|battery[-\s]storage|electric[-\s]vehicle[-\s]charging",
                       "heritage_and_conservation_langauge" : r"heritage[-\s]significance|significance|conservation[-\s]led[-\s]approach|minimal[-\s]intervention|reversible[-\s]intervention|like[-\s]for[-\s]like[-\s]repair|sensitive[-\s]alteration|heritage[-\s]impact|conservation[-\s]principles|historic[-\s]fabric|fabric[-\s]retention|less[-\s]than[-\s]substantial[-\s]harm|public[-\s]benefits|sustainable[-\s]conservation",
                       "sustainability" : r"sustainable[-\s]development|environmental[-\s]sustainability|sustainable[-\s]design|circular[-\s]economy|reuse|repair|longevity|durability|resource[-\s]efficiency|life[-\s]cycle[-\s]assessment|sustainable[-\s]materials|natural[-\s]materials|low[-\s]impact[-\s]development",
                       "policy_references" : r"climate[-\s]emergency|net[-\s]zero[-\s]strategy|local[-\s]plan[-\s]climate[-\s]policies|national[-\s]planning[-\s]policy[-\s]framework|nppf|historic[-\s]england[-\s]guidance|pas[-\s]2035[-\s](retrofit)|energy[-\s]performance[-\s]certificate|epc|whole[-\s]house[-\s]plan",
                       "general_accessibility" : r"accessibility|improved[-\s]access|inclusive[-\s]access|inclusive[-\s]design|equal[-\s]access|universal[-\s]design|step[-\s]free[-\s]access|accessible[-\s]entrance|improved[-\s]circulation|enhanced[-\s]accessibility|improved[-\s]usability|accessible[-\s]route|barrier[-\s]free[-\s]access|ease[-\s]of[-\s]access|access[-\s]improvements",
                       "physical_alterations" : r"ramp|access[-\s]ramp|platform[-\s]lift|passenger[-\s]lift|wheelchair[-\s]lift|stair[-\s]lift|new[-\s]lift[-\s]shaft|level[-\s]threshold|dropped[-\s]kerb|handrails|guardrails|new[-\s]steps|wider[-\s]doorway|automatic[-\s]doors|power[-\s]assisted[-\s]doors|entrance[-\s]alterations|new[-\s]entrance|accessible[-\s]wc|changing[-\s]places[-\s]toilet|internal[-\s]reconfiguration|wayfinding|signage|tactile[-\s]paving|tactile[-\s]signage|hearing[-\s]loop|automatic[-\s]opening[-\s]system",
                       "disability_and_inclusion" : r"disabled[-\s]access|wheelchair[-\s]access|mobility[-\s]impaired|people[-\s]with[-\s]disabilities|inclusive[-\s]environment|accessibility[-\s]for[-\s]all|independent[-\s]access|equal[-\s]opportunities|dementia[-\s]friendly|neurodiverse[-\s]users|visual[-\s]impairment|hearing[-\s]impairment",
                       "legislation_and_guidance" : r"equality[-\s]act[-\s]2010|approved[-\s]document[-\s]m|building[-\s]regulations[-\s]part[-\s]m|bs[-\s]8300|inclusive[-\s]design[-\s]guidance|historic[-\s]england[-\s]guidance[-\s]on[-\s]improving[-\s]access|access[-\s]statement|design[-\s]and[-\s]access[-\s]statement",
                       "heritage_language" : r"sensitive[-\s]intervention|minimal[-\s]intervention|reversible[-\s]works|heritage[-\s]significance|conservation[-\s]led[-\s]design|historic[-\s]fabric|less[-\s]than[-\s]substantial[-\s]harm|public[-\s]benefit|balanced[-\s]approach|proportionate[-\s]response",
                       "home_improvement_and_quality_of_life" : r"improved[-\s]living[-\s]accommodation|enhanced[-\s]living[-\s]conditions|improved[-\s]quality[-\s]of[-\s]life|better[-\s]use[-\s]of[-\s]space|modernisation|improved[-\s]functionality|contemporary[-\s]living|flexible[-\s]living|family[-\s]living|open[-\s]plan[-\s]living|adaptation[-\s]to[-\s]modern[-\s]living|better[-\s]circulation|improved[-\s]layout|rationalised[-\s]layout|increased[-\s]comfort|enhanced[-\s]amenity|increased[-\s]enjoyment[-\s]of[-\s]the[-\s]property",
                       "growing_or_changing_families" : r"family[-\s]needs|growing[-\s]family|additional[-\s]accommodation|extra[-\s]bedroom|home[-\s]office|study|playroom|multi[-\s]functional[-\s]space|flexible[-\s]accommodation|multi[-\s]generational[-\s]living|independent[-\s]living|annex|adaptable[-\s]accommodation|lifetime[-\s]home",
                       "health_and_wellbeing" : r"wellbeing|health[-\s]and[-\s]wellbeing|improved[-\s]natural[-\s]light|daylighting|ventilation|improved[-\s]ventilation|better[-\s]outlook|garden[-\s]access|outdoor[-\s]living|private[-\s]amenity[-\s]space|connection[-\s]to[-\s]the[-\s]garden|improved[-\s]comfort|reduced[-\s]overheating|quiet[-\s]enjoyment",
                       "ageing_and_future_needs" : r"future[-\s]proofing|lifetime[-\s]living|ageing[-\s]in[-\s]place|accessible[-\s]accommodation|adaptable[-\s]home|single[-\s]storey[-\s]living|ground[-\s]floor[-\s]bedroom|ground[-\s]floor[-\s]bathroom|mobility[-\s]needs",
                       "leisure_and_lifestyle" : r"garden[-\s]room|conservatory|orangery|outdoor[-\s]entertaining|home[-\s]gym|hobby[-\s]room|cinema[-\s]room|recreation|lifestyle[-\s]enhancement",
                       "working_from_home" : r"home[-\s]office|remote[-\s]working|hybrid[-\s]working|dedicated[-\s]workspace|workspace|home[-\s]working|flexible[-\s]workspace",
                       "energy_and_comfort" : r"improved[-\s]thermal[-\s]comfort|energy[-\s]efficiency|reduced[-\s]energy[-\s]bills|increased[-\s]comfort|improved[-\s]indoor[-\s]environment|sustainable[-\s]living"}

  df["green_keywords"] = [[category for category, pattern in green_terms_table.items() if re.search(pattern, text, flags = re.IGNORECASE)] for text in df["fdescription"]]

