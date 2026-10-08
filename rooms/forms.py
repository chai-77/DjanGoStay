from django import forms
from django.core.validators import MinValueValidator
from .models import Room, RoomType, HousekeepingAssignment

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
        }
        
        

class RoomTypeForm(forms.ModelForm):
    room_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    room_capacity = forms.IntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        model = RoomType
        fields = ['room_type_name', 'room_price', 'room_capacity']
        
        
class HousekeepingAssignmentForm(forms.ModelForm):
    class Meta:
        model = HousekeepingAssignment
        fields = ['room', 'assigned_to', 'assignment_date', 'is_completed']
        widgets = {
            'assignment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = (
            self.fields['assigned_to'].queryset.filter(role='housekeeping')
        )