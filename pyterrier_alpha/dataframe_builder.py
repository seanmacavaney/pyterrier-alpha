from typing import Optional

import numpy as np
import pandas as pd


class DataFrameBuilder:
    def __init__(self, columns):
        self._data = {c: [] for c in columns}

    def extend(self, values):
        assert all(c in values.keys() for c in self._data), f"all columns must be provided: {list(self._data)}"
        lens = {k: len(v) for k, v in values.items() if hasattr(v, '__len__') and not isinstance(v, str)}
        if any(lens):
            first_len = list(lens.values())[0]
        else:
            first_len = 1 # if nothing has a len, everything is gien a length of 1
        assert all(l == first_len for l in lens.values()), f"all values must have the same length {lens}"
        for k, v in values.items():
            if k not in lens:
                self._data[k].append([v] * first_len)
            elif isinstance(v, pd.Series):
                self._data[k].append(v.values)
            else:
                self._data[k].append(v)

    def to_df(self, merge_on_index: Optional[pd.DataFrame] = None):
        result = pd.DataFrame({
            k: np.concatenate(v)
            for k, v in self._data.items()
        })
        if merge_on_index is not None:
            assert '_index' in result
            merge_on_index = merge_on_index.reset_index(drop=True)
            result = result.assign(**{
                col: merge_on_index[col].iloc[result['_index']].values
                for col in merge_on_index.columns
                if col not in result.columns
            }).drop(columns=['_index'])
            merge_columns = set(merge_on_index.columns)
            column_order = list(merge_on_index.columns) + [c for c in result.columns if c not in merge_columns]
            result = result[column_order]
        return result
