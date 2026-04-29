from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Book, Order, Order_Status

from rest_framework.test import APIClient
from rest_framework import status

from unittest.mock import patch, MagicMock
import hmac, hashlib, base64
import json

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

# Payment tests_________________________________________________

class PayActionTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = make_user("buyer")
		self.book = make_book("test_book", "9.99")

	@patch("books.views.Square")  # adjust import path
	def test_pay_already_paid_order_returns_400(self, mock_square):
		order = make_order(self.user, self.book, status=Order_Status.PAID)
		self.client.force_authenticate(self.user)
		response = self.client.post(f"/api/v1/orders/{order.id}/pay/")
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("already processed", response.data["error"])
		# Square was never called
		mock_square.assert_not_called()

	@patch("books.views.Square")
	def test_pay_pending_order_calls_square_and_returns_url(self, MockSquare):
		order = make_order(self.user, self.book, status=Order_Status.PENDING)

		mock_link = MagicMock()
		mock_link.url = "https://square.link/fake"
		mock_link.order_id = "sq_order_123"
		MockSquare.return_value.checkout.payment_links.create.return_value = MagicMock(
			payment_link=mock_link, errors=None
		)

		self.client.force_authenticate(self.user)
		response = self.client.post(f"/api/v1/orders/{order.id}/pay/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("payment_url", response.data)

		order.refresh_from_db()
		self.assertEqual(order.square_order_id, "sq_order_123")

# WebhookView tests_____________________________________________________

def make_square_signature(url, body_bytes, key):
	"""Replicating verify_square_signature logic."""
	message = url.encode("utf-8") + body_bytes
	digest = hmac.new(key.encode("utf-8"), message, hashlib.sha256).digest()
	return base64.b64encode(digest).decode("utf-8")

class SquareWebhookViewTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = make_user("buyer")
		self.book = make_book("cool_book", "99.99")
		self.order = make_order(self.user, self.book, status=Order_Status.PENDING)
		self.order.square_order_id = "sq_order_test_123"
		self.order.save()

	def test_invalid_signature_returns_403(self):
		path = reverse('webhook_view')
		response = self.client.post(
			path,
			data={"type": "payment.updated"},
			format="json",
			HTTP_X_SQUARE_HMACSHA256_SIGNATURE="bad_signature",
		)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_missing_signature_returns_403(self):
		path = reverse('webhook_view')
		response = self.client.post(path, data={}, format="json")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	@patch("django.conf.settings.SQUARE_WEBHOOK_SIGNATURE_KEY", "test_key")
	def test_valid_payment_marks_order_paid(self):
		path = reverse('webhook_view')  # e.g., "/api/v1/order/webhook/"
		url = f"http://testserver{path}"
		payload = {
			"type": "payment.updated",
			"data": {
				"object": {
					"payment": {
						"status": "COMPLETED",
						"id": "sq_payment_abc",
						"order_id": self.order.square_order_id,
						"metadata": {},
					}
				}
			},
		}
		body = json.dumps(payload).encode("utf-8")
		sig = make_square_signature(url, body, "test_key")

		response = self.client.post(
			path,
			data=body,
			content_type="application/json",
			HTTP_X_SQUARE_HMACSHA256_SIGNATURE=sig,
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.order.refresh_from_db()
		self.assertEqual(self.order.status, Order_Status.PAID)

# DownloadView Tests______________________________________________________________________________

class DownloadBookViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("reader")
        self.other_user = make_user("intruder")
        self.book = make_book("lovely book", "30.00")

    @patch("books.views.supabase")
    def test_paid_order_redirects_to_signed_url(self, mock_supa):
        mock_supa.storage.from_.return_value.create_signed_url.return_value = {
            "signedURL": "https://supabase.example.com/signed-url"
        }
        order = make_order(user=self.user, book=self.book, status=Order_Status.PAID)
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/v1/orders/{order.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_unpaid_order_is_denied(self):
        order = make_order(user=self.user, book=self.book, status=Order_Status.PENDING)
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/v1/orders/{order.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_users_order_is_not_found(self):
        """User cannot download someone else's order — should 404, not 403."""
        order = make_order(user=self.other_user, book=self.book, status=Order_Status.PAID)
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/v1/orders/{order.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_download_denied(self):
        order = make_order(user=self.user, book=self.book, status=Order_Status.PAID)
        response = self.client.get(f"/api/v1/orders/{order.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)