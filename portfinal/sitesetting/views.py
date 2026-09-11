from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import (
    Certification,
    Comment,
    Education,
    Experience,
    Post,
    Project,
    SiteSettings,
    Skill,
)
from .serializers import (
    CertificationSerializer,
    CommentCreateSerializer,
    EducationSerializer,
    ExperienceSerializer,
    PostDetailSerializer,
    PostListSerializer,
    ProjectSerializer,
    SiteSettingsSerializer,
    SkillSerializer,
)


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/posts/                → paginated list (?category=&tag= filters)
    GET /api/posts/<slug>/         → full detail incl. approved comments
    """
    lookup_field = "slug"

    def get_queryset(self):
        qs = Post.objects.published().with_related()  # no N+1, filtered in SQL

        if self.action == "retrieve":
            return qs.prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.filter(is_approved=True),
                )
            )

        category = self.request.query_params.get("category")
        tag = self.request.query_params.get("tag")
        if category:
            qs = qs.filter(category__slug=category)
        if tag:
            qs = qs.filter(tags__slug=tag)
        return qs

    def get_serializer_class(self):
        return PostDetailSerializer if self.action == "retrieve" else PostListSerializer


# One round trip per page instead of four — the frontend asks once, gets everything.
class HomeAPIView(APIView):
    def get(self, request):
        latest_edu = Education.objects.filter(is_visible=True).first()
        earliest_job = (
            Experience.objects.filter(is_visible=True).order_by("start_date").first()
        )

        experience = ""
        if earliest_job:
            years = timezone.now().year - earliest_job.start_date.year
            if years > 0:
                experience = f"{years}+ years"

        return Response({
            "profile": {
                "education": (
                    f"{latest_edu.degree}, {latest_edu.institution}"
                    if latest_edu else ""
                ),
                "experience": experience,
            },
            "featured_projects": ProjectSerializer(
                Project.objects.filter(is_visible=True, is_featured=True)
                .prefetch_related("skills"),
                many=True,
            ).data,
            "skills": SkillSerializer(Skill.objects.all(), many=True).data,
        })


class ResumeAPIView(APIView):
    def get(self, request):
        return Response({
            "experiences": ExperienceSerializer(
                Experience.objects.filter(is_visible=True), many=True
            ).data,
            "education": EducationSerializer(
                Education.objects.filter(is_visible=True), many=True
            ).data,
            "skills": SkillSerializer(
                Skill.objects.all(), many=True
            ).data,
            "certifications": CertificationSerializer(
                Certification.objects.all(), many=True
            ).data,
        })


class SiteSettingsAPIView(APIView):
    def get(self, request):
        return Response(SiteSettingsSerializer(SiteSettings.load()).data)


class CommentThrottle(AnonRateThrottle):
    scope = "comments"


class CommentCreateView(generics.CreateAPIView):
    """
    POST /api/posts/<slug>/comments/
    authentication_classes = [] → no CSRF friction cross-origin.
    Abuse is handled by: throttling + honeypot + manual approval flag.
    """
    serializer_class = CommentCreateSerializer
    authentication_classes = []
    throttle_classes = [CommentThrottle]

    def perform_create(self, serializer):
        post = get_object_or_404(
            Post, slug=self.kwargs["slug"], status=Post.Status.PUBLISHED
        )
        serializer.save(post=post)