from django.http import HttpResponse, Http404, HttpResponseRedirect
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.contrib.auth.models import User, Permission, Group
from django.db import IntegrityError
from django.contrib import messages
from django.conf import settings

from django.urls import reverse

import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from urllib.parse import urlparse, urljoin

EMFSSO_AUTH_URL = 'https://identity.emfcamp.org/oauth2/authorize'
EMFSSO_TOKEN_URL = 'https://identity.emfcamp.org/oauth2/token'
EMFSSO_USERINFO_URL = 'https://identity.emfcamp.org/oauth2/userinfo'


@login_required
def userprofile(request):
    may_edit_users = request.user.has_perm("auth.add_user")
    return render(request, "registration/profile.html",
                  {'may_edit_users': may_edit_users})


class PasswordChangeForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput,
                               label="Current password")
    newpassword = forms.CharField(widget=forms.PasswordInput,
                                  label="New password",
                                  min_length=7, max_length=80)
    passwordagain = forms.CharField(widget=forms.PasswordInput,
                                    label="New password again",
                                    min_length=7, max_length=80)

    def clean(self):
        try:
            if self.cleaned_data['newpassword'] \
               != self.cleaned_data['passwordagain']:
                raise forms.ValidationError(
                    "You must enter the same new password in both fields")
        except KeyError:
            pass
        return self.cleaned_data


@login_required
def pwchange(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if request.user.check_password(cd['password']):
                request.user.set_password(cd['newpassword'])
                request.user.save()
                messages.info(request,"Password changed")
                return HttpResponseRedirect(
                    reverse("user-profile-page"))
            else:
                messages.info(request,"Incorrect password - changes not made")
            return HttpResponseRedirect(reverse("password-change-page"))
    else:
        form = PasswordChangeForm()
    return render(request, 'registration/password-change.html',
                  context={'form': form})


class UserForm(forms.Form):
    username = forms.CharField(label="Username")
    firstname = forms.CharField(label="First name")
    lastname = forms.CharField(label="Last name")
    newpassword = forms.CharField(widget=forms.PasswordInput,
                                  label="New password",
                                  min_length=7, max_length=80,
                                  required=False)
    passwordagain = forms.CharField(widget=forms.PasswordInput,
                                    label="New password again",
                                    min_length=7, max_length=80,
                                    required=False)
    privileged = forms.BooleanField(
        label="Tick if user may add/edit other users",
        required=False)

    def clean(self):
        try:
            if self.cleaned_data['newpassword'] \
               != self.cleaned_data['passwordagain']:
                raise forms.ValidationError(
                    "You must enter the same new password in both fields")
        except KeyError:
            pass
        return self.cleaned_data


@permission_required("auth.add_user")
def users(request):
    u = User.objects.all()

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                user = User.objects.create_user(
                    cd['username'],
                    password=cd['newpassword'] if cd['newpassword'] else None)
                if not cd['newpassword']:
                    messages.warning(request, "New user has no password set "
                                     "and will not be able to log in")
                user.first_name = cd['firstname']
                user.last_name = cd['lastname']
                if cd['privileged']:
                    permission = Permission.objects.get(codename="add_user")
                    user.user_permissions.add(permission)
                user.save()
                messages.info(
                    request, "Added new user '{}'".format(cd['username']))
                return HttpResponseRedirect(reverse("userlist"))
            except IntegrityError:
                form.add_error(None, "That username is already in use")
    else:
        form = UserForm()

    return render(request, 'registration/userlist.html',
                  {'users': u, 'form': form})


@permission_required("auth.add_user")
def userdetail(request, userid):
    try:
        u = User.objects.get(id=int(userid))
    except User.DoesNotExist:
        raise Http404

    if request.method == 'POST' and (u.is_staff or u.is_superuser):
        messages.error(request, "You cannot edit users marked as 'staff' "
                       "or 'superuser' here; you must use the admin interface "
                       "instead")
        return HttpResponseRedirect(reverse("userlist"))

    if request.method == 'POST' and 'update' in request.POST:
        form = UserForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if cd['newpassword'] and u == request.user:
                messages.info(request, "You can't change your own password "
                              "here; use the password change page instead")
                return HttpResponseRedirect(reverse("userlist"))
            try:
                if cd['username'] != u.username:
                    u.username = cd['username']
                if cd['firstname'] != u.first_name:
                    u.first_name = cd['firstname']
                if cd['lastname'] != u.last_name:
                    u.last_name = cd['lastname']
                if cd['newpassword']:
                    u.set_password(cd['newpassword'])
                if cd['privileged'] and not u.has_perm("auth.add_user"):
                    permission = Permission.objects.get(codename="add_user")
                    u.user_permissions.add(permission)
                if not cd['privileged'] and u.has_perm("auth.add_user"):
                    permission = Permission.objects.get(codename="add_user")
                    u.user_permissions.remove(permission)
                u.save()
                messages.info(request, "User details updated")
                return HttpResponseRedirect(reverse("userlist"))
            except IntegrityError:
                form.add_error("username", "That username is already in use")
    elif request.method == 'POST' and 'delete' in request.POST:
        if u == request.user:
            messages.error(request, "You cannot delete yourself")
            return HttpResponseRedirect(reverse("userlist"))
        u.delete()
        messages.info(request, "User '{}' removed".format(u.username))
        return HttpResponseRedirect(reverse("userlist"))
    else:
        form = UserForm(initial={
            'username': u.username,
            'firstname': u.first_name,
            'lastname': u.last_name,
            'privileged': u.has_perm('auth.add_user'),
        })

    return render(request, 'registration/userdetail.html',
                  {'form': form, 'formuser': u})


# When developing the EMF SSO integration locally, you must set the
# environment variable OAUTHLIB_INSECURE_TRANSPORT=1
def _emfsso_session(request, state=None):
    kwargs = {}
    if state:
        kwargs['state'] = state

    return OAuth2Session(
        settings.EMFSSO_CLIENT_ID,
        redirect_uri=request.build_absolute_uri(reverse("emfsso-callback")),
        scope=["profile"], **kwargs)


def emfsso_login(request):
    if not settings.EMFSSO_ENABLED:
        messages.error(request, "EMF SSO is not configured")
        return redirect("login-page")

    session = _emfsso_session(request)

    authorization_url, request.session['emfsso-auth-state'] = \
        session.authorization_url(EMFSSO_AUTH_URL)

    _next = request.GET.get('next')
    # Check that _next is sensible before storing it for use after the
    # oauth2 callback
    if _next:
        base = request.build_absolute_uri()
        ref_url = urlparse(base)
        test_url = urlparse(urljoin(base, _next))
        if test_url.scheme in ("http", "https") \
           and ref_url.netloc == test_url.netloc:
            request.session['emfsso-next'] = _next
        else:
            messages.error(request, "Invalid 'next' field in query string")
            return redirect("login-page")

    return redirect(authorization_url)


def emfsso_callback(request):
    if not request.session.get('emfsso-auth-state'):
        messages.error(request, "EMF SSO callback called unexpectedly")
        return redirect("login-page")

    session = _emfsso_session(
        request, state=request.session['emfsso-auth-state'])

    _next = request.session.get('emfsso-next')

    try:
        token = session.fetch_token(
            EMFSSO_TOKEN_URL,
            client_id=settings.EMFSSO_CLIENT_ID,
            client_secret=settings.EMFSSO_CLIENT_SECRET,
            authorization_response=request.build_absolute_uri())
    except OAuth2Error as e:
        messages.error(request, f"EMF SSO error: {e}")
        return redirect("login-page")

    del request.session['emfsso-auth-state'], request.session['emfsso-next']

    profile = session.get(EMFSSO_USERINFO_URL).json()

    username = profile['nickname']
    groups = profile['groups']
    email = profile['email']
    full_name = profile['name']

    if "team_bar" not in groups:
        messages.error(request, "EMF SSO: You are not a member of Team Bar")
        return redirect("login-page")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username)

    user.is_staff = True
    user.is_active = True

    user.email = email
    # This is horrible; it's a consequence of names being split into
    # first_name and last_name in the django User model.
    names = full_name.rsplit(' ', maxsplit=1)
    if len(names) > 1:
        user.first_name, user.last_name = names
    else:
        user.first_name = ''
        user.last_name = full_name
    user.save()

    try:
        bar_group = Group.objects.get(name="Bar")
        user.groups.add(bar_group)
    except Group.DoesNotExist:
        messages.warning(request, "Could not add user to group 'Bar': the "
                         "group does not exist")

    login(request, user)
    messages.info(request, f"Logged in as {user} via EMF SSO")

    # This flag is inserted into template contexts by the emfsso_user
    # context processor. It can be used to disable "change password"
    # links, etc.
    request.session["emfsso-user"] = True

    if _next:
        return HttpResponseRedirect(_next)
    return redirect("frontpage")
