import frappe, json
from frappe.utils.data import escape_html
from frappe.website.utils import is_signup_disabled

def sign_up( phone, role, email) -> tuple[int, str]:
	# full_name = first_name + " " + last_name
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				# "first_name": escape_html(full_name),
				"enabled": 1,
				"new_password": "HelloWorld1",
				"user_type": "Website User",
			}
		)
		user.flags.ignore_permissions = True
		user.flags.ignore_password_policy = True
		if phone:
			user.phone = phone
		# if first_name:
		# 	user.first_name = first_name
		# if last_name:
		# 	user.last_name = last_name
		# if age:
		# 	user.age = age
		user.insert()


		# set default signup role as per Portal Settings
		default_role = frappe.db.get_single_value("Portal Settings", "default_role")
		if role == "Shopkeeper":
			user.add_roles(role)
		if default_role:
			user.add_roles(default_role)

		return user

# Signup endpoint
@frappe.whitelist(allow_guest=True)
def user_signup(email, first_name, last_name, age, mobile_no, role):
	pass
    # user_data = sign_up(email, first_name, last_name,age,mobile_no, role)
    # return json.dumps({"message": f"{user_data} registered successfully"})

from frappe import auth

@frappe.whitelist(allow_guest=True)
def login(phone, role):
	print(phone)
	user_data=None
	try:
		user_data=frappe.get_doc("User", {"phone":phone})
	except:
		pass
	if not user_data:
		user_data = sign_up(phone, role, email="test2@mail.com")
		frappe.clear_messages()
		frappe.local.response["message"] = {
                "success_key": 0,
                "message":"Authentication Error!"
            }
	login_user(user_data)

def login_user(user_data):
		try:
				login_manager = auth.LoginManager()
				login_manager.authenticate(user=user_data.email, pwd="HelloWorld1")
				login_manager.post_login()
		except frappe.exceptions.AuthenticationError as e:
				frappe.clear_messages()
				frappe.local.response["message"] = {
					"success_key": 0,
					"message":"Authentication Error!",
					"error":e
				}
				return
		api_generate = generate_keys(frappe.session.user)
		user=frappe.get_doc("User", frappe.session.user)
		frappe.response['message'] = {
            "message":"Login successful",
			"data":{
				"user":user,
				"token":frappe.session.sid,
				"expire_in": frappe.session.session_expiry,
				"type":"Bearer"
			}
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
		