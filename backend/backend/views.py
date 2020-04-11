from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *
from backend.serializers import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import numpy as np
import random
import names
import json
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
	return(c * r) 

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
		probability = 0.8
		mean_price = 4
		stdev = 1
		shops = Shop.objects.filter(ShopTypeID=1)
		products = Product.objects.all()
		for shop in shops:
			for product in products:
				if product.ProductTypeID.ProductTypeID in [8,9,10,37]:
					print(shop, product)
					if random.random() < probability:
						print('saving')
						price = Price(ShopID=shop, ProductID=product, Price=np.random.normal(mean_price, stdev))
						price.save()

		num_users = 100

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
		obj.save()
		return Response("Done")

@api_view(['POST'])
def sms_order(request):
	if request.method == 'POST':

		names = ProductType.objects.all()
		b = request.data
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
		totalCost = 0
		for product in b["content"].split('\n'):
			product = product.lower()
			mindist = 100000000000
			for p in Product.objects.all():
				if decimal.Decimal(nltk.jaccard_distance(set(nltk.ngrams(product, n=3)), set(nltk.ngrams(p.ProductTypeID.ProductTypeName.lower(), n=3)).union(set(nltk.ngrams(p.ProductName.lower(), n=3))).union(set(nltk.ngrams(p.ProductBrandID.BrandName.lower(), n=3)))))/(p.ProductWeight) < mindist:
					mindist = decimal.Decimal(nltk.jaccard_distance(set(nltk.ngrams(product, n=3)), set(nltk.ngrams(p.ProductTypeID.ProductTypeName.lower(), n=3)).union(set(nltk.ngrams(p.ProductName.lower(), n=3))).union(set(nltk.ngrams(p.ProductBrandID.BrandName.lower(), n=3)))))/p.ProductWeight
					mindistproduct = p

			print(mindistproduct.ProductName, mindist)
			print(Price.objects.filter(ProductID=mindistproduct).order_by('Price')[0])
			# TODO: Return cheapest/closest combination
			if mindist<0.95:
				items.append(mindistproduct.ProductBrandID.BrandName + ' ' + mindistproduct.ProductName)
				price = Price.objects.filter(ProductID=mindistproduct).order_by('Price')[0]
				totalCost+=price.Price
				if "confirm" in b and b["confirm"]=="true":
					item = OrderItems(OrderID=order, PriceID=price, Quantity=1)
					item.save()
				else:
					item = ShoppingItem(UserID=user, PriceID=price, Quantity=1)
					item.save()
			else:
				items.append('not found')
			
		resp = {}
		resp['userID'] = user.UserID
		resp["items"] = items
		resp["cost"] = totalCost
		resp["status"]="ok"
		print(resp)
		return JsonResponse(resp)

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

STATE = {}
LAT = {}
LNG = {}
YES_REPLIES = ['yes', 'yeah', 'correct', 'yep']
NO_REPLIES = ['no', 'nope', 'wrong', 'nop']
LIST_QUERIES = ['list', 'cart']


@api_view(['POST'])
def chatbot(request):
	if request.method=='POST':
		b = request.data
		print(b)
		r = {}
		if not user_exists(b['from']) and b['from'] not in STATE:
			r['content'] =  'Welcome! I noticed you are new here. Why don\'t you go ahead and send me your address so that I can sign you up?'
			STATE[b['from']] = 'registering'
		elif b['from'] in STATE:
			if STATE[b['from']]=='registering':
				r['content'] = geocode(b)
				STATE[b['from']] = 'geocoding'
			elif STATE[b['from']]=='geocoding':
				if b['content'].lower() in YES_REPLIES:
					requests.post('https://rhubarb-cake-22341.herokuapp.com/api/v1/sms/register/', '{"from": ' + b['from'] + ', "lat": ' + LAT[b['from']] + ', "lng": ' + LNG[b['from']] + '}')
					r['content'] = 'You are now registered! Nice! You can send in orders at any time.'
					STATE[b['from']]='registered'
				elif b['content'].lower() in NO_REPLIES:
					r['content'] = 'Oh sorry about that :(\nCan you try that again with a more specific location?'
					STATE[b['from']]='registering'
			elif STATE[b['from']]=='registered':
				# Order received
				print(b)
				req = requests.post('https://rhubarb-cake-22341.herokuapp.com/api/v1/sms/order/', b)
				req = req.json()
				print(req)
				r['content'] = 'Here\'s what I found:\n'
				for item in range(len(req['items'])):
					r['content']+=b['content'].split('\n')[item] + ": " + req['items'][item] + '\n'
				r['content']+='That would cost you a total of €' + req['cost']
		else:
			STATE[b['from']] = 'registered'
		
		r['from'] = 'bot'

		return JsonResponse(r)

def user_exists(phone):
	try:
		user = User.objects.get(Userphonenumber=phone)
		return True
	except:
		return False

def geocode(msg):
	req = requests.get("https://nominatim.openstreetmap.org/search/" + msg['content'].replace(" ", '%20') + "?format=json").json()[0]
	LAT[msg['from']] = req['lat']
	LNG[msg['from']] = req['lon']
	return "So you're telling me you live here? https://www.openstreetmap.org/?mlat=" + req['lat'] + "&mlon=" + req['lon']+ " \nIt's not that I don't know, just checking if you know ;)"

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
