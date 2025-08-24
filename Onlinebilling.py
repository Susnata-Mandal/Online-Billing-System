import mysql.connector as mc
import streamlit as st
import pandas as pd
import random

# --- Database Setup ---
def setup_database():
    """
    Connects to MySQL, creates the database and tables if they don't exist,
    and populates the products table with initial data.
    """
    try:
        # Establish a connection to the MySQL server
        db = mc.connect(
            host='localhost',
            user='root',
            passwd='12345'
        )
        cur = db.cursor()

        # Create the database if it doesn't exist
        cur.execute("CREATE DATABASE IF NOT EXISTS billing_software")
        cur.execute("USE billing_software")

        # Create the tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                mobile VARCHAR(15),
                email VARCHAR(100),
                bill_no INT UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bill_no INT,
                category VARCHAR(50),
                sub_category VARCHAR(50),
                product_name VARCHAR(100),
                price DECIMAL(10, 2),
                quantity INT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(50),
                sub_category VARCHAR(50),
                product_name VARCHAR(100),
                price DECIMAL(10, 2),
                quantity INT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS paid_bills (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bill_no INT NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                paid_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bill_no) REFERENCES customers(bill_no)
            )
        """)

        # Check if products table is empty before inserting data
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            products_data = [
                ('Clothes', 'Pants', 'Raymond', 1200.00, 50), ('Clothes', 'Pants', 'Peter England', 1000.00, 30),
                ('Clothes', 'Pants', 'Denim', 1500.00, 20), ('Clothes', 'Shirt', 'Park Avenue', 1100.00, 40),
                ('Clothes', 'Shirt', 'Raymond', 1300.00, 25), ('Clothes', 'Shirt', 'Allen Solly', 1250.00, 35),
                ('Clothes', 'T-Shirt', 'Van Heusen', 800.00, 60), ('Clothes', 'T-Shirt', 'Zara', 900.00, 50),
                ('Clothes', 'T-Shirt', "Levi's", 1000.00, 40), ('Electronics', 'T.V.', 'Panasonic', 35000.00, 15),
                ('Electronics', 'T.V.', 'L.G.', 40000.00, 10), ('Electronics', 'T.V.', 'Samsung', 45000.00, 8),
                ('Electronics', 'Microwave', 'Godrej', 8000.00, 20), ('Electronics', 'Microwave', 'L.G.', 10000.00, 15),
                ('Electronics', 'Microwave', 'Samsung', 12000.00, 12), ('Electronics', 'Refrigerator', 'Samsung', 25000.00, 10),
                ('Electronics', 'Refrigerator', 'Whirlpool', 30000.00, 12), ('Electronics', 'Refrigerator', 'Voltas', 28000.00, 14),
                ('Electronics', 'Washing Machine', 'Haier', 20000.00, 10), ('Electronics', 'Washing Machine', 'Samsung', 25000.00, 8),
                ('Electronics', 'Washing Machine', 'Whirlpool', 23000.00, 7), ('Food', 'Burger', 'McDonald', 150.00, 100),
                ('Food', 'Burger', 'Burger King', 180.00, 80), ('Food', 'Burger', 'Burger Singh', 200.00, 50),
                ('Food', 'Pizza', "Domino's", 400.00, 60), ('Food', 'Pizza', 'Pizza Hut', 450.00, 50),
                ('Food', 'Pizza', 'Insta Pizza', 420.00, 40), ('Food', 'Fries', 'KFC', 120.00, 100),
                ('Food', 'Fries', 'McDonald', 130.00, 90)
            ]
            cur.executemany("""
                INSERT INTO products (category, sub_category, product_name, price, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, products_data)
            st.success("Products table populated successfully!")
        else:
            st.info("Products table already contains data.")

        db.commit()
        st.success("Database and tables are ready!")

    except mc.Error as e:
        st.error(f"Error setting up database: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            cur.close()
            db.close()

# --- Application Logic ---

# Database Connection
def create_connection():
    return mc.connect(
        host='localhost',
        user='root',
        passwd='12345',
        database='billing_software'
    )

# Generate Random Bill Number
def generate_bill_no():
    return random.randint(1000, 10000)

# Sign Up Functionality
def sign_up(db, name, mobile, email, bill_no):
    cur = db.cursor()
    cur.execute("""SELECT * FROM customers WHERE mobile=%s or email=%s""", (mobile, email))
    existing_user = cur.fetchone()

    if existing_user:
        st.warning('User already signed up. Try using a different mobile and email')
    else:
        cur.execute("""
            INSERT INTO customers (name, mobile, email, bill_no)
            VALUES (%s, %s, %s, %s)
        """, (name, mobile, email, bill_no))
        db.commit()
        st.success("Sign Up Successful!")
    cur.close()

# Add to Cart Functionality
def add_to_cart(db, category, sub_category, product_name, quantity, bill_no):
    cur = db.cursor()
    try:
        cur.execute("SELECT quantity, price FROM products WHERE product_name = %s", (product_name,))
        result = cur.fetchone()

        if cur.with_rows:
            cur.fetchall()

        if result:
            current_quantity, price = result
            if current_quantity >= quantity:
                cur.execute("""
                    INSERT INTO cart (bill_no, category, sub_category, product_name, price, quantity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (bill_no, category, sub_category, product_name, price, quantity))

                new_quantity = current_quantity - quantity
                cur.execute("""
                    UPDATE products
                    SET quantity = %s
                    WHERE product_name = %s
                """, (new_quantity, product_name))

                db.commit()
                st.success(f"{quantity} {product_name}(s) added to the cart!")
            else:
                st.error(f"Insufficient stock! Only {current_quantity} {product_name}(s) available.")
        else:
            st.error("Product not found!")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        cur.close()

# Display Full Bill
def display_bill(db, bill_no):
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT category, sub_category, product_name, price, quantity FROM cart WHERE bill_no = %s", (bill_no,))
    rows = cur.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        df['Total Price'] = df['price'] * df['quantity']
        st.subheader(f"Bill Details for Bill No: {bill_no}")
        st.dataframe(df)
        st.markdown(f"### Grand Total: ₹{df['Total Price'].sum()}")
    else:
        st.warning(f"No items found for Bill No: {bill_no}")
    cur.close()

# Pay and Exit
def pay_and_exit(db, bill_no):
    cur = db.cursor()
    try:
        cur.execute("SELECT category, sub_category, product_name, price, quantity FROM cart WHERE bill_no = %s", (bill_no,))
        rows = cur.fetchall()
        if rows:
            total_amount = sum(row[3] * row[4] for row in rows)
            cur.execute("""
                INSERT INTO paid_bills (bill_no, total_amount, paid_on)
                VALUES (%s, %s, NOW())
            """, (bill_no, total_amount))
            cur.execute("DELETE FROM cart WHERE bill_no = %s", (bill_no,))
            db.commit()
            st.success(f"Bill No: {bill_no} has been paid successfully! Total Amount: ₹{total_amount}")
            return rows, total_amount
        else:
            st.warning("No items found for this bill.")
            return None, 0
    finally:
        cur.close()

# Search Bill
def search_bill(db, bill_no):
    cur = db.cursor()
    cur.execute("""
        SELECT c.name, c.mobile, c.email, p.total_amount, p.paid_on
        FROM customers c JOIN paid_bills p ON c.bill_no = p.bill_no
        WHERE p.bill_no=%s
    """, (bill_no,))
    rows = cur.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["Name", "Mobile", "Email", "Total Amount", "Paid On"])
        st.dataframe(df)
    else:
        st.warning(f"No such bill number {bill_no} present in the database")
    cur.close()

# Main Streamlit Application
def main():
    st.title("Online Billing Software")

    if st.sidebar.button("Setup/Verify Database"):
        setup_database()

    try:
        db = create_connection()
    except mc.Error as e:
        st.error(f"Database connection failed: {e}")
        st.info("Please ensure your MySQL server is running and the credentials are correct. Then, click the 'Setup/Verify Database' button.")
        return

    if "bill_no" not in st.session_state:
        st.session_state.bill_no = generate_bill_no()
    bill_no = st.session_state.bill_no

    option = st.sidebar.selectbox("Select Operation", ("Home", "Sign Up", "Add Items", "Bill Area", "Search Your Bill"))

    if option == "Home":
        st.subheader("Welcome to the Online Billing System")
        st.write("Navigate from the sidebar to access each operation.")
        # st.image('Billing.png', width=800) # This line is commented out as the image is not provided.

    elif option == "Sign Up":
        st.subheader("Sign Up")
        name = st.text_input("Enter Your Name")
        mobile = st.text_input("Enter Your Mobile Number")
        email = st.text_input("Enter Your Email ID")
        st.write(f"Your Bill Number: {bill_no}")
        if st.button("Sign Up"):
            if name and mobile and email:
                sign_up(db, name, mobile, email, bill_no)
            else:
                st.warning("Please fill in all fields.")

    elif option == "Add Items":
        st.subheader("Add to Cart")
        # st.image('https://i.pinimg.com/originals/5a/d0/47/5ad047a18772cf0488a908d98942f9bf.gif', width=500)
        st.write(f"Current Bill Number: {bill_no}")
        category = st.selectbox("Category", ("Clothes", "Electronics", "Food"))
        
        if category == "Clothes":
            sub_category = st.selectbox("Sub-Category", ("Pants", "Shirt", "T-Shirt"))
            product = st.selectbox("Product Name", {"Pants": ["Raymond", "Peter England", "Denim"], "Shirt": ["Park Avenue", "Raymond", "Allen Solly"], "T-Shirt": ["Van Heusen", "Zara", "Levi's"]}[sub_category])
        elif category == "Electronics":
            sub_category = st.selectbox("Sub-Category", ("T.V.", "Microwave", "Refrigerator", "Washing Machine"))
            product = st.selectbox("Product Name", {"T.V.": ["Panasonic", "L.G.", "Samsung"], "Microwave": ["Godrej", "L.G.", "Samsung"], "Refrigerator": ["Samsung", "Whirlpool", "Voltas"], "Washing Machine": ["Haier", "Samsung", "Whirlpool"]}[sub_category])
        elif category == "Food":
            sub_category = st.selectbox("Sub-Category", ("Burger", "Pizza", "Fries"))
            product = st.selectbox("Product Name", {"Burger": ["McDonald", "Burger King", "Burger Singh"], "Pizza": ["Domino's", "Pizza Hut", "Insta Pizza"], "Fries": ["KFC", "McDonald"]}[sub_category])

        quantity = st.number_input("Enter Quantity", min_value=1, value=1, step=1)
        if st.button("Add to Cart"):
            add_to_cart(db, category, sub_category, product, quantity, bill_no)

    elif option == "Bill Area":
        st.subheader("View Bill")
        st.write(f"Bill Number: {bill_no}")
        display_bill(db, bill_no)
        if st.button("Pay & Exit"):
            items, total_amount = pay_and_exit(db, bill_no)
            if items:
                st.info("Thank you for shopping with us!")
                st.session_state.bill_no = generate_bill_no() # Generate new bill no for next customer

    elif option == "Search Your Bill":
        st.subheader("Search Your Bill")
        search_bill_no = st.text_input('Enter bill no:')
        if st.button("Search"):
            if search_bill_no:
                search_bill(db, search_bill_no)
            else:
                st.warning("Please enter a bill number.")
    
    db.close()

if __name__ == "__main__":
    main()
