import streamlit as st
import requests

# Configuration
API_BASE_URL = "http://127.0.0.1:53250/api/v1"

st.set_page_config(page_title="SimpleBillingLLM Client", layout="wide")

st.title("SimpleBillingLLM API Client")

# --- Authentication State ---
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = (
        "login_register"  # login_register, dashboard, predict
    )

# --- Page Navigation Logic ---
def navigate_to(page_name):
    """Navigate to a different page."""
    st.session_state.current_page = page_name
    st.rerun()

# --- Sidebar for Navigation (after login) ---
if st.session_state.api_key:
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.user_name}!")
        if st.button("Dashboard", key="nav_dashboard"):
            navigate_to("dashboard")
        if st.button("Make Prediction", key="nav_predict"):
            navigate_to("predict")
        if st.button("Logout", key="nav_logout"):
            st.session_state.api_key = None
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.current_page = "login_register"
            st.success("Logged out.")
            st.rerun()

# --- Page Rendering ---
if st.session_state.current_page == "login_register":
    st.subheader("User Access")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        st.subheader("Login")
        login_user_name = st.text_input("User Name", key="login_uname_tab")
        login_password = st.text_input(
            "Password", type="password", key="login_pwd_tab"
        )

        if st.button("Login", key="login_button_tab"):
            if not login_user_name or not login_password:
                st.error("Please enter both User Name and Password.")
            else:
                try:
                    # Check user existence by username
                    user_check_response = requests.get(
                        f"{API_BASE_URL}/users/by-name/{login_user_name}"
                    )

                    if user_check_response.status_code == 200:
                        user_data = user_check_response.json()
                        login_user_id = user_data.get("id")

                        auth = (
                            login_user_id,
                            login_password  # Basic Auth: username=name
                        )

                        response = requests.post(
                            f"{API_BASE_URL}/auth/apikey",
                            auth=auth
                        )

                        if response.status_code == 200:
                            api_key_data = response.json()  # APIKeyResponse
                            st.session_state.api_key = api_key_data.get("api_key")
                            # user_id and user_name are already known from
                            # the /users/by-name call and input
                            st.session_state.user_id = login_user_id  # Fetched
                            st.session_state.user_name = login_user_name

                        # Check if api_key was successfully retrieved
                        if st.session_state.api_key:  # user_id is set if here
                            st.success("Login successful!")
                            navigate_to("dashboard")
                        else:
                            st.error(
                                "Login Failed: Could not retrieve API key."
                            )
                    else:
                        st.error("User not found. Please register first.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")

    with register_tab:
        st.subheader("Register New User")
        reg_name = st.text_input("Name", key="reg_name")
        reg_password = st.text_input(
            "Password", type="password", key="reg_password"
        )

        if st.button("Register", key="register_button"):
            if not reg_name or not reg_password:
                st.error("Please enter Name and Password.")
            else:
                payload = {"name": reg_name, "password": reg_password}
                try:
                    # Update the registration endpoint
                    # to use the correct POST endpoint
                    response = requests.post(
                        f"{API_BASE_URL}/users/",
                        json=payload
                    )
                    if response.status_code in (200, 201):
                        user_data = response.json()
                        returned_user_id = user_data.get("id")
                        # Fallback to input name
                        returned_user_name = user_data.get("name", reg_name)

                        if returned_user_id:
                            st.success(
                                f"Registration successful for user '{returned_user_name}' "
                                f"(ID: {returned_user_id})! "
                                "Please proceed to the Login tab to obtain an "
                                "API key and access the dashboard."
                            )
                        else:
                            # This case should ideally not happen
                            # if registration is 200/201
                            st.error(
                                "Registration reported success, but user details "
                                "(like ID) were not returned. "
                                "Please try logging in or contact support."
                            )
                    else:
                        st.error(
                            f"Registration Failed: {response.status_code} - "
                            f"{response.text}"
                        )
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error during registration: {e}")

elif st.session_state.current_page == "dashboard":
    st.subheader(f"Dashboard for {st.session_state.user_name}")
    headers = {"X-API-KEY": st.session_state.api_key}

    # Display API Key
    st.text_input(
        "Your API Key",
        value=st.session_state.api_key,
        disabled=True,
        type="password"
    )

    # Fetch and Display Balance
    st.write("**Balance:**")
    try:
        # MODIFIED: Use the correct endpoint for balance
        balance_url = (
            f"{API_BASE_URL}/users/{st.session_state.user_id}/balance"
        )
        response_balance = requests.get(
            balance_url,
            headers=headers
        )
        if response_balance.status_code == 200:
            balance_data = response_balance.json()
            st.write(f"{balance_data.get('balance', 'N/A')}")
            # Removed attempt to update name from /me, as /me is not used
        else:
            st.error(
                f"Failed to fetch user balance: {response_balance.status_code} "
                f"- {response_balance.text}"
            )
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error fetching user balance: {e}")

    # Fetch and Display Predictions
    # This section is removed as the backend endpoint /me/predictions
    # is not available and not documented in 4_auth.md.
    # st.write("**Previous Predictions:**")
    # try:
    #     response_preds = requests.get(
    #         f"{API_BASE_URL}/me/predictions",
    #         headers=headers
    #     )
    #     if response_preds.status_code == 200:
    #         predictions = response_preds.json()
    #         if predictions:
    #             for pred in predictions:
    #                 with st.expander(
    #                     f"Prediction ID: {pred.get('uuid', 'N/A')} - "
    #                     f"Status: {pred.get('status', 'N/A')}"
    #                 ):
    #                     st.json(pred)
    #         else:
    #             st.write("No predictions found.")
    #     else:
    #         st.error(
    #             f"Failed to fetch predictions: {response_preds.status_code}"
    #         )
    # except requests.exceptions.RequestException as e:
    #     st.error(f"Connection error fetching predictions: {e}")

elif st.session_state.current_page == "predict":
    st.subheader("Make a New Prediction")
    headers = {"X-API-KEY": st.session_state.api_key}

    input_text = st.text_area(
        "Enter your text for prediction:",
        height=150,
        key="predict_input_text"
    )

    if st.button("Submit Prediction", key="submit_prediction_button"):
        if not input_text.strip():
            st.error("Please enter some text for prediction.")
        else:
            payload = {
                "user_id": st.session_state.user_id,
                "input_text": input_text
            }
            try:
                response = requests.post(
                    f"{API_BASE_URL}/predictions/",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 202:  # Accepted
                    prediction_data = response.json()
                    st.success("Prediction request submitted successfully!")
                    st.write("Prediction Details (Status: Pending):")
                    st.json(prediction_data)
                    # Optionally, navigate away or clear input
                    # navigate_to("dashboard")
                elif response.status_code == 402: # Insufficient balance
                    st.error(
                        "Prediction failed: Insufficient balance. "
                        "Please top up your account."
                    )
                else:
                    st.error(
                        f"Prediction failed: {response.status_code} - {response.text}"
                    )
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error during prediction: {e}")
    # Prediction form fields
    # ...
