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

def get_user_info_by_phone(phone_number):
    # Fetch user information based on phone number
    user_info = frappe.get_all(
        "User",  # Replace with the correct doctype if different
        filters={'phone': phone_number},
        fields=['name', 'email', 'phone', 'full_name']  # Add more fields as needed
    )
    
    # Check if any user was found
    if user_info:
        return user_info[0]  # Return the first matching user
    else:
        return None  # Return None if no matching user is found

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
					products = frappe.get_all(
						'Product',
						filters={
						    'category_name': category['name']
						},
						limit=10,
						order_by='price desc',
						fields=[
						    'name',
							'product_name',
							'icon',
							'expiry',
						    'description',
						    'price',
						    'usage',
						    'side_effects',
						    'alternative',
							'category_name'
						]
				    )
					product_data = []
					for product in products:
						product_detail = {
						    'name': product['name'],
							'product_name':product.get('product_name', ''),
							'icon':product.get('icon', ''),
							'expiry':product.get('expiry', ''),
						    'description': product.get('description', ''),
						    'price': product.get('price', 0.0),
						    'usage': product.get('usage', ''),
						    'side_effects': product.get('side_effects', ''),
						    'alternative': product.get('alternative', None),
						}
						product_data.append(product_detail)
						# Add the detailed product to the response
					response.append({
			"id": category['name'],
			'category_name': category['category_name'],
			'description': category.get('description', ''),
			'icon':category.get('icon'),
			'products': product_data
		})
		# for category in categories:
			
		# 	subcategories = frappe.get_all(
        #         'Product Sub Category',
        #         filters={'category_name': category['name']},
        #         fields=['name', 'subcategory_name', 'description', 'icon']
        #     )
		# 	response.append({
		# 		"id": category['name'],
        #         'category_name': category['category_name'],
        #         'description': category.get('description', ''),
		# 		'icon':category.get('icon'),
        #         'subcategories': subcategories
        #     })

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
	response = []
	try:
		if(category_name):
			categories = frappe.get_all('Product Category', filters={'category_name': category_name}, fields=['name', 'category_name', 'description', 'icon'])
			for category in categories:
						products = frappe.get_all(
							'Product',
							filters={
								'category_name': category['name']
							},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						product_data = []
						for product in products:
							product_detail = {
								'name': product['name'],
								'product_name':product.get('product_name', ''),
								'icon':product.get('icon', ''),
								'expiry':product.get('expiry', ''),
								'description': product.get('description', ''),
								'price': product.get('price', 0.0),
								'usage': product.get('usage', ''),
								'side_effects': product.get('side_effects', ''),
								'alternative': product.get('alternative', None),
								'category_name':product.get('category_name', None)
							}
							product_data.append(product_detail)
							# Add the detailed product to the response
						response.append({
				"id": category['name'],
				'category_name': category['category_name'],
				'description': category.get('description', ''),
				'icon':category.get('icon'),
				'products': product_data
			})
		# for category in categories:
			
		# 	subcategories = frappe.get_all(
        #         'Product Sub Category',
        #         filters={'category_name': category['name']},
        #         fields=['name', 'subcategory_name', 'description', 'icon']
        #     )
		# 	response.append({
		# 		"id": category['name'],
        #         'category_name': category['category_name'],
        #         'description': category.get('description', ''),
		# 		'icon':category.get('icon'),
        #         'subcategories': subcategories
        #     })

			return response
		else:
			products = frappe.get_all(
							'Product',
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
			product_data = []
			for product in products:
				product_detail = {
					'name': product['name'],
					'product_name':product.get('product_name', ''),
					'icon':product.get('icon', ''),
					'expiry':product.get('expiry', ''),
					'description': product.get('description', ''),
					'price': product.get('price', 0.0),
					'usage': product.get('usage', ''),
					'side_effects': product.get('side_effects', ''),
					'alternative': product.get('alternative', None),
					'category_name':product.get('category_name', None)

				}
				product_data.append(product_detail)
				# Add the detailed product to the response
			response.append({
				'products': product_data
			})
		# for category in categories:
			
		# 	subcategories = frappe.get_all(
        #         'Product Sub Category',
        #         filters={'category_name': category['name']},
        #         fields=['name', 'subcategory_name', 'description', 'icon']
        #     )
		# 	response.append({
		# 		"id": category['name'],
        #         'category_name': category['category_name'],
        #         'description': category.get('description', ''),
		# 		'icon':category.get('icon'),
        #         'subcategories': subcategories
        #     })

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
	# try:
	# 	response = []
	# 	if category_name:
	# 		categories = frappe.get_all(
	# 			'Product Category',
	# 			filters={'category_name': category_name},
	# 			fields=['name', 'category_name', 'description', 'icon']
	# 	    )
	# 		# return categories
	# 		for category in categories:
	# 			subcategories = frappe.get_all(
	# 			    'Product Sub Category',
	# 			    filters={'category_name': category['name']},
	# 			    fields=['name', 'subcategory_name', 'description', 'icon']
	# 			)
	# 			# return subcategories
	# 			for subcategory in subcategories:
	# 				print("subcategory",subcategory)
	# 				products = frappe.get_all(
	# 					'Product',
	# 					filters={
	# 					    'subcategory_name': subcategory['name']
	# 					},
	# 					fields=[
	# 					    'name',
	# 						'product_name',
	# 						'icon',
	# 						'expiry',
	# 					    'description',
	# 					    'price',
	# 					    'usage',
	# 					    'side_effects',
	# 					    'alternative',
	# 						'subcategory_name'
	# 					]
	# 			    )
	# 				for product in products:
	# 					product_detail = {
	# 					    'id': product['name'],
	# 						'name':product.get('product_name', ''),
	# 						'icon':product.get('icon', ''),
	# 						'expiry':product.get('expiry', ''),
	# 					    'description': product.get('description', ''),
	# 					    'price': product.get('price', 0.0),
	# 					    'usage': product.get('usage', ''),
	# 					    'side_effects': product.get('side_effects', ''),
	# 					    'alternative': product.get('alternative', None),
	# 					    'category': {
	# 							'id':category['name'],
	# 							'category_name': category['category_name'],
	# 							'description': category.get('description', ''),
	# 							'subcategories': [{
	# 								'id': subcategory['name'],
	# 							    'subcategory_name': subcategory['subcategory_name'],
	# 							    'subcategory_description': subcategory.get('description', '')
	# 							}]
	# 					    }
	# 					}

	# 					# Add the detailed product to the response
	# 					response.append(product_detail)
	# 				return response
	# 	elif subcategory_name:
	# 		subcategories = frappe.get_all(
	# 			'Product Sub Category',
	# 			filters={'subcategory_name': subcategory_name},
	# 			fields=['name', 'subcategory_name', 'description', 'category_name']
	# 	    )
	# 		for subcategory in subcategories:
	# 			category = frappe.get_doc('Product Category', subcategory['category_name'])
	# 			products = frappe.get_all(
	# 			    'Product',
	# 			    filters={
	# 					'subcategory_name': subcategory['name']
	# 			    },
	# 			    fields=[
	# 					'name',
	# 					'icon',
	# 					'expiry',
	# 					'product_name',
	# 					'description',
	# 					'price',
	# 					'usage',
	# 					'side_effects',
	# 					'alternative'
	# 			    ]
	# 			)
	# 			# For each product, add category and subcategory details
	# 			for product in products:
	# 				product_detail = {
	# 					'id': product['name'],
	# 					'name':product.get('product_name', ''),
	# 					'icon':product.get('icon', ''),
	# 					'expiry':product.get('expiry', ''),
	# 					'description': product.get('description', ''),
	# 					'price': product.get('price', 0.0),
	# 					'usage': product.get('usage', ''),
	# 					'side_effects': product.get('side_effects', ''),
	# 					'alternative': product.get('alternative', None),
	# 					'category': {
	# 					    'category_name': category.category_name,
	# 					    'description': category.description,
	# 					    'subcategories': [{
	# 							'subcategory_name': subcategory['subcategory_name'],
	# 							'subcategory_description': subcategory.get('description', '')
	# 					    }]
	# 					}
	# 			    }
	# 				response.append(product_detail)
	# 			return response
	# 	else:
	# 		categories = frappe.get_all(
	# 			'Product Category',
	# 			fields=['name', 'category_name', 'description', 'icon']
	# 	    )
	# 		# return categories
	# 		for category in categories:
	# 			subcategories = frappe.get_all(
	# 			    'Product Sub Category',
	# 			    fields=['name', 'subcategory_name', 'description', 'icon']
	# 			)
	# 			# return subcategories
	# 			for subcategory in subcategories:
	# 				print("subcategory",subcategory)
	# 				products = frappe.get_all(
	# 					'Product',
	# 					fields=[
	# 					    'name',
	# 						'icon',
	# 						'expiry',
	# 						'product_name',
	# 					    'description',
	# 					    'price',
	# 					    'usage',
	# 					    'side_effects',
	# 					    'alternative',
	# 						'subcategory_name'
	# 					]
	# 			    )
	# 				for product in products:
	# 					product_detail = {
	# 					    'id': product['name'],
	# 						'name':product.get('product_name', ''),
	# 						'icon':product.get('icon', ''),
	# 						'expiry':product.get('expiry', ''),
	# 					    'description': product.get('description', ''),
	# 					    'price': product.get('price', 0.0),
	# 					    'usage': product.get('usage', ''),
	# 					    'side_effects': product.get('side_effects', ''),
	# 					    'alternative': product.get('alternative', None),
	# 					    'category': {
	# 							'id':category['name'],
	# 							'category_name': category['category_name'],
	# 							'description': category.get('description', ''),
	# 							'subcategories': [{
	# 								'id': subcategory['name'],
	# 							    'subcategory_name': subcategory['subcategory_name'],
	# 							    'subcategory_description': subcategory.get('description', '')
	# 							}]
	# 					    }
	# 					}

	# 					# Add the detailed product to the response
	# 					response.append(product_detail)
	# 				return response
	# except frappe.exceptions.AuthenticationError as e:
	# 	frappe.clear_messages()
	# 	frappe.local.response["message"] = {
	# 	    "success_key": 0,
	# 	    "message": "Authentication Error!",
	# 	    "error": str(e)
	# 	}
	# except frappe.exceptions.ValidationError as v:
	# 	frappe.clear_messages()
	# 	frappe.local.response["message"] = {
	# 	    "success_key": 0,
	# 	    "error": str(v)
	# 	}

from datetime import datetime

def format_date(date_string):
    date = datetime.strptime(str(date_string), "%Y-%m-%d %H:%M:%S.%f")
    formatted_date = date.strftime("%a, %d %b %Y")
    
    return {formatted_date}

@frappe.whitelist()
def orders(phone=None):
	response = []
	try:
		if phone:
			orders = frappe.get_all(
                "Orders",
                filters={'phone': phone},
                fields=['name','status','order_price', 'payment_status', 'modified', 'shipping_price', 'discount', 'payable_amount']
            )
			if orders:
				for order in orders:
					order_products = frappe.get_all(
						"PIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['product', 'quantity' ]
					)
					products = []
					for order_product in order_products:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': order_product.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								products.append(product_details[0])
					order_details = {
						'order_id': order.name,
						'status':order.status,
						'modified':order.modified,
						'order_price':order.order_price,
						'payment_status': order.payment_status,
						'discount': order.discount,
						'payable_amount': order.payable_amount,
						'shipping_price': order.shipping_price,
						'products': products
					}
					response.append(order_details)
		else:
			orders = frappe.get_all(
                "Orders",
                fields=['name','status','order_price', 'payment_status', 'modified', 'shipping_price', 'discount', 'payable_amount', 'phone', 'slot_time', 'slot_date']
            )
			if orders:
				ordered_count = len([order for order in orders if order.status == "Ordered"])
				cancelled = len([order for order in orders if order.status == "Cancelled"])
				delivered = len([order for order in orders if order.status == "Delivered"])
				packaged = len([order for order in orders if order.status == "Packaged"])
				shipped = len([order for order in orders if order.status == "Shipped"])
				total_orders = len(orders)
				for order in orders:
					if order.order_traced_location:
							address = frappe.get_doc("Address", {'name': order.order_traced_location}, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
					else:
							address = ""
					order_products = frappe.get_all(
						"PIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['product', 'quantity' ]
					)
					products = []
					for order_product in order_products:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': order_product.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								products.append(product_details[0])
					order_details = {
						'order_id': order.name,
						'user': get_user_info_by_phone(order.phone),
						'address': address,
						'slot_time':order.slot_time,
						'slot_date': order.slot_date,
						'total_order':total_orders,
						'pending_order':ordered_count,
						'cancelled_order':cancelled,
						'delivered_order': delivered,
						'packaged_order': packaged,
						'shipped_order':shipped,
						'status':order.status,
						'modified':order.modified,
						'order_price':order.order_price,
						'payment_status': order.payment_status,
						'discount': order.discount,
						'payable_amount': order.payable_amount,
						'shipping_price': order.shipping_price,
						'products': products
					}
					response.append(order_details)
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

@frappe.whitelist()
def order(id=None):
	response = []
	try:
		if id:
			order = frappe.get_doc(
				"Order Data",{'name': id},['name', 'payment_status', 'modified', 'creation', 'payable_amount','discount', 'shipping_price', 'order_price', 'test_discount', 'test_shipping_price', 'test_price']
			)

			if order:
					if order.order_traced_location:
						address = frappe.get_doc("Address", order.order_traced_location, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
					else:
						address = ""
					prescription = []
					prescrip = frappe.get_all(
						"Prescribe",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['prescription'])
					for prescribe in prescrip:
							pre = frappe.get_all('Prescription',filters={'name':prescribe.prescription}, fields=['prescription', 'name'])
							if (pre):
								prescription.append({"id":pre[0].name, "url":pre[0].prescription})

					# Fetch test orders (products)
					test_orders = frappe.get_all(
						"PIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['name','product', 'price', 'quantity', 'status']
					)
					products = []
					for test_order in test_orders:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': test_order.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								product_details[0]['id'] = test_order.name
								product_details[0]['price'] = test_order.price
								product_details[0]['status'] = test_order.status
								product_details[0]['quantity'] = test_order.quantity
								products.append(product_details[0])
					test_orders = frappe.get_all(
						"LIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['name','product', 'price', 'slot_time', 'slot_date', 'quantity', 'test_status']
					)
					lab_tests = []
					for test_order in test_orders:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': test_order.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								product_details[0]['id'] = test_order.name
								product_details[0]['slot_time'] = test_order.slot_time
								product_details[0]['slot_date'] = test_order.slot_date
								product_details[0]['price'] = test_order.price
								product_details[0]['test_status'] = test_order.test_status
								product_details[0]['quantity'] = test_order.quantity
								lab_tests.append(product_details[0])
					# Append order data to response
					response.append({
						'order_id': order.name,
						'address': address,
						'modified': order.modified,
						'creation': order.creation,
						'payable_amount': order.payable_amount,
						'prescriptions': prescription,
						'product_list': {
				'pricing':{
					'discount': order.discount,
					'shipping_price': order.shipping_price,
					'status':"order.med_status",
					'order_price':order.order_price,
					},
				'products':products
				},
				'test_list': {
				'pricing':{
					'test_discount': order.test_discount,
					'test_shipping_price': order.test_shipping_price,
					'test_status':"order.lab_test_status",
					'test_price':order.test_price,
					},
				'tests':lab_tests
				}
						})

			return response
		else:
			return "ID Not found"
	
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

	# response = []
	# try:
	# 	if id:
	# 		order = frappe.get_doc("Orders", {'name': id}, ['name','status','order_price', 'payment_status', 'modified'])
	# 		if order:
	# 			order_products = frappe.get_all(
	# 						"PIO",  # Replace with the correct child table doctype name
	# 						filters={'parent': id},
	# 						fields=['product', 'quantity']
	# 					)
	# 			products = []
	# 			for order_product in order_products:
	# 						product_details = frappe.get_all(
	# 							"Product",  # Replace with the correct product doctype name
	# 							filters={'name': order_product.product},
	# 							fields=[
	# 								'name',
	# 								'product_name',
	# 								'icon',
	# 								'expiry',
	# 								'description',
	# 								'price',
	# 								'usage',
	# 								'side_effects',
	# 								'alternative',
	# 								'category_name'
	# 							]
	# 						)
	# 						if product_details:
	# 								products.append(product_details[0])
	# 			order_details = {
	# 						'order_id': order.name,
	# 						'status':order.status,
	# 						'modified':order.modified,
	# 						'order_price':order.order_price,
	# 						'payment_status': order.payment_status,
	# 						'discount': order.discount,
	# 						'payable_amount': order.payable_amount,
	# 						'shipping_price': order.shipping_price,
	# 						'products': products
	# 					}
	# 			response.append(order_details)
	# 		return response
	# except frappe.exceptions.AuthenticationError as e:
	# 	frappe.clear_messages()
	# 	frappe.local.response["message"] = {
    #         "success_key": 0,
    #         "message": "Authentication Error!",
    #         "error": str(e)
    #     }
	# except frappe.exceptions.ValidationError as v:
	# 	frappe.clear_messages()
	# 	frappe.local.response["message"] = {
    #         "success_key": 0,
    #         "error": str(v)
    #     }

# @frappe.whitelist(allow_guest=False)
# def lab_test(phone=None):
# 	response = []
# 	try:
# 		if phone:
# 			tests = frappe.get_all(
#                 "Lab Test",
#                 filters={'phone': phone},
#                 fields=['name','status','test_price', 'payment_status', 'modified', 'shipping_price', 'discount', 'payable_amount', 'slot_time', 'slot_date', 'order_traced_location']
#             )
# 			if tests:
# 				for test in tests:
# 					if test.order_traced_location:
# 						address = frappe.get_doc("Address", {'name': test.order_traced_location}, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
# 					else:
# 						address = ""
# 					test_products = frappe.get_all(
# 						"PIO",  # Replace with the correct child table doctype name
# 						filters={'parent': test.name},
# 						fields=['product', 'quantity' ]
# 					)
# 					products = []
# 					for test_product in test_products:
# 						product_details = frappe.get_all(
# 							"Product",  # Replace with the correct product doctype name
# 							filters={'name': test_product.product},
# 							fields=[
# 								'name',
# 								'product_name',
# 								'icon',
# 								'expiry',
# 								'description',
# 								'price',
# 								'usage',
# 								'side_effects',
# 								'alternative',
# 								'category_name'
# 							]
# 						)
# 						if product_details:
# 								products.append(product_details[0])
# 					test_details = {
# 						'test_id': test.name,
# 						'status':test.status,
# 						'modified':test.modified,
# 						'test_price':test.test_price,
# 						'payment_status': test.payment_status,
# 						'order_trace_location' : address,
# 						'discount': test.discount,
# 						'payable_amount': test.payable_amount,
# 						'shipping_price': test.shipping_price,
# 						'slot_date': test.slot_date,
# 						'slot_time': test.slot_time,
# 						'products': products
# 					}
# 					response.append(test_details)
# 		else:
# 			tests = frappe.get_all(
#                 "Lab Test",
#                 fields=['name','status','test_price', 'payment_status', 'modified', 'shipping_price', 'discount', 'payable_amount', 'slot_time', 'slot_date', ]
#             )
# 			if tests:
# 				for test in tests:
# 					test_products = frappe.get_all(
# 						"PIO",  # Replace with the correct child table doctype name
# 						filters={'parent': test.name},
# 						fields=['product', 'quantity' ]
# 					)
# 					products = []
# 					for test_product in test_products:
# 						if test.order_traced_location:
# 							address = frappe.get_doc("Address", {'name': test.order_traced_location}, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
# 						else:
# 							address = ""
# 						product_details = frappe.get_all(
# 							"Product",  # Replace with the correct product doctype name
# 							filters={'name': test_product.product},
# 							fields=[
# 								'name',
# 								'product_name',
# 								'icon',
# 								'expiry',
# 								'description',
# 								'price',
# 								'usage',
# 								'side_effects',
# 								'alternative',
# 								'category_name'
# 							]
# 						)
# 						if product_details:
# 								products.append(product_details[0])
# 					test_details = {
# 						'test_id': test.name,
# 						'status':test.status,
# 						'modified':test.modified,
# 						'test_price':test.test_price,
# 						'payment_status': test.payment_status,
# 						'discount': test.discount,
# 						'payable_amount': test.payable_amount,
# 						'shipping_price': test.shipping_price,
# 						'order_trace_location' : address,
# 						'slot_date': test.slot_date,
# 						'slot_time': test.slot_time,
# 						'products': products
# 					}
# 					response.append(test_details)
# 		return response
	
# 	except frappe.exceptions.AuthenticationError as e:
# 		frappe.clear_messages()
# 		frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": "Authentication Error!",
#             "error": str(e)
#         }
# 	except frappe.exceptions.ValidationError as v:
# 		frappe.clear_messages()
# 		frappe.local.response["message"] = {
#             "success_key": 0,
#             "error": str(v)
#         }

@frappe.whitelist()
def lab_test_orders():
	response = []
	if "Lab Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("You are not authorized to access this API."))
	try:
			orders = frappe.get_all(
                "Orders",
                fields=['name','status','order_price', 'payment_status', 'modified', 'shipping_price', 'discount', 'payable_amount', 'phone', 'slot_time', 'slot_date']
            )
			if orders:
				ordered_count = len([order for order in orders if order.status == "Ordered"])
				cancelled = len([order for order in orders if order.status == "Cancelled"])
				delivered = len([order for order in orders if order.status == "Delivered"])
				packaged = len([order for order in orders if order.status == "Packaged"])
				shipped = len([order for order in orders if order.status == "Shipped"])
				total_orders = len(orders)
				for order in orders:
					if order.order_traced_location:
							address = frappe.get_doc("Address", {'name': order.order_traced_location}, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
					else:
							address = ""
					if order.prescription:
						prescription = frappe.get_all(
						"Prescribe",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['prescription']
					)
					else:
						prescription = []
					order_products = frappe.get_all(
						"PIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name, 'category': "Lab Test"},
						fields=['product', 'quantity' ]
					)
					print("oreeder", order_products)
					if order_products:
						products = []
						for order_product in order_products:
							product_details = frappe.get_all(
								"Product",  # Replace with the correct product doctype name
								filters={'name': order_product.product},
								fields=[
									'name',
									'product_name',
									'icon',
									'expiry',
									'description',
									'price',
									'usage',
									'side_effects',
									'alternative',
									'category_name'
								]
							)
							if product_details:
									products.append(product_details[0])
						order_details = {
							'order_id': order.name,
							'user': get_user_info_by_phone(order.phone),
							'total_order':total_orders,
							'slot_time':order.slot_time,
						'slot_date': order.slot_date,
							'pending_order':ordered_count,
							'address': address,
							'cancelled_order':cancelled,
							'delivered_order': delivered,
							'packaged_order': packaged,
							'shipped_order':shipped,
							'status':order.status,
							'modified':order.modified,
							'order_price':order.order_price,
							'payment_status': order.payment_status,
							'discount': order.discount,
							'payable_amount': order.payable_amount,
							'shipping_price': order.shipping_price,
							'prescription': prescription,
							'products': products
						}
						response.append(order_details)
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

@frappe.whitelist()
def med_orders():
	response = []
	if "Pharmacy Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("You are not authorized to access this API."))
	try:
			orders = frappe.get_all(
                "Orders",
                fields=['name','status','order_price', 'payment_status', 'modified', 'shipping_price', 'discount', 'payable_amount', 'phone', 'slot_time', 'slot_date']
            )
			if orders:
				ordered_count = len([order for order in orders if order.status == "Ordered"])
				cancelled = len([order for order in orders if order.status == "Cancelled"])
				delivered = len([order for order in orders if order.status == "Delivered"])
				packaged = len([order for order in orders if order.status == "Packaged"])
				shipped = len([order for order in orders if order.status == "Shipped"])
				total_orders = len(orders)
				for order in orders:
					if order.order_traced_location:
							address = frappe.get_doc("Address", {'name': order.order_traced_location}, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
					else:
							address = ""
					if order.prescription:
						prescription = frappe.get_all(
						"Prescribe",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['prescription']
					)
					else:
						prescription = []
					order_products = frappe.get_all(
						"PIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name, 'category': ['!=', 'Lab Test']},
						fields=['product', 'quantity' ]
					)
					print("oreeder", order_products)
					if order_products:
						products = []
						for order_product in order_products:
							product_details = frappe.get_all(
								"Product",  # Replace with the correct product doctype name
								filters={'name': order_product.product},
								fields=[
									'name',
									'product_name',
									'icon',
									'expiry',
									'description',
									'price',
									'usage',
									'side_effects',
									'alternative',
									'category_name'
								]
							)
							if product_details:
									products.append(product_details[0])
						order_details = {
							'order_id': order.name,
							'user': get_user_info_by_phone(order.phone),
							'address':address,
							'slot_time':order.slot_time,
						'slot_date': order.slot_date,
							'total_order':total_orders,
							'pending_order':ordered_count,
							'cancelled_order':cancelled,
							'delivered_order': delivered,
							'packaged_order': packaged,
							'shipped_order':shipped,
							'status':order.status,
							'modified':order.modified,
							'order_price':order.order_price,
							'payment_status': order.payment_status,
							'discount': order.discount,
							'payable_amount': order.payable_amount,
							'shipping_price': order.shipping_price,
							'prescription':prescription,
							'products': products
						}
						response.append(order_details)
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

@frappe.whitelist()
def order_data(phone=None):
	response = []
	try:
		if phone:
			orders = frappe.get_all(
				"Order Data",
				filters={'phone': phone},
				fields=['name', 'payment_status', 'modified', 'creation', 'payable_amount','discount', 'shipping_price', 'order_price', 'test_discount', 'test_shipping_price', 'test_price']
			)

			if orders:
				for order in orders:
					# Fetch address details
					if order.order_traced_location:
						address = frappe.get_doc("Address", order.order_traced_location, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
					else:
						address = ""
					prescription = []
					prescrip = frappe.get_all(
						"Prescribe",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['prescription'])
					for prescribe in prescrip:
							pre = frappe.get_all('Prescription',filters={'name':prescribe.prescription}, fields=['prescription', 'name'])
							if (pre):
								prescription.append({"id":pre[0].name, "url":pre[0].prescription})
					# Fetch test orders (products)
					test_orders = frappe.get_all(
						"PIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['name','product', 'price', 'quantity', 'status']
					)
					products = []
					for test_order in test_orders:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': test_order.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								product_details[0]['id'] = test_order.name
								product_details[0]['price'] = test_order.price
								product_details[0]['status'] = test_order.status
								product_details[0]['quantity'] = test_order.quantity
								products.append(product_details[0])
					test_orders = frappe.get_all(
						"LIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['name','product', 'price', 'slot_time', 'slot_date', 'quantity', 'test_status']
					)
					lab_tests = []
					for test_order in test_orders:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': test_order.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'price',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								product_details[0]['id'] = test_order.name
								product_details[0]['slot_time'] = test_order.slot_time
								product_details[0]['slot_date'] = test_order.slot_date
								product_details[0]['price'] = test_order.price
								product_details[0]['test_status'] = test_order.test_status
								product_details[0]['quantity'] = test_order.quantity
								lab_tests.append(product_details[0])
					# Append order data to response
					response.append({
						'order_id': order.name,
						'address': address,
						'modified': order.modified,
						'creation': order.creation,
						'payable_amount': order.payable_amount,
						'prescription': prescription,
						'product_list': {
				'pricing':{
					'discount': order.discount,
					'shipping_price': order.shipping_price,
					'status':"order.med_status",
					'order_price':order.order_price,
					},
				'products':products
				},
				'test_list': {
				'pricing':{
					'test_discount': order.test_discount,
					'test_shipping_price': order.test_shipping_price,
					'test_status':"order.lab_test_status",
					'test_price':order.test_price,
					},
				'tests':lab_tests
				}
						})

			return response
		else:
			return "Number Not found"
	
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

# @frappe.whitelist()
# def med_order_data():
# 	response = []
# 	if "Pharmacy Manager" not in frappe.get_roles(frappe.session.user):
# 		frappe.throw(_("You are not authorized to access this API."))
# 	try:
# 			orders = frappe.get_all(
# 				"Order Data",
# 				fields=['name', 'payment_status', 'modified', 'creation', 'payable_amount', 'discount', 'shipping_price', 'med_status', 'order_price', 'phone']
# 			)

# 			if orders:
# 				# Calculate order counts
# 				ordered_count = len([order for order in orders if order.status == "Ordered"])
# 				cancelled = len([order for order in orders if order.status == "Cancelled"])
# 				delivered = len([order for order in orders if order.status == "Delivered"])
# 				packaged = len([order for order in orders if order.status == "Packaged"])
# 				shipped = len([order for order in orders if order.status == "Shipped"])
# 				total_orders = len(orders)

# 				# Process each order
# 				for order in orders:
# 					# Fetch address details
# 					if order.order_traced_location:
# 						address = frappe.get_doc("Address", order.order_traced_location, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
# 					else:
# 						address = ""

# 					# Fetch test orders (products)
# 					test_orders = frappe.get_all(
# 						"PIO",  # Replace with the correct child table doctype name
# 						filters={'parent': order.name},
# 						fields=['product', 'quantity']
# 					)
# 					products = []
# 					for test_order in test_orders:
# 						product_details = frappe.get_all(
# 							"Product",  # Replace with the correct product doctype name
# 							filters={'name': test_order.product},
# 							fields=[
# 								'name',
# 								'product_name',
# 								'icon',
# 								'expiry',
# 								'description',
# 								'price',
# 								'usage',
# 								'side_effects',
# 								'alternative',
# 								'category_name'
# 							]
# 						)
# 						if product_details:
# 								products.append(product_details[0])
# 					# Append order data to response
# 					response.append({
# 						'category':'Medicines',
# 						'order_id': order.name,
# 						'user': get_user_info_by_phone(order.phone),
# 						'address': address,
# 						'total_order': total_orders,
# 						'pending_order': ordered_count,
# 						'cancelled_order': cancelled,
# 						'delivered_order': delivered,
# 						'packaged_order': packaged,
# 						'shipped_order': shipped,
# 						'modified': order.modified,
# 						'creation': order.creation,
# 						'payable_amount': order.payable_amount,
# 						'product_list': {
# 				'pricing':{
# 					'discount': order.discount,
# 					'shipping_price': order.shipping_price,
# 					'status':order.status,
# 					'order_price':order.order_price,
# 					},
# 				'products':products
# 				}
# 						})

# 			return response

	
# 	except frappe.exceptions.AuthenticationError as e:
# 		frappe.clear_messages()
# 		frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": "Authentication Error!",
#             "error": str(e)
#         }
# 	except frappe.exceptions.ValidationError as v:
# 		frappe.clear_messages()
# 		frappe.local.response["message"] = {
#             "success_key": 0,
#             "error": str(v)
#         }

@frappe.whitelist()
def med_order_data():
	response = {}
	responseArray=[]
	if "Pharmacy Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("You are not authorized to access this API."))
	try:
			orders = frappe.get_all(
				"Order Data",
				fields=['name', 'payment_status', 'modified', 'creation', 'payable_amount','discount', 'shipping_price', 'med_status', 'order_price', 'phone']
			)

			if orders:
				# Calculate order counts
				ordered_count = len([order for order in orders if order.status == "Ordered"])
				cancelled = len([order for order in orders if order.status == "Cancelled"])
				delivered = len([order for order in orders if order.status == "Delivered"])
				packaged = len([order for order in orders if order.status == "Packaged"])
				shipped = len([order for order in orders if order.status == "Shipped"])
				total_orders = len(orders)
				response['orders_info'] = {'total_order': total_orders,
						'pending_order': ordered_count,
						'cancelled_order': cancelled,
						'delivered_order': delivered,
						'packaged_order': packaged,
						'shipped_order': shipped,}
				# Process each order
				for order in orders:
					# Fetch address details
					if order.order_traced_location:
						address = frappe.get_doc("Address", order.order_traced_location, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
					else:
						address = ""
					prescription = []
					prescrip = frappe.get_all(
						"Prescribe",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['prescription'])
					for prescribe in prescrip:
							pre = frappe.get_all('Prescription',filters={'name':prescribe.prescription}, fields=['prescription', 'name'])
							if (pre):
								prescription.append({"id":pre[0].name, "url":pre[0].prescription})
					test_orders = frappe.get_all(
						"PIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['name','product', 'price', 'quantity', 'status']
					)
					products = []
					for test_order in test_orders:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': test_order.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								product_details[0]['id'] = test_order.name
								product_details[0]['price'] = test_order.price
								product_details[0]['status'] = test_order.status
								product_details[0]['quantity'] = test_order.quantity
								products.append(product_details[0])
					# Append order data to response
					responseArray.append({
						'category':'Medicines',
						'order_id': order.name,
						'user': get_user_info_by_phone(order.phone),
						'address': address,
						'modified': order.modified,
						'creation': order.creation,
						'payable_amount': order.payable_amount,
						'prescription': prescription,
						'pricing':{
					'discount': order.discount,
					'shipping_price': order.shipping_price,
					'status':order.status,
					'order_price':order.order_price,
					},
				'products':products
						})
			response['orders'] = responseArray
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


@frappe.whitelist()
def lab_order_data():
	response = {}
	responseArray=[]
	if "Lab Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw(_("You are not authorized to access this API."))
	try:
			orders = frappe.get_all(
				"Order Data",
				fields=['name', 'payment_status', 'modified', 'creation', 'payable_amount','test_discount', 'test_shipping_price', 'test_status', 'test_price', 'phone']
			)

			if orders:
				# Calculate order counts
				ordered_count = len([order for order in orders if order.status == "Ordered"])
				cancelled = len([order for order in orders if order.status == "Cancelled"])
				delivered = len([order for order in orders if order.status == "Delivered"])
				packaged = len([order for order in orders if order.status == "Packaged"])
				shipped = len([order for order in orders if order.status == "Shipped"])
				total_orders = len(orders)
				response['orders_info'] = {'total_order': total_orders,
						'pending_order': ordered_count,
						'cancelled_order': cancelled,
						'delivered_order': delivered,
						'packaged_order': packaged,
						'shipped_order': shipped,}
				# Process each order
				for order in orders:
					# Fetch address details
					if order.order_traced_location:
						address = frappe.get_doc("Address", order.order_traced_location, ["deliver_to","name","pincode","address_line1","address_line2","city", "mobile_no", "default"])
					else:
						address = ""
					prescription = []
					prescrip = frappe.get_all(
						"Prescribe",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['prescription'])
					for prescribe in prescrip:
							pre = frappe.get_all('Prescription',filters={'name':prescribe.prescription}, fields=['prescription', 'name'])
							if (pre):
								prescription.append({"id":pre[0].name, "url":pre[0].prescription})
						
					
					test_orders = frappe.get_all(
						"LIO",  # Replace with the correct child table doctype name
						filters={'parent': order.name},
						fields=['name','product', 'price', 'slot_time', 'slot_date', 'quantity', 'test_status']
					)
					lab_tests = []
					for test_order in test_orders:
						product_details = frappe.get_all(
							"Product",  # Replace with the correct product doctype name
							filters={'name': test_order.product},
							fields=[
								'name',
								'product_name',
								'icon',
								'expiry',
								'description',
								'usage',
								'side_effects',
								'alternative',
								'category_name'
							]
						)
						if product_details:
								product_details[0]['id'] = test_order.name
								product_details[0]['slot_time'] = test_order.slot_time
								product_details[0]['slot_date'] = test_order.slot_date
								product_details[0]['price'] = test_order.price
								product_details[0]['status'] = test_order.test_status
								product_details[0]['quantity'] = test_order.quantity
								lab_tests.append(product_details[0])
					# Append order data to response
					responseArray.append({
						'category':'Lab Test',
						'order_id': order.name,
						'user': get_user_info_by_phone(order.phone),
						'address': address,
						'modified': order.modified,
						'creation': order.creation,
						'payable_amount': order.payable_amount,
						'prescription': prescription,
						'pricing':{
					'discount': order.test_discount,
					'shipping_price': order.test_shipping_price,
					'status':"order.lab_test_status",
					'order_price':order.test_price,
					},
					'products':lab_tests
						})
			response['orders'] = responseArray
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

# @frappe.whitelist()
# def delete_user(user_email):
# 	try:
# 		frappe.delete_doc("User", user_email)
# 		frappe.db.commit()
# 		return "user deleted successfully"
# 	except frappe.LinkExistsError as e:
# 		print(f"Cannot delete user {user_email} because it is linked with other documents.")
# 		# List linked documents (if needed)
# 		linked_docs = frappe.get_all("User", filters={"email": user_email}, fields=["name", "doctype"])
# 		for doc in linked_docs:
# 			print(f"Linked document: {doc['doctype']} - {doc['name']}")
# 	except Exception as e:
# 		print(f"An error occurred: {str(e)}")
# @frappe.whitelist()
# def delete_user(phone):
# 	try:
# 		user = frappe.get_list("User", filters={"phone": phone}, fields=["name"])
# 		print("user", user)
# 		if user:
# 			user_name = user[0].name
# 			frappe.delete_doc("User", user_name)
# 			frappe.db.commit()
# 			return "User deleted successfully"
# 		else:
# 			return "User not found"
# 	except frappe.LinkExistsError as e:
# 		print(f"Cannot delete user with phone number {phone} because it is linked with other documents.")
# 		# List linked documents (if needed)
# 		return "Cannot delete user because it is linked with other documents"
# 	except Exception as e:
# 		print(f"An error occurred: {str(e)}")
# 		return "An error occurred while deleting the user"

@frappe.whitelist()
def status(id, status):
	# if "Pharmacy Manager" not in frappe.get_roles(frappe.session.user):
	# 	frappe.throw(_("You are not authorized to access this API."))
	if id and status:
		doc = frappe.get_doc("PIO", id)
		doc.test_status = status
		doc.save()
		frappe.db.commit()
		return {"status": "success", "message": f"Document with ID {id} has been updated"}
	else:
		if not id:
			return {"message": f"Document with ID {id} not found"}
		elif not status:
			return {"message": f"please provide valid status!"}
		else:
			return {"message": f"please provide valid data!"}

@frappe.whitelist()
def test_status(id, test_status):
	# if "Lab Manager" not in frappe.get_roles(frappe.session.user):
	# 	frappe.throw(_("You are not authorized to access this API."))
	if id and test_status:
		doc = frappe.get_doc("LIO", id)
		doc.test_status = test_status
		doc.save()
		frappe.db.commit()
		return {"status": "success", "message": f"Document with ID {id} has been updated"}
	else:
		if not id:
			return {"message": f"Document with ID {id} not found"}
		elif not test_status:
			return {"message": f"please provide valid status!"}
		else:
			return {"message": f"please provide valid data!"}

@frappe.whitelist()
def check_pin(pin):
	docs = frappe.get_all("Pincodes", {"pin_code":pin})
	if docs:
		return True
	else:
		return False
	
@frappe.whitelist()
def get_cart(phone):
	print("hello")
	response = []
	carts = frappe.get_all(
				"Cart", filters={"owner": frappe.session.user},
				fields=['name', 'prescription', 'product','quantity']
			)
	for cart in carts:
		print("cart",cart.prescription)
		try:
			prescription = frappe.get_all('Prescription',filters={'name':cart.prescription}, fields=['prescription'])
		except:
			prescription=""
		if prescription:
			cart['prescription'] = prescription[0].prescription
		else:
			cart['prescription'] = ""
		response.append(cart)
	return carts