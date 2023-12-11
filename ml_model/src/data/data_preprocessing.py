import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from _common.database_communicator.db_connector import DBConnector
from _common.misc.variables import (
    CATEGORICAL_FEATS,
    FEAT_COLS,
    NUMERIC_FEATS,
    TARGET_COL,
)


class DataPreprocessor(DBConnector):
    def __init__(self, main: bool = True) -> None:
        """Initialize DataPreprocessor class and load data from database"""
        super().__init__()
        engine = self.create_sql_engine()

        self.df = (
            pd.read_sql_query("SELECT * FROM data_main", con=engine)
            if main
            else pd.read_sql_query("SELECT * FROM data_staging", con=engine)
        )

    def _handle_missing_and_duplicated_values(self):
        """Handle missing and duplicated values in the dataset"""
        self.df["floor"].fillna("brak informacji", inplace=True)
        self.df["status"].fillna("brak informacji", inplace=True)
        self.df["property_type"].fillna("brak informacji", inplace=True)
        self.df["rooms"].fillna(1, inplace=True)
        self.df["year_built"].fillna("brak informacji", inplace=True)
        self.df["property_condition"].fillna("brak informacji", inplace=True)

        self.df.drop_duplicates(inplace=True)

        self.df = self.df[self.df["price"].notna()]
        self.df = self.df[self.df["size"].notna()]

    def _process_price(self, filter_price: float = 0.0):
        """Process price column and filter out prices higher than filter_price"""

        mask = pd.to_numeric(self.df["price"], errors="coerce").notna()
        self.df = self.df[mask]

        self.df["price"] = self.df["price"].astype(float)

        if filter_price > 0.0:
            self.df = self.df[self.df["price"] < filter_price]

    def _process_size(self, filter_size: float = 0.0):
        """Process size column"""

        # self.df["size"] = self.df["size"].fillna(self.df["size"].median())

        if filter_size > 0.0:
            self.df = self.df[self.df["size"] < filter_size]

    def _process_floor(self, filter_floor: float = 0.0):
        """Process floor column"""

        if filter_floor > 0.0:
            self.df = self.df[self.df["floor"] < filter_floor]

    def _cast_types(self):
        numerical_col = NUMERIC_FEATS
        categorical_col = CATEGORICAL_FEATS

        for col in numerical_col:
            self.df[col] = self.df[col].astype(float)

        for col in categorical_col:
            self.df[col] = self.df[col].astype("category")

    @staticmethod
    def static_cast_types(df):
        numerical_col = NUMERIC_FEATS
        categorical_col = CATEGORICAL_FEATS

        for col in numerical_col:
            df[col] = df[col].astype(float)

        for col in categorical_col:
            df[col] = df[col].astype("category")

        return df

    def _select_features(self):
        """Select features to be used in the model"""
        self.df = self.df[FEAT_COLS + [TARGET_COL]]

    def _standardize(self):
        """Standardize numerical features"""
        scaler = StandardScaler()
        self.df[NUMERIC_FEATS] = scaler.fit_transform(self.df[NUMERIC_FEATS])

    def run_preprocessing_pipeline(
        self, cast_types: bool = True, standardize: bool = True
    ):
        """Run preprocessing pipeline"""

        if cast_types:
            self._cast_types()
        self._process_price(filter_price=17500000.0)
        self._process_size(filter_size=1000.0)
        self._process_floor(filter_floor=30.0)
        if standardize:
            self._standardize()
        self._select_features()

    def train_test_split(
        self,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split data into train and test set

        Returns:
            tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series] : train and test set
        """
        X_train, X_test, y_train, y_test = train_test_split(
            self.df[FEAT_COLS],
            self.df[TARGET_COL],
            test_size=0.2,
            random_state=42,
            shuffle=True,
        )
        return X_train, X_test, y_train, y_test

    def get(self):
        """Return data

        Returns:
            pd.DataFrame : data
        """
        return self.df


if __name__ == "__main__":
    preprocessor = DataPreprocessor()

    preprocessor.run_preprocessing_pipeline()
    X_train, X_test, y_train, y_test = preprocessor.train_test_split()
    df = preprocessor.get()
