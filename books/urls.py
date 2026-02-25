from django.urls import path, include
from . import views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'books', views.PublicBookViewSet, basename='books')
router.register(r'admin/books', views.AdminBookViewSet, basename='admin-books')

router.register(r'orders', views.UserOrderViewSet, basename='orders')
router.register(r'admin/orders', views.AdminOrderViewSet, basename='admin-orders')


urlpatterns = [
    path("", include(router.urls)),   # ViewSet routes
    path("orders/webhook/", views.SquareWebhookView.as_view()),  # webhook (NOT in router)
]