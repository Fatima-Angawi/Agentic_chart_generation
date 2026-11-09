import pandas as pd

def get_profile_data(df):
  profile = {
      "statistical_summary" : df.describe(),
      "data_types" : df.dtypes,
      "missing_values" : df.isnull().sum(),
      "unique_values" : df.nunique(),
      "column_names" : df.columns.tolist(),
      "rows" : len(df)

  }
  return profile

def get_dataframe_schema(df: pd.DataFrame) -> dict:
    """Automatically extract column names and data types."""
    return {col: str(dtype) for col, dtype in df.dtypes.items()}
