import streamlit as st
import pandas as pd
import plotly.express as px
from finance_utils import (
    save_categories,
    save_to_sqlite,
    add_keyword_to_category,
    load_transactions,
    list_tables_in_sqlite,
    load_transactions_from_sqlite,
    delete_from_sqlite,
)
from constants import INCOME_TYPE, EXPENSE_TYPE


def render_save_to_db(debits_df, credits_df, key_prefix=""):
    transaction_name = st.text_input(
        "transaction name", key=f"{key_prefix}transaction_name"
    )
    save_to_db_button = st.button("Save to database", key=f"{key_prefix}save_to_db")
    if save_to_db_button and transaction_name:
        save_to_sqlite(
            debits_df,
            table_name=f"expenses_{transaction_name}",
        )
        save_to_sqlite(
            credits_df,
            table_name=f"income_{transaction_name}",
        )
        st.success("Data saved to database")


def render_uploaded_file_section():
    uploaded_file = st.file_uploader(
        "Upload your data", type=["csv"], accept_multiple_files=True
    )
    if uploaded_file:
        df = load_transactions(uploaded_file)
        if df is not None and "Type" in df.columns:
            debits_df = df[df["Type"] == EXPENSE_TYPE].copy()
            credits_df = df[df["Type"] == INCOME_TYPE].copy()
            render_df(debits_df, credits_df, key_prefix="file_")


def render_database_table_section():
    table_names = list_tables_in_sqlite()
    options = ["-- Select a table --"] + table_names
    selected_table = st.selectbox("Select table to view", options, index=0)

    if selected_table and selected_table != "-- Select a table --":
        expenses_df, income_df = load_transactions_from_sqlite(selected_table)

        render_df(expenses_df, income_df, key_prefix="db_")
        if st.button("Delete table from database", type="primary"):
            delete_from_sqlite(selected_table)
            st.success("Table deleted from database.")
            st.rerun()


def render_manual_form(df, key_prefix):
    if f"{key_prefix}show_manual_form" not in st.session_state:
        st.session_state[f"{key_prefix}show_manual_form"] = False

    if st.button("➕ Add Transaction Manually", key=f"{key_prefix}toggle_form"):
        st.session_state[f"{key_prefix}show_manual_form"] = not st.session_state[
            f"{key_prefix}show_manual_form"
        ]

    if st.session_state[f"{key_prefix}show_manual_form"]:
        with st.form(key=f"{key_prefix}manual_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                date = st.date_input("Date", key=f"{key_prefix}date")
            with col2:
                description = st.text_input(
                    "Description", key=f"{key_prefix}description"
                )
            with col3:
                amount = st.number_input("Amount", key=f"{key_prefix}amount")
            category = st.selectbox(
                "Category",
                list(st.session_state.categories.keys()),
                key=f"{key_prefix}category",
            )
            submit_button = st.form_submit_button(label="Add Transaction")

            if submit_button:
                new_row = {
                    "Date": pd.to_datetime(date),
                    "Description": description.strip(),
                    "Amount": amount,
                    "Category": category,
                }

                df = st.session_state[f"{key_prefix}debits_df"]
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state[f"{key_prefix}debits_df"] = updated_df
                st.session_state[f"{key_prefix}show_manual_form"] = False

                st.rerun()


def render_df(debits_df, credits_df, key_prefix=""):
    if f"{key_prefix}debits_df" not in st.session_state:
        st.session_state[f"{key_prefix}debits_df"] = debits_df.copy()

    tab1, tab2 = st.tabs(["Expenses", "Income"])
    with tab1:
        new_category = st.text_input("New category", key=f"{key_prefix}new_category")
        add_button = st.button("Add category", key=f"{key_prefix}add_button")

        if add_button and new_category:
            if new_category not in st.session_state.categories:
                st.session_state.categories[new_category] = []
                save_categories()
            else:
                st.error(f"Category {new_category} already exists")
            st.rerun()

        st.subheader("Your Expenses")
        debits_df = st.session_state[f"{key_prefix}debits_df"].copy()
        if "Note" not in debits_df.columns:
            debits_df["Note"] = ""
        if "Made By" not in debits_df.columns:
            debits_df["Made By"] = ""

        edited_df = st.data_editor(
            debits_df[["Date", "Description", "Amount", "Category", "Note", "Made By"]],
            key=f"{key_prefix}category_editor",
            column_config={
                "Date": st.column_config.DateColumn(label="Date", format="DD MMM YYYY"),
                "Amount": st.column_config.NumberColumn(
                    label="Amount", format="%.2f BG"
                ),
                "Category": st.column_config.SelectboxColumn(
                    label="Category",
                    options=list(st.session_state.categories.keys()),
                ),
                "Note": st.column_config.TextColumn(label="Note"),
                "Made By": st.column_config.SelectboxColumn(
                    label="Made By", options=["Gabi", "Blago"]
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        # save_button = st.button(
        #     "Save changes", type="primary", key=f"{key_prefix}save_button"
        # )
        # if save_button:
        #     for inx, row in edited_df.iterrows():
        #         new_category = row["Category"]
        #         print(new_category)
        #         if (
        #             new_category
        #             == st.session_state[f"{key_prefix}debits_df"].at[inx, "Category"]
        #         ):
        #             continue
        #         details = row["Description"]
        #         edited_df.at[inx, "Category"] = new_category
        #         add_keyword_to_category(new_category, details)
        st.subheader("Expense Summary")
        total_expenses = edited_df["Amount"].sum()
        st.metric("Total Expenses", f"{total_expenses:,.2f} BG")
        made_by_totals = edited_df.groupby("Made By")["Amount"].sum().reset_index()
        made_by_totals = made_by_totals.sort_values(by="Amount", ascending=False)
        st.dataframe(
            made_by_totals,
            column_config={
                "Amount": st.column_config.NumberColumn("Amount", format="%.2f BG"),
            },
            use_container_width=True,
            hide_index=True,
        )
        fig1 = px.pie(
            made_by_totals,
            values="Amount",
            names="Made By",
            title="Made by summery",
        )
        st.plotly_chart(fig1, use_container_width=True)
        category_totals = edited_df.groupby("Category")["Amount"].sum().reset_index()
        category_totals = category_totals.sort_values(by="Amount", ascending=False)
        st.dataframe(
            category_totals,
            column_config={
                "Amount": st.column_config.NumberColumn("Amount", format="%.2f BG"),
            },
            use_container_width=True,
            hide_index=True,
        )
        fig = px.pie(
            category_totals,
            values="Amount",
            names="Category",
            title="Expense Summary",
        )
        st.plotly_chart(fig, use_container_width=True)
        description_totals = (
            edited_df.groupby("Description")["Amount"].sum().reset_index()
        )
        description_totals = description_totals.sort_values(
            by="Amount", ascending=False
        )
        st.dataframe(
            description_totals,
            column_config={
                "Amount": st.column_config.NumberColumn("Amount", format="%.2f BG"),
            },
            use_container_width=True,
            hide_index=True,
        )
        render_manual_form(edited_df, key_prefix)

    with tab2:
        st.subheader("Income Summary")
        total_income = credits_df["Amount"].sum()
        st.metric("Total Income", f"{total_income:,.2f} BG")
        st.write(credits_df)
    render_save_to_db(edited_df, credits_df, key_prefix=key_prefix)
