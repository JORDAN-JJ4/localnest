import os
import django
import urllib.request
import time
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image, ImageDraw

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'localnest.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import HostProfile, Profile
from properties.models import Property, FoodMenu, Amenity, PropertyImage, Destination, Experience
from bookings.models import Booking
from reviews.models import Review
from core.models import BlogPost, StoryContributor, Family, Recipe, Tradition, VoiceRecording, Story, LocalSecret, SecretRecommendation

User = get_user_model()

def create_fallback_image(width, height, color, filename):
    print(f"Generating fallback image for {filename}...")
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width-10, height-10], outline=(255, 255, 255), width=3)
    draw.ellipse([width//4, height//4, width*3//4, height*3//4], outline=(255, 255, 255), width=2)
    buf = BytesIO()
    img.save(buf, format='JPEG')
    return ContentFile(buf.getvalue(), name=filename)

def safe_save_image(field, filename, file_content, save=True):
    try:
        field.save(filename, file_content, save=save)
    except Exception as e:
        print(f"Warning: Failed to save image {filename} to storage backend: {e}")

_LOCAL_IMAGE_INDEX = {}

def _init_image_index():
    global _LOCAL_IMAGE_INDEX
    if _LOCAL_IMAGE_INDEX:
        return
    for search_dir in ['media', os.path.join('static', 'img')]:
        if os.path.exists(search_dir):
            for root, _, files in os.walk(search_dir):
                for f in files:
                    _LOCAL_IMAGE_INDEX[f.lower()] = os.path.join(root, f)

def download_image(url, filename, fallback_color=(201, 106, 61)):
    _init_image_index()
    
    # 1. Check local file index (case-insensitive for Linux/Render compatibility)
    lower_fn = filename.lower()
    if lower_fn in _LOCAL_IMAGE_INDEX:
        local_path = _LOCAL_IMAGE_INDEX[lower_fn]
        try:
            with open(local_path, 'rb') as f:
                content = f.read()
                return ContentFile(content, name=filename)
        except Exception as e:
            print(f"Error reading local image {local_path}: {e}")

    # 2. Return instant fallback image (prevents slow network timeouts during Render container startup)
    return create_fallback_image(800, 500, fallback_color, filename)


def seed():
    print("Seeding database with premium content and real images...")
    
    # Clear existing data to make the seeding script idempotent
    Booking.objects.all().delete()
    Review.objects.all().delete()
    Property.objects.all().delete()
    Destination.objects.all().delete()
    Experience.objects.all().delete()
    BlogPost.objects.all().delete()
    Story.objects.all().delete()
    Recipe.objects.all().delete()
    Tradition.objects.all().delete()
    Family.objects.all().delete()
    VoiceRecording.objects.all().delete()
    StoryContributor.objects.all().delete()
    LocalSecret.objects.all().delete()
    SecretRecommendation.objects.all().delete()
    User.objects.filter(username__in=[
        'admin', 'host_ramesh', 'host_harish', 'host_tsering', 'host_vikram', 'host_anil', 'tourist_jenish', 'tourist_sneha'
    ]).delete()
    
    # 1. Create Admin
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@localnest.com',
            'user_type': User.Types.ADMIN,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("Admin user created.")
    
    # 2. Create Amenities
    amenities_data = [
        ('Wi-Fi', 'bi-wifi'),
        ('Hot Water', 'bi-droplet-half'),
        ('Air Conditioning', 'bi-snow'),
        ('Washing Machine', 'bi-box-seam'),
        ('Parking', 'bi-car-front'),
        ('Organic Meals', 'bi-egg-fried'),
        ('Guided Village Walk', 'bi-map')
    ]
    
    amenities = {}
    for name, icon in amenities_data:
        amenity, _ = Amenity.objects.get_or_create(name=name, defaults={'icon': icon})
        amenities[name] = amenity
    print("Amenities created.")

    # 3. Create Destinations
    dest_data = [
        {
            'name': 'Munnar',
            'slug': 'munnar',
            'best_season': 'October to March',
            'weather': 'Pleasant & misty (15°C - 25°C)',
            'local_food': 'Kerala Sadya, Kappa & Fish Curry',
            'description': 'Munnar is a breathtaking hill station nestled in the Western Ghats of Kerala. Famous for its cascading tea gardens, winding mist-filled trails, and cardamom estates, it represents the epitome of slow, quiet living in South India.',
            'lat': 10.0889,
            'lon': 77.0595,
            'image_url': 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=1200&q=80',
            'color': (201, 106, 61)
        },
        {
            'name': 'Varanasi',
            'slug': 'varanasi',
            'best_season': 'October to April',
            'weather': 'Cool temple breeze (10°C - 22°C)',
            'local_food': 'Kachori Sabzi, Banarasi Jalebi & Lassi',
            'description': 'One of the oldest continuously inhabited cities on Earth, Varanasi (Kashi) is India’s spiritual heart. Built along the sacred banks of the River Ganges, it is a city of bells, ancient rituals, sand-swept ghats, and Sanskrit hymns.',
            'lat': 25.3076,
            'lon': 83.0104,
            'image_url': 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=1200&q=80',
            'color': (180, 83, 9),
            'local_filename': 'v2_varanasi_boat.jpg'
        },
        {
            'name': 'Manali',
            'slug': 'manali',
            'best_season': 'March to June, October to February',
            'weather': 'Chilly Himalayan snow winds (-2°C - 18°C)',
            'local_food': 'Himachali Siddu & Wild Apricot Jams',
            'description': 'Perched in the snowy heights of Himachal Pradesh, Manali is a gateway to the high Himalayas. Famous for its whispering pine forests, rushing Beas River, and ancient stone cottages, it is a sanctuary of cold air and warm hearths.',
            'lat': 32.2596,
            'lon': 77.1887,
            'image_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=80',
            'color': (140, 154, 91)
        },
        {
            'name': 'Jaipur',
            'slug': 'jaipur',
            'best_season': 'November to March',
            'weather': 'Warm desert climate (15°C - 28°C)',
            'local_food': 'Slow-coal Dal Baati Churma & Gatte ki Sabzi',
            'description': 'The historic capital of Rajasthan, Jaipur (the Pink City) is renowned for its grand forts, royal palaces, and rich artisanal heritage. It is a vivid canvas of desert suns, block-printed fabrics, and royal hospitality.',
            'lat': 26.9855,
            'lon': 75.8513,
            'image_url': 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80',
            'color': (217, 119, 6)
        },
        {
            'name': 'Mumbai',
            'slug': 'mumbai',
            'best_season': 'October to March',
            'weather': 'Pleasant coastal breeze (20°C - 30°C)',
            'local_food': 'Vada Pav, Misal Pav, Bombay Sandwich',
            'description': 'Mumbai, the vibrant capital of Maharashtra, is a melting pot of cultures, commerce, and colonial history. From the bustling local trains arriving at the historic Chhatrapati Shivaji Maharaj Terminus to quiet evenings on Marine Drive, it is a city of dreams.',
            'lat': 18.9696,
            'lon': 72.8230,
            'image_url': 'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=80',
            'color': (74, 20, 140),
            'local_filename': 'v2_cstm_station.jpg'
        }
    ]

    destinations = {}
    for d in dest_data:
        dest = Destination.objects.create(
            name=d['name'],
            slug=d['slug'],
            best_season=d['best_season'],
            weather=d['weather'],
            local_food=d['local_food'],
            description=d['description'],
            latitude=d['lat'],
            longitude=d['lon']
        )
        img_name = d.get('local_filename', f"dest_{d['slug']}.jpg")
        img_file = download_image(d['image_url'], img_name, d['color'])
        safe_save_image(dest.image, img_name, img_file, save=True)
        destinations[d['name']] = dest
    print("Destinations created.")    # 4. Create Hosts
    hosts_data = [
        {
            'username': 'host_ramesh',
            'email': 'ramesh@gmail.com',
            'first_name': 'Ramesh',
            'last_name': 'Pillai',
            'phone': '+91 9876543210',
            'bio': 'In Chithirapuram, the days begin before dawn. My family has tended to our wild cardamom forests and tea hills for three generations. We invite you to wake up to the sound of birds, walk through the forest shadows, and sit at our table for a slow Kerala Sadya served on banana leaves.',
            'address': 'Chithirapuram, Munnar, Kerala',
            'img_url': 'https://images.unsplash.com/photo-1566616213894-2d4e1baee5d8?auto=format&fit=crop&w=150&q=80',
            'color': (201, 106, 61),
            'family_intro': 'Our cardamom valleys have been cared for by our hands for eighty years. Every morning, the mountain mist teaches us patience.',
            'profile_filename': 'profile_host_ramesh.jpg',
            'src_profile_filename': 'localnest_family_reunion.jpg'
        },
        {
            'username': 'host_harish',
            'email': 'harish@gmail.com',
            'first_name': 'Harish',
            'last_name': 'Sharma',
            'phone': '+91 8765432109',
            'bio': 'A retired teacher of Sanskrit, I welcome you to our 150-year-old courtyard Haveli near Dashashwamedh Ghat. Kashi is a city of bells, incense, and silence. Let my family share our heritage, scriptures, and pure vegetarian satvik food cooked on slow wood-fire stoves.',
            'address': 'Dashashwamedh Ghat, Varanasi, Uttar Pradesh',
            'img_url': 'https://images.unsplash.com/photo-1618083707368-b3823daa2726?auto=format&fit=crop&w=150&q=80',
            'color': (180, 83, 9),
            'family_intro': 'In Kashi, we do not welcome a traveler; we welcome the divine. Our courtyard doors have been open since the late 19th century.',
            'profile_filename': 'profile_host_harish.jpg',
            'src_profile_filename': 'v2_grandmother.jpg'
        },
        {
            'username': 'host_tsering',
            'email': 'tsering@gmail.com',
            'first_name': 'Tsering',
            'last_name': 'Dorjee',
            'phone': '+91 7654321098',
            'bio': 'Tashi Delek. Welcome to our Himalayan cottage in Old Manali. Our orchard is full of wild apples, cherries, and apricots. We invite you to taste hot steamed siddu with pure ghee, listen to folklore around the hearth, and breathe the crisp mountain winds.',
            'address': 'Old Manali, Himachal Pradesh',
            'img_url': 'https://images.unsplash.com/photo-1509099836639-18ba1795216d?auto=format&fit=crop&w=150&q=80',
            'color': (140, 154, 91),
            'family_intro': 'Under the shadow of the pines, our wooden hearth has warmed travelers for generations. Taste the wild sweetness of our valley.',
            'profile_filename': 'profile_host_tsering.jpg',
            'src_profile_filename': 'family_watching_tv.jpg'
        },
        {
            'username': 'host_vikram',
            'email': 'vikram@gmail.com',
            'first_name': 'Vikram',
            'last_name': 'Singh',
            'phone': '+91 6543210987',
            'bio': 'Welcome to the Pink City. We live in an ancestral Haveli built in the late 19th century near the old gates of Amer. We preserve traditional block printing, puppet play, and the slow, wood-coal recipes of royal Rajasthani kitchens.',
            'address': 'Amer Road, Jaipur, Rajasthan',
            'img_url': 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=150&q=80',
            'color': (217, 119, 6),
            'family_intro': 'We believe that the story of Jaipur is written in quartz clay and limestone. Let us show you the rhythms of our workshop.',
            'profile_filename': 'profile_host_vikram.jpg',
            'src_profile_filename': 'family_playing_cards.jpg'
        },
        {
            'username': 'host_anil',
            'email': 'anil@gmail.com',
            'first_name': 'Anil',
            'last_name': 'Kulkarni',
            'phone': '+91 9543210987',
            'bio': 'Welcome to our heritage home in Dadar. My family has lived in Mumbai for four generations. We love sharing the fast-paced stories of the city, showing guests our favorite local street food spots, and preparing authentic Maharashtrian meals like Puran Poli.',
            'address': 'Dadar West, Mumbai, Maharashtra',
            'img_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80',
            'color': (74, 20, 140),
            'family_intro': 'Mumbai is a city of millions, but in our home, every guest is family. Let us show you the warm side of this bustling city.',
            'profile_filename': 'host_host_anil.jpg',
            'src_profile_filename': 'kulkarni_family.jpg'
        }
    ]

    hosts = []
    for h in hosts_data:
        user, u_created = User.objects.get_or_create(
            username=h['username'],
            defaults={
                'email': h['email'],
                'first_name': h['first_name'],
                'last_name': h['last_name'],
                'user_type': User.Types.HOST,
                'email_verified': True
            }
        )
        user.user_type = User.Types.HOST
        user.email_verified = True
        user.set_password('host123')
        user.save()
        
        hp, _ = HostProfile.objects.get_or_create(user=user)
        hp.phone_number = h['phone']
        hp.bio = h['bio']
        hp.address = h['address']
        hp.family_intro = h.get('family_intro', '')
        hp.verification_status = HostProfile.VerificationStatus.APPROVED
        hp.years_hosting = 4
        hp.response_rate = 98
        
        src_profile = h.get('src_profile_filename', h['profile_filename'])
        profile_img = download_image(h['img_url'], src_profile, h['color'])
        safe_save_image(hp.profile_photo, h['profile_filename'], profile_img, save=False)
        hp.save()

    # 5. Create Experiences for Hosts
    experiences_data = [
        {
            'host': 'host_ramesh',
            'title': 'Cardamom & Tea Harvest Walk',
            'category': 'Nature & Farming',
            'price': 350.00,
            'duration': '2 Hours',
            'description': 'Walk through our private spice plantation and learn how to harvest tea leaves and cardamom pods by hand.',
            'image_url': 'https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=600&q=80',
            'color': (201, 106, 61)
        },
        {
            'host': 'host_harish',
            'title': 'Subah-e-Banaras Ghat Tour',
            'category': 'Culture & Spiritual',
            'price': 250.00,
            'duration': '3 Hours',
            'description': 'An early morning boat ride on the sacred Ganges river, witnessing prayers, rituals, and the sunrise.',
            'image_url': 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=600&q=80',
            'color': (180, 83, 9),
            'local_filename': 'v2_varanasi_boat.jpg'
        },
        {
            'host': 'host_tsering',
            'title': 'Wild Apricot Jam Workshop',
            'category': 'Cooking & Food',
            'price': 400.00,
            'duration': '1.5 Hours',
            'description': 'Gather fresh wild apricots from our backyard orchard and cook traditional Himalayan jam with old family recipes.',
            'image_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=600&q=80',
            'color': (140, 154, 91)
        },
        {
            'host': 'host_vikram',
            'title': 'Blue Pottery Crafts Class',
            'category': 'Art & Crafts',
            'price': 500.00,
            'duration': '2.5 Hours',
            'description': 'Learn the intricate hand-painting techniques of Jaipur’s famous blue pottery from local master artisans.',
            'image_url': 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=600&q=80',
            'color': (217, 119, 6)
        },
        {
            'host': 'host_anil',
            'title': 'Mumbai Street Food Safari',
            'category': 'Cooking & Food',
            'price': 300.00,
            'duration': '3 Hours',
            'description': 'Taste the best street food Mumbai has to offer, from Dadar to Chowpatty, led by a local food lover.',
            'image_url': 'https://images.unsplash.com/photo-1601050690597-df056fb4ce78?auto=format&fit=crop&w=600&q=80',
            'color': (74, 20, 140),
            'local_filename': 'v2_cstm_station.jpg'
        }
    ]

    for exp_info in experiences_data:
        h_user = User.objects.get(username=exp_info['host'])
        exp = Experience.objects.create(
            host=h_user,
            title=exp_info['title'],
            category=exp_info['category'],
            price=exp_info['price'],
            duration=exp_info['duration'],
            description=exp_info['description']
        )
        img_name = exp_info.get('local_filename', f"exp_{exp.title.lower().replace(' ', '_')}.jpg")
        img_file = download_image(exp_info['image_url'], img_name, exp_info['color'])
        safe_save_image(exp.image, img_name, img_file, save=True)
    print("Experiences created.")

    # 6. Create Tourists
    tourists_data = [
        {
            'username': 'tourist_jenish',
            'email': 'jenish@gmail.com',
            'first_name': 'Jenish',
            'last_name': 'Patel',
            'phone': '+91 9999888877',
            'bio': 'Enthusiastic explorer and food lover looking for authentic experiences.',
            'address': 'Ahmedabad, Gujarat',
            'img_url': 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=150&q=80',
            'color': (136, 14, 79)
        },
        {
            'username': 'tourist_sneha',
            'email': 'sneha@gmail.com',
            'first_name': 'Sneha',
            'last_name': 'Reddy',
            'phone': '+91 8888777766',
            'bio': 'Travel photographer and yoga enthusiast looking to connect with local traditions.',
            'address': 'Hyderabad, Telangana',
            'img_url': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
            'color': (74, 20, 140)
        }
    ]

    tourists = []
    for t in tourists_data:
        user, u_created = User.objects.get_or_create(
            username=t['username'],
            defaults={
                'email': t['email'],
                'first_name': t['first_name'],
                'last_name': t['last_name'],
                'user_type': User.Types.TOURIST,
                'email_verified': True
            }
        )
        user.user_type = User.Types.TOURIST
        user.email_verified = True
        user.set_password('tourist123')
        user.save()
            
        tp, _ = Profile.objects.get_or_create(user=user)
        tp.phone_number = t['phone']
        tp.bio = t['bio']
        tp.address = t['address']
        
        profile_filename = f"tourist_{t['username']}.jpg"
        profile_img = download_image(t['img_url'], profile_filename, t['color'])
        safe_save_image(tp.profile_photo, profile_filename, profile_img, save=False)
        tp.save()
        
        tourists.append(user)
    print("Tourists created.")

    # 7. Create Properties
    properties_data = [
        {
            'host': 'host_ramesh',
            'destination': 'Munnar',
            'name': 'Munnar Tea Hills Sanctuary',
            'description': "Tucked under the Munnar mist, our home is a sanctuary constructed from regional stone and cedarwood. Here, time is marked not by clocks, but by the harvesting of spices and the boiling of cardamom tea. We invite you to sit under our terracotta roof tiles, share stories, and taste dishes crafted from recipes passed down by our grandmothers.",
            'price': 4800.00,
            'max_guests': 4,
            'private_room': True,
            'check_in': '12:00:00',
            'check_out': '11:00:00',
            'address': '14/23 Spice Road, near Tea Museum, Munnar',
            'village': 'Chithirapuram',
            'city': 'Munnar',
            'state': 'Kerala',
            'lat': 10.0889,
            'lon': 77.0595,
            'languages': 'Malayalam, English, Tamil',
            'amenity_list': ['Wi-Fi', 'Hot Water', 'Organic Meals', 'Guided Village Walk'],
            'image_urls': [
                'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80'
            ],
            'color': (201, 106, 61),
            'food': {
                'breakfast_included': True,
                'breakfast_details': 'Puttu & Kadala Curry or Idli with Sambhar',
                'lunch_included': True,
                'lunch_details': 'Traditional Kerala Sadya on banana leaf',
                'dinner_included': True,
                'dinner_details': 'Rice, Fish Curry (for non-veg) or Thoran, Rasam',
                'vegetarian': True,
                'non_vegetarian': True,
                'custom_notes': 'All spices and vegetables are organic and harvested from our backyard garden.'
            }
        },
        {
            'host': 'host_harish',
            'destination': 'Varanasi',
            'name': 'Kashi Ganga Heritage Haveli',
            'description': "A 150-year-old sandstone Haveli resting a few steps from Dashashwamedh Ghat. The morning begins with the fragrance of temple incense and the distant sound of Ganga Aarti. Enjoy pure satvik breakfast in our sun-dappled courtyard, and experience the slow, eternal rhythms of Kashi.",
            'price': 3600.00,
            'max_guests': 2,
            'private_room': True,
            'check_in': '13:00:00',
            'check_out': '12:00:00',
            'address': 'D-20/15 Gali Vishwanath Temple, Varanasi',
            'village': 'Dashashwamedh',
            'city': 'Varanasi',
            'state': 'Uttar Pradesh',
            'lat': 25.3076,
            'lon': 83.0104,
            'languages': 'Hindi, English, Sanskrit',
            'amenity_list': ['Hot Water', 'Air Conditioning', 'Wi-Fi', 'Organic Meals'],
            'image_urls': [
                'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1604881990409-b9f246db39da?auto=format&fit=crop&w=1200&q=80'
            ],
            'local_filenames': ['v2_varanasi_boat.jpg', 'v3_ganga_aarti.jpg', 'v3_local_market.jpg'],
            'color': (180, 83, 9),
            'food': {
                'breakfast_included': True,
                'breakfast_details': 'Garam Kachori, Sabzi, and hot Jalebi',
                'lunch_included': False,
                'lunch_details': '',
                'dinner_included': True,
                'dinner_details': 'Roti, Dal Tadka, Seasonal Mix Veg, Salad',
                'vegetarian': True,
                'non_vegetarian': False,
                'custom_notes': 'Strictly vegetarian/satvik food. No onion/garlic can be requested in advance.'
            }
        },
        {
            'host': 'host_tsering',
            'destination': 'Manali',
            'name': 'Solang Valley Pine Cottage',
            'description': "Perched high on the ancient stone ridges of Old Manali, our family cottage looks out onto Solang Valley's snow peaks and pine forests. Warm your hands by the wood stove, gather wild apricots from our orchard, and share stories of Himalayan folklore by the fire.",
            'price': 5200.00,
            'max_guests': 3,
            'private_room': True,
            'check_in': '12:00:00',
            'check_out': '10:00:00',
            'address': 'Old Manali Upper Road, Manali',
            'village': 'Old Manali',
            'city': 'Manali',
            'state': 'Himachal Pradesh',
            'lat': 32.2596,
            'lon': 77.1887,
            'languages': 'Hindi, Tibetan, English',
            'amenity_list': ['Wi-Fi', 'Hot Water', 'Organic Meals', 'Parking', 'Guided Village Walk'],
            'image_urls': [
                'https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1542718610-a1d656d1884c?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80'
            ],
            'local_filenames': ['localnest_hero_hillside.jpg'],
            'color': (140, 154, 91),
            'food': {
                'breakfast_included': True,
                'breakfast_details': 'Himachali Siddu with ghee and honey, tea',
                'lunch_included': True,
                'lunch_details': 'Local red rice, dal, and wild spinach curry (Kafru)',
                'dinner_included': True,
                'dinner_details': 'Hot thukpa, momos or standard Indian dinner',
                'vegetarian': True,
                'non_vegetarian': True,
                'custom_notes': 'We make our own jams, honey, and ghee at home.'
            }
        },
        {
            'host': 'host_vikram',
            'destination': 'Jaipur',
            'name': 'Amer Palace Courtyard Haveli',
            'description': "An ancestral architectural Haveli built in the late 19th century near Amer Road. Rest within walls of pink plaster, listen to puppet strings dance in the evening breeze, and share a Dal Baati Churma feast prepared over slow-cooked coals.",
            'price': 6800.00,
            'max_guests': 6,
            'private_room': True,
            'check_in': '12:00:00',
            'check_out': '11:00:00',
            'address': '45 Amber Road, near Jal Mahal, Jaipur',
            'village': 'Amer',
            'city': 'Jaipur',
            'state': 'Rajasthan',
            'lat': 26.9855,
            'lon': 75.8513,
            'languages': 'Hindi, Rajasthani, English',
            'amenity_list': ['Wi-Fi', 'Air Conditioning', 'Washing Machine', 'Parking', 'Organic Meals'],
            'image_urls': [
                'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1603262110263-fb0112e7cc33?auto=format&fit=crop&w=1200&q=80',
                'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80'
            ],
            'local_filenames': ['localnest_hero_full_haveli.jpg'],
            'color': (217, 119, 6),
            'food': {
                'breakfast_included': True,
                'breakfast_details': 'Poha, Masala Chai, or Paratha',
                'lunch_included': False,
                'lunch_details': '',
                'dinner_included': True,
                'dinner_details': 'Dal Baati Churma, Gatte ki Sabzi, Kadhi, and buttermilk',
                'vegetarian': True,
                'non_vegetarian': False,
                'custom_notes': 'Pure vegetarian Rajasthani feast is served in the courtyard under the stars.'
            }
        },
        {
            'host': 'host_anil',
            'destination': 'Mumbai',
            'name': 'Dadar Heritage Colonial Apartment',
            'description': "Rest in our high-ceilinged heritage apartment in the heart of Mumbai. Dadar is one of the city's oldest neighborhoods, rich in history and local markets. We invite you to experience real Mumbai life, share homemade local food, and discover hidden corners of the city.",
            'price': 4200.00,
            'max_guests': 2,
            'private_room': True,
            'check_in': '12:00:00',
            'check_out': '11:00:00',
            'address': '12 Shivaji Park Road, Dadar, Mumbai',
            'village': 'Dadar',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'lat': 18.9696,
            'lon': 72.8230,
            'languages': 'Marathi, Hindi, English',
            'amenity_list': ['Wi-Fi', 'Hot Water', 'Air Conditioning', 'Organic Meals'],
            'image_urls': [
                'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=80'
            ],
            'local_filenames': ['v2_cstm_station.jpg'],
            'color': (74, 20, 140),
            'food': {
                'breakfast_included': True,
                'breakfast_details': 'Kanda Poha, Upma, and local filter coffee',
                'lunch_included': False,
                'lunch_details': '',
                'dinner_included': True,
                'dinner_details': 'Maharashtrian Thali (Bhakri, Pithla, Usal, and local sweets)',
                'vegetarian': True,
                'non_vegetarian': True,
                'custom_notes': 'All meals are cooked with traditional cold-pressed oils and home-ground spices.'
            }
        }
    ]

    for p in properties_data:
        host_user = User.objects.get(username=p['host'])
        dest_obj = destinations[p['destination']]
        prop = Property.objects.create(
            name=p['name'],
            host=host_user,
            destination=dest_obj,
            description=p['description'],
            price_per_night=p['price'],
            max_guests=p['max_guests'],
            private_room=p['private_room'],
            check_in_time=p['check_in'],
            check_out_time=p['check_out'],
            address=p['address'],
            village=p['village'],
            city=p['city'],
            state=p['state'],
            latitude=p['lat'],
            longitude=p['lon'],
            languages_spoken=p['languages'],
            is_approved=True
        )
        
        for a_name in p['amenity_list']:
            prop.amenities.add(amenities[a_name])
            
        fd = p['food']
        FoodMenu.objects.create(
            property=prop,
            breakfast_included=fd['breakfast_included'],
            breakfast_details=fd['breakfast_details'],
            lunch_included=fd['lunch_included'],
            lunch_details=fd['lunch_details'],
            dinner_included=fd['dinner_included'],
            dinner_details=fd['dinner_details'],
            vegetarian=fd['vegetarian'],
            non_vegetarian=fd['non_vegetarian'],
            custom_notes=fd['custom_notes']
        )
        
        for idx, url in enumerate(p['image_urls']):
            local_filenames = p.get('local_filenames', [])
            target_filename = f"{prop.name.replace(' ', '_').lower()}_{idx}.jpg"
            if idx < len(local_filenames):
                src_filename = local_filenames[idx]
            else:
                src_filename = target_filename
            img_file = download_image(url, src_filename, p['color'])
            p_img = PropertyImage(property=prop)
            safe_save_image(p_img.image, target_filename, img_file, save=True)
                
        # 8. Create Booking & Review
        from datetime import date, timedelta
        start = date.today() - timedelta(days=10)
        end = date.today() - timedelta(days=7)
        
        booking = Booking.objects.create(
            property=prop,
            guest=tourists[0],
            start_date=start,
            end_date=end,
            guest_count=2,
            status=Booking.StatusChoices.APPROVED
        )
        
        # Award Passport Badges automatically
        from bookings.views import award_passport_badges
        award_passport_badges(booking)
        
        Review.objects.create(
            property=prop,
            author=tourists[0],
            booking=booking,
            overall_rating=5,
            food_rating=5,
            cleanliness_rating=5,
            host_behaviour_rating=5,
            cultural_experience_rating=5,
            room_rating=5,
            experience_rating=5,
            value_rating=5,
            comments=f"We had an absolutely fantastic time staying at {prop.name}! The family was incredibly welcoming, the food was delicious and authentic, and the host gave us a wonderful local tour. Highly recommended!"
        )

    # 9. Create Blog Posts
    posts_data = [
        {
            'title': "The Art of Slow Living in Kerala's Tea Valleys",
            'slug': 'slow-living-kerala-tea-valleys',
            'category': BlogPost.CategoryChoices.STORIES,
            'content': "In the misty peaks of Munnar, time slows down. Wake up to the aroma of freshly roasted cardamom, walk along forest paths, and learn the secret recipe of traditional Puttu with sweet banana.\n\nSlow travel is about connecting with people rather than ticking tourist boxes. Living with Ramesh and his family teaches us the beauty of growing tea and cardamom, cooking on wood fire stove, and enjoying the stillness of nature.",
            'image_url': 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=1200&q=80',
            'color': (201, 106, 61)
        },
        {
            'title': "Sunrise over Varanasi: A Spiritual Awakening",
            'slug': 'sunrise-over-varanasi-spiritual-awakening',
            'category': BlogPost.CategoryChoices.CULTURE,
            'content': "As the first golden rays touch the ancient stone ghats of Kashi, the city wakes up to the rhythm of chants, bells, and gentle oars splashing in the holy Ganga.\n\nTaking a sunrise boat trip with Harish reveals the soul of Varanasi. It is not just about visiting temples, but experiencing the stillness of ancient prayer rituals and sharing Satvik food in a family home that has stood for over 150 years.",
            'image_url': 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=1200&q=80',
            'color': (180, 83, 9),
            'local_filename': 'v2_varanasi_boat.jpg'
        },
        {
            'title': "Seeding Himalayan Tradition: The Siddu Recipe",
            'slug': 'himalayan-tradition-siddu-recipe',
            'category': BlogPost.CategoryChoices.RECIPES,
            'content': "Deep in the Kullu Valley, siddu is more than just bread. It is a warm embrace during cold winter mornings, filled with ground poppy seeds and dipped in pure liquid ghee.\n\nWe spent three days in Old Manali learning the fermentation and steaming techniques from Tsering. Here, we share the step-by-step recipe to bring the flavor of the pine forests right into your kitchen.",
            'image_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=80',
            'color': (140, 154, 91)
        },
        {
            'title': "Rhythms of the River: Lessons from Rural Waterways",
            'slug': 'rhythms-river-lessons-rural-waterways',
            'category': BlogPost.CategoryChoices.STORIES,
            'content': "Slow travel is about the quiet transitions. Moving along the rivers of India on simple wooden boats with local villagers, sharing stories of crop harvests and childhood memories. It is in these unhurried journeys where we find a deeper, slower connection to the land and its people.",
            'image_url': 'https://images.unsplash.com/photo-1543730728-70986c28dade?auto=format&fit=crop&w=1200&q=80',
            'color': (180, 83, 9),
            'local_filename': 'v2_boat_villagers.jpg'
        }
    ]

    for p_info in posts_data:
        # Resolve cross-linking relations dynamically based on slug
        rel_host = None
        rel_prop = None
        rel_dest = None
        
        if p_info['slug'] == 'slow-living-kerala-tea-valleys':
            rel_host = User.objects.get(username='host_ramesh')
            rel_prop = Property.objects.filter(host=rel_host).first()
            rel_dest = destinations.get('Munnar')
        elif p_info['slug'] == 'sunrise-over-varanasi-spiritual-awakening':
            rel_host = User.objects.get(username='host_harish')
            rel_prop = Property.objects.filter(host=rel_host).first()
            rel_dest = destinations.get('Varanasi')
        elif p_info['slug'] == 'himalayan-tradition-siddu-recipe':
            rel_host = User.objects.get(username='host_tsering')
            rel_prop = Property.objects.filter(host=rel_host).first()
            rel_dest = destinations.get('Manali')
        elif p_info['slug'] == 'rhythms-river-lessons-rural-waterways':
            rel_host = User.objects.get(username='host_harish')
            rel_prop = Property.objects.filter(host=rel_host).first()
            rel_dest = destinations.get('Varanasi')

        post = BlogPost.objects.create(
            title=p_info['title'],
            slug=p_info['slug'],
            category=p_info['category'],
            content=p_info['content'],
            author=admin_user,
            host=rel_host,
            property=rel_prop,
            destination=rel_dest
        )
        img_name = p_info.get('local_filename', f"post_{post.slug}.jpg")
        img_file = download_image(p_info['image_url'], img_name, p_info['color'])
        post.featured_image.save(img_name, img_file, save=True)

    # 10. Seed Families
    print("Seeding Families, Recipes, Traditions, Stories, and Secrets...")
    
    # Fetch existing host users
    host_ramesh = User.objects.get(username='host_ramesh')
    host_harish = User.objects.get(username='host_harish')
    host_tsering = User.objects.get(username='host_tsering')
    host_vikram = User.objects.get(username='host_vikram')
    host_anil = User.objects.get(username='host_anil')
    
    families_data = [
        {
            'name': 'The Pillai Family',
            'slug': 'pillai-family',
            'host_user': host_ramesh,
            'intro': 'Cardamom forest custodians for eighty years.',
            'bio': 'Our family has tended to the hills of Munnar for generations. Every morning, the mountain mist gathers over our cardamom bushes, and we begin our day by brewing fresh tea on our wood-fire stove.',
            'languages': 'Malayalam, English, Tamil',
            'home_description': 'A traditional Kerala homestead crafted from regional stone, slate roofs, and teak wood.',
            'home_history': "Built by Ramesh's grandfather in the early 1940s as a shelter for spice farmers, it has been expanded into a warm family house over the decades.",
            'home_architecture': 'Features a central sunlit courtyard, high teak beams, and wide open-air verandas designed to catch the mountain breeze.',
            'photo_url': 'https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80',
            'home_photo_url': 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=1200&q=80',
            'photo_file': 'pillai_family.jpg',
            'src_photo_file': 'localnest_family_reunion.jpg',
            'home_photo_file': 'munnar_tea_hills_sanctuary_0.jpg'
        },
        {
            'name': 'The Sharma Family',
            'slug': 'sharma-family',
            'host_user': host_harish,
            'intro': 'Courtyard keepers in the oldest city on Earth.',
            'bio': 'A family of retired Sanskrit teachers and traditional home cooks. Our Haveli doors have been open to travelers since the late 19th century.',
            'languages': 'Hindi, English, Sanskrit',
            'home_description': 'A 150-year-old sandstone Haveli a few steps from the Ganges.',
            'home_history': "Dating back to the late 19th century, this sandstone structure has housed generations of priests, scholars, and travelers seeking Kashi's spiritual heart.",
            'home_architecture': 'Restored traditional Haveli with hand-carved pillars, and a central stone courtyard that remains cool in the summer heat.',
            'photo_url': 'https://images.unsplash.com/photo-1604881990409-b9f246db39da?auto=format&fit=crop&w=800&q=80',
            'home_photo_url': 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=1200&q=80',
            'photo_file': 'sharma_family.jpg',
            'src_photo_file': 'v2_grandmother.jpg',
            'home_photo_file': 'v2_varanasi_boat.jpg'
        },
        {
            'name': 'The Dorjee Family',
            'slug': 'dorjee-family',
            'host_user': host_tsering,
            'intro': 'Pine forest weavers and Himalayan orchard keepers.',
            'bio': 'Welcome to Old Manali. We spend our summers growing apples and wild apricots, and our winters weaving traditional woolens around the wooden hearth.',
            'languages': 'Hindi, Tibetan, English',
            'home_description': 'A stone and pine wood cottage facing the snowy peaks of Solang.',
            'home_history': "Built by Tsering's father in Old Manali, using traditional wood-and-stone Kathkuni architecture that naturally resists earthquakes.",
            'home_architecture': 'Traditional Himachali design featuring dry-stone walls layered with cedarwood beams and slate roof tiles.',
            'photo_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
            'home_photo_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=80',
            'photo_file': 'dorjee_family.jpg',
            'src_photo_file': 'family_watching_tv.jpg',
            'home_photo_file': 'solang_valley_pine_cottage_0.jpg'
        },
        {
            'name': 'The Singh Family',
            'slug': 'singh-family',
            'host_user': host_vikram,
            'intro': 'Amer block print master artisans.',
            'bio': 'We preserve traditional hand-block printing, blue pottery, and the coal-fired recipes of royal Rajputana kitchens.',
            'languages': 'Hindi, Rajasthani, English',
            'home_description': 'A royal-styled ancestral Haveli with sandstone arches.',
            'home_history': "An ancestral Haveli built in 1894 by Vikram's great-grandfather, a royal painter for the Amer court.",
            'home_architecture': 'Intricate lime plaster (Chunnam) finish, hand-painted frescoes, and a multi-level layout centered around a private zen courtyard.',
            'photo_url': 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=800&q=80',
            'home_photo_url': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80',
            'photo_file': 'singh_family.jpg',
            'src_photo_file': 'family_playing_cards.jpg',
            'home_photo_file': 'amer_palace_courtyard_haveli_0.jpg'
        },
        {
            'name': 'The Kulkarni Family',
            'slug': 'kulkarni-family',
            'host_user': host_anil,
            'intro': "Heritage keepers of Mumbai's Dadar neighborhood.",
            'bio': 'We are teachers, writers, and local historians who love showing travelers the deep, historic roots of Mumbai away from commercial hotels.',
            'languages': 'Marathi, Hindi, English',
            'home_description': 'A high-ceilinged colonial apartment full of antique books and photographs.',
            'home_history': 'Housed in a 1930s art deco building in Dadar Shivaji Park, this home has been owned by the Kulkarni family for nearly a century.',
            'home_architecture': 'Features iconic high ceilings, red oxide flooring, teakwood windows, and a balcony looking out over the local streets.',
            'photo_url': 'https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?auto=format&fit=crop&w=800&q=80',
            'home_photo_url': 'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=80',
            'photo_file': 'kulkarni_family.jpg',
            'src_photo_file': 'kulkarni_family.jpg',
            'home_photo_file': 'v2_cstm_station.jpg'
        }
    ]
    
    families = {}
    for fd in families_data:
        fam = Family.objects.create(
            name=fd['name'],
            slug=fd['slug'],
            host_user=fd['host_user'],
            intro=fd['intro'],
            bio=fd['bio'],
            languages=fd['languages'],
            home_description=fd['home_description'],
            home_history=fd['home_history'],
            home_architecture=fd['home_architecture']
        )
        src_photo = fd.get('src_photo_file', fd['photo_file'])
        photo_file = download_image(fd['photo_url'], src_photo, (201, 106, 61))
        safe_save_image(fam.photo, fd['photo_file'], photo_file, save=False)
        home_photo_file = download_image(fd['home_photo_url'], fd['home_photo_file'], (201, 106, 61))
        safe_save_image(fam.home_photo, fd['home_photo_file'], home_photo_file, save=False)
        fam.save()
        families[fam.slug] = fam
        
    # 11. Seed Recipes
    recipes_data = [
        {
            'name': 'Munnar Cardamom Puttu',
            'slug': 'munnar-cardamom-puttu',
            'ingredients': '2 cups red rice flour, 1 cup grated coconut, 1 tsp ground cardamom, water, salt.',
            'preparation_steps': '1. Mix rice flour with a splash of cardamom water until damp but crumbly.\n2. Layer flour and coconut in a cylindrical puttu steamer.\n3. Steam for 10 minutes until aromatic and serve hot with sweet mountain banana.',
            'family_memory': 'My grandmother used to boil cardamom pods on the stove, using the water to mix the flour. The scent of sweet cardamom puttu was how we knew it was morning.',
            'family': families['pillai-family'],
            'image_url': 'https://images.unsplash.com/photo-1626132647523-66f5bf380027?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'food_cardamom_puttu.jpg'
        },
        {
            'name': 'Banarasi Satvik Kachori Sabzi',
            'slug': 'banarasi-satvik-kachori',
            'ingredients': 'Wheat flour, ground lentils (urad dal), asafoetida (hing), ginger, potatoes, green chilies, coriander, ghee, oil.',
            'preparation_steps': '1. Prepare lentil-spiced stuffing with hing and ginger.\n2. Stuff in wheat dough, roll into circles, and deep-fry in pure ghee.\n3. Prepare a thin potato curry (no onion/garlic) cooked on a slow wood fire stove.',
            'family_memory': 'In our household, we cook without onion and garlic. My mother made kachoris on special festival mornings, and the entire lane would smell of pure hing and ginger.',
            'family': families['sharma-family'],
            'image_url': 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'food_kachori_sabzi.jpg'
        },
        {
            'name': 'Kullu Apple Siddu',
            'slug': 'kullu-apple-siddu',
            'ingredients': 'Wheat flour, yeast, warm water, fresh apples, wild apricot paste, sugar, cardamom, ghee.',
            'preparation_steps': '1. Knead a soft dough with yeast and let it ferment for 4 hours.\n2. Stuff with a sweet mixture of wild apples and apricot paste.\n3. Steam in a traditional steamer, then slice and dip in hot, melted ghee.',
            'family_memory': 'During cold winter snowfalls, the whole family would sit around the wood-fire hearth, eating hot siddus. The sweet apricot filling is what kept us warm.',
            'family': families['dorjee-family'],
            'image_url': 'https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'food_apple_siddu.jpg'
        },
        {
            'name': 'Slow-Coal Dal Baati Churma',
            'slug': 'slow-coal-dal-baati',
            'ingredients': 'Wheat flour, ghee, milk, mixed lentils (panchmel dal), jaggery, cardamom, almonds.',
            'preparation_steps': '1. Knead wheat flour with ghee and milk, shaping into tight rounds (baatis).\n2. Cook the baatis on slow cow-dung coals until golden brown.\n3. Serve dipped in ghee alongside a rich, slow-simmered mixed lentil dal.',
            'family_memory': "Every monsoon, we hold a family picnic in our courtyard. Vikram's father sets up the slow coals, and we spend hours turning the baatis while laughing and singing folk songs.",
            'family': families['singh-family'],
            'image_url': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'food_dal_baati.jpg'
        }
    ]
    
    recipes = {}
    for rd in recipes_data:
        rel_exp = Experience.objects.filter(host=rd['family'].host_user).first()
        rec = Recipe.objects.create(
            name=rd['name'],
            slug=rd['slug'],
            ingredients=rd['ingredients'],
            preparation_steps=rd['preparation_steps'],
            family_memory=rd['family_memory'],
            family=rd['family'],
            experience=rel_exp
        )
        img_file = download_image(rd['image_url'], rd['image_file'], (201, 106, 61))
        safe_save_image(rec.image, rd['image_file'], img_file, save=True)
        recipes[rec.slug] = rec
        
    # 12. Seed Traditions
    traditions_data = [
        {
            'name': 'Cardamom Drying Ritual',
            'slug': 'cardamom-drying',
            'description': 'Every harvest season, our family gathers in the courtyard to sort and dry cardamom pods. We dry them on slow coal burners to preserve their natural oils and green color.',
            'family': families['pillai-family'],
            'image_url': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'munnar_tea_hills_sanctuary_2.jpg'
        },
        {
            'name': 'Subah-e-Banaras Ghat Aarti',
            'slug': 'subah-e-banaras-aarti',
            'description': 'Waking up before dawn to participate in the silent morning prayer at the ghats, offering clay lamps (diyas) to the holy river Ganges.',
            'family': families['sharma-family'],
            'image_url': 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'v3_ganga_aarti.jpg'
        },
        {
            'name': 'Old Manali Kathkuni Weaving',
            'slug': 'kathkuni-weaving',
            'description': 'Weaving traditional wool blankets and caps using sheep wool on an old wooden handloom in our family basement during winter.',
            'family': families['dorjee-family'],
            'image_url': 'https://images.unsplash.com/photo-1574786198875-49f5d09fe2d2?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'tradition_kathkuni_weaving.jpg'
        },
        {
            'name': 'Amer Hand-Block Printing',
            'slug': 'amer-block-printing',
            'description': 'Using hand-carved teakwood blocks and natural plant dyes to print intricate patterns onto cotton sheets in our workshop.',
            'family': families['singh-family'],
            'image_url': 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80',
            'image_file': 'amer_palace_courtyard_haveli_2.jpg'
        }
    ]
    
    traditions = {}
    for td in traditions_data:
        trad = Tradition.objects.create(
            name=td['name'],
            slug=td['slug'],
            description=td['description'],
            family=td['family']
        )
        img_file = download_image(td['image_url'], td['image_file'], (201, 106, 61))
        safe_save_image(trad.image, td['image_file'], img_file, save=True)
        traditions[trad.slug] = trad

    # 13. Seed Voice Recordings
    voice = VoiceRecording.objects.create(
        title="Lakshmi's Story: The Cardamom Harvest",
        transcript="Every morning in Munnar, the fog is so thick you can't see the mountains. We walk into the cardamom fields by feeling our way through. My grandmother taught me that you don't harvest with your eyes, you harvest with your touch. The pods are ready when they feel soft and full. Listen to the forest, she used to say, it tells you when it is ready.",
        duration="1:42"
    )

    # 14. Seed Stories
    stories_data = [
        {
            'title': 'The Recipe that Survived Four Generations',
            'slug': 'recipe-survived-four-generations',
            'category': 'FOOD',
            'intro': 'Every winter, the Sharma family gathers in their 150-year-old Haveli courtyard, preparing a lentil-stuffed kachori that has stayed unchanged since the late 19th century.',
            'content': 'CHAPTER 1: The Kitchen that Time Forgot\nIn the narrow lanes of Kashi, the sound of bells and smell of temple incense fill the air. If you walk down the lane to Dashashwamedh, you will find a heavy wooden gate leading into the Sharma family\'s Haveli. Here, the kitchen stove is still lit with wood and slow coals.\n\nCHAPTER 2: A Mother\'s Blessing\n\'My grandmother taught my mother, and my mother taught me,\' says Harish. \'We do not use scales or books; the hand knows the weight of spiced dal and flour.\' The secret lies in the long fermentation of the dough and the pure, fragrant asafoetida (hing) sourced from old spice markets.\n\nCHAPTER 3: Sharing the Table\nSitting on low wooden stools in the courtyard, guests at LocalNest share these hot kachoris. \'Food is not just fuel,\' Harish says. \'It is how we tell our guests: you are welcome under our roof.\'',
            'family': families['sharma-family'],
            'recipe': recipes['banarasi-satvik-kachori'],
            'tradition': traditions['subah-e-banaras-aarti'],
            'voice_recording': None,
            'destination_slug': 'varanasi',
            'image_url': 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=1200&q=80',
            'local_filename': 'v3_ganga_aarti.jpg'
        },
        {
            'title': 'The Rhythms of the Cardamom Hills',
            'slug': 'rhythms-cardamom-hills',
            'category': 'HERITAGE',
            'intro': 'Lakshmi Pillai walks us through the misty cardamom paths of Munnar, explaining how the scent of green cardamom has shaped her family\'s memories.',
            'content': 'CHAPTER 1: The Mountain Mist\nMunnar wakes up before the sun. In the early morning mist, Ramesh and Lakshmi walk into their cardamom hills. The dew on the leaves is cold, and the air is thick with the scent of wild herbs and soil.\n\nCHAPTER 2: The Harvest Hands\n\'We harvest cardamom one pod at a time,\' Ramesh explains. \'It requires patience. You look for the plump, yellow-green ones.\' Sorting them is a family ritual where grandchildren and grandparents sit together on the veranda, talking and laughing.\n\nCHAPTER 3: The Smoking Hearth\nOnce sorted, the cardamom is dried in a traditional smokehouse. The slow, aromatic wood fire cures the pods, locking in their unique green color and oil. It is a slow, quiet craft that has defined the Pillai family for generations.',
            'family': families['pillai-family'],
            'recipe': recipes['munnar-cardamom-puttu'],
            'tradition': traditions['cardamom-drying'],
            'voice_recording': voice,
            'destination_slug': 'munnar',
            'image_url': 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=1200&q=80',
            'local_filename': 'v2_boat_villagers.jpg'
        }
    ]

    for sd in stories_data:
        rel_dest = Destination.objects.get(slug=sd['destination_slug'])
        rel_prop = Property.objects.filter(destination=rel_dest).first()
        rel_exp = Experience.objects.filter(host=sd['family'].host_user).first()
        
        story = Story.objects.create(
            title=sd['title'],
            slug=sd['slug'],
            category=sd['category'],
            intro=sd['intro'],
            content=sd['content'],
            family=sd['family'],
            recipe=sd['recipe'],
            tradition=sd['tradition'],
            voice_recording=sd['voice_recording'],
            destination=rel_dest,
            property=rel_prop,
            experience=rel_exp,
            moderation_status='PUBLISHED',
            visibility='PUBLIC'
        )
        img_file = download_image(sd['image_url'], sd['local_filename'], (180, 83, 9))
        safe_save_image(story.featured_image, sd['local_filename'], img_file, save=True)

    # 15. Seed Local Secrets & Recommendations
    secrets_data = [
        {
            'title': 'The 80-Year-Old Morning Chai Corner',
            'slug': 'dashashwamedh-morning-chai',
            'category': 'EAT',
            'description': 'A tiny, unnamed stall run by an elderly tea seller near the ghats, serving masala tea in fresh clay cups (kulhads).',
            'location_name': 'Dashashwamedh Ghat Steps, Varanasi',
            'image_url': 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&w=1200&q=80',
            'local_filename': 'v3_ganga_aarti.jpg',
            'why_love': 'This is not a fancy café. But for eighty years, our family has stopped here after our morning prayers. The owner, Pappu, brews the tea with fresh ginger, black pepper, and milk from local dairies.',
            'what_to_try': 'Try the Special Ginger Pepper Chai with a fresh bun-maska.',
            'when_to_go': '6:00 AM right after the Ganga Aarti.',
            'local_etiquette': 'Please discard your clay cup in the designated recycling baskets, not in the river. Talk softly as locals are performing their morning prayers.',
            'price_range': 'Budget',
            'family': families['sharma-family'],
            'visibility': 'PUBLIC'
        },
        {
            'title': 'The Whispering Pines and Apple Trail',
            'slug': 'old-manali-apple-trail',
            'category': 'WALK',
            'description': 'A quiet walking trail behind Old Manali that passes through pine orchards and leads to a hidden river crossing.',
            'location_name': 'Old Manali Forest Trail, Manali',
            'image_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=80',
            'local_filename': 'solang_valley_pine_cottage_0.jpg',
            'why_love': 'We walk here when we want to escape the main streets. It is shaded by ancient towering pine trees and passes through wild apple and apricot orchards.',
            'what_to_try': 'Take a slow, quiet walk and taste a fresh wild apricot if they are in season (July-August).',
            'when_to_go': 'Late afternoon around 4:00 PM.',
            'local_etiquette': 'Keep to the path and do not litter. Respect the villagers tending to their apple orchards.',
            'price_range': 'Free',
            'family': families['dorjee-family'],
            'visibility': 'GUESTS'
        },
        {
            'title': 'The Heritage Stone Benches of Shivaji Park',
            'slug': 'slug-shivaji-park-benches',
            'category': 'SUNSET',
            'description': 'A row of stone benches along the perimeter of Shivaji Park facing the Arabian Sea.',
            'location_name': 'Shivaji Park perimeter, Dadar, Mumbai',
            'image_url': 'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=80',
            'local_filename': 'v3_local_market.jpg',
            'why_love': 'We have sat on these benches for generations. It is where Mumbaikars come to breathe, watch kids play cricket, and see the sun set behind the Bandra-Worli Sea Link.',
            'what_to_try': 'Buy a spicy Bhel Puri from a local vendor and sit on the benches.',
            'when_to_go': '5:30 PM to 6:30 PM.',
            'local_etiquette': 'The park is heavily loved by locals; keep conversations polite and dispose of garbage responsibly.',
            'price_range': 'Free',
            'family': families['kulkarni-family'],
            'visibility': 'COMMUNITY'
        }
    ]

    for sd in secrets_data:
        secret = LocalSecret.objects.create(
            title=sd['title'],
            slug=sd['slug'],
            category=sd['category'],
            description=sd['description'],
            location_name=sd['location_name']
        )
        img_file = download_image(sd['image_url'], sd['local_filename'], (180, 83, 9))
        safe_save_image(secret.image, sd['local_filename'], img_file, save=True)
        
        SecretRecommendation.objects.create(
            local_secret=secret,
            recommended_by_user=sd['family'].host_user,
            recommended_by_family=sd['family'],
            why_love=sd['why_love'],
            what_to_try=sd['what_to_try'],
            when_to_go=sd['when_to_go'],
            local_etiquette=sd['local_etiquette'],
            price_range=sd['price_range'],
            visibility=sd['visibility'],
            is_approved=True
        )

    print("Properties, food menus, bookings, and reviews created.")
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed()
