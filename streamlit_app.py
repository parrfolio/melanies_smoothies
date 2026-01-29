# ----------------------------------
# ORDER FORM APP
# ----------------------------------
import streamlit as st
import requests
from snowflake.snowpark.functions import col

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
# Load fruit options (DISPLAY names)
# ----------------------------------
fruit_options_df = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"), col("SEARCH_ON"))
    .sort(col("FRUIT_NAME"))
)

fruit_options_pd = fruit_options_df.to_pandas()

# ----------------------------------
# UI Inputs
# ----------------------------------
customer_name = st.text_input(
    "Name for this order (optional):",
    max_chars=100
)

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_options_pd["FRUIT_NAME"].tolist()
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
    # 🔑 Convert UI labels → SEARCH_ON values (PRESERVE ORDER)
    search_on_values = [
        fruit_options_pd.loc[
            fruit_options_pd["FRUIT_NAME"] == fruit,
            "SEARCH_ON"
        ].iloc[0]
        for fruit in ingredients_list
    ]

    ingredients_string = ", ".join(search_on_values)

    st.subheader("Order Preview")
    st.text(ingredients_string)

    if st.button("Submit Order", disabled=too_many):
        session.create_dataframe(
            [[
                False,                          # ORDER_FILLED
                customer_name.strip(),          # NAME_ON_ORDER
                ingredients_string              # INGREDIENTS (canonical)
            ]],
            schema=[
                "ORDER_FILLED",
                "NAME_ON_ORDER",
                "INGREDIENTS"
            ],
        ).write.mode("append").save_as_table(
            "SMOOTHIES.PUBLIC.ORDERS",
            column_order="name"
        )

        st.session_state.order_submitted = True
        st.rerun()

# ----------------------------------
# Confirmation state
# ----------------------------------
if st.session_state.order_submitted:
    st.success("Order submitted! 🥤")

    if st.button("Place another order"):
        st.session_state.order_submitted = False
        st.rerun()

# ----------------------------------
# Nutrition Information (PER FRUIT)
# ----------------------------------
if ingredients_list:
    st.header("🥗 Nutrition Information")

    for fruit_name, search_on in zip(ingredients_list, search_on_values):
        st.subheader(f"{fruit_name} Nutrition Information")

        smoothiefruit_response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{search_on}"
        )

        st.dataframe(
            smoothiefruit_response.json(),
            use_container_width=True
        )
