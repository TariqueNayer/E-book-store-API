from rest_framework import serializers
from .models import Book, Order

class AdminBookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book 
        fields = ['id', 'title', 'pdf_file','author', 'description', 'price']

class PublicBookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book 
        fields = ['id', 'title', 'author', 'description', 'price']

class AdminOrderSerializer(serializers.ModelSerializer):
    # This automatically add the tag if the book is gone ma boy
    book_info = serializers.ReadOnlyField(source='book_display_info')
    class Meta:
        model = Order
        fields = ['id', 'user', 'book', 'book_info', 'price', 'status']
        read_only_fields = ['user']

class PublicOrderSerializer(serializers.ModelSerializer):
    # This automatically add the tag if the book is gone ma boy
    book_info = serializers.ReadOnlyField(source='book_display_info')
    status = serializers.CharField(read_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = ['id', 'user', 'book', 'book_info', 'price', 'status']