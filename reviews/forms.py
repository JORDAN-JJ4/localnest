from django import forms
from .models import Review
from accounts.forms import BootstrapFormMixin

class ReviewForm(BootstrapFormMixin, forms.ModelForm):
    RATING_CHOICES = [(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)]

    overall_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Overall Experience")
    food_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Homemade Food Rating")
    cleanliness_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Cleanliness Rating")
    host_behaviour_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Host Behaviour Rating")
    cultural_experience_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Cultural Experience Rating")
    room_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Room Comfort Rating")
    experience_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Signature Experience Rating")
    value_rating = forms.ChoiceField(choices=RATING_CHOICES, label="Value for Money Rating")

    class Meta:
        model = Review
        fields = (
            'overall_rating', 'food_rating', 'cleanliness_rating', 
            'host_behaviour_rating', 'cultural_experience_rating', 
            'room_rating', 'experience_rating', 'value_rating',
            'photo', 'video', 'comments'
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience staying with the host family...'}),
        }
