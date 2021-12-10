from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False,
                              verbose_name='Владелец', related_name='owner')

    name = models.CharField(null=False, blank=False, default='Новый кошелек', max_length=20,
                            verbose_name='Наименование')

    funds = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False, default=0.00,
                                verbose_name='Средства', validators=[MinValueValidator(0)])

    def __str__(self):
        return f'ID#{self.id}: {self.owner}: {self.funds}'


class Transaction(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False,
                               verbose_name='Отправитель', related_name='sender_id')

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False,
                                  verbose_name='Получатель', related_name='recipient_id')

    date = models.DateTimeField(auto_now_add=True, null=False, verbose_name='Дата совершения')

    TYPE_CHOICES = (
        ('P2P', 'Перевод средств'),
        ('ACQ', 'Зачисление средств'),
        ('WTH', 'Снятие средств')
    )

    type = models.CharField(null=False, blank=False, choices=TYPE_CHOICES, max_length=3, verbose_name='Тип транзакции')

    amount = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False, verbose_name='Сумма')

    description = models.CharField(null=True, blank=True, max_length=200, verbose_name='Описание')

    def __str__(self):
        return f'ID#{self.id}'
