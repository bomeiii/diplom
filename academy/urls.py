from django.urls import path

from . import views

app_name = "academy"

urlpatterns = [
    path("", views.home, name="home"),
    path("analytics/", views.analytics_overview, name="analytics_overview"),
    path("psychologist/<int:psychologist_id>/", views.psychologist_dashboard, name="psychologist_dashboard"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path("lesson/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("test/<int:content_id>/submit/", views.submit_test, name="submit_test"),
]
