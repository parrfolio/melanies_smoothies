# ----------------------------------
# ORDER FORM APP
# ----------------------------------
import streamlit as st
from snowflake.snowpark.functions import col

import requests
smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")


# ----------------------------------
# Snowflake session
# ----------------------------------

cnx = st.connection("snowflake")
session = cnx.session()            


# ----------------------------------
# Session state init
# ----------------------------------
if "order_submitted" not in st.session_state:
    st.session_state.order_submitted = False

# ----------------------------------
# App Header
# ----------------------------------
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# ----------------------------------
# Load fruit options
# ----------------------------------
fruits_df = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"))
    .sort(col("FRUIT_NAME"))
)

customer_name = st.text_input(
    "Name for this order (optional):",
    max_chars=100
)

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruits_df
)

# ----------------------------------
# Validation
# ----------------------------------
too_many = len(ingredients_list) > 5
if too_many:
    st.error("Please choose 5 ingredients or fewer.")

# ----------------------------------
# Order preview + submit
# ----------------------------------
if ingredients_list:
    ingredients_string = ", ".join([str(x) for x in ingredients_list])

    st.subheader("Order Preview")
    st.text(ingredients_string)

    if st.button("Submit Order", disabled=too_many):
        session.create_dataframe(
            [[
                None,                                # ORDER_UID (sequence)
                False,                               # ORDER_FILLED
                customer_name.strip() or None,       # NAME_ON_ORDER
                ingredients_string,                  # INGREDIENTS
                None                                 # ORDER_TS (default)
            ]],
            schema=[
                "ORDER_UID",
                "ORDER_FILLED",
                "NAME_ON_ORDER",
                "INGREDIENTS",
                "ORDER_TS"
            ],
        ).write.mode("append").save_as_table(
            "SMOOTHIES.PUBLIC.ORDERS"
        )

        st.session_state.order_submitted = True

# ----------------------------------
# Confirmation state
# ----------------------------------
if st.session_state.order_submitted:
    st.success("Order submitted! 🥤")

    if st.button("Place another order"):
        st.session_state.order_submitted = False
        st.rerun()


st.text(smoothiefroot_response.json())
