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
        max_length=30, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
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
    level = serializers.IntegerField(
        required=False, default=1)  # Добавленное поле
    sports_category = serializers.CharField(
        max_length=100, required=False, allow_blank=True)  # Добавленное поле

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'email', 'phone', 'birth_date',
                  'gender', 'passport_data', 'experience_years', 'bio', 'sports_title', 'photo', 'password', 'role', 'level', 'sports_category')

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
        fields = ['id', 'name', 'metro_station',
                  'district', 'description', 'photo']


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
        queryset=Trainer.objects.all(), source='trainer', write_only=True)
    gym_id = serializers.PrimaryKeyRelatedField(
        queryset=Gym.objects.all(), source='gym', write_only=True)
    unenroll_deadline = serializers.DateTimeField(required=False)
    gender = serializers.ChoiceField(
        choices=Training.GENDER_CHOICES, default='any')
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Training
        fields = ['id', 'date', 'level', 'max_participants', 'current_participants', 'trainer', 'gym', 'trainer_id',
                  'gym_id', 'is_recurring', 'recurrence_end_date', 'unenroll_deadline', 'gender', 'participants']

    def create(self, validated_data):
        validated_data.pop('id', None)
        return Training.objects.create(**validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    days_of_week = serializers.CharField(required=False)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'gym', 'type', 'start_date', 'end_date', 'trainings_left',
                  'price', 'trainer', 'payment_id', 'days_of_week', 'client_type', 'month']

    def validate_days_of_week(self, value):
        valid_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        days = value.split(',')
        for day in days:
            if day not in valid_days:
                raise serializers.ValidationError(
                    f"{day} is not a valid choice.")
        return value


class TrainingFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingFeedback
        fields = '__all__'
