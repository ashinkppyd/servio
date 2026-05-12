from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.models import Booking
from company.models import Site
from payments.models import Payment

# Create your views here.


class WorkerSitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        sites = Site.objects.filter(date__gte=today)
        data = []
        for site in sites:
            slots = []
            for s in site.slots.all():
                slots.append(
                    {
                        "id": s.id,
                        "position": s.position,
                        "available_slots": s.available_slots,
                        "salary": s.salary,
                    }
                )

            data.append(
                {
                    "id": site.id,
                    "name": site.name,
                    "location": site.location,
                    "date": site.date,
                    "slots": slots,
                }
            )
        return Response(data)


class WorkerSiteReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        bookings = Booking.objects.filter(
            worker=request.user, slot__site__date__gte=today
        ).select_related("slot__site")
        data = []
        for b in bookings:
            data.append(
                {
                    "site": b.slot.site.name,
                    "location": b.slot.site.location,
                    "date": b.slot.site.date,
                    "role": b.slot.position,
                    "status": b.status,
                    "salary": b.slot.salary,
                }
            )
        return Response(data)


class WorkerPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(worker=request.user)
        data = []
        for p in payments:
            data.append(
                {
                    "amount": p.amount,
                    "status": p.status,
                    "site": p.booking.slot.site.name,
                    "role": p.booking.slot.position,
                    "date": p.created_at,
                }
            )
        return Response(data)
