from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Profile, HostProfile

User = get_user_model()

class BootstrapFormMixin:
    """Helper mixin to automatically apply LocalNest Tailwind form classes to all widgets"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput, forms.NullBooleanSelect)):
                field.widget.attrs['class'] = 'w-4 h-4 rounded border-outline-variant/35 text-secondary focus:ring-secondary/30 accent-secondary cursor-pointer'
            elif isinstance(field.widget, (forms.FileInput, forms.ClearableFileInput)):
                field.widget.attrs['class'] = 'w-full text-xs text-on-surface-variant file:mr-4 file:py-2 file:px-4 file:rounded-sm file:border-0 file:text-[10px] file:font-bold file:uppercase file:tracking-wider file:bg-secondary/10 file:text-secondary hover:file:bg-secondary/20 file:cursor-pointer'
            else:
                field.widget.attrs['class'] = 'ln-input'


class TouristRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone_number = forms.CharField(max_length=20, required=True, label="Phone Number")
    address = forms.CharField(max_length=255, required=False, label="Full Address")
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="A short bio about yourself")
    profile_photo = forms.ImageField(required=False, label="Profile Photo")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.Types.TOURIST
        if commit:
            user.save()
            profile = user.profile
            profile.phone_number = self.cleaned_data['phone_number']
            profile.address = self.cleaned_data['address']
            profile.bio = self.cleaned_data['bio']
            if self.cleaned_data['profile_photo']:
                profile.profile_photo = self.cleaned_data['profile_photo']
            profile.save()
        return user


class HostRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone_number = forms.CharField(max_length=20, required=True, label="Phone Number")
    address = forms.CharField(max_length=255, required=True, label="Homestay Address")
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=True, label="Tell guests about yourself and your family")
    profile_photo = forms.ImageField(required=True, label="Profile Photo")
    
    # Host specific verification fields
    government_id = forms.FileField(required=True, label="Upload Government ID (PDF, JPG, PNG)")
    selfie_photo = forms.ImageField(required=True, label="Upload Selfie for Identity Verification")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.Types.HOST
        if commit:
            user.save()
            host_profile = user.host_profile
            host_profile.phone_number = self.cleaned_data['phone_number']
            host_profile.address = self.cleaned_data['address']
            host_profile.bio = self.cleaned_data['bio']
            host_profile.profile_photo = self.cleaned_data['profile_photo']
            host_profile.government_id = self.cleaned_data['government_id']
            host_profile.selfie_photo = self.cleaned_data['selfie_photo']
            host_profile.verification_status = HostProfile.VerificationStatus.PENDING
            host_profile.save()
        return user


class TouristProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ('phone_number', 'address', 'bio', 'profile_photo', 'emergency_contact_name', 'emergency_contact_phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile


class HostProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = HostProfile
        fields = (
            'phone_number', 'address', 'bio', 'profile_photo',
            'family_intro', 'occupation', 'years_hosting',
            'response_time', 'response_rate',
            'fav_local_place', 'fav_homemade_dish',
            'emergency_contact_name', 'emergency_contact_phone',
            'government_id', 'selfie_photo'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            
            # If already verified, disable verification uploads to prevent accidental re-triggering of verification
            if self.instance.verification_status == HostProfile.VerificationStatus.APPROVED:
                self.fields['government_id'].required = False
                self.fields['selfie_photo'].required = False

    def save(self, commit=True):
        host_profile = super().save(commit=False)
        if commit:
            user = host_profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            
            # Reset verification status to pending if they changed documents
            if (('government_id' in self.changed_data and self.cleaned_data['government_id']) or 
                ('selfie_photo' in self.changed_data and self.cleaned_data['selfie_photo'])):
                host_profile.verification_status = HostProfile.VerificationStatus.PENDING
                
            host_profile.save()
        return host_profile
