
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    


def show_token(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/google/login/')
    
    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    
    return render(request, 'token_display.html', {
        'access_token': access_token,
        'user': request.user
    })