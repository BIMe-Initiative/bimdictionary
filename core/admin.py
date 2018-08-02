from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.flatpages.models import FlatPage

from froala_editor.widgets import FroalaEditor

from .models import TextBlock
from .models import UserProfile


class TextBlockForm(forms.ModelForm):
    text = forms.CharField(widget=FroalaEditor)

    class Meta:
        model = TextBlock
        fields = ['slug', 'text']


@admin.register(TextBlock)
class TextBlockAdmin(admin.ModelAdmin):
    form = TextBlockForm


class FlatPageForm(forms.ModelForm):
    content = forms.CharField(widget=FroalaEditor)

    class Meta:
        model = FlatPage
        fields = ['url', 'title', 'content', 'template_name', 'sites']


class FlatPageAdmin(admin.ModelAdmin):
    form = FlatPageForm


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = UserProfile
        fields = ['email']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = UserProfile
        fields = ['email', 'password', 'is_active', 'is_admin']

    def clean_password(self):
        return self.initial["password"]


@admin.register(UserProfile)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    fieldsets = (
        (None, {
            'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_admin',
                'is_superuser',
                'groups')}),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    filter_horizontal = []
    form = UserChangeForm
    list_display = ['__str__', 'first_name', 'last_name']
    list_filter = ['is_admin', 'last_login', 'date_joined']
    ordering = ['email']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['date_joined', 'last_login']

