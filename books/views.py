import uuid
import json
import hmac
import hashlib
import base64

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import FileResponse

from rest_framework.views import APIView
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, NotFound

from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter

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

    @extend_schema(
    parameters=[
        OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH)
    ]
    )
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
            order.square_order_id = result.payment_link.order_id
            order.save()
            return Response({
                "payment_url": result.payment_link.url
            })

        return Response(result.errors, status=400)

def verify_square_signature(request):
    signature = request.headers.get("x-square-hmacsha256-signature")

    if not signature:
        return False

    url = request.build_absolute_uri()
    body = request.body  # raw bytes

    message = url.encode("utf-8") + body

    key = settings.SQUARE_WEBHOOK_SIGNATURE_KEY.encode("utf-8")

    digest = hmac.new(key, message, hashlib.sha256).digest()
    computed_signature = base64.b64encode(digest).decode("utf-8")

    return hmac.compare_digest(computed_signature, signature)

@extend_schema(request=None, responses=None)
@method_decorator(csrf_exempt, name="dispatch")
class SquareWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    async def post(self, request):
        if not verify_square_signature(request):
            return Response({"error": "Invalid signature"}, status=403)

        event = request.data

        if event.get("type") == "payment.updated":
            payment = event["data"]["object"]["payment"]
            
            if payment.get("status") == "COMPLETED":

                metadata = payment.get("metadata", {})
                order_id = metadata.get("order_id")

                try:
                    if order_id:
                        order = Order.objects.filter(id=order_id).first()
                    
                    if not order_id:
                        square_order_id = payment.get("order_id")

                        if not square_order_id:
                            return Response({"status": "no square order id"})

                        order = Order.objects.get(square_order_id=square_order_id)

                        
                    if order.status == Order_Status.PAID:
                        return Response({"status": "already processed"})

                    order.status = Order_Status.PAID
                    order.square_payment_id = payment.get("id")
                    order.save()

                    print(f"Order {order.id} marked as PAID")

                except Order.DoesNotExist:
                    print("Order not found for square order:", square_order_id)

        return Response({"status": "ok"})

@extend_schema(
    responses={200: OpenApiTypes.BINARY}
)
class DownloadBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except order.DoesNotExist:
            raise NotFound("Order not found")

        if order.status != Order_Status.PAID:
            raise PermissionDenied("Payment_required")

        file_path = order.book.pdf_file.path

        return FileResponse(open(file_path, "rb"), content_type="application/pdf")