from .models import Subscription
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Profile, Gym, Training, Subscription, TrainingFeedback, Trainer, CustomUser
from .serializers import UserSerializer, LoginSerializer, GymSerializer, TrainingSerializer, SubscriptionSerializer, TrainingFeedbackSerializer, TrainerSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .permissions import IsAdminUser, IsTrainerUser, IsRegularUser
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .payment import create_split_payment
from django.db import transaction
import logging
from decimal import Decimal
import requests
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from yookassa import Configuration, Payment
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
from django.core.files.base import ContentFile
import base64

logger = logging.getLogger(__name__)

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received data: {data}")
            if data['event'] == 'payment.succeeded':
                payment_object = data['object']
                payment_id = payment_object['id']
                try:
                    subscription = Subscription.objects.get(
                        payment_id=payment_id)
                    if not subscription.is_paid:
                        logger.info(
                            f"Marking subscription {payment_id} as paid")
                        subscription.is_paid = True
                        subscription.save()
                        logger.info(
                            f"Calling enroll_user_to_trainings for subscription {payment_id}")
                        subscription.enroll_user_to_trainings()
                        logger.info(
                            f"Subscription {payment_id} marked as paid and user enrolled to trainings")
                    else:
                        logger.info(
                            f"Subscription {payment_id} was already marked as paid")
                    return HttpResponse(status=200)
                except Subscription.DoesNotExist:
                    logger.error(
                        f"Subscription with payment_id {payment_id} not found")
                    return HttpResponse(status=404, content='Абонемент не найден')
            else:
                logger.warning(f"Unhandled event: {data['event']}")
                return HttpResponse(status=200)
        except json.JSONDecodeError:
            logger.error("Invalid data format")
            return HttpResponse(status=400, content='Неверный формат данных')
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            return HttpResponse(status=500, content=f'Ошибка сервера: {str(e)}')
    logger.warning("Invalid request method")
    return HttpResponse(status=405, content='Неверный метод запроса')


@method_decorator(csrf_protect, name='dispatch')
class CreatePaymentView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            recipient_account_id = data.get('recipient_account_id')
            recipient_amount = data.get('recipient_amount')

            if amount is None or recipient_amount is None:
                return Response({"error": "Amount and recipient_amount must be provided"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                amount = float(amount)
                recipient_amount = float(recipient_amount)
            except ValueError:
                return Response({"error": "Amount and recipient_amount must be valid numbers"}, status=status.HTTP_400_BAD_REQUEST)

            payment = Payment.create({
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "payment_method_data": {
                    "type": "bank_card"
                },
                "confirmation": {
                    "type": "redirect",
                    # Replace with your actual return URL
                    "return_url": "https://abcd1234.ngrok.io/return_url"
                },
                "capture": True,
                "description": "Payment for subscription",
                "receipt": {
                    "customer": {
                        "email": "customer@example.com"  # Replace with actual customer email
                    },
                    "items": [
                        {
                            "description": "Subscription",
                            "quantity": "1.00",
                            "amount": {
                                "value": str(amount),
                                "currency": "RUB"
                            },
                            "vat_code": 1
                        }
                    ]
                },
                "splits": [
                    {
                        "account_id": recipient_account_id,
                        "amount": {
                            "value": str(recipient_amount),
                            "currency": "RUB"
                        }
                    },
                    {
                        "account_id": Configuration.account_id,
                        "amount": {
                            "value": str(amount - recipient_amount),
                            "currency": "RUB"
                        }
                    }
                ]
            })
            return Response({"payment_url": payment.confirmation.confirmation_url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


def amocrm_callback(request):
    # Получаем код авторизации из параметров запроса
    auth_code = request.GET.get('code')

    if not auth_code:
        return JsonResponse({"error": "Authorization code not provided"}, status=400)

    # Параметры для получения токенов
    url = "https://ilya33533.amocrm.ru/oauth2/access_token"
    data = {
        "client_id": "11593038",
        "client_secret": "YOUR_CLIENT_SECRET",
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": "http://45.8.229.240:8000/oauth/callback/"
    }

    # Запрос токенов
    response = requests.post(url, json=data)

    # Проверка и обработка ответа
    if response.status_code == 200:
        tokens = response.json()
        # Сохраните токены для дальнейшего использования
        # Например, в сессии или базе данных
        return JsonResponse(tokens)
    else:
        return JsonResponse({"error": "Failed to get tokens", "details": response.json()}, status=response.status_code)


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'email': user.email,
                'role': user.role
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'role': user.role})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise Http404("User does not exist")


class GymListView(generics.ListCreateAPIView):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class GymDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class TrainingListView(generics.ListCreateAPIView):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        training = serializer.save()

        if training.is_recurring and training.recurrence_end_date:
            self.create_recurring_trainings(training)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def create_recurring_trainings(self, training):
        current_date = training.date
        end_date = training.recurrence_end_date

        while current_date.date() + timezone.timedelta(days=7) <= end_date:
            current_date += timezone.timedelta(days=7)
            Training.objects.create(
                gym=training.gym,
                trainer=training.trainer,
                date=current_date,
                level=training.level,
                max_participants=training.max_participants,
                intensity=training.intensity,
                is_recurring=True,
                recurrence_end_date=training.recurrence_end_date,
                parent_training=training
            )


class ManageRecurringTrainingsView(APIView):
    permission_classes = [permissions.IsAuthenticated(
    ), permissions.OR(IsAdminUser(), IsTrainerUser())]

    def post(self, request):
        today = timezone.now().date()
        trainings = Training.objects.filter(
            is_recurring=True,
            recurrence_end_date__gte=today,
            date__date=today
        )

        created_trainings = []
        for training in trainings:
            next_week = today + timezone.timedelta(days=7)
            if not Training.objects.filter(parent_training=training, date__date=next_week).exists():
                new_training = Training.objects.create(
                    gym=training.gym,
                    trainer=training.trainer,
                    date=training.date + timezone.timedelta(days=7),
                    level=training.level,
                    max_participants=training.max_participants,
                    intensity=training.intensity,
                    is_recurring=True,
                    recurrence_end_date=training.recurrence_end_date,
                    parent_training=training
                )
                created_trainings.append(str(new_training))

        return Response({
            "message": f"Created {len(created_trainings)} new recurring trainings.",
            "created_trainings": created_trainings
        }, status=status.HTTP_200_OK)


class TrainingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), permissions.OR(IsAdminUser(), IsTrainerUser())]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SubscriptionListView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        gym_id = self.request.data.get('gym')
        trainer_id = self.request.data.get('trainer')
        gym = Gym.objects.get(id=gym_id)
        trainer = Trainer.objects.get(id=trainer_id)
        serializer.save(user=self.request.user, gym=gym, trainer=trainer)


class SubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        obj = get_object_or_404(
            Subscription, id=self.kwargs['pk'], user=self.request.user)
        self.check_object_permissions(self.request, obj)
        return obj


class CreateSubscriptionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request):
        # Если пользователь не передан в запросе, используем пользователя из токена аутентификации
        if 'user' not in request.data:
            request.data['user'] = request.user.id

        serializer = SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                subscription = serializer.save()
                gym = subscription.gym
                trainer = subscription.trainer
                amount = subscription.price
                recipient_amount = amount * \
                    Decimal('0.7')  # 70% на р/с тренера

                # Проверка наличия тренера и зала
                if not gym:
                    logger.error("Gym not found")
                    return Response({'error': 'Gym not found'}, status=status.HTTP_400_BAD_REQUEST)
                if not trainer:
                    logger.error("Trainer not found")
                    return Response({'error': 'Trainer not found'}, status=status.HTTP_400_BAD_REQUEST)

                # Создание сплитованного платежа
                try:
                    payment = create_split_payment(
                        amount, trainer.user.account_id, recipient_amount)
                except Exception as e:
                    logger.error(f"Error creating payment: {e}")
                    return Response({'error': 'Failed to create payment'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Сохранение данных платежа в базе данных
                subscription.payment_id = payment.id
                subscription.save()

                # Автоматическая запись на тренировки
                subscription.enroll_user_to_trainings()

                return Response({'payment_url': payment.confirmation.confirmation_url}, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Error creating subscription: {e}")
                return Response({'error': 'Failed to create subscription'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingFeedbackListView(generics.ListCreateAPIView):
    serializer_class = TrainingFeedbackSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return TrainingFeedback.objects.filter(user=self.request.user)


class TrainerListView(generics.ListAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Trainer.objects.filter(user__role='trainer')


class TrainerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    parser_classes = (JSONParser,)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        user_data = request.data.get('user', {})

        # Обработка фото
        if 'photo' in user_data:
            if user_data['photo'] == 'delete_photo':
                user_data['photo'] = None
            elif isinstance(user_data['photo'], str) and user_data['photo'].startswith('data:image'):
                format, imgstr = user_data['photo'].split(';base64,')
                ext = format.split('/')[-1]
                user_data['photo'] = ContentFile(
                    base64.b64decode(imgstr), name=f'photo.{ext}')

        # Объединяем данные пользователя с остальными данными
        data = request.data.copy()
        data['user'] = user_data

        serializer = self.get_serializer(instance, data=data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingEnrollView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            training = Training.objects.get(pk=pk)
        except Training.DoesNotExist:
            return Response({'error': 'Тренировка не найдена'}, status=status.HTTP_404_NOT_FOUND)

        if request.user in training.participants.all():
            return Response({'error': 'Вы уже записались на эту тренировку'}, status=status.HTTP_400_BAD_REQUEST)

        if training.current_participants >= training.max_participants:
            training.add_to_reserve(request.user)
            return Response({'success': 'Вы добавлены в резерв'}, status=status.HTTP_200_OK)

        subscription = Subscription.objects.filter(
            user=request.user, is_paid=True).first()
        if not subscription:
            return Response({'error': 'У вас нет абонемента'}, status=status.HTTP_403_FORBIDDEN)

        if not subscription.is_valid_for_training(training):
            return Response({'error': 'Ваш абонемент не действителен для этой тренировки'}, status=status.HTTP_403_FORBIDDEN)

        training.participants.add(request.user)
        training.current_participants = training.participants.count()
        training.save()

        subscription.use_training()

        return Response({'success': 'Вы записались на тренировку'}, status=status.HTTP_200_OK)


class TrainingConfirmView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            training = Training.objects.get(pk=pk)
        except Training.DoesNotExist:
            return Response({'error': 'Тренировка не найдена'}, status=status.HTTP_404_NOT_FOUND)

        subscription = Subscription.objects.filter(
            user=request.user, is_paid=True).first()
        if not subscription:
            return Response({'error': 'У вас нет абонемента'}, status=status.HTTP_403_FORBIDDEN)

        if subscription.confirmed:
            return Response({'error': 'Вы уже подтвердили запись'}, status=status.HTTP_400_BAD_REQUEST)

        subscription.confirm_enrollment()

        return Response({'success': 'Вы подтвердили запись на тренировку'}, status=status.HTTP_200_OK)


class TrainingUnenrollView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            training = Training.objects.get(pk=pk)
        except Training.DoesNotExist:
            return Response({'error': 'Тренировка не найдена'}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in training.participants.all():
            return Response({'error': 'Вы не записаны на эту тренировку'}, status=status.HTTP_400_BAD_REQUEST)

        subscription = Subscription.objects.filter(
            user=request.user, is_paid=True).first()
        if not subscription:
            return Response({'error': 'У вас нет абонемента'}, status=status.HTTP_403_FORBIDDEN)

        if subscription.confirmed:
            return Response({'error': 'Вы уже подтвердили запись и не можете отменить её'}, status=status.HTTP_400_BAD_REQUEST)

        training.participants.remove(request.user)
        training.current_participants = training.participants.count()
        training.save()

        return Response({'success': 'Вы отменили запись на тренировку'}, status=status.HTTP_200_OK)


class TrainingConfirmView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            training = Training.objects.get(pk=pk)
        except Training.DoesNotExist:
            return Response({'error': 'Тренировка не найдена'}, status=status.HTTP_404_NOT_FOUND)

        subscription = Subscription.objects.filter(
            user=request.user, is_paid=True).first()
        if not subscription:
            return Response({'error': 'У вас нет абонемента'}, status=status.HTTP_403_FORBIDDEN)

        if subscription.confirmed:
            return Response({'error': 'Вы уже подтвердили запись'}, status=status.HTTP_400_BAD_REQUEST)

        subscription.confirm_enrollment()

        return Response({'success': 'Вы подтвердили запись на тренировку'}, status=status.HTTP_200_OK)


class TrainerPhotoUpdateView(APIView):
    def put(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)

        # Удаляем старое фото, если оно существует
        if trainer.user.photo:
            trainer.user.photo.delete(save=False)

        # Обновляем фото
        trainer.user.photo = request.FILES['photo']
        trainer.user.save()

        return Response({"message": "Photo updated successfully"}, status=status.HTTP_200_OK)


class TrainerPhotoDeleteView(APIView):
    def delete(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)

        # Удаляем фото, если оно существует
        if trainer.user.photo:
            trainer.user.photo.delete(save=False)
            trainer.user.photo = None
            trainer.user.save()

        return Response({"message": "Photo deleted successfully"}, status=status.HTTP_200_OK)


class TrainerPhotoDeleteView(APIView):
    def delete(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)

        # Удаляем фото, если оно существует
        if trainer.user.photo:
            trainer.user.photo.delete(save=False)
            trainer.user.photo = None
            trainer.user.save()

        return Response({"message": "Photo deleted successfully"}, status=status.HTTP_200_OK)
