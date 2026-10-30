from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import EventForm
from .models import Event


INDONESIAN_WEEKDAYS = (
    "Senin",
    "Selasa",
    "Rabu",
    "Kamis",
    "Jumat",
    "Sabtu",
    "Minggu",
)
INDONESIAN_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
)


def event_page(request):
    events = []
    for event in Event.objects.select_related("organizer").order_by("date", "time"):
        if event.category == "Thrift/Bazaar":
            event_type = "Bazar"
            category = "Bazar thrift"
            tag = "THRIFT / BAZAAR"
        else:
            event_type = event.category
            category = "Fashion sirkular" if event_type == "Swap" else event_type
            tag = event_type.upper()

        events.append(
            {
                "id": str(event.pk),
                "name": event.name,
                "tag": tag,
                "category": category,
                "type": event_type,
                "date": event.date.isoformat(),
                "time": event.time.strftime("%H.%M")
                + (f"–{event.end_time.strftime('%H.%M')}" if event.end_time else ""),
                "location": event.location,
                "distance": None,
                "latitude": float(event.latitude) if event.latitude is not None else None,
                "longitude": float(event.longitude) if event.longitude is not None else None,
                "description": event.desc,
                "detail_url": reverse("event:event_detail", args=[event.pk]),
            }
        )

    user_location = ""
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile:
            user_location = profile.location

    return render(
        request,
        "pages/event/event.html",
        {"events": events, "user_location": user_location},
    )


def event_detail(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related("organizer").prefetch_related("attendees"),
        pk=event_id,
    )
    attendee_count = event.attendees.count()
    is_attending = (
        request.user.is_authenticated
        and event.attendees.filter(pk=request.user.pk).exists()
    )
    can_manage = (
        request.user.is_authenticated and event.organizer_id == request.user.pk
    )
    event_date_label = (
        f"{INDONESIAN_WEEKDAYS[event.date.weekday()]}, "
        f"{event.date.day:02d} {INDONESIAN_MONTHS[event.date.month - 1]} "
        f"{event.date.year}"
    )
    event_time_label = event.time.strftime("%H.%M")
    if event.end_time:
        event_time_label += f"–{event.end_time.strftime('%H.%M')}"
    event_time_label += " WIB"

    return render(
        request,
        "pages/event/eventdetails.html",
        {
            "event": event,
            "attendee_count": attendee_count,
            "is_attending": is_attending,
            "can_manage": can_manage,
            "is_full": (
                event.max_attendees is not None
                and attendee_count >= event.max_attendees
                and not is_attending
            ),
            "event_date_label": event_date_label,
            "event_time_label": event_time_label,
        },
    )


@login_required
def event_create(request):
    form = EventForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.organizer = request.user
        event.save()
        messages.success(request, "Event berhasil dibuat.")
        return redirect("event:event_detail", event_id=event.pk)

    return render(
        request,
        "pages/event/event_form.html",
        {"form": form, "is_edit": False},
    )


@login_required
def event_edit(request, event_id):
    event = get_object_or_404(Event, pk=event_id, organizer=request.user)
    form = EventForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=event,
    )
    if request.method == "POST" and form.is_valid():
        event = form.save()
        messages.success(request, "Perubahan event berhasil disimpan.")
        return redirect("event:event_detail", event_id=event.pk)

    return render(
        request,
        "pages/event/event_form.html",
        {"form": form, "event": event, "is_edit": True},
    )


@login_required
@require_http_methods(["GET", "POST"])
def event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id, organizer=request.user)
    if request.method == "POST":
        event_name = event.name
        event.delete()
        messages.success(request, f'Event "{event_name}" berhasil dihapus.')
        return redirect("event:event_page")

    return render(
        request,
        "pages/event/event_delete.html",
        {"event": event},
    )


@login_required
@require_POST
def register_for_event(request, event_id):
    action = request.POST.get("action", "join")
    if action not in {"join", "leave"}:
        messages.error(request, "Permintaan pendaftaran tidak valid.")
        return redirect("event:event_detail", event_id=event_id)

    with transaction.atomic():
        event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
        already_attending = event.attendees.filter(pk=request.user.pk).exists()

        if action == "leave":
            if already_attending:
                event.attendees.remove(request.user)
                messages.success(request, "Pendaftaran event berhasil dibatalkan.")
            else:
                messages.info(request, "Kamu belum terdaftar pada event ini.")
        elif already_attending:
            messages.info(request, "Kamu sudah terdaftar pada event ini.")
        elif (
            event.max_attendees is not None
            and event.attendees.count() >= event.max_attendees
        ):
            messages.error(request, "Maaf, kuota event ini sudah penuh.")
        else:
            event.attendees.add(request.user)
            messages.success(request, "Kamu berhasil terdaftar pada event ini.")

    return redirect("event:event_detail", event_id=event_id)
