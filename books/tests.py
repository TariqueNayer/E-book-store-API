from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Book, Order, Order_Status

from rest_framework.test import APIClient
from rest_framework import status

from unittest.mock import patch, MagicMock
import hmac, hashlib, base64

# Helper tools __________________________________________________________
User_model = get_user_model()
def make_user(username : str ,is_staff : bool = False ):
	return User_model.objects.create_user(username=username, is_staff=is_staff)

def make_book(title : str, price : float):
	return Book.objects.create(title=title, price=price)

def make_order(user, book, status=Order_Status.PENDING):
	return Order.objects.create(user=user, book=book, status=status,  price=book.price)


# Book Views _________________________________________________________

class AdminBookViewSetTest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin = make_user("admin_user", is_staff=True)
		self.user = make_user("normal_user")

	def test_Unauthenticated_cannot_access(self):
		response = self.client.get("/api/v1/admin/books/")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_admin_can_create_book(self):
		self.client.force_authenticate(self.admin)
		response = self.client.post("/api/v1/admin/books/", {"title": "nice_title", "price": "5.00"})
		self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_other_user_can_not_create_book(self):
		self.client.force_authenticate(self.user)
		response = self.client.post("/api/v1/admin/books/", {"title": "nice_title", "price": "5.00"})
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

# Order Views _______________________________________________________

class UserOrderViewSetTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user_a = make_user("user_a")
		self.user_b = make_user("user_b")
		self.book = make_book("test_book", "9.99")

	def test_unauthenticated_cannot_list_orders(self):
		response = self.client.get("/api/v1/orders/")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_user_only_sees_their_own_orders(self):
		"""user A must never see user B's orders."""
		make_order(self.user_a, self.book)
		make_order(self.user_b, self.book)

		self.client.force_authenticate(self.user_a)
		response = self.client.get("/api/v1/orders/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		for order in response.data:
			# Every returned order must belong to user_a
			retrieved = Order.objects.get(id=order["id"])
			self.assertEqual(retrieved.user, self.user_a)

	def test_cancelled_orders_appear_in_list(self):
		make_order(self.user_a, self.book, status=Order_Status.CANCELLED)
		self.client.force_authenticate(self.user_a)
		response = self.client.get("/api/v1/orders/")
		self.assertEqual(len(response.data), 1)

	def test_create_sets_status_to_pending(self):
		self.client.force_authenticate(self.user_a)
		response = self.client.post("/api/v1/orders/", {"book": self.book.id})
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		order = Order.objects.get(id=response.data["id"])
		self.assertEqual(order.status, Order_Status.PENDING)

	def test_create_response_includes_pay_url(self):
		self.client.force_authenticate(self.user_a)
		response = self.client.post("/api/v1/orders/", {"book": self.book.id})
		self.assertIn("pay_url", response.data)
		self.assertIn(str(response.data["id"]), response.data["pay_url"])

	