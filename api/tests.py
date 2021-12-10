from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

# Create your tests here.
from api import Wallet, TransactionType, Transaction


class RegistrationTestCase(APITestCase):
    def test_registration(self):
        input_data = {
            'username': 'test_user',
            'password': 1111,
            'last_name': 'test_last_name',
            'first_name': 'test_first_name',
        }

        response = self.client.post("/api/registration", input_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # тестирование необходимости ввода полей
    def test_invalid_fields(self):
        input_data = {
            'username': 'test_user',
            'password': 1111,
        }

        response = self.client.post("/api/registration", input_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AccountManagementTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='test_password')
        self.token = Token.objects.create(user=self.user)
        self.api_auth()

        self.wallet = Wallet.objects.create(owner=self.user)

    def api_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + str(self.token))

    def test_wallets_data(self):
        self.wallet = Wallet.objects.create(owner=self.user)

        response = self.client.post("/api/wallets")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_balance_data(self):
        response = self.client.post("/api/balance")

        if self.assertEqual(response.status_code, status.HTTP_200_OK):
            self.assertEqual(response.data['total_balance'], 0)

    def test_balance_exchange_data(self):
        currency = 'USD'

        response = self.client.post(f"/api/balance?currency={currency}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exchange_currency'], currency)


class FundsPrivateTransferTestCase(APITestCase):
    def setUp(self):
        self.sender_user = User.objects.create_user(username='test_sender_user', password='test_password')
        self.token = Token.objects.create(user=self.sender_user)
        self.api_auth()

        self.wallet = Wallet.objects.create(owner=self.sender_user)

        # аккаунт получателя (без авторизации)
        self.recipient_user = User.objects.create_user(username='test_recipient_user', password='test_password')

        self.recipient_wallet = Wallet.objects.create(owner=self.recipient_user)

        # добавление типов транзакций (для п2п переводов используется идентификатор 3)
        TransactionType.objects.create(type_name='p2p', id=3)

    def api_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + str(self.token))

    def test_private_transfer_failure_no_funds(self):
        input_data = {
            'total_amount': 100,
            'recipient_id': self.recipient_user.id,
            'wallet_id': self.wallet.id
        }

        response = self.client.post("/api/send", input_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_private_transfer_with_funds(self):
        self.wallet.funds += 100.0
        self.wallet.save()

        input_data = {
            'total_amount': 100,
            'recipient_id': self.recipient_user.id,
            'wallet_id': self.wallet.id
        }

        response = self.client.post("/api/send", input_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['transaction_status'], True)

        # проверка, что транзакция была добавлена
        self.assertEqual(Transaction.objects.all().count(), 1)

        # проверка, что у отправителя были сняты средства
        self.assertEqual(Wallet.objects.get(id=self.wallet.id).funds, 0)

        # проверка, что получатель получил средства
        self.assertEqual(Wallet.objects.get(id=self.recipient_wallet.id).funds, 100)


class FundsSystemTransferTestCase(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='test_admin_user', password='test_password')
        self.token = Token.objects.create(user=self.admin_user)
        self.api_auth()

        # аккаунт получателя (без авторизации)
        self.recipient_user = User.objects.create_user(username='test_recipient_user', password='test_password')

        self.recipient_wallet = Wallet.objects.create(owner=self.recipient_user, funds=100.0)

        # добавление типов транзакций
        TransactionType.objects.create(type_name='withdrawal', id=2)
        TransactionType.objects.create(type_name='acquisition', id=1)

    def api_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + str(self.token))

    def test_system_funds_acquisition(self):
        input_data = {
            'total_amount': 1000.0,
            'recipient_id': self.recipient_user.id,
            'wallet_id': self.recipient_wallet.id
        }

        response = self.client.post("/api/acquire", input_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Transaction.objects.all().count(), 1)

        self.assertEqual(Wallet.objects.get(id=self.recipient_wallet.id).funds, 1100)

    def test_system_funds_withdrawal(self):
        input_data = {
            'total_amount': 100.0,
            'recipient_id': self.recipient_user.id,
            'wallet_id': self.recipient_wallet.id
        }

        response = self.client.post("/api/withdraw", input_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Transaction.objects.all().count(), 1)

        self.assertEqual(Wallet.objects.get(id=self.recipient_wallet.id).funds, 0)

    def test_system_funds_withdrawal_by_recipient_id(self):
        input_data = {
            'total_amount': 100.0,
            'recipient_id': self.recipient_user.id
        }

        response = self.client.post("/api/withdraw", input_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Wallet.objects.get(id=self.recipient_wallet.id).funds, 0)

    def test_system_funds_acquisition_by_recipient_id(self):
        input_data = {
            'total_amount': 100.0,
            'recipient_id': self.recipient_user.id
        }

        response = self.client.post("/api/acquire", input_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Wallet.objects.get(id=self.recipient_wallet.id).funds, 200)

    def test_system_funds_withdrawal_without_recipient_id(self):
        input_data = {
            'total_amount': 100.0,
            'wallet_id': self.recipient_wallet.id
        }

        response = self.client.post("/api/withdraw", input_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Wallet.objects.get(id=self.recipient_wallet.id).funds, 100)


class ListTransactionsTestCase(APITestCase):
    def setUp(self):
        self.sender_user = User.objects.create_user(username='test_sender_user', password='test_password')
        self.token = Token.objects.create(user=self.sender_user)
        self.api_auth()

        self.wallet = Wallet.objects.create(owner=self.sender_user)

        # аккаунт получателя (без авторизации)
        self.recipient_user = User.objects.create_user(username='test_recipient_user', password='test_password')

        self.recipient_wallet = Wallet.objects.create(owner=self.recipient_user)

        # добавление типов транзакций (для п2п переводов используется идентификатор 3)
        TransactionType.objects.create(type_name='p2p', id=3)

        # добавление транзакций для сортировки
        Transaction.objects.create(amount=100.0, sender=self.sender_user, recipient=self.recipient_user, type_id=3)
        Transaction.objects.create(amount=10.0, sender=self.sender_user, recipient=self.recipient_user, type_id=3)
        Transaction.objects.create(amount=1000.0, sender=self.sender_user, recipient=self.recipient_user, type_id=3)
        Transaction.objects.create(amount=10000.0, sender=self.sender_user, recipient=self.recipient_user, type_id=3)

    def api_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + str(self.token))

    def test_transactions_list_request(self):
        response = self.client.post("/api/transactions")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_transactions_list_sort_by(self):
        response = self.client.post("/api/transactions?sort_by=date")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['user_transactions'][0]['amount']), 100.0)

        response = self.client.post("/api/transactions?sort_by=amount")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['user_transactions'][0]['amount']), 10.0)

    def test_transactions_list_sort_direction(self):
        response = self.client.post("/api/transactions?sort_by=date&direction=desc")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['user_transactions'][0]['amount']), 10000.0)

        response = self.client.post("/api/transactions?sort_by=date&direction=asc")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['user_transactions'][0]['amount']), 100.0)

        response = self.client.post("/api/transactions?sort_by=amount&direction=desc")

        self.assertEqual(float(response.data['user_transactions'][0]['amount']), 10000.0)

        response = self.client.post("/api/transactions?sort_by=amount&direction=asc")

        self.assertEqual(float(response.data['user_transactions'][0]['amount']), 10.0)

    def test_transactions_list_pagination(self):
        response = self.client.post("/api/transactions?items=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['user_transactions']), 2)

        response = self.client.post("/api/transactions?sort_by=amount&direction=desc&items=3")

        self.assertEqual(len(response.data['user_transactions']), 3)
        self.assertEqual(float(response.data['user_transactions'][0]['amount']), 10000.0)
        self.assertEqual(float(response.data['user_transactions'][1]['amount']), 1000.0)
        self.assertEqual(float(response.data['user_transactions'][2]['amount']), 100.0)
