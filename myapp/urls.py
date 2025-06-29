from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static



app_name = 'myapp'
urlpatterns = [
    path('', views.dash_view, name = 'Dash'),
    path('home/', views.home, name = 'Home'),
    path('about/', views.about_view, name = 'About'),
    path('register/', views.register_view, name = 'Signup'),
    path('login/', views.login_view, name = 'Login'),
    path('logout/', views.logout_view, name = 'Logout'),
    path('userProfile/', views.profile_view, name = 'Profile'),
    path('station-autocomplete/', views.station_autocomplete, name='station_autocomplete'),
    path('search/', views.trainSearch_view, name = 'train_search'),
    path('search/result/', views.trainSearch_result_view, name='train_search_result'),
    path('book/<int:train_id>/<int:from_id>/<int:to_id>/<str:journey_date>/', views.book_train, name='book_train'),
    path('delete/<int:index>/', views.delete_entry, name = 'delete_passenger'),
    path('pay/', views.initiate_payment, name = 'init_pay'),
    path('paid/', views.payment_success, name = 'paid'),
    path('yourbookings/', views.your_bookings_view, name = 'YourBookings'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),

    path('getName/', views.get_name, name = 'ourTest'),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
