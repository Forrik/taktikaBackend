from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import Profile, Gym, Training, Subscription, TrainingFeedback, Trainer


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
