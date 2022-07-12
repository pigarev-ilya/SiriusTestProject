from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView, UpdateView, DeleteView
from openpyxl import Workbook

from app.forms import EmployeeForm, EmployeeFilterForm, DeleteFilterForm
from app.models import Employee
import datetime
import apiclient
import httplib2
from oauth2client.service_account import ServiceAccountCredentials


class EmployeeMainFormView(TemplateView):
    template_name = "form.html"
    form_create = EmployeeForm
    filter_form = EmployeeFilterForm
    filter_delete_form = DeleteFilterForm
    queryset = Employee.objects.all()

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type")
        if form_type == 'create':
            form = self.form_create(data=request.POST)
            if form.is_valid():
                form.save()
                messages.info(self.request, 'Сотрудник добавлен')
                return redirect(reverse('home'))
        if form_type == 'list':
            form = self.filter_form(data=request.POST, queryset=self.queryset)
            if form.is_valid():
                branch = form.cleaned_data['branch']
                position = form.cleaned_data['position']
                messages.info(self.request, 'Выборка успешно сформирована')
                return redirect(reverse('employees-list', args=[branch, position]))
        if form_type == 'delete':
            form = self.filter_delete_form(data=request.POST, queryset=self.queryset)
            if form.is_valid():
                form.cleaned_data['employee'].delete()
                messages.info(self.request, 'Cотрудник удален')
                return redirect(reverse('home'))
        if form_type == 'update':
            form = self.filter_delete_form(data=request.POST, queryset=self.queryset)
            if form.is_valid():
                employee_id = form.cleaned_data['employee'].id
                return redirect(reverse('employee-update', args=[employee_id]))
        else:
            messages.info(self.request, form.errors)
            return redirect(reverse('home'))

    def get_context_data(self, **kwargs):
        context = {'form_create': self.form_create, 'filter_form': self.filter_form(self.queryset),
                   'filter_delete_form': self.filter_delete_form(self.queryset)}
        return context


class EmployeeUpdateFormView(SuccessMessageMixin, UpdateView):
    model = Employee
    template_name = "update.html"
    success_url = '/'
    fields = '__all__'
    success_message = 'Данные сотрудника обновлены'


class EmployeeDeleteView(DeleteView):
    model = Employee
    success_url = '/'


class CreateExcelView(View):
    def get(self, request, *args, **kwargs):
        queryset = Employee.objects.all()
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['id', 'Филиал', 'Должность', 'Имя', 'Зарплата', 'Дата трудоустройства', 'Дата рождения'])
        link = f'static/reports/{datetime.date.today()}.xlsx'
        for obj in queryset:
            sheet.append([obj.internal_id, obj.branch, obj.position,
                          obj.full_name, obj.salary, obj.employment_date, obj.birth_date])
        workbook.save(link)
        return render(request, template_name='link_excel.html', context={'link': link})


class SubmitGoogleSheetsView(View):
    def get(self, request, *args, **kwargs):
        CREDENTIALS_FILE = settings.CREDENTIALS_FILE
        queryset = Employee.objects.all()
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
        title = f'Отчет по сотрудникам от {datetime.date.today()}'
        spreadsheet = service.spreadsheets().create(body={
            'properties': {'title': title, 'locale': 'ru_RU'}}).execute()
        driveService = apiclient.discovery.build('drive', 'v3', http=httpAuth)
        driveService.permissions().create(
            fileId=spreadsheet['spreadsheetId'],
            body={'type': 'anyone', 'role': 'reader'},
            fields='id'
        ).execute()
        values = [['id', 'Филиал', 'Должность', 'Имя', 'Зарплата', 'Дата трудоустройства', 'Дата рождения']]
        # Если база большая лучше разбить на участки с учетом размера списка и квоты API
        for obj in queryset:
            values.append([obj.internal_id, obj.branch, obj.position,
                           obj.full_name, float(obj.salary), str(obj.employment_date), str(obj.birth_date)])
        body = {
            'values': values
        }
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet['spreadsheetId'], valueInputOption="USER_ENTERED", body=body,
            range="Лист1").execute()
        return render(request, template_name='link_gs.html', context={'link': spreadsheet['spreadsheetUrl']})


class EmployeeListView(TemplateView):
    template_name = "list.html"

    def get_context_data(self, branch, position, **kwargs):
        data = Employee.objects.filter(branch=branch, position=branch).all()
        context = {'data': data}
        return context
