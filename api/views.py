from django.db.models import Q
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import *


class Test(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        content = {
            'test_data': 254
        }

        return Response(content)


class InitializeApp(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if create_superuser():
            content = {
                'username': 'avito',
                'password': 'avito'
            }
        else:
            content = {
                'error_test': 'Superuser already created.'
            }

        return Response(content)


class Registration(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer


class Wallets(APIView):
    permission_classes = [IsAuthenticated]

    # используем POST для сокрытия токена
    def post(self, request):
        user = self.request.user

        data = WalletSerializer(get_balance(user.id), many=True).data

        return Response(data)


class Balance(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        currency = self.request.query_params.get('currency')

        user = self.request.user
        queryset = Wallet.objects.filter(owner=user)

        total_balance = sum(wallet_data.funds for wallet_data in queryset)

        response_data = {
            'total_balance': total_balance
        }

        if currency:
            _status, exchange_total, exchange_ratio = request_exchange_rate(currency, total_balance)

            if _status:
                response_data['exchange_total'] = exchange_total
                response_data['exchange_ratio'] = exchange_ratio
                response_data['exchange_currency'] = currency
            else:
                response_data['exchange_error'] = 'Currency is not available.'

        return Response(response_data)


class SendFunds(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id

        # проверка корректности запроса и реквизитов перевода средств
        transaction_data = PrivateTransactionRequestSerializer(data=request.data, context={'user_id': user_id})

        response_data = dict()

        if transaction_data.is_valid():
            recipient_wallet_id = get_available_wallet_id(transaction_data.data['recipient_id']),

            if recipient_wallet_id:
                transfer_status, error_text = private_funds_transfer(
                    transaction_data.data['wallet_id'],
                    get_available_wallet_id(transaction_data.data['recipient_id']),
                    transaction_data.data['total_amount']
                )

                response_data['transaction_status'] = transfer_status

                if transfer_status:
                    serializer = PrivateTransactionSerializer()

                    response_data['private_transaction_id'] = serializer.create({
                        'sender_id': user_id,
                        'recipient_id': transaction_data.data['recipient_id'],
                        'total_amount': transaction_data.data['total_amount'],
                        'description': transaction_data.data['description'],
                    })

                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    response_data['error_text'] = error_text

                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            else:
                response_data['transaction_status'] = False
                response_data['error_text'] = 'No available wallets.'
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_data['transaction_status'] = False
            response_data = transaction_data.errors
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class AcquireFunds(APIView):
    # только административные аккаунты могут начислять средства извне платежной системы
    permission_classes = [IsAdminUser, IsAuthenticated]

    def post(self, request):
        # проверка корректности запроса и реквизитов перевода средств
        transaction_data = SystemTransactionRequestSerializer(data=request.data)

        response_data = dict()

        if transaction_data.is_valid():
            # если id кошелька указан явно
            if 'wallet_id' in transaction_data.data:
                transfer_status, error_text = system_funds_acquisition(transaction_data.data['recipient_id'],
                                                                       transaction_data.data['total_amount'],
                                                                       transaction_data.data['wallet_id'])
            else:
                transfer_status, error_text = system_funds_acquisition(transaction_data.data['recipient_id'],
                                                                       transaction_data.data['total_amount'])
            if transfer_status:
                serializer = SystemFundsAcquiringTransactionSerializer()

                response_data['system_transaction_id'] = serializer.create(transaction_data.validated_data)

                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data['error_text'] = error_text

                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        else:
            response_data['transaction_status'] = False
            response_data = transaction_data.errors
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class WithdrawFunds(APIView):
    # только административные аккаунты могут начислять средства извне платежной системы
    permission_classes = [IsAdminUser, IsAuthenticated]

    def post(self, request):
        # проверка корректности запроса и реквизитов перевода средств
        transaction_data = SystemTransactionRequestSerializer(data=request.data)

        response_data = dict()

        if transaction_data.is_valid():
            # если id кошелька указан явно
            if 'wallet_id' in transaction_data.data:
                transfer_status, error_text = system_funds_disposal(transaction_data.data['recipient_id'],
                                                                    transaction_data.data['total_amount'],
                                                                    transaction_data.data['wallet_id'])
            else:
                transfer_status, error_text = system_funds_disposal(transaction_data.data['recipient_id'],
                                                                    transaction_data.data['total_amount'])
            if transfer_status:
                serializer = SystemFundsWithdrawalTransactionSerializer()

                response_data['system_transaction_id'] = serializer.create(transaction_data.validated_data)

                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data['error_text'] = error_text

                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        else:
            response_data['transaction_status'] = False
            response_data = transaction_data.errors
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class ListTransactions(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_data = self.request.user
        response_data = dict()
        response_data['error_text'] = list()

        queryset = Transaction.objects.all()

        sort_by = self.request.query_params.get('sort_by')
        items = self.request.query_params.get('items')
        direction = self.request.query_params.get('direction')

        sorting_direction = ''
        sorting_field = 'id'
        sorting_quantity = 100

        if sort_by:
            if sort_by == 'date' or sort_by == 'amount':
                sorting_field = sort_by
            else:
                response_data['error_text'].append('Sorting parameter is incorrect.')
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if direction:
            if direction.lower() == 'asc':
                sorting_direction = ''
            elif direction.lower() == 'desc':
                sorting_direction = '-'
            else:
                response_data['error_text'].append('Sorting direction is incorrect.')
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if items:
            if 0 < int(items) < 1000:
                sorting_quantity = int(items)
            else:
                response_data['error_text'].append('Requested transactions amount is incorrect.')
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        # запрашиваем только те транзакции, где участвовал пользователь + параметры
        queryset = queryset.filter(Q(sender_id=user_data.id) | Q(recipient_id=user_data.id)).order_by(
            f'{sorting_direction}{sorting_field}')[:int(sorting_quantity)]

        response_data['user_transactions'] = ListTransactionsSerializer(queryset, many=True).data

        return Response(response_data)
