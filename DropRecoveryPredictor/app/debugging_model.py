import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from app.base import RecoveryPredictor


class DebuggingModel(RecoveryPredictor):

    def __init__(self, db_uri: str):
        super().__init__(db_uri)

    def update_model(self):
        drop_df = self.create_price_drop_df(10, 15, 25)

        if not drop_df.empty:
            drop_df['recovery'] = drop_df['1 month recovery'].apply(lambda x: 1 if x > 100 else 0)

            self.model = self.train_model(drop_df)

    @staticmethod
    def transform_data(df: pd.DataFrame):
        date_counts = df['date'].value_counts()
        df['amount of other stock dropping this date'] = df['date'].map(date_counts)

        return df

    def train_model(self, df: pd.DataFrame):
        # First we will add some potentially useful data
        df = self.transform_data(df)

        features = df.drop(
            ['date', '1 month recovery', 'recovery'],
            axis=1)
        target = df['recovery']

        categorical_columns = features.select_dtypes(include=['object', 'category']).columns
        numeric_columns = features.select_dtypes(include=['number']).columns

        # Preprocessing for categorical data: impute missing with a constant then one-hot encode
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),  # fill NaNs with 'missing'
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        # Preprocessing for numeric data: impute missing with median
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median'))
        ])

        # Combine preprocessing steps
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_columns),
                ('cat', categorical_transformer, categorical_columns)
            ]
        )

        # Create the final pipeline
        rf_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier())
        ])

        # Split dataset
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

        # Fit the model
        rf_pipeline.fit(X_train, y_train)

        # Optional: evaluate
        accuracy = rf_pipeline.score(X_test, y_test)
        self.logger.info(f"Model Accuracy: {accuracy:.2f}")

        return rf_pipeline

    def predict(self, df: pd.DataFrame):
        a = self.model.predict(df)
        return a