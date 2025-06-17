import os
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from base import RecoveryPredictor


class DebuggingModel(RecoveryPredictor):
    DATA_DIR_NAME = 'data'
    COMPANY_DIR = 'companies'


    def __init__(self, base_dir, refresh_data: bool = False):
        name = ''
        super().__init__(base_dir, refresh_data)

    def transform_data(self, df: pd.DataFrame):
        splitted = df['Date'].str.split('-', expand=True)

        df['Month'] = splitted[1].astype('int')
        df['Year'] = splitted[0].astype('int')

        df['Quarter end'] = np.where(df['Month'] % 3 == 0, 1, 0)

        date_counts = df['Date'].value_counts()
        df['Amount of other stock dropping this date'] = df['Date'].map(date_counts)

        return df

    def train_model(self, df: pd.DataFrame):
        # First we will add some potentially useful data
        df = self.transform_data(df)

        features = df.drop(
            ['Date', '1 month recovery', 'Recovery', 'Date added', 'Founded', 'Headquarters Location', "CIK", "Symbol"],
            axis=1)
        target = df['Recovery']

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



if __name__ == "__main__":
    a = DebuggingModel(os.getcwd(), False)
    price_drop_df = a.create_price_drop_df(10, 15, 25)

    price_drop_df['Recovery'] = price_drop_df['1 month recovery'].apply(lambda x: 1 if x > 100 else 0)

    price_drop_df.to_csv(os.path.join(a.base_dir, a.DATA_DIR_NAME, "notebook", "price_drop_df.csv"), index=False)

    model = a.train_model(price_drop_df)
