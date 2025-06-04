from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Train)
admin.site.register(Coach)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Booking)
admin.site.register(BookingOrder)



