from django import forms
from .models import Property, FoodMenu, PropertyImage, Experience
from accounts.forms import BootstrapFormMixin

class PropertyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Property
        fields = (
            'destination', 'name', 'description', 'price_per_night', 'max_guests', 
            'private_room', 'check_in_time', 'check_out_time', 
            'address', 'village', 'city', 'state', 
            'latitude', 'longitude', 'amenities', 'languages_spoken', 
            'nearby_attractions', 'house_rules'
        )
        widgets = {
            'check_in_time': forms.TimeInput(attrs={'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'house_rules': forms.Textarea(attrs={'rows': 3}),
            'nearby_attractions': forms.Textarea(attrs={'rows': 3}),
            'amenities': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure amenities are listed nicely and labeled
        self.fields['amenities'].help_text = "Select all amenities available at your homestay."
        self.fields['destination'].empty_label = "Select Destination Region"
        # Coordinate defaults for mapping picker (centered on India/generic if not set)
        if not self.initial.get('latitude'):
            self.fields['latitude'].initial = 20.5937
        if not self.initial.get('longitude'):
            self.fields['longitude'].initial = 78.9629


class FoodMenuForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = FoodMenu
        fields = (
            'breakfast_included', 'breakfast_details',
            'lunch_included', 'lunch_details',
            'dinner_included', 'dinner_details',
            'vegetarian', 'non_vegetarian', 'vegan', 'jain',
            'cooking_style', 'spice_level', 'special_dishes', 'local_desserts',
            'food_photo_1', 'food_photo_2', 'custom_notes'
        )
        widgets = {
            'custom_notes': forms.Textarea(attrs={'rows': 3}),
        }


class PropertyImageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ('image',)


class ExperienceForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Experience
        fields = ('title', 'description', 'price', 'duration', 'image', 'category')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
