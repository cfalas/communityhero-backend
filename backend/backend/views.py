from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *
from backend.serializers import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db import IntegrityError
import numpy as np
import random
import names
import json
import os
import decimal
import nltk
import requests

from math import radians, cos, sin, asin, sqrt
def distance(lat1, lon1, lat2, lon2):
	# The math module contains a function named
	# radians which converts from degrees to radians.
	lon1 = radians(lon1)
	lon2 = radians(lon2)
	lat1 = radians(lat1)
	lat2 = radians(lat2)

	# Haversine formula
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * asin(sqrt(a))
	# Radius of earth in kilometers. Use 3956 for miles
	r = 6371
	# calculate the result
	return c * r

@api_view(['GET'])
def category_collection(request):
	if request.method == 'GET':
		posts = Category.objects.all()
		serializer = CategorySerializer(posts, many=True)
		return Response(serializer.data)


@api_view(['GET'])
def category_element(request, pk):
	try:
		post = Category.objects.get(CategoryID=pk)
	except Category.DoesNotExist:
		return HttpResponse(status=404)

	if request.method == 'GET':
		serializer = CategorySerializer(post)
		return Response(serializer.data)


@api_view(['GET'])
def producttype_collection(request):
	if request.method == 'GET':
		posts = ProductType.objects.all()
		serializer = ProductTypeSerializer(posts, many=True)
		return Response(serializer.data)

@api_view(['GET'])
def producttype_name(request, name):
	if request.method == 'GET':
		posts = ProductType.objects.filter(Q(ProductTypeName__icontains=name) | Q(CategoryID__CategoryName__icontains=name))
		serializer = ProductTypeSerializer(posts, many=True)
		return Response(serializer.data)

@api_view(['GET'])
def producttype_element(request, pk):
	try:
		post = ProductType.objects.get(ProductTypeID=pk)
	except ProductType.DoesNotExist:
		return HttpResponse(status=404)

	if request.method == 'GET':
		serializer = ProductTypeSerializer(post)
		return Response(serializer.data)

@api_view(['GET'])
def product_name(request, name):
	if request.method == 'GET':
		posts = Product.objects.filter(Q(ProductName__icontains=name) | Q(ProductTypeID__ProductTypeName__icontains=name))
		serializer = ProductSerializer(posts, many=True)
		return Response(serializer.data)

@api_view(['GET'])
def product_barcode(request):
	barcode = request.query_params['barcode']
	try:
		post = Product.objects.get(ProductBarcode=barcode)
	except Product.DoesNotExist:
		return HttpResponse(status=404)

	if request.method == 'GET':
		serializer = ProductSerializer(post)
		return Response(serializer.data)

@api_view(['GET'])
def product_element(request, pk):
	try:
		post = Product.objects.get(ProductID=pk)
	except ProductType.DoesNotExist:
		return HttpResponse(status=404)

	if request.method == 'GET':
		serializer = ProductSerializer(post)
		return Response(serializer.data)

@api_view(['GET'])
def user_radius(request):
	if request.method == 'GET':
		lat = float(request.query_params['lat'])
		lng = float(request.query_params['lng'])
		rad = float(request.query_params['rad'])
		# TODO: Implement direct distance from DB
		users = PastOrder.objects.filter(OrderDelivered=False)
		result_users = []
		for user in users:
			if distance(lat, lng, user.UserID.Userlatitude, user.UserID.Userlongitude)<rad:
				result_users.append(user)

		serializer = OrderSerializer(result_users, many=True)
		return Response(serializer.data)

@api_view(['GET'])
def order_by_id(request):
	if request.method == 'GET':
		oid = int(request.query_params['orderId'])
		orders = OrderItems.objects.filter(OrderID=oid)
		serializer = OrderItemSerializer(orders, many=True)
		return Response(serializer.data)

@api_view(['GET'])
def create_data(request):
	if request.method == 'GET':
		probability = 1
		mean_price = 4
		stdev = 1
		shops = Shop.objects.all()
		products = Product.objects.all()
		for shop in shops:
			for product in products:
				print(shop, product)
				price = Price(ShopID=shop, ProductID=product, Price=np.random.normal(mean_price, stdev))
				try:
					price.save()
				except:
					pass

		num_users = 0

		for j in range(num_users):
			phonenumber = '99' + ''.join(random.choice("0123456789") for _ in range(6))
			username = names.get_first_name()
			print(phonenumber, username)
			user = User(Userlatitude=np.random.normal(35.15938300, 0.1), Userlongitude=np.random.normal(33.39632500, 0.1), Userphonenumber=phonenumber, UserName=username)
			user.save()

		users = User.objects.all()
		for user in users:
			if len(PastOrder.objects.filter(UserID=user.UserID, OrderDelivered=False))>0:
				continue
			shop = random.choice(Shop.objects.all())
			available_items = Price.objects.all().filter(ShopID=shop.ShopID)
			num_of_items = random.randint(1, len(available_items)-1)

			items = random.sample(list(available_items), num_of_items)

			order = PastOrder(UserID=user, OrderDelivered=False)
			order.save()
			for item in items:
				order_item = OrderItems(OrderID=order, PriceID=item, Quantity=random.randint(1, 5))
				order_item.save()


		return Response("Done")


@api_view(['POST'])
def deliver_order(request, order):
	if request.method == 'POST':
		print(request.data)
		obj = PastOrder.objects.get(OrderID=order)
		obj.OrderDelivered = True
		if(obj.UserID.UserMessenger==True):
			send_fb_msg(obj.UserID.Userphonenumber, 'Your order has been claimed by a volunteer! 🥳')
		obj.save()
		return Response("Done")

@api_view(['POST'])
def sms_order(request):
	if request.method == 'POST':

		b = request.data
		return JsonResponse(create_order(b))

@api_view(['POST'])
def sms_register(request):
	if request.method == 'POST':
		print(request.body.decode('utf-8'))
		b = json.loads(request.body.decode('utf-8'))
		lt = 0
		ln = 0
		if "address" in b:
			req = requests.get("https://nominatim.openstreetmap.org/search/" + b['address'].replace(" ", '%20') + "?format=json").json()[0]
			lt = req['lat']
			ln = req['lon']
		else:
			lt = b['lat']
			ln = b['lng']
		


		u = User(Userphonenumber=b["from"], Userlatitude=float(lt), Userlongitude=float(ln))
		u.save()
		return Response("Done")

@api_view(['GET'])
def download_products(request, shop):
	# Create the HttpResponse object with the appropriate CSV header.
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
	b = Price.objects.filter(ShopID=shop)
	
	t = loader.get_template('csv.txt')
	c = {'data': b}
	response.write(t.render(c))
	return response

STATE = {
	'registering': 0,
	'geocoding': 1,
	'choose_supermarket': 2,
	'registered': 99
}

YES_REPLIES = ['yes', 'yeah', 'correct', 'yep']
NO_REPLIES = ['no', 'nope', 'wrong', 'nop']
LIST_QUERIES = ['list', 'cart']


@api_view(['POST'])
def chatbot(request):
	if request.method=='POST':
		b = request.data
		print(b)
		r = {}
		r['content'] = ''
		if not user_exists(b['from']):
			r['content'] =  'Welcome! I noticed you are new here. Why don\'t you go ahead and send me your address so that I can sign you up?'
			u = User(Userphonenumber=b['from'], UserState=STATE['registering'])
			u.save()
		else:
			u = User.objects.get(Userphonenumber=b['from'])
			print(u.UserState)
			if u.UserState==STATE['registering']:
				r['content'], u.Userlatitude, u.Userlongitude = geocode(b)
				u.UserState = STATE['geocoding']
				u.save()
			elif u.UserState==STATE['geocoding']:
				if b['content'].lower() in YES_REPLIES:
					r['content'] = 'You are now registered! Nice! You can send in orders at any time.'
					u.UserState = STATE['registered']
					u.save()
				elif b['content'].lower() in NO_REPLIES:
					r['content'] = 'Oh sorry about that :(\nCan you try that again with a more specific location?'
					u.UserState = STATE['registering']
					u.save()
				else:
					r['content'] = 'Sorry, didn\'t get you. Can you try once more?'
			elif u.UserState==STATE['registered']:
				# Order received
				print('Sending ORDER request using items', b)
				req = create_order(b)
				print('ORDER request response:', req)
				r['content'] = 'Here\'s what I found:\n'
				for item in range(len(req['items'])):
					if req['items'][item] == 'not found':
						r['content']+=b['content'].split('\n')[item] + ": " + req['items'][item] + '\n'
					else:
						r['content']+=req['items'][item] + '\n'
				r['content']+='That would cost you a total of €' + str(req['cost']) + '\nYou can edit or complete your order here: http://192.168.30.179/wordpress/index.php/cart/?fill_cart='
				for item in range(len(req['itemsWordpress'])):
					r['content']+=str(req['itemsWordpress'][item])
					if item!=len(req['items'])-1:
						r['content']+=','
		
		r['from'] = 'bot'

		return JsonResponse(r)

def user_exists(phone):
	try:
		user = User.objects.get(Userphonenumber=phone)
		return True
	except:
		return False

def geocode(msg):
	req = requests.get("https://nominatim.openstreetmap.org/search/" + msg['content'].replace(" ", '%20') + "?format=json").json()
	if len(req)>0:
		req = req[0]
	else:
		return None, None, None
	return "So you're telling me you live here? https://www.openstreetmap.org/?mlat=" + req['lat'] + "&mlon=" + req['lon']+ " \nIt's not that I don't know, just checking if you know ;)", req['lat'], req['lon']

def area(box):
	return distance(box[1], box[2], box[0], box[2])*distance(box[3], box[0], box[2], box[0])
@api_view(['GET'])
def get_user_by_phone(request, phone):
	try:
		post = User.objects.get(Userphonenumber=phone)
	except User.DoesNotExist:
		return HttpResponse(status=404)
	return HttpResponse(post.UserName)


@api_view(['DELETE'])
def cart_price_user(request, price, user):
	if request.method=='DELETE':
		try:
			ShoppingItem.objects.get(PriceID=price, UserID=user).delete()
		except ShoppingItem.DoesNotExist:
			return HttpResponse(status=404)
		return HttpResponse("Done")

@api_view(['GET'])
def cart_user(request, user):
	if request.method=='GET':
		cart = ShoppingItem.objects.filter(UserID=user)
		serializer = ShoppingItemSerializer(cart, many=True)
		return Response(serializer.data)

@api_view(['POST'])
def cart_order(request, user):
	if request.method=='POST':
		cart = ShoppingItem.objects.filter(UserID=user)
		order = PastOrder(UserID=User.objects.get(UserID=user))
		order.save()
		for item in cart:
			o = OrderItems(OrderID=order, PriceID=item.PriceID, Notes=item.Notes, Quantity=item.Quantity)
			o.save()
		cart = ShoppingItem.objects.filter(UserID=user).delete()		
		return HttpResponse(status=200)

@api_view(['GET', 'POST'])
def messenger(request, *args, **kwargs):
	if request.method=='POST':
		# Converts the text payload into a python dictionary
		incoming_message = json.loads(request.body.decode('utf-8'))
		# Facebook recommends going through every entry since they might send
		# multiple messages in a single call during high load
		for entry in incoming_message['entry']:
			for message in entry['messaging']:
				# Check to make sure the received call is a message call
				# This might be delivery, optin, postback for other events 
				if 'message' in message:
					# Print the message to the terminal
					print(message)
					if 'quick_reply' in message['message']:
						payload = message['message']['quick_reply']['payload']
						if "CHOOSE_STORE" in payload:
							choose_shop(message['sender']['id'], payload.split('|')[1])
						if 'CHECKOUT_YES' in payload:
							checkout(message['sender']['id'])

					else:
						# Assuming the sender only sends text. Non-text messages like stickers, audio, pictures
						# are sent as attachments and must be handled accordingly. 
						post_facebook_message(message['sender']['id'], message['message']['text'])  
				elif 'postback' in message:
					payload = message['postback']['payload']
					if 'REGISTER' in payload:
						messenger_chatbot({'from': message['sender']['id'], 'content': "Hi"})
					elif 'SHOWCART' in payload:
						show_cart(message['sender']['id'])
					elif 'HELP' in payload:
						send_fb_msg(message['sender']['id'], 'Hi! I\'m the Community Hero Facebook Messenger bot. I can help you find items that you need to shop, and deliver them  to you by volunteers. Once finished with the registration process, you can send anything that you need to add to your cart. A list of options will be returned, and by clicking \'Add to Cart\' below the option that you like, that specific product will be added to your cart.')
					elif 'ADD_CART' in payload:
						add_cart(message['sender']['id'], payload.split('|')[1])
					elif 'REMOVE_CART' in payload:
						remove_cart(message['sender']['id'], payload.split('|')[1])
					elif 'CHECKOUT' in payload:
						show_cart(message['sender']['id'])
						confirm(message['sender']['id'], 'CHECKOUT', 'Are you sure you want to checkout?')
						


	else:
		if request.GET['hub.verify_token'] == "communityhero":
			return HttpResponse(request.GET['hub.challenge'])
		else:
			return HttpResponse('Error, invalid token')
	return HttpResponse()    

def post_facebook_message(fbid, recevied_message):
	# Remove all punctuations, lower case the text and split it based on space
	PAGE_ACCESS_TOKEN = os.environ['FB_TOKEN']
	user_details_url = "https://graph.facebook.com/v6.0/%s"%fbid 
	user_details_params = {'fields':'first_name,last_name,profile_pic', 'access_token':PAGE_ACCESS_TOKEN} 
	user_details = requests.get(user_details_url, user_details_params).json() 

	r = messenger_chatbot({"from": fbid, "content": recevied_message})
	if r==None:
		print('Chatbot didn\'t return')
	else:
		print('Chatbot returned:', r)
		send_fb_msg(fbid, r['content'])

def send_fb_msg(fbid, msg, quick_replies=None):
	print('Sending message', msg, 'to', fbid)
	PAGE_ACCESS_TOKEN = os.environ['FB_TOKEN']
	post_message_url = 'https://graph.facebook.com/v6.0/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
	if quick_replies==None: response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":msg}})
	else:
		response_msg = json.dumps({
			"recipient": {"id": fbid},
			"messaging_type": "RESPONSE",
			"message":{
				"text": msg,
				"quick_replies": quick_replies
			}
		})
	status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
	print('FB Response:', status)

def create_order(b):
	names = ProductType.objects.all()
	print(b)
	print(b["from"])
	resp = {}
	print(b["content"].split('\n'))
	try:
		user = User.objects.get(Userphonenumber=b['from'])
	except User.DoesNotExist:
		resp["status"]="user_error"
		return JsonResponse(resp)
	if "confirm" in b and b["confirm"]=="true":
		order = PastOrder(UserID=user)
		order.save()

	items = []
	itemsWordpress = []
	totalCost = 0
	for product in b["content"].split('\n'):
		product = product.lower()
		mindist = 100000000000
		for p in Product.objects.all():
			if nltk.jaccard_distance(set(nltk.ngrams(product, n=3)), set(nltk.ngrams(p.ProductTypeID.ProductTypeName.lower(), n=3)).union(set(nltk.ngrams(p.ProductName.lower(), n=3))).union(set(nltk.ngrams(p.ProductBrandID.BrandName.lower(), n=3))))/(p.ProductWeight) < mindist:
				mindist = nltk.jaccard_distance(set(nltk.ngrams(product, n=3)), set(nltk.ngrams(p.ProductTypeID.ProductTypeName.lower(), n=3)).union(set(nltk.ngrams(p.ProductName.lower(), n=3))).union(set(nltk.ngrams(p.ProductBrandID.BrandName.lower(), n=3))))/p.ProductWeight
				mindistproduct = p

		print(mindistproduct.ProductName, mindist)
		# TODO: Return cheapest/closest combination
		if mindist<0.95 and len(Price.objects.filter(ProductID=mindistproduct).order_by('Price'))>0:
			print(Price.objects.filter(ProductID=mindistproduct).order_by('Price')[0])
			items.append(mindistproduct.ProductBrandID.BrandName + ' ' + mindistproduct.ProductName)
			itemsWordpress.append(mindistproduct.WordpressID)
			price = Price.objects.filter(ProductID=mindistproduct).order_by('Price')[0]
			totalCost+=price.Price
			if "confirm" in b and b["confirm"]=="true":
				try:
					item = OrderItems(OrderID=order, PriceID=price, Quantity=1)
					item.save()
				except IntegrityError:
					print('Item already existed, increased quantity')
					item = OrderItems.objects.get(OrderID=order, PriceID=price)
					item.Quantity+=1
					item.save()
			else:
				try:
					item = ShoppingItem(UserID=user, PriceID=price, Quantity=1)
					item.save()
				except IntegrityError:
					print('Item already existed, increased quantity')
					item = ShoppingItem.objects.get(UserID=user, PriceID=price)
					item.Quantity+=1
					item.save()
		else:
			items.append('not found')
		
	resp = {}
	resp['userID'] = user.UserID
	resp["items"] = items
	resp["cost"] = totalCost
	resp["status"]="ok"
	resp['itemsWordpress'] = itemsWordpress
	print('sms_order returning to chatbot:', resp)
	return resp

def messenger_chatbot(b):
	print(b)
	r = {}
	r['content'] = ''
	if not user_exists(b['from']):
		r['content'] =  'Welcome! I noticed you are new here. Why don\'t you go ahead and send me your address so that I can sign you up?'
		u = User(Userphonenumber=b['from'], UserState=STATE['registering'], UserMessenger=True)
		u.save()
	else:
		u = User.objects.get(Userphonenumber=b['from'])
		print(u.UserState)
		if u.UserState==STATE['registering']:
			r['content'], u.Userlatitude, u.Userlongitude = geocode(b)
			if r['content'] == None:
				r['content'] = 'Sorry, I didn\'t find any results. Can you try again with a different query?'
			else:
				u.UserState = STATE['geocoding']
				u.save()
		elif u.UserState == STATE['geocoding']:
			if b['content'].lower() in YES_REPLIES:
				u.UserState = STATE['choose_supermarket']
				u.save()
				send_fb_msg(u.Userphonenumber, 'Which store in your region do you prefer?', quick_replies=shops_around_user(u))
			elif b['content'].lower() in NO_REPLIES:
				r['content'] = 'Oh sorry about that :(\nCan you try that again with a more specific location?'
				u.UserState = STATE['registering']
				u.save()
			else:
				r['content'] = 'Sorry, didn\'t get you. Can you try once more?'
		elif u.UserState == STATE['choose_supermarket']:
			send_fb_msg(u.Userphonenumber, 'You still haven\'t chosen your preferred supermarket. Please choose one from the list below', quick_replies=shops_around_user(u))
			return None
		elif u.UserState == STATE['registered']:
			# Order received
			print('Sending ORDER request using items', b)
			for query in b['content'].split('\n'):
				search_results = search_products(query)
				print('Search results:',search_results)
				if len(search_results)>0:
					carousel = []
					for result in search_results:
						minp,maxp = min_max_price(result)
						subtitle_string = ''
						if minp==None:
							subtitle_string = 'Not available currently'
						else:
							subtitle_string = 'Usually ranges from €' + str(minp) + ' to €' + str(maxp)
						carousel.append({
							"title":get_full_product_name(result.ProductID),
							"image_url": "https://rhubarb-cake-22341.herokuapp.com/static/images/"+str(result.ProductID)+".jpg",
							"subtitle": subtitle_string,
							"buttons": [
								{
									"type": "postback",
									"title": "Add to Cart",
									"payload": "ADD_CART|"+str(result.ProductID)
								}
							]
						})
					PAGE_ACCESS_TOKEN = os.environ['FB_TOKEN']
					send_fb_msg(u.Userphonenumber, "Here's what I found for " + query + ":")
					post_message_url = 'https://graph.facebook.com/v6.0/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
					response_msg = json.dumps({"recipient":{"id":u.Userphonenumber}, "message":{"attachment":{"type": "template", "payload":{"template_type": "generic", "elements":carousel}}}})
					status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
					print("Sending to FB:", response_msg)
					print('Message status', status)
				else:
					send_fb_msg(u.Userphonenumber, "I didn't find anything for " + query + " :(")

			# Prevents from trying to send another empty message
			return None

	r['from'] = 'bot'

	return r

def search_products(product):
	product = product.lower()
	search_results = []
	search_results_scores = []
	print(f'============ {product} STARTED =============')
	for p in Product.objects.all():
		search_results.append(p)
		search_results_scores.append(nltk.jaccard_distance(set(nltk.ngrams(product, n=3)), set(nltk.ngrams(p.ProductTypeID.ProductTypeName.lower(), n=3)).union(set(nltk.ngrams(p.ProductName.lower(), n=3))).union(set(nltk.ngrams(p.ProductBrandID.BrandName.lower(), n=3))))/(p.ProductWeight))
	sorted_indexes = sorted(zip(search_results_scores, range(len(search_results))))
	mindist = float(sorted_indexes[0][0])
	if mindist > 0.95:
		return []
	results_returned = []
	all_results = {}
	for a,b in sorted_indexes:
		if a < 1.17 * mindist and a < 0.96: results_returned.append(search_results[b])
		all_results[get_full_product_name(search_results[b].ProductID)] = a
	print(all_results)
	print(f'============ {product} FINISHED =============')

	return results_returned

def show_cart(fbid):
	print('Show cart requested')
	cart_contents = ShoppingItem.objects.filter(UserID=User.objects.get(Userphonenumber=fbid))
	carousel = []
	if len(cart_contents) > 0:
		send_fb_msg(fbid, 'Here is your cart: ')
		for result in cart_contents:
			minp,maxp = min_max_price(result.PriceID.ProductID)
			carousel.append({
							"title":get_full_product_name(result.PriceID.ProductID.ProductID),
							"image_url": "https://rhubarb-cake-22341.herokuapp.com/static/images/"+str(result.PriceID.ProductID.ProductID)+".jpg",
							"subtitle": 'Usually ranges from €' + str(minp) + ' to €' + str(maxp) + '\nQuantity: ' + str(result.Quantity),
							"buttons": [{
										"type": "postback",
										"title": "Remove from cart",
										"payload": "REMOVE_CART|"+str(result.PriceID.ProductID.ProductID)
								}
							]
						})
			print('Cart contents: ', str(result.PriceID.ProductID))
		PAGE_ACCESS_TOKEN = os.environ['FB_TOKEN']
		post_message_url = 'https://graph.facebook.com/v6.0/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
		response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"attachment":{"type": "template", "payload":{"template_type": "generic", "elements":carousel}}}})
		status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
	else:
		send_fb_msg(fbid, 'Your cart is empty :(\nYou can add something to your cart by sending it as a message')

def min_max_price(product_id):
	price_list = Price.objects.filter(ProductID=product_id).order_by('Price')
	min_price = price_list.first()
	max_price = price_list.last()
	if min_price==None:
		return None
	return (min_price.Price, max_price.Price)

def add_cart(fbid, pid):
	print(Price.objects.filter(ProductID=pid).order_by('Price')[0])
	price = Price.objects.filter(ProductID=pid).order_by('Price')[0]
	try:
		item = ShoppingItem(UserID=User.objects.get(Userphonenumber=fbid), PriceID=price, Quantity=1)
		item.save()
		send_fb_msg(fbid, get_full_product_name(pid) + " added to cart!")
	except IntegrityError:
		print('Item already existed, increased quantity')
		item = ShoppingItem.objects.get(UserID=User.objects.get(Userphonenumber=fbid), PriceID=price)
		item.Quantity+=1
		item.save()
		send_fb_msg(fbid, get_full_product_name(pid) + " was already in cart, increased quanitity")
	
	# Update popularities
	update_popularities()

def remove_cart(fbid, pid):
	item = ShoppingItem.objects.get(PriceID__ProductID__ProductID=pid).delete()
	send_fb_msg(fbid, get_full_product_name(pid) + " removed from cart.")

def get_full_product_name(pid):
	p = Product.objects.get(ProductID=pid)
	return str(p.ProductBrandID.BrandName) + ' ' + str(p.ProductName)

def send_fb_template(fbid, payload):
	PAGE_ACCESS_TOKEN = os.environ['FB_TOKEN']
	post_message_url = 'https://graph.facebook.com/v6.0/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
	response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"attachment":{"type": "template", "payload":payload}}})
	status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
	print("Sending to FB:", response_msg)
	print('Message status', status)

def shops_around_user(user):
	RADIUS = 5
	shops = Shop.objects.all()
	result_shops = []
	for shop in shops:
		if shop.ShopLatitude==None or shop.ShopLongitude==None: continue
		if distance(shop.ShopLatitude, shop.ShopLongitude, user.Userlatitude, user.Userlongitude)<RADIUS:
			result_shops.append(shop)

	print('Shops available:', result_shops)
	btns = []
	for s in result_shops:
		btns.append({
			"content_type": "text",
			"title": s.ShopName,
			"payload": f"CHOOSE_STORE|{s.ShopID}"
		})
	btns.append({
		"content_type": "text",
		"title": "Don't mind/Cheapest",
		"payload": "CHOOSE_STORE|-1"
	})
	return btns

def choose_shop(fbid, shop):
	u = User.objects.get(Userphonenumber=fbid)
	if shop=='-1':
		print('No shop preferred by user', fbid)
	else:
		u.UserShopID = Shop.objects.get(ShopID=shop)
	
	u.UserState=STATE['registered']
	u.save()
	send_fb_msg(fbid, 'You are now registered! Nice! You can send in orders at any time.')

def checkout(fbid):
	def find_cheapest_store():
		RADIUS = 5
		def total_price_at_shop(shop):
			cart = ShoppingItem.objects.filter(UserID__Userphonenumber=fbid)
			total_price = decimal.Decimal(0)
			for item in cart:
				price = Price.objects.get(ProductID=item.PriceID.ProductID, ShopID=shop)
				total_price+= price.Price * item.Quantity
			return total_price
		
		shops = Shop.objects.all()
		user = User.objects.get(Userphonenumber=fbid)
		close_shops = []
		for shop in shops:
			if shop.ShopLatitude==None or shop.ShopLongitude==None: continue
			if distance(shop.ShopLatitude, shop.ShopLongitude, user.Userlatitude, user.Userlongitude)<RADIUS:
				close_shops.append(shop)

		if len(close_shops)==0:
			send_fb_msg(fbid, 'No stores near you were found :(\nCould not proceed with checkout')
			return None
		minprice = total_price_at_shop(close_shops[0].ShopID)
		minprice_store = close_shops[0].ShopID
		for shop in close_shops:
			if total_price_at_shop(shop)<minprice:
				minprice = total_price_at_shop(shop.ShopID)
				minprice_store = shop.ShopID
		return minprice_store
				
	# For the given user (fbid), the contents of the cart are made into an order from the shop specified
	# Returns: Total Cost	
	def checkout_shop(shop):
		total_cost = 0
		cart = ShoppingItem.objects.filter(UserID__Userphonenumber=fbid)
		order = PastOrder(UserID=User.objects.get(Userphonenumber=fbid))
		order.save()
		for item in cart:
			o = OrderItems(OrderID=order, PriceID=Price.objects.get(ShopID=shop, ProductID=item.PriceID.ProductID), Notes=item.Notes, Quantity=item.Quantity)
			total_cost += item.Quantity * Price.objects.get(ShopID=shop, ProductID=item.PriceID.ProductID).Price
			o.save()
		cart = ShoppingItem.objects.filter(UserID__Userphonenumber=fbid).delete()
		return total_cost
	
	u = User.objects.get(Userphonenumber=fbid)
	if u.UserShopID==None:
		store = find_cheapest_store()
		if store==None:
			return
	else:
		store = u.UserShopID
	getcontext.prec = 2
	price = checkout_shop(store)
	send_fb_msg(fbid, f'Your order was placed! The total cost is €{decimal.Decimal(price)}. We\'ll send you a message when someone claims it.')
	
def confirm(user, tag, message):
	send_fb_msg(user, message, quick_replies=[
		{
			"content_type": "text",
			"title": "Yes",
			"payload": tag+"_YES"
		}, {
			"content_type": "text",
			"title": "No",
			"payload": tag+"_NO"
		},
	])

def update_popularities():
	count_items = {}
	for i in Product.objects.all():
		count_items[i.ProductID] = 0
	for i in ShoppingItem.objects.all():
		count_items[i.PriceID.ProductID.ProductID]+= float(i.Quantity)
	print(count_items)
	min_item = count_items[min(count_items, key=count_items.get)]
	max_item = count_items[max(count_items, key=count_items.get)]
	print(min_item, max_item)
	if min_item == max_item:
		for item in count_items:
			count_items[item] = 1
	else:
		for i in count_items:
			count_items[i] = (count_items[i] - min_item) / (max_item - min_item)*0.02 + 1
	print(count_items)
	for item in count_items:
		p = Product.objects.get(ProductID=item)
		p.ProductWeight = count_items[item]
		p.save()
		