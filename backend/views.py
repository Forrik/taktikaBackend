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
logger = logging.getLogger(__name__)


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
        serializer = SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                subscription = serializer.save(user=request.user)
                gym = subscription.gym
                trainer = subscription.trainer
                amount = subscription.price
                recipient_amount = amount * \
                    Decimal('0.7')  # 70% на р/с тренера

                # Проверка наличия тренера и зала
                if not gym or not trainer:
                    return Response({'error': 'Gym or trainer not found'}, status=status.HTTP_400_BAD_REQUEST)

                # Создание сплитованного платежа
                payment = create_split_payment(
                    amount, trainer.user.account_id, recipient_amount)

                # Сохранение данных платежа в базе данных
                subscription.payment_id = payment.id
                subscription.save()

                return Response({'payment_url': payment.confirmation.confirmation_url}, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Error creating subscription: {e}")
                return Response({'error': 'Failed to create subscription'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class TrainingEnrollView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            training = Training.objects.get(pk=pk)
        except Training.DoesNotExist:
            return Response({'error': 'Training not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user in training.participants.all():
            return Response({'error': 'You are already enrolled in this training'}, status=status.HTTP_400_BAD_REQUEST)

        if training.current_participants >= training.max_participants:
            return Response({'error': 'This training is full'}, status=status.HTTP_400_BAD_REQUEST)

        training.participants.add(request.user)
        training.current_participants = training.participants.count()
        training.save()

        return Response({'success': 'You have been enrolled in the training'}, status=status.HTTP_200_OK)


class TrainingUnenrollView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            training = Training.objects.get(pk=pk)
        except Training.DoesNotExist:
            return Response({'error': 'Training not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in training.participants.all():
            return Response({'error': 'You are not enrolled in this training'}, status=status.HTTP_400_BAD_REQUEST)

        training.participants.remove(request.user)
        training.current_participants = training.participants.count()
        training.save()

        return Response({'success': 'You have been unenrolled from the training'}, status=status.HTTP_200_OK)
