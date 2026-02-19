"""
Accounts app models for LocalFreelance AI.
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUserManager(BaseUserManager):
    """Custom user manager for CustomUser model."""

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Base user model for both freelancers and clients."""

    ROLE_CHOICES = [
        ('freelancer', 'Freelancer'),
        ('client', 'Client'),
        ('admin', 'Admin'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class FreelancerProfile(models.Model):
    """Extended profile for freelancers."""

    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]

    LANGUAGE_PROFICIENCY_CHOICES = [
        ('native', 'Native'),
        ('fluent', 'Fluent'),
        ('conversational', 'Conversational'),
        ('basic', 'Basic'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='freelancer_profile')
    display_name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    profile_photo = models.URLField(blank=True)
    cover_photo = models.URLField(blank=True)

    # Location
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number for clients to contact you")

    # Pricing
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_min = models.PositiveIntegerField(null=True, blank=True)
    price_max = models.PositiveIntegerField(null=True, blank=True)

    # Availability & Response
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='offline')
    response_time_hours = models.PositiveIntegerField(null=True, blank=True, help_text="Typical response time in hours")

    # Experience
    years_experience = models.PositiveIntegerField(null=True, blank=True, help_text="Years of professional experience")

    # Languages (stored as JSON: [{"language": "English", "proficiency": "native"}])
    languages = models.JSONField(default=list, blank=True, help_text="List of languages with proficiency level")

    # Social Links
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    # Professional Info (stored as JSON arrays)
    education = models.JSONField(default=list, blank=True, help_text="Education history")
    work_experience = models.JSONField(default=list, blank=True, help_text="Work experience")
    certifications = models.JSONField(default=list, blank=True, help_text="Certifications and achievements")

    # System fields
    ai_tags = models.JSONField(default=list)
    activity_score = models.FloatField(default=0.0)
    profile_views = models.PositiveIntegerField(default=0)
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def avg_rating(self):
        from apps.reviews.models import Review
        reviews = Review.objects.filter(freelancer=self)
        if reviews.exists():
            return sum(r.rating for r in reviews) / reviews.count()
        return 0.0

    @property
    def review_count(self):
        from apps.reviews.models import Review
        return Review.objects.filter(freelancer=self).count()

    def __str__(self):
        return self.display_name


class ClientProfile(models.Model):
    """Extended profile for clients."""

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='client_profile')
    full_name = models.CharField(max_length=100)
    profile_photo = models.URLField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number for freelancers to contact you")
    is_profile_complete = models.BooleanField(default=False, help_text="Whether the profile has minimum required information")
    bookmarks = models.ManyToManyField(FreelancerProfile, blank=True, related_name='bookmarked_by')

    def __str__(self):
        return self.full_name


class Work(models.Model):
    """Work/Job posting created by clients."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    DURATION_UNIT_CHOICES = [
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ]

    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='works')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True)

    # Payment
    pay_per_hour = models.DecimalField(max_digits=10, decimal_places=2, help_text="Hourly rate in dollars")

    # Duration
    duration_value = models.PositiveIntegerField(help_text="Duration value")
    duration_unit = models.CharField(max_length=20, choices=DURATION_UNIT_CHOICES, default='hours')

    # Location (optional)
    location = models.CharField(max_length=200, blank=True, help_text="Job location")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    # Skills/tags
    skills = models.JSONField(default=list, blank=True, help_text="Required skills")

    # Contact info visibility
    show_contact_info = models.BooleanField(default=True, help_text="Show contact info to freelancers")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Quote(models.Model):
    """Quote/Proposal submitted by freelancers for work opportunities."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='quotes')
    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name='quotes')
    
    # Quote details
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Hourly rate quoted by freelancer")
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in hours")
    cover_letter = models.TextField(help_text="Cover letter/proposal message")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Email tracking
    email_sent = models.BooleanField(default=False, help_text="Whether quote email was sent to client")
    email_sent_at = models.DateTimeField(null=True, blank=True, help_text="When email was sent")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['work', 'freelancer']  # One quote per freelancer per work

    def __str__(self):
        return f"Quote by {self.freelancer.user.username} for {self.work.title}"

    def send_quote_email(self):
        """Send quote details to the client via email."""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.utils import timezone

        client = self.work.client
        freelancer = self.freelancer

        subject = f"New Quote for '{self.work.title}' - {freelancer.display_name}"

        message = f"""
Hello {client.full_name},

You have received a new quote for your work posting: "{self.work.title}"

Freelancer Details:
- Name: {freelancer.display_name}
- Email: {freelancer.user.email}
- Phone: {freelancer.phone or 'Not provided'}

Quote Details:
- Proposed Rate: ${self.proposed_rate}/hour
- Estimated Duration: {self.estimated_duration} hours
- Total Estimated Cost: ${float(self.proposed_rate) * self.estimated_duration}

Cover Letter:
{self.cover_letter}

Original Job Details:
- Title: {self.work.title}
- Description: {self.work.description}
- Your Budget: ${self.work.pay_per_hour}/hour
- Location: {self.work.location or 'Not specified'}

You can respond directly to this email to contact the freelancer.

Best regards,
LinKerala Team
"""

        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Email settings - HOST: {settings.EMAIL_HOST}, USER: {settings.EMAIL_HOST_USER}, PASSWORD length: {len(settings.EMAIL_HOST_PASSWORD)}")
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else settings.EMAIL_HOST_USER,
                recipient_list=[client.user.email],
                fail_silently=False,
            )
            self.email_sent = True
            self.email_sent_at = timezone.now()
            self.save(update_fields=['email_sent', 'email_sent_at'])
            return True
        except Exception as e:
            print(f"Error sending quote email: {e}")
            return False
