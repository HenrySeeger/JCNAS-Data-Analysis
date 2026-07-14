import pandas as pd

class DataObject:
  def __init__(self, name, applications, responses):
    self.name = name
    self.applications = applications
    self.responses = responses