from rest_framework import serializers

from .models import (
    Category, Certification, Comment, Education, Experience,
    Post, Project, SiteSettings, Skill, Tag,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "slug"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "slug"]


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["name", "category", "level"]


class ProjectSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "title", "slug", "description", "featured_image",
            "live_url", "repo_url", "skills",
        ]


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = [
            "company", "role", "company_url", "location",
            "description", "start_date", "end_date",
        ]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "institution", "degree", "field_of_study",
            "start_date", "end_date", "grade", "description",
        ]


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "name", "issuer", "issue_date", "expiry_date",
            "credential_id", "credential_url",
        ]


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            "title", "tagline", "description", "favicon", "logo",
            "email", "github_url", "linkedin_url", "twitter_url", "resume",
        ]


# --- Blog: two payloads, because lists and details have different needs ---

class PostListSerializer(serializers.ModelSerializer):
    """Lean payload for listing pages — no full content."""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.StringRelatedField()

    class Meta:
        model = Post
        fields = [
            "title", "slug", "excerpt", "featured_image",
            "category", "tags", "author", "published_at",
        ]


class CommentPublicSerializer(serializers.ModelSerializer):
    """What visitors see — never exposes email or approval status."""
    class Meta:
        model = Comment
        fields = ["name", "body", "created_at"]


class PostDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.StringRelatedField()
    comments = CommentPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "title", "slug", "content", "featured_image",
            "category", "tags", "author", "published_at",
            "updated_at", "comments",
        ]


class CommentCreateSerializer(serializers.ModelSerializer):
    """Honeypot still works over an API — bots POST 'website', humans never do."""
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Comment
        fields = ["name", "email", "body", "website"]

    def validate_website(self, value):
        if value:
            raise serializers.ValidationError("Spam detected.")
        return value