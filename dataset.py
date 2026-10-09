import pandas as pd
import numpy as np

archivo = "Datos/Volumetria Web Hasta Julio.xlsx"


# Importación de librerias
#Librerias para la ejecución de código 
import pandas as pd
import numpy as np

#Visualización
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = pd.read_excel("Datos/Volumetria Web Hasta Julio.xlsx")

st.set_page_config(page_title="Mi app", layout="wide",
                   initial_sidebar_state="collapsed")


df1 = pd.read_excel("Datos/sc_task.xlsx")
