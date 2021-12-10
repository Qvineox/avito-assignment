from decimal import Decimal

import django.db
from django.contrib.auth.models import User
from django.core import exceptions

from api.models import *
from django.conf import settings as conf_settings

import requests


def create_superuser():
    try:
        super_user = User.objects.create_superuser(username='avito', password='avito')
    except django.db.Error:
        return False
    else:
        Wallet.objects.create(
            owner=super_user
        )

    return True


def get_balance(user_id):
    queryset = Wallet.objects.filter(owner_id=user_id)

    return queryset


def private_funds_transfer(sender_wallet_id, recipient_wallet_id, total_funds_amount) -> (bool, str):
    result, status = wallet_funds_withdrawal(sender_wallet_id, total_funds_amount)

    # выполняется зачисление средств только в случае, если они были успешно сняты
    if result:
        wallet_funds_deposit(recipient_wallet_id, total_funds_amount)

    return result, status


def wallet_funds_withdrawal(wallet_id, total_funds_amount) -> (bool, str):
    wallet = Wallet.objects.get(id=wallet_id)

    wallet.funds -= Decimal(total_funds_amount)

    # перед снятием средств проверяется, не станет ли баланс отрицательным
    # в случае если баланс окажется отрицательным текущий экзепляр транзакции не исполняется
    try:
        wallet.full_clean()
    except exceptions.ValidationError as error_text:
        return False, error_text
    else:
        wallet.save()
        return True, None


def wallet_funds_deposit(wallet_id, total_funds_amount) -> (bool, str):
    wallet = Wallet.objects.get(id=wallet_id)

    wallet.funds += Decimal(total_funds_amount)

    # доп. проверки на валидацию при зачислении средств
    try:
        wallet.full_clean()
    except exceptions.ValidationError as error_text:
        return False, error_text
    else:
        wallet.save()
        return True, None


# применяется для получения id первого кошелька получателя (кошелек по умолчанию)
def get_available_wallet_id(user_id):
    available_wallets = Wallet.objects.filter(owner_id=user_id).order_by('id')

    if len(available_wallets) > 0:
        print('Obama')
        return available_wallets[0].id
    else:
        return False


# для зачисления средств на счет пользователя системой (полный механизм в реальных условиях включал бы
# внесение средств извне на аккаунт системы (id1), затем перечисление виртуального кредита на счет
# пользователя, но в данном проекте представленая условная реализация
def system_funds_acquisition(user_id, total_funds_amount, wallet_id=None):
    if wallet_id is None:
        wallet_id = get_available_wallet_id(user_id)
        print(wallet_id)
        if not wallet_id:
            return False, "No available wallets."

    return wallet_funds_deposit(wallet_id, total_funds_amount)


# предполагается, что данной функцией средства будут выводиться из платженой системы в
# виде наличных или на переводом счет в банк
def system_funds_disposal(user_id, total_funds_amount, wallet_id=None):
    if wallet_id is None:
        available_wallets = Wallet.objects.filter(owner_id=user_id).order_by('id')

        # списываются средства и первого подходящего кошелька
        for wallet in available_wallets:
            if wallet.funds >= Decimal(total_funds_amount):
                wallet_id = wallet.id

    if wallet_id:
        return wallet_funds_withdrawal(wallet_id, total_funds_amount)
    else:
        return False, 'Not enough funds on any wallet.'


def request_exchange_rate(currency, base_amount):
    api_key = conf_settings.EXCHANGE_RATES_API_KEY

    # HTTPS не поддерживается в бесплатной версии
    url = f'http://api.exchangeratesapi.io/v1/latest?access_key={api_key}'

    response = requests.get(url)
    data = response.json()

    if currency in data['rates'].keys():
        ratio = round(data['rates']['RUB'] / data['rates'][currency], 4)
        return True, round(base_amount / Decimal(ratio), 4), ratio
    else:
        return False, None, None
