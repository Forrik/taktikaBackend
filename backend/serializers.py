from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import CustomUser, Profile, Gym, Training, Subscription, TrainingFeedback, Trainer


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    middle_name = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(
        max_length=15, required=False, allow_blank=True)
    level = serializers.IntegerField(default=1)
    city = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False, allow_blank=True
    )
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=CustomUser.ROLES, default='user')

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'email',
                  'phone', 'level', 'city', 'gender', 'password', 'role')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Такая почта уже используется.")
        return value

    def validate_password(self, value):
        if value and len(value) < 8:
            raise serializers.ValidationError(
                "Пароль должен содержать не менее 8 символов.")
        return value

    def create(self, validated_data):
        profile_fields = ['phone', 'level', 'city', 'gender']
        profile_data = {field: validated_data.pop(
            field, '') for field in profile_fields}

        email = validated_data.pop('email')
        password = validated_data.pop('password', None)
        role = validated_data.pop('role', 'user')

        user = CustomUser.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=role,
            **validated_data
        )

        Profile.objects.update_or_create(user=user, defaults=profile_data)

        if role == 'trainer':
            Trainer.objects.get_or_create(user=user)

        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        profile = instance.profile
        profile_fields = ['phone', 'level', 'city', 'gender']
        for field in profile_fields:
            representation[field] = getattr(profile, field, '')

        # Handle middle_name separately
        representation['middle_name'] = getattr(instance, 'middle_name', '')

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
        if not isinstance(user, CustomUser):
            raise serializers.ValidationError('User model is not CustomUser')
        attrs['user'] = user
        return attrs


class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = '__all__'


class TrainerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = ['id', 'user', 'full_name', 'experience_years', 'bio']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class TrainingSerializer(serializers.ModelSerializer):
    trainer = TrainerSerializer(read_only=True)
    gym = GymSerializer(read_only=True)
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=Trainer.objects.all(),
        source='trainer',
        write_only=True
    )
    gym_id = serializers.PrimaryKeyRelatedField(
        queryset=Gym.objects.all(),
        source='gym',
        write_only=True
    )

    class Meta:
        model = Training
        fields = ['id', 'date', 'level', 'max_participants',
                  'current_participants', 'trainer', 'gym',
                  'trainer_id', 'gym_id']

    def create(self, validated_data):
        validated_data.pop('id', None)  # Удаляем id, если он есть
        return Training.objects.create(**validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'


class TrainingFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingFeedback
        fields = '__all__'
