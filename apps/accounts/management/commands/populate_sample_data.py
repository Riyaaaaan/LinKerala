"""
Management command to populate sample data for LocalFreelance AI.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import FreelancerProfile, ClientProfile
from apps.portfolio.models import Category, Skill, Portfolio, PortfolioItem

CustomUser = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create Categories
        categories_data = [
            {'name': 'Photography', 'slug': 'photography', 'icon': '📷'},
            {'name': 'Videography', 'slug': 'videography', 'icon': '🎬'},
            {'name': 'Graphic Design', 'slug': 'graphic-design', 'icon': '🎨'},
            {'name': 'Web Development', 'slug': 'web-development', 'icon': '💻'},
            {'name': 'Tutoring', 'slug': 'tutoring', 'icon': '📚'},
            {'name': 'Home Repair', 'slug': 'home-repair', 'icon': '🔧'},
            {'name': 'Music Lessons', 'slug': 'music-lessons', 'icon': '🎵'},
            {'name': 'Personal Training', 'slug': 'personal-training', 'icon': '💪'},
            {'name': 'Event Planning', 'slug': 'event-planning', 'icon': '🎉'},
            {'name': 'Writing', 'slug': 'writing', 'icon': '✍️'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(f'  Created category: {cat.name}')

        # Create Skills
        skills_data = [
            {'name': 'Portrait Photography', 'category': 'Photography'},
            {'name': 'Wedding Photography', 'category': 'Photography'},
            {'name': 'Product Photography', 'category': 'Photography'},
            {'name': 'Logo Design', 'category': 'Graphic Design'},
            {'name': 'Brand Identity', 'category': 'Graphic Design'},
            {'name': 'React Development', 'category': 'Web Development'},
            {'name': 'WordPress', 'category': 'Web Development'},
            {'name': 'Python/Django', 'category': 'Web Development'},
            {'name': 'Math Tutoring', 'category': 'Tutoring'},
            {'name': 'English Tutoring', 'category': 'Tutoring'},
            {'name': 'Piano Lessons', 'category': 'Music Lessons'},
            {'name': 'Guitar Lessons', 'category': 'Music Lessons'},
            {'name': 'Fitness Training', 'category': 'Personal Training'},
            {'name': 'Plumbing', 'category': 'Home Repair'},
            {'name': 'Electrical', 'category': 'Home Repair'},
            {'name': 'Content Writing', 'category': 'Writing'},
            {'name': 'Copywriting', 'category': 'Writing'},
        ]

        skills = {}
        for skill_data in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults={'category': categories.get(skill_data['category'])}
            )
            skills[skill_data['name']] = skill
            if created:
                self.stdout.write(f'  Created skill: {skill.name}')

        # Create Sample Freelancers
        freelancers_data = [
            {
                'email': 'sarah.photo@email.com',
                'username': 'sarah_photo',
                'display_name': 'Sarah Johnson',
                'profile_photo': 'https://ui-avatars.com/api/?name=Sarah+Johnson&background=c7d2fe&color=3730a3&size=200&bold=true',
                'tagline': 'Professional photographer capturing life\'s moments',
                'bio': 'I am a professional photographer with over 8 years of experience in portrait, wedding, and event photography. I love capturing authentic moments that tell a story.',
                'city': 'San Francisco',
                'state': 'CA',
                'country': 'USA',
                'price_min': 150,
                'price_max': 500,
                'availability': 'available',
                'ai_tags': ['photographer', 'portraits', 'weddings', 'events'],
            },
            {
                'email': 'mike.dev@email.com',
                'username': 'mike_dev',
                'display_name': 'Mike Chen',
                'profile_photo': 'https://ui-avatars.com/api/?name=Mike+Chen&background=fde68a&color=92400e&size=200&bold=true',
                'tagline': 'Full-stack developer specializing in modern web apps',
                'bio': 'I build fast, responsive websites and web applications using the latest technologies. From simple landing pages to complex web apps, I can bring your ideas to life.',
                'city': 'Austin',
                'state': 'TX',
                'country': 'USA',
                'price_min': 50,
                'price_max': 150,
                'availability': 'available',
                'ai_tags': ['developer', 'web', 'react', 'python'],
            },
            {
                'email': 'emma.tutor@email.com',
                'username': 'emma_tutor',
                'display_name': 'Emma Williams',
                'profile_photo': 'https://ui-avatars.com/api/?name=Emma+Williams&background=bbf7d0&color=166534&size=200&bold=true',
                'tagline': 'Patient math tutor helping students succeed',
                'bio': 'I have a passion for teaching mathematics and helping students build confidence in their abilities. I tutor all levels from elementary to college calculus.',
                'city': 'Seattle',
                'state': 'WA',
                'country': 'USA',
                'price_min': 40,
                'price_max': 80,
                'availability': 'available',
                'ai_tags': ['tutor', 'math', 'education'],
            },
            {
                'email': 'jose.music@email.com',
                'username': 'jose_music',
                'display_name': 'Jose Rodriguez',
                'profile_photo': 'https://ui-avatars.com/api/?name=Jose+Rodriguez&background=fbcfe8&color=9d174d&size=200&bold=true',
                'tagline': 'Professional musician and patient instructor',
                'bio': 'I have been playing guitar for 15 years and teaching for 8. I believe anyone can learn to play music with the right guidance and practice.',
                'city': 'Los Angeles',
                'state': 'CA',
                'country': 'USA',
                'price_min': 45,
                'price_max': 75,
                'availability': 'busy',
                'ai_tags': ['music', 'guitar', 'lessons'],
            },
            {
                'email': 'lisa.design@email.com',
                'username': 'lisa_design',
                'display_name': 'Lisa Park',
                'profile_photo': 'https://ui-avatars.com/api/?name=Lisa+Park&background=fed7aa&color=9a3412&size=200&bold=true',
                'tagline': 'Creative designer bringing brands to life',
                'bio': 'I specialize in logo design, brand identity, and visual design. Let me help you create a memorable brand that stands out from the competition.',
                'city': 'New York',
                'state': 'NY',
                'country': 'USA',
                'price_min': 200,
                'price_max': 1000,
                'availability': 'available',
                'ai_tags': ['designer', 'logo', 'branding', 'graphic'],
            },
            {
                'email': 'tom.repair@email.com',
                'username': 'tom_repair',
                'display_name': 'Tom Wilson',
                'profile_photo': 'https://ui-avatars.com/api/?name=Tom+Wilson&background=ddd6fe&color=5b21b6&size=200&bold=true',
                'tagline': 'Reliable handyman for all your home repair needs',
                'bio': 'I have been doing home repairs for over 20 years. From minor fixes to major renovations, I can handle it all with quality workmanship.',
                'city': 'Denver',
                'state': 'CO',
                'country': 'USA',
                'price_min': 50,
                'price_max': 200,
                'availability': 'available',
                'ai_tags': ['repair', 'handyman', 'home'],
            },
        ]

        for freelancer_data in freelancers_data:
            email = freelancer_data['email']
            username = freelancer_data['username']
            display_name = freelancer_data['display_name']

            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'role': 'freelancer',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('demo1234')
                user.save()

            # Create freelancer profile data without email/username
            profile_data = {k: v for k, v in freelancer_data.items() if k not in ['email', 'username']}
            profile_data['user'] = user

            profile, created = FreelancerProfile.objects.get_or_create(
                user=user,
                defaults=profile_data
            )
            if created:
                self.stdout.write(f'  Created freelancer: {display_name}')

                # Create portfolio for each freelancer
                portfolio = Portfolio.objects.create(
                    freelancer=profile,
                    title=f"{profile.display_name}'s Portfolio",
                    description=profile.bio,
                    is_published=True,
                )
                portfolio.categories.add(categories.get('Photography') or categories.get('Web Development') or categories.get('Tutoring'))
                portfolio.calculate_completeness()

                self.stdout.write(f'    Created portfolio for {profile.display_name}')

        # Create a sample client
        client_user, created = CustomUser.objects.get_or_create(
            email='client@email.com',
            defaults={
                'username': 'demo_client',
                'role': 'client',
                'is_active': True,
            }
        )
        if created:
            client_user.set_password('demo1234')
            client_user.save()

        client_profile, created = ClientProfile.objects.get_or_create(
            user=client_user,
            defaults={
                'full_name': 'Demo Client',
                'city': 'Boston',
            }
        )
        if created:
            self.stdout.write(f'  Created client: {client_profile.full_name}')

        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!'))
        self.stdout.write('\nSample accounts:')
        self.stdout.write('  Freelancer: sarah.photo@email.com / demo1234')
        self.stdout.write('  Freelancer: mike.dev@email.com / demo1234')
        self.stdout.write('  Client: client@email.com / demo1234')
