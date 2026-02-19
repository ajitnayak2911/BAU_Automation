import streamlit as st
import importlib
import os

import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="Automation Hub", layout="wide")

st.title("Automation Hub")

MODULE_PATH = "modules"

modules = [
    m for m in os.listdir(MODULE_PATH)
    if os.path.isdir(os.path.join(MODULE_PATH, m))
]

selected = st.sidebar.selectbox("Select Use Case", modules)

if selected:
    module = importlib.import_module(f"modules.{selected}.ui")
    module.run()