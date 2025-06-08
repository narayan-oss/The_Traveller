from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import  *

User = get_user_model()


class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['user_profile_image']
        widgets = {
            'user_profile_image': forms.FileInput(attrs={
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        super(ProfileImageForm, self).__init__(*args, **kwargs)
        self.fields['user_profile_image'].label = ""  # Optional: remove label


#Registration Form

class RegistrationForm(UserCreationForm):

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    DOB = forms.DateField(
        label="Date of Birth",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    gender = forms.ChoiceField(
        label="Gender",
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'DOB', 'gender']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }



# Login Form~
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Username or Email",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Password",
    )


#password change form
class CustomPasswordChangeForm(PasswordChangeForm):

    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm New Password"
    )




# Passenger form
class PassengerForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'age', 'gender', 'travel_class']





#simple Test form
class TrainSearchForm(forms.Form):
    From = forms.CharField(label="From", max_length=100)
    To = forms.CharField(label="To", max_length=100)
    date = forms.DateField(
        label="date",
        widget=forms.DateInput(attrs={'type': 'date'})
        )
    
    def clean_date(self):
        travel_date = self.cleaned_data['date']
        if travel_date < date.today():
            raise forms.ValidationError("Date must be today or in the future.")
        return travel_date










class TestForm(forms.Form) :
    username = forms.CharField(label = "Uname", max_length = 100)
    gmail = forms.EmailField(label = "email")
    phone = forms.CharField(
            label="tel",
            widget=forms.TextInput(attrs={
                'type': 'tel',
                'pattern': '[0-9]{10}'
            })
    )

