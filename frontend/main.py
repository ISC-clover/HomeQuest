import streamlit as st
import os
from hq_api import HomeQuestAPI

API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")
API_KEY = os.getenv("APP_API_KEY")
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "http://localhost:8000")

if "api" not in st.session_state:
    st.session_state.api = HomeQuestAPI(
        api_url=API_URL, 
        api_key=API_KEY, 
        image_base_url=IMAGE_BASE_URL
    )
