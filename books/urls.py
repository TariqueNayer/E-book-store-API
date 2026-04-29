from django.urls import path, include
from . import views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'books', views.PublicBookViewSet, basename='books')
router.register(r'admin/books', views.AdminBookViewSet, basename='admin-books')

router.register(r'orders', views.UserOrderViewSet, basename='orders')
router.register(r'admin/orders', views.AdminOrderViewSet, basename='admin-orders')


urlpatterns = [
    path("order/webhook/", views.SquareWebhookView.as_view(), name="webhook_view"), 
    path("", include(router.urls)),   # ViewSet routes
    path("orders/<uuid:order_id>/download/", views.DownloadBookView.as_view(), name="download_order") # download odered book
    
]