import pandas as pd

from backend.prediction.models.base import BaseModel


class LightGBMModel(BaseModel):
    def __init__(self):
        self._model = None

    def train(self, df: pd.DataFrame) -> None:
        import lightgbm as lgb
        X = self._feature_matrix(df)
        y = (df["Close"].shift(-1) > df["Close"]).astype(int).loc[X.index]
        dtrain = lgb.Dataset(X[:-1], label=y[:-1])
        params = {"objective": "binary", "metric": "binary_logloss", "num_leaves": 63, "learning_rate": 0.05, "verbose": -1}
        self._model = lgb.train(params, dtrain, num_boost_round=200)

    def predict(self, df: pd.DataFrame) -> dict:
        if self._model is None:
            return {"probability": 0.5}
        X = self._feature_matrix(df)
        prob = float(self._model.predict(X.iloc[[-1]])[0])
        return {"probability": prob}
