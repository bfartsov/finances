import streamlit as st
from finance_utils import load_categories, login
from ui import render_uploaded_file_section, render_database_table_section

# Set page title and favicon
st.set_page_config(
    page_title="Finances", page_icon=":chart_with_upwards_trend:", layout="wide"
)


def main():
    login()
    load_categories()
    st.title("Finances Dashboard")
    render_uploaded_file_section()
    st.divider()
    render_database_table_section()


if __name__ == "__main__":
    main()
