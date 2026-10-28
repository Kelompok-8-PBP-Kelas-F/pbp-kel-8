from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile
from forum.models import Forum


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'location', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        profile.user.save()
        if commit:
            profile.save()
        return profile


def landing_page(request):
    top_forum = Forum.objects.order_by('-total_likes', '-created_at').first()
    return render(request, 'pages/core/landing.html', {
        'top_forum': top_forum,
    })


def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    listings = user.listings.filter(is_available=True).order_by('-created_at')
    return render(request, 'pages/core/profile.html', {
        'profile_user': user,
        'listings': listings,
    })


@login_required
def profile_edit(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if form.is_valid():
        form.save()
        return redirect('core:profile', username=request.user.username)
    return render(request, 'pages/core/profile_edit.html', {'form': form})
