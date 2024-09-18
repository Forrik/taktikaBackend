from django.conf.urls.static import static
from django.conf import settings
from .views import (
    RegisterView, LoginView, ProfileView, GymListView, GymDetailView,  TrainingListView,
    SubscriptionListView, TrainingFeedbackListView, TrainerListView,
    TrainerDetailView, TrainingDetailView, TrainingEnrollView, TrainingUnenrollView
)
from django.urls import path
from django.contrib import admin
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Profile, Gym, Training, Subscription, TrainingFeedback, Trainer
from .serializers import UserSerializer, LoginSerializer, GymSerializer, TrainingSerializer, SubscriptionSerializer, TrainingFeedbackSerializer, TrainerSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User


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
                'email': user.email
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
        return Response({'token': token.key, 'user_id': user.id})


class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        return User.objects.get(id=user_id)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        profile = Profile.objects.get(user=instance)
        data = serializer.data
        data.update({
            'middle_name': profile.middle_name,
            'phone': profile.phone,
            'level': profile.level,
            'city': profile.city,
            'gender': profile.gender,
            'total_trainings': profile.total_trainings,
            'first_training_date': profile.first_training_date,
            'occupation': profile.occupation,
            'preferred_area': profile.preferred_area
        })
        return Response(data)


class GymListView(generics.ListCreateAPIView):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class GymDetailView(generics.RetrieveAPIView):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class TrainingListView(generics.ListCreateAPIView):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class TrainingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SubscriptionListView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class TrainingFeedbackListView(generics.ListCreateAPIView):
    serializer_class = TrainingFeedbackSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return TrainingFeedback.objects.filter(user=self.request.user)


class TrainerListView(generics.ListCreateAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class TrainerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


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
        training.current_participants += 1
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
        training.current_participants -= 1
        training.save()

        return Response({'success': 'You have been unenrolled from the training'}, status=status.HTTP_200_OK)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    level = models.IntegerField(default=1)
    total_trainings = models.IntegerField(default=0)
    first_training_date = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    preferred_area = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=[
                              ('M', 'Male'), ('F', 'Female')], blank=True)


class Gym(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    metro_station = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='gym_photos/', blank=True)
    level = models.IntegerField()

    def __str__(self):
        return self.name


class Trainer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='trainer_profile')
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Trainer"


class Training(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    trainer = models.ForeignKey(
        Trainer, on_delete=models.CASCADE, null=False, related_name='trainings')
    date = models.DateTimeField()
    level = models.IntegerField()
    max_participants = models.IntegerField()
    current_participants = models.IntegerField(default=0)
    intensity = models.IntegerField(null=True, blank=True)
    participants = models.ManyToManyField(
        User, related_name='trainings', blank=True)

    def __str__(self):
        return f"Training at {self.gym.name} on {self.date}"


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    trainings_left = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class TrainingFeedback(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    middle_name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(max_length=15, required=False)
    level = serializers.IntegerField(default=1)
    city = serializers.CharField(max_length=100, required=False)
    gender = serializers.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'middle_name', 'email',
                  'phone', 'level', 'city', 'gender', 'password')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Такая почта уже используется.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Пароль должен содержать не менее 8 символов.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        Profile.objects.create(
            user=user,
            phone=validated_data.get('phone', ''),
            level=validated_data.get('level', 1),
            city=validated_data.get('city', ''),
            gender=validated_data.get('gender', ''),
            middle_name=validated_data.get('middle_name', '')
        )
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        profile = Profile.objects.get(user=instance)
        representation['middle_name'] = profile.middle_name
        representation['phone'] = profile.phone
        representation['level'] = profile.level
        representation['city'] = profile.city
        representation['gender'] = profile.gender
        return representation


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid email or password')
        attrs['user'] = user
        return attrs


class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = '__all__'


class TrainerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Trainer
        fields = ['id', 'user', 'experience_years', 'bio']


class TrainingSerializer(serializers.ModelSerializer):
    trainer = TrainerSerializer(read_only=True)
    gym = GymSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Training
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'


class TrainingFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingFeedback
        fields = '__all__'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('profile/<int:user_id>/', ProfileView.as_view(), name='profile'),
    path('gyms/', GymListView.as_view(), name='gym-list'),
    path('gyms/<int:pk>/', GymDetailView.as_view(), name='gym-detail'),
    path('trainings/', TrainingListView.as_view(), name='training-list'),
    path('trainings/<int:pk>/', TrainingDetailView.as_view(), name='training-detail'),
    path('trainings/<int:pk>/enroll/',
         TrainingEnrollView.as_view(), name='training-enroll'),
    path('trainings/<int:pk>/unenroll/',
         TrainingUnenrollView.as_view(), name='training-unenroll'),
    path('subscriptions/', SubscriptionListView.as_view(),
         name='subscription-list'),
    path('feedback/', TrainingFeedbackListView.as_view(), name='feedback-list'),
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
