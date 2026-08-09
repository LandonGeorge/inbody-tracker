from django.urls import path

from . import views

urlpatterns = [
    path("upload/", views.upload_scan, name="upload_scan"),
    path("", views.scan_list, name="scan_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("result/<int:pk>/edit/", views.edit_scan_result, name="edit_scan_result"),
    path("scan/<int:pk>/delete/", views.delete_scan, name="delete_scan"),
]
