import streamlit as st
import requests
import time  # Added for auto-check timing
import html # Added for escaping HTML in strings

# Configuration
API_BASE_URL = "http://127.0.0.1:53250/api/v1"

st.set_page_config(page_title="SimpleBillingLLM Client", layout="wide")

st.title("SimpleBillingLLM API Client")


# --- Helper function for status colors ---
def get_status_color(status):
    """Returns a color string based on prediction status."""
    status_str = str(status).upper()  # Ensure status is uppercase string
    if status_str == "COMPLETED":
        return "green"
    elif status_str == "PROCESSING":
        return "blue"
    elif status_str == "PENDING":
        return "orange"
    elif status_str == "FAILED":
        return "red"
    else:
        return "grey"  # Default for unknown or other statuses


# --- New Helper function for TINY Prediction Display ---
def format_prediction_html_tiny(pred_data):
    """
    Formats a prediction into a compact HTML representation.

    Shows Status, ID, and snippets for Input/Output, each separated by a line.
    Full details should be handled by the caller using an expander.
    """
    status_val = pred_data.get('status', 'N/A')
    color = get_status_color(status_val)
    uuid_val = pred_data.get('uuid', 'N/A')

    input_text_full = pred_data.get('input_text', '')
    output_text_raw = pred_data.get('output_text')  # Can be None

    # Escape all dynamic string data for HTML display
    escaped_uuid = html.escape(str(uuid_val))
    escaped_status = html.escape(str(status_val))

    # Shorter snippets for tiny view (e.g., 70 chars)
    input_text_display = html.escape(input_text_full[:70])
    input_ellipsis = '...' if len(input_text_full) > 70 else ''

    if output_text_raw is not None:
        output_text_full = str(output_text_raw)
        output_text_display = html.escape(output_text_full[:70])
        output_ellipsis = '...' if len(output_text_full) > 70 else ''
    else:
        output_text_display = "Not available"
        output_ellipsis = ''

    # Tiny HTML structure
    # Reduced padding, elements separated by <hr>
    html_content = f"""
    <div style="border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;">
        <p style="margin-bottom: 3px;">
            <strong>Input:</strong> {input_text_display}{input_ellipsis}
        </p>
        <hr style="margin-top: 5px; margin-bottom: 5px; border-width: 0 0 1px;">
        <p style="margin-bottom: 3px;">
            <strong>Output:</strong> {output_text_display}{output_ellipsis}
        </p>
    </div>
    """
    return html_content


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
# Added for auto-check
if 'auto_check_prediction_info' not in st.session_state:
    st.session_state.auto_check_prediction_info = None


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
        else:
            st.error(
                f"Failed to fetch user balance: {response_balance.status_code} "
                f"- {response_balance.text}"
            )
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error fetching user balance: {e}")

    # Fetch and Display Predictions
    st.write("**Your Predictions:**")
    try:
        preds_url = (
            f"{API_BASE_URL}/predictions/user/{st.session_state.user_id}"
        )
        response_preds = requests.get(preds_url, headers=headers)
        if response_preds.status_code == 200:
            predictions = response_preds.json()
            if predictions:
                for pred_item in predictions:  # Renamed to avoid conflict
                    # Use the new tiny HTML formatter
                    tiny_html_content = format_prediction_html_tiny(pred_item)
                    st.markdown(tiny_html_content, unsafe_allow_html=True)
                    # Expander for full details remains
                    expander_title = (
                        f"View Full Details for ID: {pred_item.get('uuid', 'N/A')}"
                    )
                    with st.expander(expander_title):
                        st.json(pred_item)
            else:
                st.write("No predictions found.")
        else:
            st.error(
                f"Failed to fetch predictions: {response_preds.status_code} - "
                f"{response_preds.text}"
            )
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error fetching predictions: {e}")

elif st.session_state.current_page == "predict":
    st.subheader("Make a New Prediction")
    headers = {"X-API-KEY": st.session_state.api_key}

    # --- Helper functions for prediction status display on this page ---
    def display_prediction_status_nicely(status_data, prefix=""):
        """Displays prediction status using the new tiny formatter."""
        if not status_data or not isinstance(status_data, dict):
            st.warning(
                f"{html.escape(prefix)}Could not retrieve or parse status details."
            )
            return

        # Use the new tiny HTML formatter
        tiny_html_content = format_prediction_html_tiny(status_data)

        # Optional: Add prefix if still needed, outside the main box
        if prefix:
            st.markdown(f"*{html.escape(prefix)}*")

        st.markdown(tiny_html_content, unsafe_allow_html=True)

        # Expander for full details
        expander_title = (
            f"View Full Details for ID: {status_data.get('uuid', 'N/A')}"
        )
        with st.expander(expander_title):
            st.json(status_data)

    def fetch_prediction_status_for_auto_check(uuid_to_check,
                                               display_prefix=""):
        """Fetches and displays prediction status, returns status data."""
        try:
            status_url = f"{API_BASE_URL}/predictions/{uuid_to_check}"
            # No API key for this specific endpoint as per original code
            response_status = requests.get(status_url)

            if response_status.status_code == 200:
                status_data = response_status.json()
                display_prediction_status_nicely(status_data, display_prefix)
                return status_data
            elif response_status.status_code == 404:
                st.error(
                    f"{display_prefix}Prediction with UUID "
                    f"'{uuid_to_check}' not found."
                )
            else:
                err_text = response_status.text
                st.error(
                    f"{display_prefix}Failed to fetch status: "
                    f"{response_status.status_code} - {err_text}"
                )
        except requests.exceptions.RequestException as e:
            st.error(f"{display_prefix}Connection error: {e}")
        return None
    # --- End Helper Functions ---

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
                    prediction_uuid = prediction_data.get("uuid")
                    st.success(
                        f"Prediction for UUID `{prediction_uuid}` submitted! "
                        "Initiating status check..."
                    )

                    if prediction_uuid:
                        st.session_state.auto_check_prediction_info = {
                            "uuid": prediction_uuid,
                            "submitted_at": time.time(),
                            "status_after_submit": None,
                            "status_after_5s": None,
                        }
                        st.rerun()  # Rerun to trigger the auto-check logic
                    else:
                        st.warning(
                            "Prediction submitted but UUID not found. "
                            "Cannot auto-check."
                        )
                        st.json(prediction_data)

                elif response.status_code == 402:  # Insufficient balance
                    st.error(
                        "Prediction failed: Insufficient balance. "
                        "Please top up your account."
                    )
                else:
                    st.error(
                        f"Prediction failed: {response.status_code} - "
                        f"{response.text}"
                    )
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error during prediction: {e}")

    # --- Auto-check logic for the last submitted prediction ---
    if st.session_state.auto_check_prediction_info:
        info = st.session_state.auto_check_prediction_info
        uuid_to_track = info["uuid"]
        # Use container for cleaner updates
        auto_check_placeholder = st.empty()

        with auto_check_placeholder.container():
            # --- Immediate Check ---
            if info["status_after_submit"] is None:
                st.write(
                    f"Performing initial status check for `{uuid_to_track}`..."
                )
                s_data = fetch_prediction_status_for_auto_check(
                    uuid_to_track, "Current "
                )
                info["status_after_submit"] = s_data if s_data else "failed"
                st.rerun()

            # --- 5-Second Check ---
            elif info["status_after_submit"] != "failed" and \
                 info["status_after_5s"] is None:
                now = time.time()
                if now - info["submitted_at"] >= 5:
                    st.write(
                        f"Performing 5s check for `{uuid_to_track}`..."
                    )
                    s_data = fetch_prediction_status_for_auto_check(
                        uuid_to_track, "Status after 5s: "
                    )
                    info["status_after_5s"] = s_data if s_data else "failed"
                    # No st.rerun() here, let display update
                else:
                    rem_time = 5 - (now - info["submitted_at"])
                    st.info(
                        f"Next check for `{uuid_to_track}` in {rem_time:.0f}s."
                    )
                    if rem_time > 0:
                        # Brief pause to allow UI update for countdown
                        time.sleep(1)
                        st.rerun()

            # --- Both checks done or first failed ---
            elif info["status_after_5s"] is not None or \
                 info["status_after_submit"] == "failed":
                msg = f"Auto-checks for `{uuid_to_track}` done."
                if info["status_after_submit"] == "failed":
                    msg = f"Initial check for `{uuid_to_track}` failed."
                elif info["status_after_5s"] == "failed":
                    msg = f"5s check for `{uuid_to_track}` failed."
                st.info(msg)
                # Clear info so it doesn't re-run indefinitely
                # st.session_state.auto_check_prediction_info = None

    st.divider()
    st.subheader("Check Prediction Status Manually")
    prediction_uuid_to_check = st.text_input(
        "Enter Prediction UUID to check status:",
        key="prediction_uuid_check"
    )
    if st.button("Check Status", key="check_status_button"):
        if not prediction_uuid_to_check.strip():
            st.error("Please enter a Prediction UUID.")
        else:
            uuid_str = prediction_uuid_to_check.strip()
            # Reusing the fetch and display function
            fetch_prediction_status_for_auto_check(uuid_str, "Manual Check: ")
