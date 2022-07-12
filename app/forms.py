from datetime import date

from django import forms
from django_select2 import forms as s2forms

from app.models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        this_year = date.today().year
        year_range_birth_date = [x for x in range(this_year - 75, this_year - 18)]
        year_range_employment_date = [x for x in range(this_year - 15, this_year + 1)]
        model = Employee
        fields = '__all__'
        widgets = {
            'birth_date': forms.SelectDateWidget(years=year_range_birth_date),
            'employment_date': forms.SelectDateWidget(years=year_range_employment_date),
            'salary': forms.NumberInput(attrs={'min': 0.01})
        }


class EmployeeFilterForm(forms.Form):
    branch = forms.ChoiceField(widget=s2forms.Select2Widget)
    position = forms.ChoiceField(widget=s2forms.Select2Widget)

    def __init__(self, queryset=None, *args, **kwargs):
        super(EmployeeFilterForm, self).__init__(*args, **kwargs)
        if queryset:
            self.fields['branch'].choices = [(branch['branch'], branch['branch']) for branch in
                                             queryset.values('branch').distinct()]
            self.fields['position'].choices = [(branch['position'], branch['position']) for branch in
                                               queryset.values('position').distinct()]


class EmployeeDeleteChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return f'Имя: {obj.full_name}, Филиал: {obj.branch}, Должность: {obj.position}, ID: {obj.internal_id}'


class DeleteFilterForm(forms.Form):
    employee = EmployeeDeleteChoiceField(queryset=None, widget=s2forms.Select2Widget)

    def __init__(self, queryset=None, *args, **kwargs):
        super(DeleteFilterForm, self).__init__(*args, **kwargs)
        if queryset:
            self.fields['employee'].queryset = queryset
