import uuid
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from square import Square
from square.environment import SquareEnvironment
from square.types.currency import Currency

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

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        order = self.get_object()

        if order.status != Order_Status.PENDING:
            return Response({"error": "Order already processed"}, status=400)

        client = Square(
            token=settings.SQUARE_ACCESS_TOKEN,
            environment=SquareEnvironment.SANDBOX,
        )


        result = client.checkout.payment_links.create(
            idempotency_key=str(uuid.uuid4()),
            quick_pay={
                "name": f"Order {order.id}",
                "price_money": {
                    "amount": int(order.price * 100),
                    "currency": "USD"
                },
                "location_id": settings.SQUARE_LOCATION_ID,
                },
            
        )

        if result.payment_link:
            return Response({
                "payment_url": result.payment_link.url
            })

        return Response(result.errors, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class SquareWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        event = request.data

        if event.get("type") == "payment.updated":
            payment = event["data"]["object"]["payment"]

            if payment["status"] == "COMPLETED":
                order_id = payment["metadata"].get("order_id")

                try:
                    order = Order.objects.get(id=order_id)
                    order.status = Order_Status.PAID
                    order.save()
                except Order.DoesNotExist:
                    pass

        return Response({"status": "ok"})

