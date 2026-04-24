from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment

# Create your views here.


class WorkerPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(worker=request.user)

        data = []
        for p in payments:
            data.append(
                {
                    "id": p.id,
                    "amount": p.amount,
                    "status": p.status,
                    "date": p.created_at,
                }
            )

        return Response(data)


class CompanyPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(booking__slot__site__company=request.user)

        data = []
        for p in payments:
            data.append(
                {
                    "worker": p.worker.username,
                    "amount": p.amount,
                    "status": p.status,
                    "booking_id": p.booking.id,
                }
            )

        return Response(data)


class MarkPaymentPaidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = "paid"
            payment.save()
            return Response({"message": "Payment marked as paid"})
        except Payment.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
