from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from booking.models import Booking
from company.models import Site, Slot

User = get_user_model()


class BookingDateRulesTest(APITestCase):
    def setUp(self):
        self.worker = User.objects.create_user(
            username="worker1",
            email="worker1@test.com",
            password="test123",
            role="worker",
            phone="9000000001",
        )
        self.company = User.objects.create_user(
            username="company1",
            email="company1@test.com",
            password="test123",
            role="company",
            phone="9000000002",
        )
        self.client.force_authenticate(self.worker)

    def create_slot(self, days_from_today, position="juicer"):
        site = Site.objects.create(
            company=self.company,
            name=f"Event {days_from_today}",
            location="Malappuram",
            date=timezone.localdate() + timezone.timedelta(days=days_from_today),
            reporting_time="09:00",
        )
        return Slot.objects.create(
            site=site,
            position=position,
            total_slots=2,
            available_slots=2,
        )

    @patch("booking.views.send_to_sqs")
    def test_worker_can_apply_for_different_event_days(self, mock_send_to_sqs):
        day_one_slot = self.create_slot(1)
        day_two_slot = self.create_slot(2, "captain")

        first_response = self.client.post("/api/apply/", {"slot": day_one_slot.id})
        second_response = self.client.post("/api/apply/", {"slot": day_two_slot.id})

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(Booking.objects.filter(worker=self.worker).count(), 2)

    @patch("booking.views.send_to_sqs")
    def test_worker_cannot_apply_twice_on_same_event_day(self, mock_send_to_sqs):
        first_slot = self.create_slot(1)
        second_slot = self.create_slot(1, "captain")

        first_response = self.client.post("/api/apply/", {"slot": first_slot.id})
        second_response = self.client.post("/api/apply/", {"slot": second_slot.id})

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(Booking.objects.filter(worker=self.worker).count(), 1)

    def test_all_sites_hides_past_events(self):
        past_slot = self.create_slot(-1)
        future_slot = self.create_slot(1, "captain")

        response = self.client.get("/api/all-sites/")

        self.assertEqual(response.status_code, 200)
        site_ids = {site["id"] for site in response.data["sites"]}
        self.assertNotIn(past_slot.site.id, site_ids)
        self.assertIn(future_slot.site.id, site_ids)

    def test_worker_sites_hides_past_events(self):
        past_slot = self.create_slot(-1)
        future_slot = self.create_slot(1, "captain")

        response = self.client.get("/api/sites/")

        self.assertEqual(response.status_code, 200)
        site_ids = {site["id"] for site in response.data}
        self.assertNotIn(past_slot.site.id, site_ids)
        self.assertIn(future_slot.site.id, site_ids)

    def test_worker_report_hides_past_bookings(self):
        past_slot = self.create_slot(-1)
        future_slot = self.create_slot(1, "captain")
        Booking.objects.create(worker=self.worker, slot=past_slot)
        Booking.objects.create(worker=self.worker, slot=future_slot)

        response = self.client.get("/api/report/")

        self.assertEqual(response.status_code, 200)
        dates = {booking["date"] for booking in response.data}
        self.assertNotIn(past_slot.site.date, dates)
        self.assertIn(future_slot.site.date, dates)
