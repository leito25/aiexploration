# -*- coding: utf-8 -*-
"""
Created on Sun Sep 25 16:28:10 2022

@author: maxim migutin
"""


import joblib
from PIL import Image
import pandas as pd
import streamlit as st

# loading pre-trained classifier
model = joblib.load(open('./classification_model.sav', 'rb'))

# main App layout
st.header("ML Iris Classificator:")
image = Image.open('irises.jpeg')
st.image(image, use_column_width=True)
st.write("Feed flower properties for automatic classification:")

SepalLengthCm = st.slider('SepalLengthCm:', 2.01, 6.01)
SepalWidthCm = st.slider('SepalWidthCm:', 0.0, 5.01)
PetalLengthCm = st.slider('PetalLengthCm',0.0, 3.01)
PetalWidthCm = st.slider('PetalWidthCm:', 0.0, 2.01)

data = {'SepalLengthCm': SepalLengthCm,
        'SepalWidthCm': SepalWidthCm,
        'PetalLengthCm': PetalLengthCm,
        'PetalWidthCm': PetalWidthCm}

features = pd.DataFrame(data, index=[0])

pred_proba = model.predict_proba(features)

st.subheader('Class probabilities:') 

# Results
st.write('**Setosa: `{}`%**:'.format(round(pred_proba[0][0]*100, 2)))
st.write('**Versicolor: `{}`%**'.format(round(pred_proba[0][1]*100, 2)))
st.write('**Virginica: `{}`%**'.format(round(pred_proba[0][2]*100, 2)))


