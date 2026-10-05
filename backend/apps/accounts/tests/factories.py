"""factory-boy factories for accounts."""

import factory

from apps.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@vrms.test")
    name = factory.Faker("name")
    mobile_no = factory.Sequence(lambda n: f"+9190000{n:05d}")
    role = User.Role.CUSTOMER
    password = factory.django.Password("Test@12345")
