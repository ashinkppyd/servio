from rest_framework import serializers

from .models import Site, Slot


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = "__all__"
        read_only_fields = ["available_slots", "site"]


class SiteSerializer(serializers.ModelSerializer):
    slots = SlotSerializer(many=True, read_only=True)
    company_id = serializers.IntegerField(source="company.custom_id", read_only=True)

    class Meta:
        model = Site
        fields = "__all__"


class CreateSiteSerializer(serializers.ModelSerializer):
    slots = SlotSerializer(many=True, required=False)

    class Meta:
        model = Site
        fields = ["name", "location", "date", "reporting_time", "slots"]

    def create(self, validated_data):
        slots_data = validated_data.pop("slots", [])
        user = self.context["request"].user

        site = Site.objects.create(company=user, **validated_data)

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

        if not slots_data:
            for pos in DEFAULT_POSITIONS:
                Slot.objects.create(
                    site=site, position=pos, total_slots=0, available_slots=0
                )
        else:
            for slot in slots_data:
                Slot.objects.create(
                    site=site,
                    position=slot.get("position"),
                    total_slots=slot.get("total_slots", 0),
                    available_slots=slot.get("total_slots", 0),
                )

            existing = [s["position"] for s in slots_data]
            for pos in DEFAULT_POSITIONS:
                if pos not in existing:
                    Slot.objects.create(
                        site=site, position=pos, total_slots=0, available_slots=0
                    )
        return site
