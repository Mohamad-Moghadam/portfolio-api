from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def generate_unique_slug(model, source: str, instance) -> str:
    """Slugify `source`, appending -2, -3... on collisions to avoid IntegrityError."""
    base = slugify(source)
    slug = base
    counter = 1
    while model._default_manager.filter(slug=slug).exclude(pk=instance.pk).exists():
        counter += 1
        slug = f"{base}-{counter}"
    return slug


class SiteSettings(models.Model):
    """Global site configuration. Singleton — access anywhere with SiteSettings.load()."""

    title = models.CharField(max_length=50)
    tagline = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    role = models.CharField(max_length=100, blank=True)      # e.g. "Full-Stack Engineer"
    location = models.CharField(max_length=100, blank=True)  # e.g. "Cairo, Egypt"
    favicon = models.ImageField(upload_to="favicons/", null=True, blank=True)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    email = models.EmailField(blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Category, self.name, self)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Tag, self.name, self)
        super().save(*args, **kwargs)


class PostQuerySet(models.QuerySet):
    """Reusable, chainable query logic — keeps views thin and prevents N+1 queries."""

    def published(self):
        return self.filter(status=self.model.Status.PUBLISHED)

    def with_related(self):
        return self.select_related("author", "category").prefetch_related("tags")


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_posts",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    featured_image = models.ImageField(upload_to="blog/images/", null=True, blank=True)
    excerpt = models.TextField(
        blank=True,
        help_text="Short summary shown on blog listing pages.",
    )
    content = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Post, self.title, self)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    body = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "is_approved"]),
        ]

    def __str__(self):
        return f"Comment by {self.name} on {self.post}"


# ---------------------------------------------------------------------------
# Portfolio (resume) models — fully dynamic via admin
# ---------------------------------------------------------------------------

class Experience(models.Model):
    company = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    company_url = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField(
        help_text="One achievement/responsibility per line — rendered as bullet points."
    )
    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave empty if this is your current position.",
    )
    is_visible = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(
        default=0, help_text="Lower numbers appear first."
    )

    class Meta:
        ordering = ["order", "-start_date"]
        verbose_name_plural = "Experience"

    def __str__(self):
        return f"{self.role} at {self.company}"

    @property
    def is_current(self):
        return self.end_date is None

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")


class Education(models.Model):
    institution = models.CharField(max_length=150)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(
        null=True, blank=True, help_text="Leave empty if currently enrolled."
    )
    grade = models.CharField(
        max_length=50, blank=True, help_text="e.g. GPA 3.8/4.0 or First Class Honours"
    )
    description = models.TextField(blank=True)
    is_visible = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "-start_date"]

    def __str__(self):
        return f"{self.degree}, {self.institution}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")


class Skill(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. Backend, Frontend, DevOps, Data",
    )
    level = models.CharField(
        max_length=12, choices=Level.choices, default=Level.INTERMEDIATE
    )
    icon = models.CharField(
        max_length=10,
        blank=True,
        help_text="Emoji shown on the frontend, e.g. 🌱",
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Hex color for hover effects, e.g. #10b981",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField()
    featured_image = models.ImageField(upload_to="projects/images/", null=True, blank=True)
    live_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="projects")
    is_featured = models.BooleanField(
        default=False, help_text="Show on the homepage."
    )
    is_visible = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Project, self.title, self)
        super().save(*args, **kwargs)


class Certification(models.Model):
    name = models.CharField(max_length=150)
    issuer = models.CharField(max_length=100)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.name} ({self.issuer})"