from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import LoginForm


class Login(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm
