import os
import sqlite3
import streamlit as st
import json
from constants import category_file, users
import pandas as pd


def login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
        st.stop()


def list_tables_in_sqlite(dp_path="transactions.db"):
    conn = sqlite3.connect(dp_path)
    query = "SELECT name FROM sqlite_master WHERE type='table'"
    tables = pd.read_sql_query(query, conn)
    conn.close()
    tables_names = tables["name"].tolist()
    transaction_date = [
        name.split("_")[1] for name in tables_names if "expenses" in name
    ]
    return transaction_date


def load_transactions_from_sqlite(table_name, dp_path="transactions.db"):
    conn = sqlite3.connect(dp_path)
    expenses_table_name = "expenses_" + table_name
    income_table_name = "income_" + table_name

    query = f'SELECT * FROM "{expenses_table_name}"'
    expenses_df = pd.read_sql_query(query, conn)
    query = f'SELECT * FROM "{income_table_name}"'
    income_df = pd.read_sql_query(query, conn)
    conn.close()
    if "Date" in expenses_df.columns:
        expenses_df["Date"] = pd.to_datetime(expenses_df["Date"])
    if "Date" in income_df.columns:
        income_df["Date"] = pd.to_datetime(income_df["Date"])
    return (expenses_df, income_df)


def load_categories():
    if "categories" not in st.session_state:
        st.session_state.categories = {
            "Uncategorized": [],
        }
    if os.path.exists(category_file):
        with open(category_file, "r") as f:
            st.session_state.categories = json.load(f)


def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)


def save_to_sqlite(df, db_path="transactions.db", table_name="transactions"):
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()


def delete_from_sqlite(table_name, db_path="transactions.db"):
    conn = sqlite3.connect(db_path)
    expenses_table_name = "expenses_" + table_name
    income_table_name = "income_" + table_name
    conn.execute(f'DROP TABLE IF EXISTS "{expenses_table_name}"')
    conn.execute(f'DROP TABLE IF EXISTS "{income_table_name}"')

    conn.commit()
    conn.close()


def categorized_transactions(df):
    df["Category"] = "Uncategorized"
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue

        lowerd_keywords = [kw.lower().strip() for kw in keywords]

        for idx, row in df.iterrows():
            details = row["Description"].lower().strip()
            if details in lowerd_keywords:
                df.at[idx, "Category"] = category
    return df


def load_transactions(uploaded_file):
    combined_df = None
    try:
        for files in uploaded_file:
            df = pd.read_csv(files)
            df.columns = [col.strip() for col in df.columns]
            df["Amount"] = (
                df["Amount"]
                .astype(str)
                .str.replace(",", "")
                .str.replace("-", "")
                .astype(float)
            )
            df["Date"] = pd.to_datetime(df["Started Date"], format="%Y-%m-%d %H:%M:%S")
            combined_df = (
                pd.concat([combined_df, df]) if combined_df is not None else df
            )

    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None
    if combined_df is None:
        st.error("No valid CSV files were uploaded.")
        return None
    return categorized_transactions(combined_df)


def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        # st.success(f"Keyword {keyword} added to category {category}")
        return True
    return False
