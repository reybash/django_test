from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import include, path

from courses.views import (AvailableCoursesAPIView, PaymentAPIView,
                           CourseListView)

app_name = 'api'

urlpatterns = [path('api/v1/', include('api.v1.urls')),
               path('admin/', admin.site.urls),
               path('available-courses/',
                    AvailableCoursesAPIView.as_view(),
                    name='available-courses'),
               path('pay/', PaymentAPIView.as_view(),
                    name='pay-course'),
               path('courses-details/', CourseListView.as_view(),
                    name='course-detail-list'),
               ] + debug_toolbar_urls()
