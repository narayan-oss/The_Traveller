from django.contrib import messages
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistrationForm, LoginForm, TestForm, CustomPasswordChangeForm, TrainSearchForm, PassengerForm, ProfileImageForm
from .models import *
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect

# Create your views here.

def dash_view(request) :
    return render(request, "myapp/base.html")

@login_required
def home(request) :
    return render(request, "myapp/home.html")


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




def trainSearch_view(request):

    if(request.method == 'POST'):
        form = TrainSearchForm(request.POST)
        
        if(form.is_valid()):

            # used cleaned data instead of direct form.From or form.To
            start_station = form.cleaned_data['From']
            end_station = form.cleaned_data['To']
            day = form.cleaned_data['date'].weekday()
            date = form.cleaned_data['date']

            
            # Save results in session temporarily
            request.session['search_result'] = {
                'start': start_station,
                'end': end_station,
                'day': day,
                'date': date.isoformat(),  # convert to string
            }
            return redirect('myapp:train_search_result')  # go to a clean GET view

    else:
        form = TrainSearchForm()
        
    
    return render(request, "myapp/train_search.html", {"form" : form, "show_form" : True})



def trainSearch_result_view(request):
    data = request.session.get('search_result')
    full_train = []

    if data:
        start_station = data['start']
        end_station = data['end']
        # day_int = data['date'].weekday()
        day_int = data['day']
        journey_date = data['date']

        start_station_obj = Station.objects.get(station_name=start_station)

        half_route = Route.objects.filter(station__station_name=start_station, day_of_week__contains=str(day_int))
        half_train = {r.train.train_number: [r.step_distance, r.departure_time] for r in half_route}
        

        for key, value in half_train.items():
            full_route = Route.objects.filter(train__train_number=key, station__station_name=end_station)
            
            for route in full_route:
                if route.step_distance > value[0]:
                    
                    trn = route.train.train_number
                    v = [trn, route.train.train_name, start_station, str(value[1]), end_station, str(route.arrival_time)
                         , route.train.id, start_station_obj.id, route.station.id]

                    full_train.append(v)

    form = TrainSearchForm()
    print(full_train)

    return render(request, "myapp/train_search.html", {"form": form, "full_train": full_train, "show_form" : False, "journey_date": journey_date,
        "start_station": start_station,
        "end_station": end_station
        })



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



    for data in passengers:
        Booking.objects.create(
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
    
    # clear all session data
    request.session.flush()
    return render(request, 'myapp/booking_cnf.html')




# @login_required
# def payment_failed(request):
#     order_id = request.session.get('pending_order')
#     if order_id:
#         BookingOrder.objects.filter(id=order_id).delete()
#     request.session.flush()
#     return render(request, 'payment_failed.html')


def your_bookings_view(request):

    User = request.user

    groups = Booking.objects.filter(user = User)

    return render(request, 'myapp/yourBookings.html', {'groups' : groups})




















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
    