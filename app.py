# ... all imports
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import json
from fpdf import FPDF
import datetime
import matplotlib.pyplot as plt
from google.cloud import firestore

# Firebase Initialization
with open("firebase_config.json") as f:
    firebase_config = json.load(f)

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# Firestore Initialization
db = firestore.Client.from_service_account_json("serviceAccountKey.json")

# Streamlit Page Setup
st.set_page_config(page_title="FinWise - Smart Finance App", page_icon="💰")
st.title("Welcome to FinWise - Financial Planning App")
st.write("This app will help you plan your finances.")

# Session State Defaults
for key in ["logged_in", "email", "income", "total_expenses", "savings"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ""

# Firebase Auth Functions
def login_user(email, password):
    try:
        auth.get_user_by_email(email)
        return True
    except:
        return False
def signup_user(email, password):
    try:
        auth.create_user(email=email, password=password)
        return True
    except firebase_admin._auth_utils.EmailAlreadyExistsError:
        st.error("This email is already in use.")
        return False
    except firebase_admin.exceptions.FirebaseError as e:
        if "WEAK_PASSWORD" in str(e):
            st.error("Password must be at least 6 characters.")
        else:
            st.error(f"Firebase Error: {e}")
        return False
    except Exception as e:
        st.error(f"Something went wrong: {e}")
        return False

# ---------------------- LOGIN / SIGNUP ----------------------
if not st.session_state.logged_in:
    st.title("Please Log In to Continue")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        if login_user(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Logged in successfully!")
        else:
            st.error("Invalid credentials.")

    if st.button("Sign Up"):
        if signup_user(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Sign-up successful!")
        else:
            st.warning("Check the sign-up error above.")
else:
    st.title(f"Welcome back, {st.session_state.email}!")

    # ---------------------- BUDGET TRACKING ----------------------
    st.title("📊 Budget Tracking Tool")
    with st.form("budget_form"):
        st.header("Enter Your Financial Details")
        income = st.number_input("Monthly Income ($)", min_value=0)
        rent = st.number_input("Rent ($)", min_value=0)
        groceries = st.number_input("Groceries ($)", min_value=0)
        utilities = st.number_input("Utilities ($)", min_value=0)
        entertainment = st.number_input("Entertainment ($)", min_value=0)
        others = st.number_input("Other Expenses ($)", min_value=0)
        submit_button = st.form_submit_button("Calculate")

    if submit_button:
        total_expenses = rent + groceries + utilities + entertainment + others
        savings = income - total_expenses

        st.session_state.income = income
        st.session_state.total_expenses = total_expenses
        st.session_state.savings = savings

        st.write(f"Total Expenses: ${total_expenses}")
        st.write(f"Savings: ${savings}")

        fig, ax = plt.subplots()
        ax.pie([rent, groceries, utilities, entertainment, others],
               labels=['Rent', 'Groceries', 'Utilities', 'Entertainment', 'Others'],
               autopct='%1.1f%%')
        ax.axis('equal')
        st.pyplot(fig)

        if savings < 0:
            st.warning("You're overspending.")
        elif savings == 0:
            st.info("You're breaking even.")
        else:
            st.success(f"You're saving ${savings} per month. Good job!")

    # ---------------------- INVESTMENT TIPS ----------------------
    st.subheader("💹 Investment Tips & Recommendations")
    risk_profile = st.selectbox("Select Your Risk Tolerance", ["Low", "Medium", "High"])
    if risk_profile == "Low":
        st.markdown("- Fixed Deposits\n- PPF\n- NSC\n- Low-Risk Mutual Funds")
    elif risk_profile == "Medium":
        st.markdown("- Balanced Mutual Funds\n- SIPs\n- Gold ETFs\n- Index Funds")
    else:
        st.markdown("- Direct Stocks\n- Crypto\n- Thematic Mutual Funds\n- Startups/REITs")

    st.info("⚠️ These are general tips. Consult a financial advisor for detailed planning.")

    # ---------------------- GOAL PLANNING ----------------------
    st.subheader("🎯 Goal-Based Financial Planning")
    goal_name = st.text_input("Enter Your Goal (e.g., Buy a Laptop)")
    goal_amount = st.number_input("Goal Amount ($)", min_value=0)
    target_months = st.number_input("Target Duration (months)", min_value=1)

    if st.button("Calculate Monthly Savings"):
        if goal_amount > 0 and target_months > 0:
            st.success(f"To achieve '{goal_name}', save **${goal_amount/target_months:.2f}** monthly.")
        else:
            st.warning("Please enter valid values.")

    # ---------------------- PDF DOWNLOAD ----------------------
    st.subheader("📄 Download Your Financial Summary")

    def generate_pdf(income, expenses, savings, risk_profile, goal_name, goal_amount, target_months):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="FinWise - Financial Summary", ln=True, align="C")

        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True)
        pdf.cell(200, 10, txt=f"Income: ${income}", ln=True)
        pdf.cell(200, 10, txt=f"Expenses: ${expenses}", ln=True)
        pdf.cell(200, 10, txt=f"Savings: ${savings}", ln=True)
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Risk Profile: {risk_profile}", ln=True)
        pdf.cell(200, 10, txt=f"Goal: {goal_name} (${goal_amount} in {target_months} months)", ln=True)

        file_path = "financial_summary.pdf"
        pdf.output(file_path)
        return file_path

    if all(k in st.session_state and st.session_state[k] != "" for k in ("income", "total_expenses", "savings")):
        if st.button("📥 Generate and Download PDF"):
            pdf_path = generate_pdf(
                st.session_state.income,
                st.session_state.total_expenses,
                st.session_state.savings,
                risk_profile,
                goal_name,
                goal_amount,
                target_months
            )
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="FinWise_Summary.pdf")

    # ---------------------- FIRESTORE SAVE ----------------------
    def save_summary_to_firestore(email, income, expenses, savings, risk_profile, goal_name, goal_amount, target_months):
        db.collection("summaries").add({
            "email": email,
            "date": datetime.datetime.now(),
            "income": income,
            "expenses": expenses,
            "savings": savings,
            "risk_profile": risk_profile,
            "goal_name": goal_name,
            "goal_amount": goal_amount,
            "target_months": target_months
        })

    if all(k in st.session_state and st.session_state[k] != "" for k in ("income", "total_expenses", "savings")):
        save_summary_to_firestore(
            st.session_state.email,
            st.session_state.income,
            st.session_state.total_expenses,
            st.session_state.savings,
            risk_profile,
            goal_name,
            goal_amount,
            target_months
        )

    # ---------------------- OPTIONAL: HISTORY DISPLAY ----------------------
    show_history = st.checkbox("📂 Show Financial Summary History")

    if show_history:
        st.subheader("📊 Your Financial Summary History")
        try:
            summaries_ref = db.collection("summaries").where("email", "==", st.session_state.email).order_by("date", direction=firestore.Query.DESCENDING)
            summaries = summaries_ref.stream()
            for doc in summaries:
                record = doc.to_dict()
                st.markdown(f"""
                **📅 Date:** {record['date'].strftime('%Y-%m-%d %H:%M:%S')}
                - 💵 Income: ${record['income']}
                - 💸 Expenses: ${record['expenses']}
                - 💰 Savings: ${record['savings']}
                - 🧠 Risk Profile: {record['risk_profile']}
                - 🎯 Goal: {record['goal_name']} (${record['goal_amount']} in {record['target_months']} months)
                ---
                """)
        except Exception as e:
            st.error("⚠️ Please create the Firestore index for this query. [Click here to create index](https://console.firebase.google.com/u/0/project/YOUR_PROJECT_ID/firestore/indexes)")
