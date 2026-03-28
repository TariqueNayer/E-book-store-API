from django.db import models
from django.contrib.auth import get_user_model
import uuid

from .storage_backends import PublicMediaStorage

# Create your models here.
class Book(models.Model):
	id = models.UUIDField(
		primary_key=True,
		default=uuid.uuid4,
		editable=False,
	)
	title = models.CharField(max_length=200)

	cover = models.ImageField(upload_to='books/cover/', blank=True, storage=PublicMediaStorage())

	author = models.CharField(max_length=500)

	description = models.TextField()

	pdf_file = models.FileField(upload_to='books/pdf_file/', blank=True)

	uploaded_at = models.DateTimeField(auto_now_add=True)
	
	price = models.DecimalField(max_digits=6, decimal_places=2)

	def __str__(self):
		return self.title


class Order_Status(models.TextChoices):
		# Value stored in database  | Human-readable name
		PENDING = "WT", "Pending"
		PAID = "PD", "Paid"
		CANCELLED = "CN", "Cancelled"


class Order(models.Model):
	id = models.UUIDField(
		primary_key=True,
		default=uuid.uuid4,
		editable=False,
	)

	user = models.ForeignKey(
		get_user_model(),
		on_delete=models.CASCADE,
	)

	book = models.ForeignKey(
		Book, on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)

	book_history = models.CharField(max_length=500, editable=False, help_text="Stores UUID | Title | [Status]")

	created_at = models.DateTimeField(auto_now_add=True)

	price = models.DecimalField(max_digits=6, decimal_places=2)

	square_payment_id = models.CharField(max_length=100, blank=True, null=True)

	square_order_id = models.CharField(max_length=100, blank=True, null=True)
	
	status = models.CharField(
		max_length=2,
		choices=Order_Status.choices,
		default=Order_Status.PENDING,
	)

	@property
	def book_display_info(self) -> str:
		if self.book:
			return f"{self.book.id} | {self.book.title}"
		else:
			return f"{self.book_history} [Discontinued]"

	def save(self, *args, **kwargs):

		if self._state.adding and self.book:
			self.book_history = f"{self.book.id} | {self.book.title}"
			self.price = self.book.price

		super().save(*args, **kwargs)

	