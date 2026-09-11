from django.contrib import admin, messages
from django.utils.html import format_html

from .models import (
    Category,
    Certification,
    Comment,
    Education,
    Experience,
    Post,
    Project,
    SiteSettings,
    Skill,
    Tag,
)

admin.site.site_header = "Portfolio Admin"
admin.site.site_title = "Portfolio Admin"
admin.site.index_title = "Content management"


class ImageThumbnailMixin:
    """Small image preview in the changelist — you instantly see what's uploaded."""

    @admin.display(description="Image")
    def thumbnail(self, obj):
        image = getattr(obj, "featured_image", None) or getattr(obj, "logo", None)
        if image:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px" />', image.url
            )
        return "—"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Branding", {"fields": ("title", "tagline", "role", "location", "description", "logo", "favicon")}),
        ("Contact & Social", {"fields": ("email", "github_url", "linkedin_url", "twitter_url")}),
        ("Files", {"fields": ("resume",)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    # Required: autocomplete_fields on Post reads this
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Post)
class PostAdmin(ImageThumbnailMixin, admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "published_at", "thumbnail"]
    list_filter = ["status", "category", "tags"]
    list_select_related = ["author", "category"]  # no N+1 in the changelist
    search_fields = ["title", "excerpt", "content"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["author", "category"]  # stays fast at thousands of rows
    filter_horizontal = ["tags"]
    date_hierarchy = "published_at"
    readonly_fields = ["created_at", "updated_at", "published_at"]
    actions = ["publish_posts", "unpublish_posts"]
    empty_value_display = "—"

    fieldsets = (
        (None, {"fields": ("title", "slug", "author", "category", "tags")}),
        ("Content", {"fields": ("featured_image", "excerpt", "content")}),
        ("Publishing", {"fields": ("status", "published_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.action(description="Publish selected posts")
    def publish_posts(self, request, queryset):
        count = 0
        for post in queryset.filter(status=Post.Status.DRAFT):
            post.status = Post.Status.PUBLISHED
            post.save()  # sets published_at + fires post_save → Next.js revalidation
            count += 1
        self.message_user(request, f"{count} post(s) published.", messages.SUCCESS)

    @admin.action(description="Unpublish selected posts")
    def unpublish_posts(self, request, queryset):
        count = 0
        for post in queryset.filter(status=Post.Status.PUBLISHED):
            post.status = Post.Status.DRAFT
            post.save()  # fires post_save → Next.js purges the now-private page
            count += 1
        self.message_user(request, f"{count} post(s) moved back to draft.", messages.SUCCESS)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["name", "post", "excerpt", "is_approved", "created_at"]
    list_filter = ["is_approved", "created_at"]
    list_editable = ["is_approved"]  # toggle approval right in the list
    search_fields = ["name", "email", "body", "post__title"]
    autocomplete_fields = ["post"]
    readonly_fields = ["created_at"]
    actions = ["approve_comments", "unapprove_comments"]

    fieldsets = (
        (None, {"fields": ("post", "name", "email", "created_at")}),
        ("Comment", {"fields": ("body",)}),
        ("Moderation", {"fields": ("is_approved",)}),
    )

    @admin.display(description="Comment")
    def excerpt(self, obj):
        return obj.body[:60] + ("…" if len(obj.body) > 60 else "")

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        count = 0
        for comment in queryset.filter(is_approved=False):
            comment.is_approved = True
            comment.save()  # fires post_save → post page revalidates with the new comment
            count += 1
        self.message_user(request, f"{count} comment(s) approved.", messages.SUCCESS)

    @admin.action(description="Unapprove selected comments")
    def unapprove_comments(self, request, queryset):
        count = queryset.filter(is_approved=True).update(is_approved=False)
        self.message_user(request, f"{count} comment(s) hidden.", messages.SUCCESS)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ["role", "company", "start_date", "end_date", "current", "is_visible", "order"]
    list_editable = ["is_visible", "order"]
    list_filter = ["is_visible"]
    search_fields = ["role", "company", "description"]

    @admin.display(boolean=True, description="Current")
    def current(self, obj):
        return obj.is_current


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ["degree", "institution", "start_date", "end_date", "grade", "is_visible", "order"]
    list_editable = ["is_visible", "order"]
    list_filter = ["is_visible"]
    search_fields = ["institution", "degree", "field_of_study"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "icon", "category", "level", "color_swatch", "order"]
    list_editable = ["order"]
    list_filter = ["category", "level"]
    search_fields = ["name"]

    @admin.display(description="Color")
    def color_swatch(self, obj):
        if obj.color:
            return format_html(
                '<span style="display:inline-block;width:14px;height:14px;border-radius:3px;'
                'background:{};border:1px solid rgba(255,255,255,0.3)"></span> <code>{}</code>',
                obj.color,
                obj.color,
            )
        return "—"

@admin.register(Project)
class ProjectAdmin(ImageThumbnailMixin, admin.ModelAdmin):
    list_display = ["title", "is_featured", "is_visible", "order", "thumbnail", "created_at"]
    list_editable = ["is_featured", "is_visible", "order"]
    list_filter = ["is_featured", "is_visible", "skills"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["skills"]
    readonly_fields = ["created_at", "updated_at"]
    empty_value_display = "—"

    fieldsets = (
        (None, {"fields": ("title", "slug", "description", "featured_image")}),
        ("Links", {"fields": ("live_url", "repo_url")}),
        ("Display", {"fields": ("skills", "is_featured", "is_visible", "order")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ["name", "issuer", "issue_date", "expiry_date", "credential_url"]
    search_fields = ["name", "issuer"]