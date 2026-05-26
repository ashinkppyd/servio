from django.db.models import Avg
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.models import Booking, WaitlistApplication
from company.models import Slot

from .models import Site
from .serializers import CreateSiteSerializer, SiteSerializer


class CreateSiteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateSiteSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            site = serializer.save()
            print("Site created:", site)

            return Response(
                {
                    "message": "Site created successfully",
                    "data": SiteSerializer(site).data,
                },
                status=201,
            )
        print(serializer.errors)
        return Response(serializer.errors, status=400)


class CompanySitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sites = Site.objects.filter(company=request.user)
        serializer = SiteSerializer(sites, many=True)
        return Response(serializer.data)


class AllSitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        sites = Site.objects.filter(date__gte=today)
        serializer = SiteSerializer(sites, many=True)

        bookings = Booking.objects.filter(
            worker=request.user, slot__site__date__gte=today
        )
        print("User Bookings:", bookings)

        booking_map = {b.slot.id: b.status for b in bookings}
        print("Booking Map:", booking_map)
        waitlist_map = {
            w.slot.id: w.status
            for w in WaitlistApplication.objects.filter(
                worker=request.user, slot__site__date__gte=today
            )
        }

        return Response(
            {
                "sites": serializer.data,
                "user_bookings": booking_map,
                "user_waitlist": waitlist_map,
            }
        )


class DeleteSiteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, site_id):
        try:
            site = Site.objects.get(id=site_id, company=request.user)
            site.delete()
            return Response({"message": "Deleted"})
        except Site.DoesNotExist:
            return Response({"error": "Not found"}, status=404)


class UpdateSiteView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            site = Site.objects.get(id=id, company=request.user)
        except Site.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        site.name = request.data.get("name", site.name)
        site.location = request.data.get("location", site.location)
        site.date = request.data.get("date", site.date)
        site.reporting_time = request.data.get("reporting_time", site.reporting_time)
        site.save()

        slots_data = request.data.get("slots", [])

        DEFAULT_POSITIONS = [
            "juicer",
            "juicer_helper",
            "catering_boy",
            "main_boy",
            "supervisor",
            "captain",
            "chef_helper",
            "decoration",
        ]

        for slot_data in slots_data:
            position = slot_data.get("position")
            total_slots = slot_data.get("total_slots")
            slot = Slot.objects.filter(site=site, position=position).first()

            if slot:
                booked = slot.total_slots - slot.available_slots

                if total_slots < booked:
                    return Response(
                        {"error": f"{position} already has {booked} workers"},
                        status=400,
                    )
                slot.total_slots = total_slots
                slot.available_slots = total_slots - booked
                slot.save()
            else:
                Slot.objects.create(
                    site=site,
                    position=position,
                    total_slots=total_slots,
                    available_slots=total_slots,
                )

        for pos in DEFAULT_POSITIONS:
            Slot.objects.get_or_create(
                site=site,
                position=pos,
                defaults={"total_slots": 0, "available_slots": 0},
            )
        return Response({"message": "Updated successfully"})


class SiteReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, site_id):
        bookings = Booking.objects.filter(
            slot__site_id=site_id, status="approved"
        ).select_related("worker", "slot")
        avg_rating = bookings.aggregate(Avg("rating"))["rating__avg"]
        data = []

        for b in bookings:
            data.append(
                {
                    "booking_id": b.id,
                    "worker_name": b.worker.username,
                    "phone": getattr(b.worker, "phone", ""),
                    "location": getattr(b.worker, "place", ""),
                    "role": b.slot.position,
                    "salary": getattr(b, "salary", 0),
                    "attendance": getattr(b, "attendance", "pending"),
                    "rating": getattr(b, "rating", 0),
                }
            )

        return Response({"site_rating": avg_rating or 0, "workers": data})
