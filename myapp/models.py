import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager
from datetime import datetime, time
from multiselectfield import MultiSelectField
from django.utils import timezone

# Create your models here.

# Custom User Model
class CustomUser(AbstractUser):
    DOB = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Male')
    user_profile_image = models.ImageField(upload_to="profile", default='profile/4.jpg')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.username


class Train(models.Model):
    train_number = models.CharField(max_length=10, unique=True)
    train_name = models.CharField(max_length=100)
    total_seats = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.train_number} - {self.train_name}"


class Station(models.Model):
    station_code = models.CharField(max_length=10, unique=True)
    station_name = models.CharField(max_length=100)
    state = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.station_name} ({self.station_code})"


class Route(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='routes')
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='routes')
    sequence = models.PositiveIntegerField()
    platform_no = models.PositiveIntegerField(default=0)

    day_of_week = MultiSelectField(choices=DAYS_OF_WEEK, default=[0])  
    arrival_time = models.TimeField(default=time(0, 0))
    departure_time = models.TimeField(default=time(0, 0))
    departure_next_day = models.BooleanField(default=False)
    step_distance = models.FloatField(help_text="Distance in kilometers", null=True, blank=True)
    

    class Meta:
        unique_together = ('train', 'station', 'sequence', 'platform_no')
        ordering = ['train', 'sequence', 'arrival_time']

    def __str__(self):
        return f"{self.train} - {self.station} (Seq {self.sequence})"

    
    def get_distance_between_stations(train, from_station, to_station):
        routes = Route.objects.filter(train=train).order_by('sequence')
        from_route = routes.filter(station=from_station).first()
        to_route = routes.filter(station=to_station).first()

        if not from_route or not to_route:
            return -1

        # Ensure from_route comes BEFORE to_route in sequence
        if from_route.sequence >= to_route.sequence:
            return -2  

        # DIRECT CALCULATION 
        distance = to_route.step_distance - from_route.step_distance
        return distance 


class Coach(models.Model):
    COACH_TYPES = [
        ('AC', 'AC'),
        ('ECONOMY', 'ECONOMY'),
        ('SLEEPER', 'SLEEPER'),
    ]

    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='coaches')
    coach_type = models.CharField(max_length=10, choices=COACH_TYPES)
    total_seats = models.PositiveIntegerField(default=0)
    coach_seats = models.PositiveIntegerField(default=0)
    day_of_reset = models.CharField(
        max_length=14,  # Enough for "0,1,2,3,4,5,6"
        help_text="Comma-separated days (e.g. 0,2,4)",
        default='0'
    )

    def __str__(self):
        return f"{self.train.train_name} - ({self.coach_type})"
    



class BookingOrder(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    total_fare = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid')], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)





class Booking(models.Model):

    BOOKING_STATUS_CHOICES = [
        ('Waiting', 'Waiting'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    ]
    CLASS_CHOICES = [
        ('AC', 'AC'),
        ('ECONOMY', 'ECONOMY'),
        ('SLEEPER', 'SLEEPER'),
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='bookings')
    booking_order = models.ForeignKey(BookingOrder, on_delete=models.CASCADE, null=True)
    from_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='departure_bookings')
    to_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='arrival_bookings')
    journey_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(choices=GENDER_CHOICES, default='Other')
    travel_class = models.CharField(choices=CLASS_CHOICES, default='AC')
    fare = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='Waiting')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    coach_n_seat_num = models.CharField(max_length=20, blank=True)

    pnr_number = models.CharField(max_length=10, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pnr_number:
            self.pnr_number = self.generate_pnr()
        super().save(*args, **kwargs)
    
    def generate_pnr(self):
        date_part = timezone.now().strftime('%d%m')
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"{date_part}{random_part}"

    def cancel(self):

        if self.booking_status in ['Waiting', 'Confirmed']:

            self.booking_status = 'Cancelled'
            self.coach_n_seat_num = ''
            self.save()
            return True
        
        return False

    def __str__(self):
        return f"{self.user.username} - {self.train} - {self.journey_date}"
    
    



