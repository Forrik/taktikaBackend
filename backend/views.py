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
