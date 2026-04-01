
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def get_response(self):
        response = super().get_response()
        access_token = response.data.get("access")
        if access_token:
            response.set_cookie(
                key="bookapi-auth",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="Lax",
            )
        return response
    