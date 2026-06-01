from abc import ABC, abstractmethod

import pandas as pd


class BaseModel(ABC):
    @abstractmethod
    def train(self, df: pd.DataFrame) -> None: ...

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> dict:
        """Return {"probability": float, "features": dict}"""
        ...

    def _feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        feature_cols = [
            c for c in df.columns
            if c not in ("Open", "High", "Low", "Close", "Volume")
        ]
        return df[feature_cols].dropna()
