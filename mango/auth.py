from mango import Model, database as db
from django.utils.encoding import smart_str
from django.contrib import auth
from django.contrib.auth.models import UNUSABLE_PASSWORD, get_hexdigest, check_password
import datetime
import urllib

class User(Model):
    collection = db.users

    def __unicode__(self):
        return self.username

    def get_absolute_url(self):
        return "/users/%s/" % urllib.quote(smart_str(self.username))

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_full_name(self):
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)

    def check_password(self, raw_password):
        if '$' not in self.password:
            is_correct = (self.password == get_hexdigest('md5', '', raw_password))
            if is_correct:
                self.set_password(raw_password)
                self.save()
            return is_correct
        return check_password(raw_password, self.password)

    def set_unusable_password(self):
        self.password = UNUSABLE_PASSWORD

    def has_usable_password(self):
        return self.password != UNUSABLE_PASSWORD

    def get_group_permissions(self):
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                permissions.update(backend.get_group_permissions(self))
        return permissions

    def get_all_permissions(self):
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_all_permissions"):
                permissions.update(backend.get_all_permissions(self))
        return permissions

    def has_perm(self, perm):
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        for backend in auth.get_backends():
            if hasattr(backend, "has_perm"):
                if backend.has_perm(self, perm):
                    return True
        return False

    def has_perms(self, perm_list):
        for perm in perm_list:
            if not self.has_perm(perm):
                return False
        return True

    def has_module_perms(self, app_label):
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        for backend in auth.get_backends():
            if hasattr(backend, "has_module_perms"):
                if backend.has_module_perms(self, app_label):
                    return True
        return False

    def get_and_delete_messages(self):
        return []

    def email_user(self, subject, message, from_email=None):
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email])

    def get_profile(self):
        raise SiteProfileNotAvailable

    @classmethod
    def create_user(cls, username, email, password=None):
        "Creates and saves a User with the given username, e-mail and password."
        now = datetime.datetime.now()
        user = cls({'username': username, 
                    'first_name': '', 
                    'last_name': '', 
                    'email': email.strip().lower(), 
                    'password': 'placeholder', 
                    'is_staff': False, 
                    'is_active': True, 
                    'is_superuser': False, 
                    'last_login': now,
                    'date_joined': now,
                    })
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

class Backend(object):
    """
    Authenticates against a mongodb 'users' collection.
    """
    def authenticate(self, username=None, password=None):
        user = User.get({'username': username})
        if user:
            if user.check_password(password):
                return user
        return None

    def get_user(self, user_id):
        return User.get({'_id': user_id})

    
