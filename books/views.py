from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import Book, Order, Order_Status
from .serializers import AdminBookSerializer, PublicBookSerializer, AdminOrderSerializer, PublicOrderSerializer

# Create your views here.

# Book.

class PublicBookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.all()
    serializer_class = PublicBookSerializer
    

class AdminBookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = AdminBookSerializer
    permission_classes = [permissions.IsAdminUser]


# Order.

# renders admin/orders/
class AdminOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = AdminOrderSerializer
    permission_classes = [permissions.IsAdminUser]

# orders/
class UserOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PublicOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.action in ["list", "retrieve", "pay"]:
            return Order.objects.filter(
                user=self.request.user,
                status__in=[Order_Status.PAID, Order_Status.CANCELLED, Order_Status.PENDING]
            )
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        self.order = serializer.save(
            status=Order_Status.PENDING
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        order_id = response.data["id"]
        pay_url = f"/orders/{order_id}/pay/"

        response.data["pay_url"] = pay_url

        return response

    @action(detail=True, methods=["get"])
    def pay(self, request, pk=None):
        order = self.get_object()

        if order.status != Order_Status.PENDING:
            return Response(
                {"detail": "Order is not pending."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "message": "Proceed to payment",
            "order_id": order.id,
            "amount": order.price
        })




