# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# disable undefined variable error, which erroneously triggers
# on forward declarations of classes in lambdas
# pylint: disable=E0602

import graphene

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.graphql_base import OdooObjectType

class Property(OdooObjectType):
    code = graphene.String(required=True)
    name = graphene.String(required=True)

class Country(OdooObjectType):
    code = graphene.String(required=True)
    name = graphene.String(required=True)

class Nationality(OdooObjectType):
    code = graphene.String(required=True)
    name = graphene.String(required=True)

class Passport(OdooObjectType):
    active = graphene.Boolean(required=True)
    passport = graphene.String(required=True)
    issue_date = graphene.Date(required=True)
    expire_date = graphene.Date(required=True)

class Partner(OdooObjectType):
    name = graphene.String(required=True)
    street = graphene.String()
    street2 = graphene.String()
    city = graphene.String()
    zip = graphene.String()
    property_id = graphene.Field(Property)
    country = graphene.Field(Country)
    nationality = graphene.Field(Nationality)
    email = graphene.String()
    phone = graphene.String()
    is_company = graphene.Boolean(required=True)
    is_guest = graphene.Boolean(required=True)
    is_group = graphene.Boolean(required=True)
    contacts = graphene.List(graphene.NonNull(lambda: Partner), required=True)
    passport = graphene.List(Passport)

    @staticmethod
    def resolve_property_id(root, info):
        return root.property_id or None

    @staticmethod
    def resolve_country(root, info):
        return root.country_id or None

    @staticmethod
    def resolve_nationality(root,info):
        return root.nationality_id or None

    @staticmethod
    def resolve_contacts(root, info):
        return root.child_ids

    @staticmethod
    def resolve_passport(root, info):
        return root.passport_id or None
class Query(graphene.ObjectType):
    all_partners = graphene.List(
        graphene.NonNull(Partner),
        required=True,
        companies_only=graphene.Boolean(),
        guests_only=graphene.Boolean(),
        limit=graphene.Int(),
        offset=graphene.Int(),
    )

    reverse = graphene.String(
        required=True,
        description="Reverse a string",
        word=graphene.String(required=True),
    )
    error_example = graphene.String()

    @staticmethod
    def resolve_all_partners(root, info, companies_only=False,
    guests_only=False, groupsonly=False, limit=None, offset=None):
        domain = []
        if companies_only:
            domain.append(("is_company", "=", True))
        elif guests_only:
            domain.append(("is_guest", "=", True))
        elif groupsonly:
            domain.append(("is_group", "=", True))
        return info.context["env"]["res.partner"].search(
            domain, limit=limit, offset=offset
        )

    @staticmethod
    def resolve_reverse(root, info, word):
        return word[::-1]

    @staticmethod
    def resolve_error_example(root, info):
        raise UserError(_("UserError example"))

class CreatePartner(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        is_company = graphene.Boolean()
        is_guest = graphene.Boolean()
        is_group = graphene.Boolean()
        raise_after_create = graphene.Boolean()

    Output = Partner

    @staticmethod
    def mutate(self, info, name, email, is_company=False,
    is_guest=False, is_group=False, raise_after_create=False):
        env = info.context["env"]
        partner = env["res.partner"].create(
            {"name": name, "email": email, "is_company": is_company, 
            "is_guest": is_guest,"is_group": is_group}
        )
        if raise_after_create:
            raise UserError(_("as requested"))
        return partner

class Mutation(graphene.ObjectType):
    create_partner = CreatePartner.Field(
        description="Documentation of CreatePartner")


schema = graphene.Schema(query=Query, mutation=Mutation)
