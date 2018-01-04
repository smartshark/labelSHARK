import pandas as pd
from sklearn.base import TransformerMixin


def map_mongo_to_pandas(query_set):
    """Converts mongoengine QuerySet to pandas dataframe for data analysis."""

    raw_documents = query_set.as_pymongo()
    df = pd.DataFrame(list(raw_documents))

    return df


class DataFrameColumnExtracter(TransformerMixin):
    def __init__(self, column):
        self.column = column

    def fit(self,  x, y=None):
        return self

    def transform(self, df):
        if isinstance(df[self.column], str):
            return df[self.column]
        else:
            return df[self.column].values.astype('U')