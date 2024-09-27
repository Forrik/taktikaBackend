from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import CustomUser, Profile, Gym, Training, Subscription, TrainingFeedback, Trainer


from rest_framework import serializers
from .models import CustomUser, Profile, Gym, Training, Subscription, TrainingFeedback, Trainer


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    middle_name = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(
        max_length=15, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    city = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=[(
        'M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False, allow_blank=True)
    passport_data = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    experience_years = serializers.IntegerField(
        required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    sports_title = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=CustomUser.ROLES, default='user')

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'email', 'phone', 'birth_date', 'city',
                  'gender', 'passport_data', 'experience_years', 'bio', 'sports_title', 'photo', 'password', 'role')

    def validate_email(self, value):
        if self.instance and self.instance.email == value:
            return value
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Такая почта уже используется.")
        return value

    def validate_password(self, value):
        if value and len(value) < 8:
            raise serializers.ValidationError(
                "Пароль должен содержать не менее 8 символов.")
        return value

    def create(self, validated_data):
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

        if role == 'trainer':
            Trainer.objects.get_or_create(user=user)

        return user

    def update(self, instance, validated_data):
        email = validated_data.get('email', instance.email)
        if email != instance.email and CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "Такая почта уже используется."})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
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
                  'current_participants', 'trainer', 'gym', 'trainer_id', 'gym_id',
                  'is_recurring', 'recurrence_end_date']

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
