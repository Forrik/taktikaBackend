from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Gym, Training, Subscription, TrainingFeedback, Trainer


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('email', 'first_name', 'middle_name', 'last_name', 'role', 'is_staff', 'is_active', 'phone',
                    'birth_date', 'city', 'gender', 'passport_data', 'experience_years', 'bio', 'sports_title', 'photo')
    list_filter = ('is_staff', 'is_active', 'role')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'middle_name', 'last_name', 'role', 'phone', 'birth_date',
         'city', 'gender', 'passport_data', 'experience_years', 'bio', 'sports_title', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'middle_name', 'last_name', 'role', 'phone', 'birth_date', 'city', 'gender', 'passport_data', 'experience_years', 'bio', 'sports_title', 'photo', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('email', 'first_name', 'middle_name', 'last_name')
    ordering = ('email',)

    actions = ['make_trainer', 'make_user', 'make_admin']

    def make_trainer(self, request, queryset):
        updated = queryset.update(role='trainer')
        self.message_user(
            request, f'{updated} users were successfully updated to trainer role.')
    make_trainer.short_description = "Change selected users' role to trainer"

    def make_user(self, request, queryset):
        updated = queryset.update(role='user')
        self.message_user(
            request, f'{updated} users were successfully updated to user role.')
    make_user.short_description = "Change selected users' role to user"

    def make_admin(self, request, queryset):
        updated = queryset.update(role='admin')
        self.message_user(
            request, f'{updated} users were successfully updated to admin role.')
    make_admin.short_description = "Change selected users' role to admin"


class GymAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'metro_station', 'district', 'level')
    list_filter = ('district', 'level')
    search_fields = ('name', 'address', 'metro_station')


class TrainingAdmin(admin.ModelAdmin):
    list_display = ('gym', 'trainer', 'date', 'level',
                    'max_participants', 'current_participants')
    list_filter = ('gym', 'trainer', 'level', 'date')
    search_fields = ('gym__name', 'trainer__user__email')
    date_hierarchy = 'date'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'start_date',
                    'end_date', 'trainings_left', 'price')
    list_filter = ('type', 'start_date', 'end_date')
    search_fields = ('user__email',)


class TrainingFeedbackAdmin(admin.ModelAdmin):
    list_display = ('training', 'user', 'rating', 'date')
    list_filter = ('rating', 'date')
    search_fields = ('user__email', 'training__gym__name')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Trainer)
admin.site.register(Gym, GymAdmin)
admin.site.register(Training, TrainingAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(TrainingFeedback, TrainingFeedbackAdmin)
