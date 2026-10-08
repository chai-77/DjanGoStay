from django import forms
from django.db.models import Q

from .models import Booking, Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'address',
        ]


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'customer',
            'room',
            'check_in_date',
            'check_out_date',
            'number_of_guests',
        ]
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = self.fields['room'].queryset.filter(is_available=True)

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data:
            return cleaned_data

        room = cleaned_data.get('room')
        number_of_guests = cleaned_data.get('number_of_guests')
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')

        if room and not room.is_available:
            self.add_error('room', 'This room is marked unavailable.')

        if room and number_of_guests is not None and number_of_guests > room.room_type.room_capacity:
            self.add_error('number_of_guests', 'Number of guests exceeds the room capacity.')

        if room and check_in and check_out:
            overlaps = Booking.objects.filter(
                room=room,
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
            ).exclude(status__in=['canceled', 'checked_out'])
            if self.instance and self.instance.pk:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                self.add_error(None, 'This room is already booked for the selected dates.')

        return cleaned_data
