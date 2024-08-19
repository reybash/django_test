from datetime import timezone

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import CustomUser
from .models import Course
from .serializers import (CourseSerializer, PaymentSerializer,
                          CourseDetailSerializer)


class AvailableCoursesAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        # Получаем все курсы, к которым пользователь не имеет доступ и которые доступны по дате
        courses = Course.objects.filter(
            start_date__lte=now  # Фильтрация по дате
        ).exclude(
            user_accesses__user=user
            # Исключаем курсы, к которым у пользователя есть доступ
        ).prefetch_related(
            Prefetch('lessons')  # Загружаем уроки
        )

        return courses


class PaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            course_id = serializer.validated_data['course_id']
            user_id = serializer.validated_data['user_id']

            user = get_object_or_404(CustomUser, id=user_id)
            course = get_object_or_404(Course, id=course_id)

            # Проверка доступа пользователя к курсу
            if user.course_accesses.filter(course=course).exists():
                return Response(
                    {"detail": "You already have access to this course."},
                    status=status.HTTP_400_BAD_REQUEST)

            # Проверка доступности курса
            if not course.is_available:
                return Response({"detail": "Course is not available."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Проверка стоимости курса
            if course.price <= 0:
                return Response(
                    {"detail": "Course price must be greater than zero."},
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():
                    # Проверка баланса пользователя
                    balance = user.balance
                    if balance.amount < course.price:
                        return Response({"detail": "Insufficient balance."},
                                        status=status.HTTP_400_BAD_REQUEST)

                    # Списание средств с баланса пользователя
                    balance.amount -= course.price
                    balance.save()

                    # Предоставление доступа к курсу
                    user.course_accesses.create(course=course)

                    return Response(
                        {"detail": "Payment successful. Access granted."},
                        status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseListView(generics.ListAPIView):
    serializer_class = CourseDetailSerializer

    def get_queryset(self):
        return Course.objects.prefetch_related(
            'groups__students',
            'user_accesses'
        ).all()
