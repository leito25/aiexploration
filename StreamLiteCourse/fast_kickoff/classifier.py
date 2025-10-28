# -*- coding: utf-8 -*-
"""
Created on Sun Sep 25 16:28:10 2022

@author: maxim migutin
"""


import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
from loguru import logger

import warnings
warnings.filterwarnings("ignore")

def main():
    logger.info("Modules loaded")

    df = pd.read_csv('iris.csv')
    logger.info("Data loaded")

    df.drop(['Id'],axis=1,inplace=True)

    df.Species[df.Species == 'Iris-setosa'] = 1
    df.Species[df.Species == 'Iris-versicolor'] = 2
    df.Species[df.Species == 'Iris-virginica'] = 3

    X=df[['SepalLengthCm','SepalWidthCm','PetalLengthCm','PetalWidthCm']]
    y=df[['Species']]

    y=y.astype(int)

    logger.info("Data processed")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.15, random_state = 0)


    LR = LogisticRegression()
    LR.fit(X_train, y_train)

    logger.info("Model trained")

    pred=LR.predict(X_test)
    logger.info("Accuracy score achieved: {}".format(accuracy_score(pred,y_test)))

    model = LR.fit(X, y)

    joblib.dump(model, "classification_model.sav")
    logger.info("ML model dumped into binary")

if __name__=='__main__':
    main()