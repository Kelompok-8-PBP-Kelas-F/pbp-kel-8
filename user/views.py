from django import forms
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def login(request):
    if request.user.is_authenticated:
        return redirect("core:landing_page")

    username = ""
    error = ""
    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        account = User.objects.filter(username__iexact=username).first()
        if account:
            user = authenticate(
                request,
                username=account.username,
                password=password,
            )
        else:
            user = None

        if user is None:
            error = "Username atau password salah."
        else:
            auth_login(request, user)

            if request.POST.get("remember_me"):
                request.session.set_expiry(60 * 60 * 24 * 14)
            else:
                request.session.set_expiry(0)

            if url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("core:landing_page")

    return render(
        request,
        "pages/user/login.html",
        {"username": username, "error": error, "next_url": next_url},
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("core:landing_page")

    username = ""
    error = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        try:
            username = forms.CharField(max_length=150).clean(username)
        except ValidationError:
            error = "Username tidak boleh kosong."
        else:
            if User.objects.filter(username__iexact=username).exists():
                error = "Username sudah digunakan."
            elif password != password_confirm:
                error = "Konfirmasi password tidak cocok."
            else:
                new_user = User(username=username)
                try:
                    validate_password(password, user=new_user)
                except ValidationError as exc:
                    error = " ".join(exc.messages)
                else:
                    new_user = User.objects.create_user(
                        username=username,
                        password=password,
                    )
                    auth_login(request, new_user)
                    return redirect("core:landing_page")

    return render(
        request,
        "pages/user/register.html",
        {"username": username, "error": error},
    )


def logout(request):
    auth_logout(request)
    return redirect("core:landing_page")