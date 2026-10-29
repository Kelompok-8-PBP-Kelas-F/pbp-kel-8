from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "organizer", "date", "time", "location", "attendee_count")
    list_filter = ("date",)
    search_fields = ("name", "location", "organizer__username")

    @admin.display(description="Peserta")
    def attendee_count(self, event):
        return event.attendees.count()
