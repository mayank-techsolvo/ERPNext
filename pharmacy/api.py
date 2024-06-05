import frappe, json
from frappe.utils.data import escape_html
from frappe.website.utils import is_signup_disabled

def sign_up(email: str, full_name: str, first_name, last_name,age, mobile_no) -> tuple[int, str]:

	user = frappe.db.get("User", {"email": email})
	if user:
		if user.enabled:
			return 0, _("Already Registered")
		else:
			return 0, _("Registered but disabled")
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": escape_html(full_name),
				"enabled": 1,
				"new_password": "HelloWorld",
				"user_type": "Website User",
			}
		)
		user.flags.ignore_permissions = True
		user.flags.ignore_password_policy = True
		user.insert()
		user.first_name = first_name
		user.last_name = last_name
		user.mobile_no = mobile_no
		user.age = age

		# set default signup role as per Portal Settings
		default_role = frappe.db.get_single_value("Portal Settings", "default_role")
		if default_role:
			user.add_roles(default_role)

		return user

# Signup endpoint
@frappe.whitelist(allow_guest=True)
def user_signup(email, first_name, last_name, age, mobile_no, role):
    # Validate input data
    # Handle validation errors
    full_name = first_name + " " + last_name
    # Call Frappe's signup function
    user_data = sign_up(email, full_name, first_name, last_name,age,mobile_no)
    print("user", user_data)
    # Return success response
    return json.dumps({"message": f"{user_data} registered successfully"})

from frappe import auth

@frappe.whitelist(allow_guest=True)
def login(mobile_no):
	print(mobile_no)
	user_data=frappe.get_doc("User", {"mobile_no":mobile_no})
	print(user_data.email)
	if user_data.email:
		try:
			login_manager = auth.LoginManager()
			login_manager.authenticate(user=user_data.email, pwd="HelloWorld1")
			login_manager.post_login()
		except frappe.exceptions.AuthenticationError:
			frappe.clear_messages()
			frappe.local.response["message"] = {
                "success_key": 0,
                "message":"Authentication Error!"
            }
			return
		api_generate = generate_keys(frappe.session.user)
		user=frappe.get_doc("User", frappe.session.user)
		frappe.response['message'] = {
            "success_key":1,
            "message":"Authentication success",
            "sid":frappe.session.sid,
            "api_key":user.api_key,
            "api_secret": api_generate,
            "email": user.email
        }
	else:
		frappe.clear_messages()
		frappe.local.response["message"] = {
                "success_key": 0,
                "message":"Authentication Error!"
            }

def generate_keys(user):
	user_details = frappe.get_doc("User", user)
	api_secret = frappe.generate_hash(length=15)
	if not user_details.api_key:
		api_key = frappe.generate_hash(length=15)
		user_details.api_key = api_key
	user_details.api_secret = api_secret
	user_details.save()
	return api_secret
		
###  
# Login endpoint
# @frappe.whitelist(allow_guest=True)
# def user_login(email, password):
#     # Authenticate user
#     user = authenticate(email, password)

#     # Check if authentication was successful
#     if user:
#         # Create session for the user
#         frappe.local.login_manager.user = user.name
#         frappe.local.login_manager.post_login()

#         # Return success response with user information
#         return jsonify({"message": "Login successful", "user": user.as_dict()})
#     else:
#         # Return error response
#         return jsonify({"message": "Invalid credentials"})
# curl -X POST \
#   http://127.0.0.1:8000/api/method/pharmacy.api.user_signup \
#   -H 'Content-Type: application/json' \
#   -d '{
#     "email": "mrwwf@gmail.com",
#     "password": "password123",  
#     "first_name": "John",
#     "last_name": "Doe",
#     "age": 30,
#     "role": "Customer"  
# }'   
# hooks.py
# from .api import user_signup#, user_login

# # Whitelisted methods
# whitelist = ["user_signup"]

# api.py