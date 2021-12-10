from django.contrib.auth.models import User
from rest_framework import serializers

from api.models import *
from api.services import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "password", "last_name", "first_name")
        extra_kwargs = {'password': {'write_only': True}, 'first_name': {'required': True},
                        'last_name': {'required': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            last_name=validated_data['last_name'],
            first_name=validated_data['first_name'],
        )

        # здесь же создаем привязанный кошелек по умолчанию
        wallet = Wallet.objects.create(
            owner=user
        )

        return user


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ("funds", "name")

    funds = serializers.DecimalField(read_only=True, max_digits=8, decimal_places=2)
    name = serializers.StringRelatedField(read_only=True)


class PrivateTransactionRequestSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    recipient_id = serializers.IntegerField()
    description = serializers.CharField(max_length=200, default='...')

    wallet_id = serializers.IntegerField()

    def validate(self, attrs):
        user_id = self.context['user_id']

        wallet_queryset = Wallet.objects.filter(id=attrs['wallet_id'])

        # проверка наличия, владения и платежеспособности кошелька/владельца
        if wallet_queryset:
            wallet_data = wallet_queryset[0]
            if wallet_data.owner.id != user_id:
                raise serializers.ValidationError('Wallet is not linked to this account.')
            else:
                if wallet_data.funds < attrs['total_amount']:
                    raise serializers.ValidationError('Not enough funds in this wallet.')
        else:
            raise serializers.ValidationError('Wallet does not exist.')

        # существует ли принимающий аккаунт
        if not User.objects.filter(id=attrs['recipient_id']):
            raise serializers.ValidationError('Recipient does not exist.')
        else:
            if not get_available_wallet_id(attrs['recipient_id']):
                raise serializers.ValidationError('Available wallet does not exist.')

        return attrs


class PrivateTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("date", "id", "sender_id", "recipient_id", "type", "amount", "description")

    def create(self, validated_data):
        new_transaction = Transaction.objects.create(
            sender_id=validated_data['sender_id'],
            recipient_id=validated_data['recipient_id'],
            amount=validated_data['total_amount'],
            type='P2P'
        )

        if 'description' in validated_data.keys():
            new_transaction.description = validated_data['description']

        new_transaction.save()

        return str(new_transaction)


class SystemTransactionRequestSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    recipient_id = serializers.IntegerField()

    wallet_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        # существует ли принимающий аккаунт
        if not User.objects.filter(id=attrs['recipient_id']):
            raise serializers.ValidationError('Recipient does not exist.')

        if 'wallet_id' in attrs:
            wallet_queryset = Wallet.objects.filter(id=attrs['wallet_id'])

            # проверка наличия, владения и платежеспособности кошелька/владельца
            if wallet_queryset:
                wallet_data = wallet_queryset[0]
                if wallet_data.owner.id != attrs['recipient_id']:
                    raise serializers.ValidationError('Wallet is not linked to the account.')
            else:
                raise serializers.ValidationError('Wallet does not exist.')

        if attrs['total_amount'] <= 0:
            raise serializers.ValidationError('Funds amount could not be 0 or negative')

        return attrs


class SystemFundsAcquiringTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("date", "id", "recipient_id", "type", "amount", "description")

    def create(self, validated_data):
        new_transaction = Transaction.objects.create(
            # не самая хорошая практика, но указывает на системный аккаунт
            sender_id=User.objects.filter(is_superuser=True).first().id,
            recipient_id=validated_data['recipient_id'],
            amount=validated_data['total_amount'],
            # поплнение баланса
            type='ACQ',
            description='Пополнение баланса %таким-то методом%'
        )

        if 'description' in validated_data.keys():
            new_transaction.description = validated_data['description']

        new_transaction.save()

        return str(new_transaction)


class SystemFundsWithdrawalTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("date", "id", "recipient_id", "type", "amount", "description")

    def create(self, validated_data):
        new_transaction = Transaction.objects.create(
            sender_id=validated_data['recipient_id'],
            recipient_id=User.objects.filter(is_superuser=True).first().id,
            amount=validated_data['total_amount'],
            # снятие средств
            type='WTH',
            description='Снятие средств %таким-то методом%'
        )

        if 'description' in validated_data.keys():
            new_transaction.description = validated_data['description']

        new_transaction.save()

        return str(new_transaction)


class ListTransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
