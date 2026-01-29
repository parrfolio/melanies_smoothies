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
# DEBUG: Show FRUIT_NAME + SEARCH_ON
# (This is the section shown in the image)
# ----------------------------------
my_dataframe = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(
        col("FRUIT_NAME"),
        col("SEARCH_ON")
    )
    .sort(col("FRUIT_NAME"))
)

st.dataframe(
    data=my_dataframe,
    use_container_width=True
)

# STOP HERE so we can focus on this section
st.stop()

# ----------------------------------
# Load fruit options for multiselect
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
                None,                                # ORDER_UID (sequence default)
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

# ----------------------------------
# Nutrition Information (PER FRUIT)
# ----------------------------------
if ingredients_list:
    st.header("🥗 Nutrition Information")

    for fruit_chosen in ingredients_list:
        st.subheader(fruit_chosen + " Nutrition Information")

        smoothiefruit_response = requests.get(
            "https://my.smoothiefroot.com/api/fruit/" + fruit_chosen
        )

        st.dataframe(
            smoothiefruit_response.json(),
            use_container_width=True
        )
