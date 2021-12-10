from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

from .views import *

app_name = 'api'
urlpatterns = [
    path('test', Test.as_view()),
    path('init', InitializeApp.as_view()),
    path('registration', Registration.as_view()),
    path('wallets', Wallets.as_view()),
    path('balance', Balance.as_view()),
    path('send', SendFunds.as_view()),
    path('acquire', AcquireFunds.as_view()),
    path('withdraw', WithdrawFunds.as_view()),
    path('transactions', ListTransactions.as_view())
]
