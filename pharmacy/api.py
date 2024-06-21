import frappe
from frappe.utils.data import now_datetime
from frappe import _
def sign_up( phone, role, email) -> tuple[int, str]:
	# full_name = first_name + " " + last_name
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "test",
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
import random
@frappe.whitelist(allow_guest=True)
def login(phone, role):
	# frappe.local.login_manager.logout()
	# frappe.db.commit()
	# print(phone)
	email=f"test{random.randint(1, 100)}@mail.com"
	user_data=None
	try:
		user_data=frappe.get_doc("User", {"phone":phone})
	except:
		pass
	if not user_data:
		user_data = sign_up(phone, role, email=email)
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
		frappe.response['data'] = {
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
		
import frappe.model.rename_doc as rd
@frappe.whitelist(allow_guest=True)
def edit_profile(phone, email, fullname, age, gender):
	if phone:
		try:
			user_data=frappe.get_doc("User", {"phone":phone})
			if user_data.enabled == 0:
				frappe.response['http_status_code'] = 403  # Forbidden
				frappe.response['data'] = {
					"message": f"User {user_data.email} is disabled. Please contact your System Manager."
				}
				return
			user_data.flags.ignore_permissions = True
			user_data.flags.ignore_password_policy = True
			if fullname:
				user_data.first_name = fullname.split(" ")[0]
				user_data.last_name = fullname.split(" ")[-1]
			if age:
				user_data.age = age
			if gender:
				user_data.gender = gender
			user_data.save()
			if email:
				old = user_data.email
				rd.rename_doc("User", old, email, force=True)
			frappe.response['data'] = {
				"status":200,
				"message":"Data updated successfully",
				}
		except frappe.exceptions.AuthenticationError as e:
					frappe.clear_messages()
					frappe.local.response["message"] = {
						"success_key": 0,
						"message":"Authentication Error!",
						"error":e
					}
		except frappe.exceptions.ValidationError as v:
			frappe.clear_messages()
			frappe.local.response["message"] = {
					"success_key": 0,
					"error": v
				}
	else:
		frappe.clear_messages()
		frappe.local.response["message"] = {
			"success_key": 0,
			"error": "Phone not found"
			}


@frappe.whitelist()
def categories():
	try:
		categories = frappe.get_all('Product Category', fields=['name', 'category_name', 'description', 'icon'])
		response = []
		for category in categories:
			
			subcategories = frappe.get_all(
                'Product Sub Category',
                filters={'category_name': category['name']},
                fields=['name', 'subcategory_name', 'description', 'icon']
            )
			response.append({
				"id": category['name'],
                'category_name': category['category_name'],
                'description': category.get('description', ''),
				'icon':category.get('icon'),
                'subcategories': subcategories
            })

		return response
	except frappe.exceptions.AuthenticationError as e:
		frappe.clear_messages()
		frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Authentication Error!",
            "error": str(e)
        }
	except frappe.exceptions.ValidationError as v:
		frappe.clear_messages()
		frappe.local.response["message"] = {
            "success_key": 0,
            "error": str(v)
        }


@frappe.whitelist(allow_guest=True)
def products(category_name=None, subcategory_name=None):
	try:
		response = []
		if category_name:
			categories = frappe.get_all(
				'Product Category',
				filters={'category_name': category_name},
				fields=['name', 'category_name', 'description', 'icon']
		    )
			# return categories
			for category in categories:
				subcategories = frappe.get_all(
				    'Product Sub Category',
				    filters={'category_name': category['name']},
				    fields=['name', 'subcategory_name', 'description', 'icon']
				)
				# return subcategories
				for subcategory in subcategories:
					print("subcategory",subcategory)
					products = frappe.get_all(
						'Product',
						filters={
						    'subcategory_name': subcategory['name']
						},
						fields=[
						    'name',
							'product_name',
							'icon',
						    'description',
						    'price',
						    'usage',
						    'side_effects',
						    'alternative',
							'subcategory_name'
						]
				    )
					for product in products:
						product_detail = {
						    'id': product['name'],
							'name':product.get('product_name', ''),
							'icon':product.get('icon', ''),
						    'description': product.get('description', ''),
						    'price': product.get('price', 0.0),
						    'usage': product.get('usage', ''),
						    'side_effects': product.get('side_effects', ''),
						    'alternative': product.get('alternative', None),
						    'category': {
								'id':category['name'],
								'category_name': category['category_name'],
								'description': category.get('description', ''),
								'subcategories': [{
									'id': subcategory['name'],
								    'subcategory_name': subcategory['subcategory_name'],
								    'subcategory_description': subcategory.get('description', '')
								}]
						    }
						}

						# Add the detailed product to the response
						response.append(product_detail)
					return response
		elif subcategory_name:
			subcategories = frappe.get_all(
				'Product Sub Category',
				filters={'subcategory_name': subcategory_name},
				fields=['name', 'subcategory_name', 'description', 'category_name']
		    )
			for subcategory in subcategories:
				category = frappe.get_doc('Product Category', subcategory['category_name'])
				products = frappe.get_all(
				    'Product',
				    filters={
						'subcategory_name': subcategory['name']
				    },
				    fields=[
						'name',
						'icon',
						'product_name',
						'description',
						'price',
						'usage',
						'side_effects',
						'alternative'
				    ]
				)
				# For each product, add category and subcategory details
				for product in products:
					product_detail = {
						'id': product['name'],
						'name':product.get('product_name', ''),
						'icon':product.get('icon', ''),
						'description': product.get('description', ''),
						'price': product.get('price', 0.0),
						'usage': product.get('usage', ''),
						'side_effects': product.get('side_effects', ''),
						'alternative': product.get('alternative', None),
						'category': {
						    'category_name': category.category_name,
						    'description': category.description,
						    'subcategories': [{
								'subcategory_name': subcategory['subcategory_name'],
								'subcategory_description': subcategory.get('description', '')
						    }]
						}
				    }
					response.append(product_detail)
				return response
		else:
			categories = frappe.get_all(
				'Product Category',
				fields=['name', 'category_name', 'description', 'icon']
		    )
			# return categories
			for category in categories:
				subcategories = frappe.get_all(
				    'Product Sub Category',
				    fields=['name', 'subcategory_name', 'description', 'icon']
				)
				# return subcategories
				for subcategory in subcategories:
					print("subcategory",subcategory)
					products = frappe.get_all(
						'Product',
						fields=[
						    'name',
							'icon',
							'product_name',
						    'description',
						    'price',
						    'usage',
						    'side_effects',
						    'alternative',
							'subcategory_name'
						]
				    )
					for product in products:
						product_detail = {
						    'id': product['name'],
							'name':product.get('product_name', ''),
							'icon':product.get('icon', ''),
						    'description': product.get('description', ''),
						    'price': product.get('price', 0.0),
						    'usage': product.get('usage', ''),
						    'side_effects': product.get('side_effects', ''),
						    'alternative': product.get('alternative', None),
						    'category': {
								'id':category['name'],
								'category_name': category['category_name'],
								'description': category.get('description', ''),
								'subcategories': [{
									'id': subcategory['name'],
								    'subcategory_name': subcategory['subcategory_name'],
								    'subcategory_description': subcategory.get('description', '')
								}]
						    }
						}

						# Add the detailed product to the response
						response.append(product_detail)
					return response
	except frappe.exceptions.AuthenticationError as e:
		frappe.clear_messages()
		frappe.local.response["message"] = {
		    "success_key": 0,
		    "message": "Authentication Error!",
		    "error": str(e)
		}
	except frappe.exceptions.ValidationError as v:
		frappe.clear_messages()
		frappe.local.response["message"] = {
		    "success_key": 0,
		    "error": str(v)
		}

