"""Utility to build a DataFrame from a sequence of dictionaries."""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class DataFrameBuilder:
    """Utility to build a DataFrame from a sequence of dictionaries.

    .. versionadded:: 0.1.0

    The dictionaries must have the same keys, and the values must be either scalars, or lists of the same length.
    """
    def __init__(self, columns: List[str]):
        """Create a DataFrameBuilder with the given columns.

        Args:
            columns: the columns of the resulting DataFrame, required to be present in each
                call to :meth:`~pyterrier_alpha.DataFrameBuilder.extend`.
        """
        if '_index' not in columns:
            columns = ['_index'] + columns
        self._data = {c: [] for c in columns}
        self._auto_index = 0

    def extend(self, values: Dict[str, Any]) -> None:
        """Add a dictionary of values to the DataFrameBuilder.

        .. versionchanged:: 0.4.1
            Allow all fields to be scalars (assumes length of 1).

        .. versionchanged:: 0.7.0
            Automatically infer the ``_index`` field.

        Args:
            values: a dictionary of values to add to the DataFrameBuilder. The keys must be the same as the columns
                provided to the constructor, and the values must be either scalars, or lists (all of the same length).
        """
        if '_index' not in values.keys():
            values['_index'] = self._auto_index
            self._auto_index += 1
        assert all(c in values.keys() for c in self._data), f"all columns must be provided: {list(self._data)}"
        lens = {k: len(v) for k, v in values.items() if hasattr(v, '__len__') and not isinstance(v, str)}
        if any(lens):
            first_len = list(lens.values())[0]
        else:
            first_len = 1 # if nothing has a len, everything is gien a length of 1
        assert all(i == first_len for i in lens.values()), f"all values must have the same length {lens}"
        for k, v in values.items():
            if k not in lens:
                self._data[k].append([v] * first_len)
            elif isinstance(v, pd.Series):
                self._data[k].append(v.values)
            else:
                self._data[k].append(v)

    def to_df(self, merge_on_index: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Convert the DataFrameBuilder to a DataFrame.

        .. versionchanged:: 0.1.1
            Added ``merge_on_index`` argument.

        .. versionchanged:: 0.1.1
            Columns from ``merge_on_index`` come first.

        Args:
            merge_on_index: an optional DataFrame to merge the resulting DataFrame on.

        Returns:
            A DataFrame with the values added to the DataFrameBuilder.
        """
        result = pd.DataFrame({
            k: np.concatenate(v)
            for k, v in self._data.items()
        })
        if merge_on_index is not None:
            merge_on_index = merge_on_index.reset_index(drop=True)
            result = result.assign(**{
                col: merge_on_index[col].iloc[result['_index']].values
                for col in merge_on_index.columns
                if col not in result.columns
            })
            merge_columns = set(merge_on_index.columns)
            column_order = list(merge_on_index.columns) + [c for c in result.columns if c not in merge_columns]
            result = result[column_order]
        result = result.drop(columns=['_index'])
        return result
