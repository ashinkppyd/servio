from django.db import transaction
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from company.models import Slot
from notifications.sqs_service import send_to_sqs
from notifications.utils import send_notification
from payments.models import Payment

from .models import Booking, Rating
from .serializers import BookingSerializer
from .utils import calculate_salary, update_worker_progress

ACTIVE_BOOKING_STATUSES = ["pending", "approved"]


def active_booking_conflict(worker, event_date):
    return Booking.objects.filter(
        worker=worker,
        status__in=ACTIVE_BOOKING_STATUSES,
        slot__site__date=event_date,
    )


def first_serializer_error(errors):
    for value in errors.values():
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, dict):
            nested = first_serializer_error(value)
            if nested:
                return nested
        return str(value)
    return "Invalid booking request"


class ApplyBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        serializer = BookingSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            slot = serializer.validated_data["slot"]
            event_date = slot.site.date
            today = timezone.localdate()

            if event_date < today:
                return Response(
                    {
                        "error": "This work date is already over",
                        "code": "WORK_DATE_OVER",
                        "work_date": event_date,
                        "today": today,
                    },
                    status=400,
                )

            existing = (
                active_booking_conflict(user, event_date)
                .select_related("slot", "slot__site")
                .first()
            )
            if existing:
                return Response(
                    {
                        "error": "You can only apply for one role on the same day",
                        "code": "SAME_DAY_BOOKING_EXISTS",
                        "work_date": event_date,
                        "existing_role": existing.slot.position,
                        "existing_status": existing.status,
                    },
                    status=400,
                )

            serializer.save()
            try:
                response = send_to_sqs(
                    {
                        "type": "BOOKING_APPLICATION",
                        "user_id": user.id,
                        "message": (
                            f"Hello {user.username}, " "You have successfully applied"
                        ),
                        "fcm_token": request.user.fcm_token,
                    }
                )
                print("SQS RESPONSE:", response)
                print("SQS message sent ✅")
            except Exception as e:
                print("SQS ERROR:", str(e))
            return Response({"message": "Applied successfully"}, status=201)
        return Response(
            {
                "error": first_serializer_error(serializer.errors),
                "code": "INVALID_BOOKING_REQUEST",
                "details": serializer.errors,
            },
            status=400,
        )


class UpdateBookingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.select_related("slot", "worker").get(
                id=booking_id
            )
        except Booking.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        status = request.data.get("status")

        if status not in ["approved", "rejected"]:
            return Response({"error": "Invalid status"}, status=400)

        if status == "approved":
            with transaction.atomic():
                booking = (
                    Booking.objects.select_for_update()
                    .select_related("slot", "slot__site", "worker")
                    .get(id=booking.id)
                )

                if booking.status == "approved":
                    return Response({"error": "Already approved"}, status=400)

                event_date = booking.slot.site.date
                if event_date < timezone.localdate():
                    return Response({"error": "This event is already over"}, status=400)

                if (
                    active_booking_conflict(booking.worker, event_date)
                    .exclude(id=booking.id)
                    .exists()
                ):
                    return Response(
                        {
                            "error": (
                                "This worker already has a booking on the same day"
                            )
                        },
                        status=400,
                    )

                slot = Slot.objects.select_for_update().get(id=booking.slot.id)

                if slot.available_slots <= 0:
                    return Response({"error": "Slot full"}, status=400)

                slot.available_slots -= 1
                slot.save()
                salary = calculate_salary(booking.slot.position)
                booking.salary = salary
                Payment.objects.create(
                    worker=booking.worker, booking=booking, amount=salary
                )

        if status == "rejected" and booking.status == "approved":
            with transaction.atomic():
                slot = Slot.objects.select_for_update().get(id=booking.slot.id)
                slot.available_slots += 1
                slot.save()

        booking.status = status
        booking.save()
        send_notification(
            booking.worker, f"Your booking is {status} for {booking.slot.position}"
        )
        return Response({"message": f"{status} success"})


class CompanyBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = timezone.localdate()
            bookings = Booking.objects.filter(
                slot__site__company_id=request.user.id,
                slot__site__date__gte=today,
            ).select_related("worker", "slot", "slot__site")

            data = []
            for b in bookings:
                data.append(
                    {
                        "id": b.id,
                        "worker_user_id": b.worker.id,
                        "company_custom_id": b.slot.site.company.custom_id,
                        "worker_name": b.worker.username,
                        "phone": getattr(b.worker, "phone", ""),
                        "location": getattr(b.worker, "place", ""),
                        "role": b.slot.position,
                        "salary": getattr(b, "salary", 0),
                        "status": b.status,
                        "attendance": getattr(b, "attendance", "pending"),
                        "site_name": b.slot.site.name,
                        "date": b.slot.site.date,
                    }
                )
            return Response(data)

        except Exception as e:
            print("ERROR:", e)
            return Response({"error": str(e)}, status=500)


class MarkAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.select_related("worker").get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        attendance = request.data.get("attendance")

        if attendance not in ["present", "absent"]:
            return Response({"error": "Invalid"}, status=400)
        booking.attendance = attendance
        booking.save()
        if attendance == "present":
            update_worker_progress(booking.worker)
            send_notification(booking.worker, "You attended the event ✅")
        else:
            send_notification(booking.worker, "You were marked absent ❌")
        return Response({"message": "Attendance updated"})


class AddRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        rating = request.data.get("rating")
        review = request.data.get("review", "")

        Rating.objects.create(
            worker=booking.worker, booking=booking, rating=rating, review=review
        )
        send_notification(booking.worker, f"You received a rating ⭐ ({rating})")
        return Response({"message": "Rating added"})


class BookingUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        try:
            booking = Booking.objects.select_related("worker").get(id=id)
        except Booking.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        attendance = request.data.get("attendance")
        rating = request.data.get("rating")

        if attendance:
            booking.attendance = attendance
            if attendance == "present":
                update_worker_progress(booking.worker)
        if rating and booking.attendance == "present":
            booking.rating = rating
        booking.save()

        return Response({"message": "Updated successfully"})
