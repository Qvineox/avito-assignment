from django.contrib import admin

# Register your models here.
from .models import Wallet, Transaction


@admin.register(Wallet)
class Wallets(admin.ModelAdmin):
    list_display = ('id', 'owner', 'name', 'funds')


@admin.register(Transaction)
class Transactions(admin.ModelAdmin):
    list_display = ('id', 'date', 'sender', 'recipient', 'description', 'type', 'amount')
