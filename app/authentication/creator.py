import uuid
from typing import Optional, Union

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Role, User
from .tasks import send_verification_mail
from .exceptions import *

from .mailboxlayer import validate_email

from django.conf import settings


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            'id'
        ]


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role'
        ]


class UserCreateDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class UserCreator:
    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: int,
        **kwargs
    ) -> None:

        self.data = {
            'username': username,
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            **kwargs
        }

        self.verification_url = 'http://localhost:8080/verify/'
        self.extra_fields = True if len(kwargs) > 0 else False

    def __call__(self) -> User:
        user = self.create()

        if user is None:
            raise ValidationError("Can`t create user")

        if settings.DEBUG is False:
            if validate_email(self.data['email']):
                self.verify_email(
                    user.email_verification_code,
                    self.verification_url
                )
                self.subscribe()
            else:
                raise EmailNotValid("Your email is not valid.")
        else:
            self.verify_email(
                user.email_verification_code,
                self.verification_url
            )
            self.subscribe()
        return user

    def create(self):
        try:
            if int(self.data['role']) == 1:
                self.user = self.get_user() or self.create_performer()

            elif int(self.data['role']) == 2:
                self.user = self.get_user() or self.create_employer()

            else:
                raise UserRoleError(f"No role with such id({self.data['role']})")
            return self.user
        except ValueError:
            raise UserRoleError('Role must be integer like')

    def create_performer(self) -> Optional[User]:
        serializer = UserCreateDetailSerializer(data=self.data)

        if serializer.is_valid():
            serializer.save()

            return serializer.instance
        else:
            raise ValidationError(serializer.errors)

    def create_employer(self) -> Optional[User]:
        serializer = UserCreateDetailSerializer(data=self.data)

        if serializer.is_valid():
            serializer.save()

            return serializer.instance
        else:
            raise ValidationError(serializer.errors)

    def get_user(self) -> User:
        return User.objects.get_or_none(email=self.data['email'])

    def verify_email(
        self,
        verification_code: uuid,
        verification_link: str
    ) -> Union[int, None]:

        _mail = send_verification_mail.delay(
            self.data['email'],
            verification_link,
            verification_code
        )

        return _mail.collect()

    def subscribe(self):
        pass
