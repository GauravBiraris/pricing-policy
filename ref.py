import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
from datetime import datetime
import csv
import re
import numpy as np

st.set_page_config(page_title="Enwise Price", page_icon=":chart:", layout="wide")

# Definitions of functions

def create_user_dir(username):
    # Create folder
    os.mkdir(username)
def valid_username(username):
    # Regex to allow a-z, 0-9 and _
    return re.match(r"^[a-zA-Z0-9_]+$", username)
def valid_password(password):
    # Password rules
    return len(password) >= 8
def user_exists(username):
    with open("users.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == username:
                return True
            else:
                return False
def save_credentials(username, password, email):
    with open("users.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([username, password, email])
def create_pricing_policy(username):
  filename = f"{username}/pricing_policy.csv"
  with open(filename, 'w', newline='') as f:
    writer = csv.writer(f) 
    writer.writerow(["Sale MRP", "Endings", "Min Margin", "Max Margin", "Price Change Min", "Price Change Max", "Clear Stock", "Shelf Life", "Sales Insights"])
def create_products_csv(username):
  filename = f"{username}/products.csv"
  with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Product ID", "Locked Price", "Class", "Flow"])    
def create_current_prices(username):
  filename = f"{username}/currentprices.csv"
  with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Product ID", "Recommended Price", "Validity", "Prevalence"])

# Authentication
if "username" not in st.session_state:
    st.session_state.username = None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "registration_complete" not in st.session_state:
   st.session_state.registration_complete = False

if not st.session_state.authenticated:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        with open('users.csv') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0]==username and row[1]==password:
                    st.success("Logged in successfully!")
        # Validate credentials
        st.session_state.username = username
        st.session_state.authenticated = True
    st.write("Not having the account? You can register instead!")
    if st.button("Register as New User"):
        if not st.session_state.registration_complete:
            st.title("Register")

            with st.form("register"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                email = st.text_input("Email ID")
                submit = st.form_submit_button("Register")
            # Validate inputs
            if not valid_username(username):
                st.error("Invalid username")

            if not valid_password(password):
                st.error("Weak password")
            
            # Check if username already exists
            if user_exists(username):
                st.error("User already exists")
            if valid_username(username) and valid_password(password) and not user_exists(username):
                if submit:
                    st.session_state.registration_complete = True
                    st.session_state.username = username
        if st.session_state.registration_complete:
            #User registration
            with open('users.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([st.session_state.username, password, email])

            # Create user directory and files
            create_user_dir(st.session_state.username)

            # Create files
            create_pricing_policy(st.session_state.username)
            create_products_csv(st.session_state.username)
            create_current_prices(st.session_state.username)

            # Create sales directory
            os.mkdir(f"{st.session_state.username}/sales")

            # Save credentials
            save_credentials(username, password, email)
            if os.path.exists(username):
                st.success("Registered successfully")

if st.session_state.authenticated:

    # # Create user directory
    # if not os.path.exists(st.session_state.username):
    #     os.mkdir(st.session_state.username)

    # Create pricing policy file
    policy_file = f"{st.session_state.username}/pricing_policy.csv"

    # Load policy
    policy = pd.read_csv(policy_file)

    # Open other files
    products_file = f"{st.session_state.username}/products.csv"
    prices_file = f"{st.session_state.username}/current_prices.csv"
    sales_dir = f"{st.session_state.username}/sales"

    # Streamlit app
    st.title(f"Welcome {st.session_state.username}")

    menu = option_menu(
        menu_title="My Pricing Engine",
        options=["Home", "Pricing Policy", "Get Pricing", "Analytics", "Archives"],
        icons=["house", "cash-coin", "tags", "bar-chart-steps", "archive"],
        menu_icon="joystick",
        default_index=0,
        orientation="horizontal",
    )

    if menu == "Pricing Policy":

        tab1, tab2, tab3 = st.tabs(["General", "Productwise", "Store"])

        with tab1:

            st.header("General Policy")
            
            mrp = st.checkbox("Sale products with MRP printed?")

            endings_options = ["0", "1", "9"]
            endings = st.selectbox("Preferred price endings", endings_options, index=int(policy["Endings"].iloc[0]))

            min_margin = st.number_input("Minimum margin %", min_value=0.0, max_value=100.0, value=float(policy["Min Margin"].iloc[0]))

            max_margin = st.number_input("Maximum margin %", min_value=0.0, max_value=500.0, value=float(policy["Max Margin"].iloc[0]))
            
            # price_change = st.slider("Acceptable price change %", 0, 50, 
            #     (int(policy["Price Change Min"].iloc[0]), int(policy["Price Change Max"].iloc[0])))
            price_change_min = policy["Price Change Min"].iloc[0]
            price_change_max = policy["Price Change Max"].iloc[0]

            if not np.isnan(price_change_min):
                price_change_min = int(price_change_min)

            if not np.isnan(price_change_max):  
                price_change_max = int(price_change_max)
            
            # price_change = st.slider("Acceptable price change %", 0, 50, (price_change_min, price_change_max), 1)

            clear_stock = st.checkbox("Clear stock before expiry?")

            # shelf_life_options = ["90%", "80%", "70%", "None"]
            # index = policy["Shelf Life"].iloc[0]
            # if not pd.isna(index):
            #     index = {"90%": 0, "80%": 1, "70%": 2, "None": 3}[index]

            # shelf_life = st.selectbox("Shelf life preference", shelf_life_options, index=index)

            sales_insights = st.checkbox("Get sales insights?")

            upGen = st.button('Update', key='A')

            if upGen:

                policy["Sale MRP"] = mrp
                policy["Endings"] = endings
                policy["Min Margin"] = min_margin  
                policy["Max Margin"] = max_margin
                # policy["Price Change Min"] = price_change[0]
                # policy["Price Change Max"] = price_change[1]
                policy["Clear Stock"] = clear_stock
                # policy["Shelf Life"] = shelf_life 
                policy["Sales Insights"] = sales_insights
                
                policy.to_csv(policy_file, index=False)

        with tab2:
            st.header("Productwise Policy")

            competitor = st.radio("Use competitor pricing?", ["Yes", "No"], index={"Yes": 0, "No": 1}[policy["Use Competitor"].iloc[0]])
            strategy = st.radio("Competitor pricing strategy", ["Average", "Median", "Mode"], index={"Average": 0, "Median": 1, "Mode":2}[policy["Strategy"].iloc[0]])

            lock_prices = st.checkbox("Lock prices?")
            if lock_prices:
                products = pd.read_csv(products_file)
                products = st.data_editor(products[["Product ID", "Locked Price"]])

                if st.button("Save"):
                    products.to_csv(products_file, index=False)

            holiday_effect = st.radio("Consider holiday Effect?", ["Yes", "No"], index={"Yes": 0, "No": 1}[policy["Holiday Effect"].iloc[0]])
            # occasion_effect = st.checkbox("Consider occasions?")
            inventory_cycle = st.number_input("Inventory cycle (weeks)", min_value=1, max_value=12)
            upProd = st.button('Update', key='B')
            if upProd:
                policy["Use Competitor"] = competitor
                policy["Strategy"] = strategy
                policy["Holiday Effect"] = holiday_effect                 

        with tab3:
            st.header("Store Policy")

            overheads = st.number_input("Overheads", min_value=0)
            electricity = st.number_input("Electricity cost")
            rent = st.number_input("Rent")
            salaries = st.number_input("Salaries")

            if st.button("Update Overheads"):
                overheads = electricity + rent + salaries

    elif menu == "Get Pricing":

        inventory = st.file_uploader("Upload Inventory", type=["csv", "xlsx"])
        if inventory:
            df = pd.read_csv(inventory)
            if not df.columns.isin(['Product ID']).any() or not df.columns.isin(['Cost Price']).any():
                st.error("Please ensure that the file has at least two columns as 'Product ID' and'Cost Price'")
            else:
                st.dataframe(df, hide_index= True)

                if st.button("Get Prices"):
                    # Pricing calculations

                    # Initialize output dataframe
                    prices = pd.DataFrame()
                    # Load inventory
                    inventory = df

                    # Load product prices
                    product_prices = pd.read_csv("prices.csv")

                    # Load pricing policy
                    min_margin = policy['Min Margin'].iloc[0]
                    max_margin = policy['Max Margin'].iloc[0]
                    # Load locked prices
                    locked_prices = pd.read_csv(f"{st.session_state.username}/products.csv")

                    # Merge inventory with product prices
                    df = inventory.merge(product_prices, on='Product ID')

                    # Initialize output dataframe 
                    output = pd.DataFrame()
                    output['Product ID'] = inventory['Product ID']
                    output["Validity"]= product_prices["Validity"]
                    for i, row in output.iterrows():
                        output.loc[i, 'Recommended Price'] = inventory.loc[i, 'Cost Price']+ max_margin*inventory.loc[i, 'Cost Price']/100
                    # Check if locked price exists
                    # output['Locked Price'] = locked_prices['Locked Price']
                    output['Recommended Price'] = locked_prices['Locked Price']
                    # output.loc[output['Locked Price'].isna(), 'Recommended Price'] = None

                    # Apply competitive pricing strategy
                    if policy['Use Competitor'].iloc[0] == 'Yes':
                        strategy = policy['Strategy'].iloc[0]
                        output['Recommended Price'] = df[strategy]
                        
                    # Calculate margin %
                    output['Margin %'] = (output['Recommended Price'] - inventory['Cost Price']) / inventory['Cost Price'] * 100

                    # Adjust prices based on margin policy
                    for i, row in output.iterrows():
                        if row['Margin %'] < min_margin:
                        
                            # Increase price
                            target_margin = min_margin 
                            current_margin = row['Margin %']
                            cost_price = inventory.loc[i, 'Cost Price']
                            
                            # Margin formula: (Price - Cost) / Cost * 100
                            # Rearrange to get new price
                            new_price = (target_margin/100 * cost_price) + cost_price 
                            
                            output.loc[i, 'Recommended Price'] = new_price
                            
                        elif row['Margin %'] > max_margin:
                        
                            # Decrease price
                            target_margin = max_margin
                            current_margin = row['Margin %']  
                            cost_price = inventory.loc[i, 'Cost Price']

                            # Similar rearrangement of margin formula 
                            new_price = (target_margin/100 * cost_price) + cost_price
                            
                            output.loc[i, 'Recommended Price'] = new_price                        
                    # Apply expiry based discounts
                    today = datetime.today()

                    for i, row in output.iterrows():
                            # Apply discount based on policy
                        expiry = datetime.strptime(inventory.loc[i, 'Earliest Expiry'], '%d-%m-%Y')
                        remaining = expiry - today

                        if remaining.days <= 60 and inventory.loc[i, 'Qty of Earliest Expiry'] > 0.4 * inventory.loc[i, 'Quantity in Stock']:
                            new_price = (95/100 * cost_price) + cost_price
                            output.loc[i, 'Recommended Price'] = new_price
                        if remaining.days <= 30 and inventory.loc[i, 'Qty of Earliest Expiry'] > 0.4 * inventory.loc[i, 'Quantity in Stock']:
                            new_price = (80/100 * cost_price) + cost_price
                            output.loc[i, 'Recommended Price'] = new_price
                        if remaining.days <= 15 and inventory.loc[i, 'Qty of Earliest Expiry'] > 0.4 * inventory.loc[i, 'Quantity in Stock']:
                            new_price = (50/100 * cost_price) + cost_price
                            output.loc[i, 'Recommended Price'] = new_price

                    # Write output
                    output['Margin %'] = (output['Recommended Price'] - inventory['Cost Price']) / inventory['Cost Price'] * 100
                    output[['Product ID', 'Recommended Price', 'Validity']].to_csv(f"{st.session_state.username}/current_prices.csv", index = False)
                    st.dataframe(output, hide_index=True)
                    pd.concat([inventory['Product ID'], locked_prices], axis=1, ignore_index=False, sort=False).to_csv(f"{st.session_state.username}/products1.csv", index =False)

    elif menu == "Analytics":
        taba, tabb = st.tabs(["Price Elasticity", "Periodic Trends"])
        
        with taba:
            st.markdown("### Price Elasticity")
            st.button("Request Analysis", key="X")

        with tabb:
            st.markdown("### Periodic Trends")
            st.button("Request Analysis", key='Y')
            
    elif menu == "Archives":
        
        sales_files = os.listdir(sales_dir)
        for i, file in enumerate(sales_files[:5]):
            df = pd.read_csv(f"{sales_dir}/{file}")
            st.header(file)
            st.dataframe(df.head())
            
else:
    st.error("You are not logged in")