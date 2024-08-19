from rest_framework import serializers

from users.models import CustomUser
from .models import Course
from .consts import MAX_GROUP_USERS


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'author', 'start_date', 'price']


class CourseDetailSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    average_fill_percentage = serializers.SerializerMethodField()
    acquisition_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'author', 'start_date', 'price',
                  'student_count', 'average_fill_percentage',
                  'acquisition_percentage']

    def get_student_count(self, obj):
        return obj.user_accesses.count()

    def get_average_fill_percentage(self, obj):
        groups = obj.groups.all()
        if groups.exists():
            total_students = sum(group.students.count() for group in groups)
            average_students_per_group = total_students / groups.count()
            return (average_students_per_group / MAX_GROUP_USERS) * 100
        return 0

    def get_acquisition_percentage(self, obj):
        total_users = CustomUser.objects.count()
        if total_users > 0:
            return (obj.user_accesses.count() / total_users) * 100
        return 0


class PaymentSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
