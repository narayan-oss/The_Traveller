from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib import messages
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistrationForm, LoginForm, TestForm, CustomPasswordChangeForm, TrainSearchForm, PassengerForm, ProfileImageForm
from .models import *
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseForbidden
from django.db.models import Q
import re

# Create your views here.

def dash_view(request) :
    return render(request, "myapp/base.html")

def home(request):
    if not request.user.is_authenticated:
        return redirect('myapp:Login')
    return render(request, "myapp/home.html")

def about_view(request):
    return render(request, "myapp/about.html")

def register_view(request):

    if request.method == 'POST' :
        form = RegistrationForm(request.POST)

        if form.is_valid() :
            user = form.save()
            return redirect('myapp:Login')

    else :
        form = RegistrationForm()
    
    return render(request, 'myapp/register.html', {'form': form})



def login_view(request):

    # If user is already logged in, redirect to Home
    if request.user.is_authenticated:
        return redirect('myapp:Home')
    
    if request.method == 'POST':
        form = LoginForm(data = request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('myapp:Home')
    
    else:
        form = LoginForm()

    return render(request, 'myapp/login.html', {'form':form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "you have been logged out.")
    return redirect('myapp:Dash')



@login_required
def profile_view(request):
    # Initialize both forms with current data
    image_form = ProfileImageForm(instance=request.user)
    password_form = CustomPasswordChangeForm(request.user)

    if request.method == 'POST':
        # Handle image update
        if 'update_image' in request.POST:
            image_form = ProfileImageForm(request.POST, request.FILES, instance=request.user)
            if image_form.is_valid():
                image_form.save()
                messages.success(request, 'Profile picture updated!')
                # Reinitialize the form to clear file input
                image_form = ProfileImageForm(instance=request.user)
        
        # Handle password change
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                # Reinitialize password form
                password_form = CustomPasswordChangeForm(request.user)
    
    context = {
        'user': request.user,
        'image_form': image_form,
        'password_form': password_form,
    }
    return render(request, 'myapp/profile.html', context)





def station_autocomplete(request):
    query = request.GET.get('q', '')
    stations = Station.objects.filter(
        Q(station_name__icontains=query) | 
        Q(station_code__icontains=query)
    )[:5]
    suggestions = [{
        'name': f"{s.station_name} ({s.station_code})",
        'code': s.station_code,
        'raw_name': s.station_name
    } for s in stations]
    return JsonResponse({'results': suggestions})

def trainSearch_view(request):
    if 'preserved_form_data' in request.session:
        form = TrainSearchForm(request.session['preserved_form_data'])
        del request.session['preserved_form_data']
    elif request.method == 'POST':
        form = TrainSearchForm(request.POST)
        
        if form.is_valid():
            try:
                start_station = form.cleaned_data['From']
                end_station = form.cleaned_data['To']
                
                # Validate stations exist
                start_code, start_clean = extract_station_info(start_station)
                end_code, end_clean = extract_station_info(end_station)
                
                # Check if stations exist
                Station.objects.get(
                    Q(station_code=start_code) if start_code else 
                    Q(station_name__iexact=start_clean)
                )
                Station.objects.get(
                    Q(station_code=end_code) if end_code else 
                    Q(station_name__iexact=end_clean)
                )
                
                request.session['search_result'] = {
                    'start': start_station,
                    'end': end_station,
                    'day': form.cleaned_data['date'].weekday(),
                    'date': form.cleaned_data['date'].isoformat(),
                }
                return redirect('myapp:train_search_result')
                
            except Station.DoesNotExist as e:
                messages.error(request, "One or more stations not found")
                request.session['preserved_form_data'] = request.POST
                return redirect('myapp:train_search')
                
            except Exception as e:
                messages.error(request, "An error occurred. Please try again.")
                request.session['preserved_form_data'] = request.POST
                return redirect('myapp:train_search')
    else:
        form = TrainSearchForm()
    
    return render(request, "myapp/train_search.html", {
        "form": form,
        "show_form": True
    })

def extract_station_info(station_string):
    match = re.search(r'(.+?)\s*\((\w+)\)$', station_string)
    if match:
        return match.group(2), match.group(1).strip()
    return None, station_string.strip()



def extract_coach_info(id):

    train_instance = Train.objects.get(id=id)
    coach_instances = Coach.objects.filter(train=train_instance)

    info = {}
    for obj in coach_instances:
        info[obj.coach_type] = obj.coach_seats

    return info


def trainSearch_result_view(request):
    data = request.session.get('search_result')
    if not data:
        messages.error(request, "Search data expired. Please search again.")
        return redirect('myapp:train_search')

    try:
        start_code, start_clean = extract_station_info(data['start'])
        end_code, end_clean = extract_station_info(data['end'])
        
        # Get station objects
        start_station = Station.objects.get(
            Q(station_code=start_code) if start_code else 
            Q(station_name__iexact=start_clean)
        )
        end_station = Station.objects.get(
            Q(station_code=end_code) if end_code else 
            Q(station_name__iexact=end_clean)
        )
        
        # Find routes
        day_int = data['day']
        routes_from = Route.objects.filter(
            station=start_station,
            day_of_week__contains=str(day_int)
        )
        
        full_train = []
        for route in routes_from:
            connecting_routes = Route.objects.filter(
                train=route.train,
                station=end_station,
                step_distance__gt=route.step_distance
            )
            
            for conn_route in connecting_routes:
                full_train.append([
                    route.train.train_number,
                    route.train.train_name,
                    start_clean,
                    route.departure_time.strftime("%H:%M"),
                    end_clean,
                    conn_route.arrival_time.strftime("%H:%M"),
                    route.train.id,
                    start_station.id,
                    end_station.id,
                    extract_coach_info(route.train.id)
                ])

        return render(request, "myapp/train_search.html", {
            "form": TrainSearchForm(),
            "full_train": full_train,
            "show_form": False,
            "journey_date": data['date'],
            "start_station": start_clean,
            "end_station": end_clean
        })
        
    except Station.DoesNotExist:
        messages.error(request, "Station not found in our database")
        request.session['preserved_form_data'] = {
            'From': data['start'],
            'To': data['end'],
            'date': data['date']
        }
        return redirect('myapp:train_search')
        
    except Exception as e:
        messages.error(request, "Error processing your request")
        import traceback
        traceback.print_exc()  # Log the full error to console
        messages.error(request, f"Error: {str(e)}")  # Show actual error to user
        request.session['preserved_form_data'] = {
            'From': data['start'],
            'To': data['end'],
            'date': data['date']
        }
        return redirect('myapp:train_search')


MAX_ENTRIES = 5

# Booking view
@login_required
def book_train(request, train_id, from_id, to_id, journey_date):
    
    train = get_object_or_404(Train, id=train_id)
    start = get_object_or_404(Station, id=from_id)
    end = get_object_or_404(Station, id=to_id)

    dist = Route.get_distance_between_stations(train, start, end)

    passengers = request.session.get('passengers', [])
    request.session['general_info'] = [
        train_id,
        from_id,
        to_id,
        journey_date,
        dist,
    ]


    flag = False
    if request.method == 'POST' and len(passengers) < MAX_ENTRIES:
        form = PassengerForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            passengers.append(data)
            request.session['passengers'] = passengers
            return redirect('myapp:book_train',
                            train_id=train_id,
                            from_id=from_id,
                            to_id=to_id,
                            journey_date=journey_date,
                            )


    elif len(passengers) >= MAX_ENTRIES:
        # set Flag to true
        flag = True
        print("No more Bookings are allowed from single user!")
        form = PassengerForm()
        
    else:
        form = PassengerForm()
    
    return render(request, 'myapp/booking.html', {
            'form' : form,
            'entries' : passengers,
            'flag' : flag,
            'num': train.train_number,        
            'name': train.train_name,         
            'st': start.station_name,         
            'end': end.station_name,          
            'journey_date': journey_date,
            'MAX_ENTRIES': MAX_ENTRIES, 
        })



def delete_entry(request, index):
    try:
        # Get passengers from session
        passengers = request.session.get('passengers', [])
        
        # Debugging: Print session contents
        print("Session contents:", request.session.items())
        
        # Get general_info - now it should always exist
        general_info = request.session.get('general_info', None)
        
        if general_info is None:
            raise ValueError("General info not found in session")
            
        if len(general_info) < 4:
            raise ValueError("Incomplete general_info in session")
            
        # Validate index
        if 0 <= index < len(passengers):
            passengers.pop(index)
            request.session['passengers'] = passengers
            request.session.modified = True  # Ensure session is saved
        else:
            raise ValueError("Invalid passenger index")
            
        return redirect('myapp:book_train',
            train_id=general_info[0],
            from_id=general_info[1],
            to_id=general_info[2],
            journey_date=general_info[3],
        )
        
    except Exception as e:
        print(f"Error in delete_entry: {str(e)}")
        # Redirect to a safe page or show error
        return redirect('myapp:Home')  # Change to your appropriate fallback URL

@login_required
def initiate_payment(request):
    passengers = request.session.get('passengers', [])
    general_info = request.session.get('general_info', [])
    dist = general_info[4]

    # Calculate total fare (your existing logic)
    total_fare = 0
    times = {
        'AC' : 4, 'ECONOMY' : 3, 'SLEEPER' : 2
    }

    for data in passengers:

        multi = 0.5
        if data['age'] > 14:
            multi *= 2
        
        total_fare = total_fare + multi*dist*times[data['travel_class']]
    
    # Create booking order
    order = BookingOrder.objects.create(
        user=request.user,
        total_fare=total_fare,
        payment_status='Pending'
    )
    
    # Store order ID in session for payment completion
    request.session['pending_order'] = order.id
    return render(request, 'myapp/payment_page.html', {'order': order})




def payment_success(request):

    order_id = request.session.get('pending_order')
    if not order_id:
        return HttpResponse("Invalid session")
    
    order = BookingOrder.objects.get(id=order_id)
    order.payment_status = 'Paid'
    order.save()

    passengers = request.session.get('passengers', [])
    general_info = request.session.get('general_info', [])

    train = Train.objects.get(id=general_info[0])
    from_station = Station.objects.get(id=general_info[1])
    to_station = Station.objects.get(id=general_info[2])
    journey_date = general_info[3]
    dist = general_info[4]

    

    total_fare = 0
    times = {
        'AC' : 4, 'ECONOMY' : 3, 'SLEEPER' : 2
    }

    for data in passengers:

        multi = 0.5
        if data['age'] > 14:
            multi *= 2
        
        total_fare = total_fare + multi*dist*times[data['travel_class']]


    bookings = []
    for data in passengers:
        booking = Booking.objects.create(
            user = request.user,
            train = train,
            booking_order=order,
            from_station = from_station,
            to_station = to_station,
            journey_date = journey_date,
            name = data['name'],
            age = data['age'],
            gender = data['gender'],
            travel_class = data['travel_class'],
            fare = total_fare,
            payment_status='Paid'
            
        )
        bookings.append(booking)
    

    # Get departure and arrival times
    departure_route = Route.objects.filter(
        train=train,
        station=from_station
    ).first()
    arrival_route = Route.objects.filter(
        train=train,
        station=to_station
    ).first()

    departure_time = departure_route.departure_time.strftime("%H:%M") if departure_route else "N/A"
    arrival_time = arrival_route.arrival_time.strftime("%H:%M") if arrival_route else "N/A"
    
    # Calculate arrival date (accounting for next day arrival if needed)
    arrival_date = journey_date
    if arrival_route and arrival_route.departure_next_day:
        arrival_date += timedelta(days=1)

        
    keys_to_remove = ['pending_order', 'passengers', 'general_info']
    for key in keys_to_remove:
        if key in request.session:
            del request.session[key]


    context = {
        'booking': bookings[0],  # Use first booking for header info
        'passengers': bookings,
        'departure_time': departure_time,
        'arrival_time': arrival_time,
        'arrival_date': arrival_date,
        'distance': dist,
        'total_fare': total_fare,
        'total_fare_with_fee': total_fare + 23.60,
    }

    print(f"Saved journey_date: {booking.journey_date}")  # or log it

    return render(request, 'myapp/ticket_pdf.html', context)




# @login_required
# def payment_failed(request):
#     order_id = request.session.get('pending_order')
#     if order_id:
#         BookingOrder.objects.filter(id=order_id).delete()
#     request.session.flush()
#     return render(request, 'payment_failed.html')


def your_bookings_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    User = request.user
    current_date = timezone.now().date()
    bookings = Booking.objects.filter(user=request.user).order_by('journey_date')

    return render(request, 'myapp/yourBookings.html', {
        'groups' : bookings,
        'current_date' : current_date,
        })






def download_ticket(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user:
        return HttpResponseForbidden()
    
    # Get related bookings for the same order
    bookings = Booking.objects.filter(booking_order=booking.booking_order)
    
    # Get route info
    departure_route = Route.objects.filter(
        train=booking.train,
        station=booking.from_station
    ).first()
    arrival_route = Route.objects.filter(
        train=booking.train,
        station=booking.to_station
    ).first()

    context = {
        'booking': booking,
        'passengers': bookings,
        'departure_time': departure_route.departure_time.strftime("%H:%M") if departure_route else "N/A",
        'arrival_time': arrival_route.arrival_time.strftime("%H:%M") if arrival_route else "N/A",
        'distance': Route.get_distance_between_stations(booking.train, booking.from_station, booking.to_station),
        'total_fare': booking.booking_order.total_fare,
        'total_fare_with_fee': booking.booking_order.total_fare + 23.60,
    }

    # Render HTML
    html_string = render_to_string('myapp/ticket_pdf.html', context)
    html = HTML(string=html_string)
    
    # Generate PDF
    result = html.write_pdf()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{booking.booking_order.pnr_number}.pdf"'
    response.write(result)
    
    return response




def cancel_booking(request, booking_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.journey_date < timezone.now().date():
        messages.error(request, "Cannot cancel past bookings")
    elif booking.booking_status == 'Cancelled':
        messages.warning(request, "Booking is already cancelled")
    elif booking.cancel():
        messages.success(request, "Booking cancelled successfully")
    else:
        messages.error(request, "Unable to cancel booking")
    
    return redirect('myapp:YourBookings')








def get_name(request) :
    print("get_name view called")
    if request.method == 'POST' :
        form = TestForm(request.POST)

        if form.is_valid() : 
            print("Thanks for correct Data !")
            # we can preprocss the data here
            # redirect to new URL
            return HttpResponseRedirect("/")

    else :
        form = TestForm()
    
    return render(request, 'myapp/name.html', {"form" : form})
    