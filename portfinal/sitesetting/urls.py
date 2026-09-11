from django.urls import path

from . import views

urlpatterns = [
    path("api/home/", views.HomeAPIView.as_view(), name="api_home"),
    path("api/resume/", views.ResumeAPIView.as_view(), name="api_resume"),
    path("api/settings/", views.SiteSettingsAPIView.as_view(), name="api_settings"),
    path("api/posts/", views.PostViewSet.as_view({"get": "list"}), name="api_posts"),
    path("api/posts/<slug:slug>/", views.PostViewSet.as_view({"get": "retrieve"}), name="api_post_detail"),
    path("api/posts/<slug:slug>/comments/", views.CommentCreateView.as_view(), name="api_add_comment"),
]