import datetime
import logging

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResUsersRole(models.Model):
    _name = "res.users.role"
    _inherits = {"res.groups": "group_id"}
    _description = "User role"

    group_id = fields.Many2one(
        comodel_name="res.groups",
        required=True,
        ondelete="cascade",
        readonly=True,
        string="Associated group",
    )
    line_ids = fields.One2many(
        comodel_name="res.users.role.line", inverse_name="role_id", string="Role lines"
    )
    user_ids = fields.One2many(
        comodel_name="res.users", string="Users list", compute="_compute_user_ids"
    )
    group_category_id = fields.Many2one(
        related="group_id.category_id",
        default=lambda cls: cls.env.ref("hms.ir_module_category_role").id,
        string="Associated category",
        help="Associated group's category",
    )

    @api.depends("line_ids.user_id")
    def _compute_user_ids(self):
        for role in self:
            role.user_ids = role.line_ids.mapped("user_id")

    @api.model
    def create(self, vals):
        new_record = super(ResUsersRole, self).create(vals)
        new_record.update_users()
        return new_record

    def write(self, vals):
        res = super(ResUsersRole, self).write(vals)
        self.update_users()
        return res

    def unlink(self):
        users = self.mapped("user_ids")
        res = super(ResUsersRole, self).unlink()
        users.set_groups_from_roles(force=True)
        return res

    def update_users(self):
        """Update all the users concerned by the roles identified by `ids`."""
        users = self.mapped("user_ids")
        users.set_groups_from_roles()
        return True

    @api.model
    def cron_update_users(self):
        logging.info("Update user roles")
        self.search([]).update_users()


class ResUsersRoleLine(models.Model):
    _name = "res.users.role.line"
    _description = "Users associated to a role"

    role_id = fields.Many2one(
        comodel_name="res.users.role", required=True, string="Role", ondelete="cascade"
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        string="User",
        domain=[("id", "!=", SUPERUSER_ID)],
        ondelete="cascade",
    )
    date_from = fields.Date("From")
    date_to = fields.Date("To")
    is_enabled = fields.Boolean("Enabled", compute="_compute_is_enabled")
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.user.company_id
    )

    @api.constrains("user_id", "company_id")
    def _check_company(self):
        for record in self:
            if (
                record.company_id
                and record.company_id != record.user_id.company_id
                and record.company_id not in record.user_id.company_ids
            ):
                raise ValidationError(
                    _('User "{}" does not have access to the company "{}"').format(
                        record.user_id.name, record.company_id.name
                    )
                )

    @api.depends("date_from", "date_to")
    def _compute_is_enabled(self):
        today = datetime.date.today()
        for role_line in self:
            role_line.is_enabled = True
            if role_line.date_from:
                date_from = role_line.date_from
                if date_from > today:
                    role_line.is_enabled = False
            if role_line.date_to:
                date_to = role_line.date_to
                if today > date_to:
                    role_line.is_enabled = False

    def unlink(self):
        users = self.mapped("user_id")
        res = super(ResUsersRoleLine, self).unlink()
        users.set_groups_from_roles(force=True)
        return res


class Users(models.Model):
    _inherit = "res.users"

    property_id = fields.Many2many("hms.property",
                                   'property_id',
                                   'user_id',
                                   "hms_property_user_rel",
                                   "Property",
                                   store=True,
                                   track_visibility=True)

    role_line_ids = fields.One2many(
        comodel_name="res.users.role.line",
        inverse_name="user_id",
        string="Role lines",
        default=lambda self: self._default_role_lines(),
    )
    role_ids = fields.One2many(
        comodel_name="res.users.role", string="Roles", compute="_compute_role_ids"
    )

    @api.model
    def _default_role_lines(self):
        default_user = self.env.ref("base.default_user", raise_if_not_found=False)
        default_values = []
        if default_user:
            for role_line in default_user.role_line_ids:
                default_values.append(
                    {
                        "role_id": role_line.role_id.id,
                        "date_from": role_line.date_from,
                        "date_to": role_line.date_to,
                        "is_enabled": role_line.is_enabled,
                    }
                )
        return default_values

    @api.depends("role_line_ids.role_id")
    def _compute_role_ids(self):
        for user in self:
            user.role_ids = user.role_line_ids.mapped("role_id")

    @api.model
    def create(self, vals):
        new_record = super(Users, self).create(vals)
        new_record.set_groups_from_roles()
        return new_record

    def write(self, vals):
        res = super(Users, self).write(vals)
        self.sudo().set_groups_from_roles()
        return res

    def _get_enabled_roles(self):
        return self.role_line_ids.filtered(
            lambda rec: rec.is_enabled
            and (not rec.company_id or rec.company_id == rec.user_id.company_id)
        )

    def set_groups_from_roles(self, force=False):
        """Set (replace) the groups following the roles defined on users.
        If no role is defined on the user, its groups are let untouched unless
        the `force` parameter is `True`.
        """
        role_groups = {}
        # We obtain all the groups associated to each role first, so that
        # it is faster to compare later with each user's groups.
        for role in self.mapped("role_line_ids.role_id"):
            role_groups[role] = list(
                set(
                    role.group_id.ids
                    + role.implied_ids.ids
                    + role.trans_implied_ids.ids
                )
            )
        for user in self:
            if not user.role_line_ids and not force:
                continue
            group_ids = []
            for role_line in user._get_enabled_roles():
                role = role_line.role_id
                group_ids += role_groups[role]
            group_ids = list(set(group_ids))  # Remove duplicates IDs
            groups_to_add = list(set(group_ids) - set(user.groups_id.ids))
            groups_to_remove = list(set(user.groups_id.ids) - set(group_ids))
            to_add = [(4, gr) for gr in groups_to_add]
            to_remove = [(3, gr) for gr in groups_to_remove]
            groups = to_remove + to_add
            if groups:
                vals = {"groups_id": groups}
                super(Users, user).write(vals)
        return True