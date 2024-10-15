# Import python packages
import streamlit as st
import requests
import snowflake.connector
from snowflake.snowpark.functions import col
from snowflake.snowpark.session import Session


# Create connection using Streamlit secrets
conn_info = st.secrets["connections"]["snowflake"]
snowpark_session = Session.builder.configs(conn_info).create()

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom Smoothie!
    """
)

# Text input for the Smoothie name
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Fetch data from the 'fruit_options' table using Snowpark
my_dataframe = snowpark_session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert Snowpark DataFrame to Pandas for display in Streamlit
df = my_dataframe.to_pandas()
st.dataframe(data=df, use_container_width=True)

# Multiselect for choosing ingredients (up to 5)
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    df['FRUIT_NAME'].tolist(),  # Extract list of fruit names from the Pandas DataFrame
    max_selections=5
)

# If the user selected ingredients
if ingredients_list:
    # Concatenate the selected ingredients into a string
    ingredients_string = ' '.join(ingredients_list)
    st.write(f"Ingredients: {ingredients_string}")

    # For each selected ingredient, retrieve its corresponding SEARCH_ON value and display it
    for fruit_chosen in ingredients_list:
        search_on = df.loc[df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f'The search value for {fruit_chosen} is {search_on}.')

        # API request using the 'search_on' value
        fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
        st.subheader(f"{fruit_chosen} Nutrition Information")
        st.write(fruityvice_response.json())

    # SQL statement for inserting the order
    my_insert_stmt = f"""
    INSERT INTO SMOOTHIES.PUBLIC.ORDERS(ingredients, name_on_order)
    VALUES ('{ingredients_string}', '{name_on_order}')
    """
    
    # Show the SQL statement for debugging purposes (optional)
    # st.write(my_insert_stmt)
    
    # Submit button for inserting the order into Snowflake
    time_to_insert = st.button('Submit Order')

    # Insert the order when the button is clicked
    if time_to_insert:
        snowpark_session.sql(my_insert_stmt).collect()  # Execute the SQL insert
        st.success('Your Smoothie is ordered!', icon="✅")
