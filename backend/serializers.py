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
        'male', 'male'), ('female', 'female')], required=False, allow_blank=True)
    passport_data = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    experience_years = serializers.IntegerField(
        required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    sports_title = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=CustomUser.ROLES, default='user')
    level = serializers.IntegerField(required=False, default=1)
    sports_category = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    photo = serializers.ImageField(
        required=False, allow_null=True, allow_empty_file=True)
    delete_photo = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'email', 'phone', 'birth_date',
                  'gender', 'passport_data', 'experience_years', 'bio', 'sports_title', 'photo', 'password', 'role', 'level', 'sports_category', 'delete_photo')

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
        validated_data.pop('delete_photo', None)

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
        delete_photo = validated_data.pop('delete_photo', False)
        photo = validated_data.pop('photo', None)

        if delete_photo:
            instance.photo.delete(save=False)
            instance.photo = None
        elif photo is not None:
            instance.photo = photo

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'middle_name', 'email', 'phone', 'birth_date',
                  'gender', 'passport_data', 'experience_years', 'bio', 'sports_title',
                  'photo', 'level', 'sports_category']
        extra_kwargs = {field: {'required': False} for field in fields}

    def update(self, instance, validated_data):
        # Обработка удаления фото
        if 'photo' in validated_data and validated_data['photo'] is None:
            instance.photo.delete(save=False)

        # Проверка уникальности email
        email = validated_data.get('email')
        if email and email != instance.email:
            if CustomUser.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {'email': 'This email is already in use.'})

        # Обновляем только предоставленные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class TrainerSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = Trainer
        fields = ['id', 'user', 'experience_years', 'bio']
        extra_kwargs = {'experience_years': {
            'required': False}, 'bio': {'required': False}}

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Обновляем данные пользователя
        user_serializer = CustomUserSerializer(
            user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

        # Обновляем данные тренера
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


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
        extra_kwargs = {
            'photo': {'required': False}
        }

    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            if validated_data['photo'] == '':
                instance.photo.delete(save=False)
                instance.photo = None
            else:
                instance.photo = validated_data['photo']
        return super().update(instance, validated_data)


class TrainerSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = Trainer
        fields = ['id', 'user', 'experience_years', 'bio']
        extra_kwargs = {'experience_years': {
            'required': False}, 'bio': {'required': False}}

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Обновляем данные пользователя
        user_serializer = CustomUserSerializer(
            user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

        # Обновляем данные тренера
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


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
                  'price', 'trainer', 'payment_id', 'days_of_week', 'client_type', 'month', 'is_paid']

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
