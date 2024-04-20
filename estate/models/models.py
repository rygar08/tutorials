from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.odoo import api, _
from odoo.odoo.exceptions import UserError, ValidationError


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "id desc"

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', _('Document type name must be unique')),
        ('positive_expected_price', 'CHECK(expected_price > 0)', _('The expected price must be positive')),
    ]

    def _default_date_availability(self):
        return fields.Date.context_today(self) + relativedelta(months=3)

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date("Available From", default=lambda self: self._default_date_availability(),
                                    copy=False)
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    living_area = fields.Integer()
    garden_area = fields.Integer()
    total_area = fields.Integer(compute="_compute_total_area", store=True, string="Total area (sqm)")
    garden_orientation = fields.Selection(
        string="Garden orientation",
        selection=[("north", "North"), ("south", "South"), ("east", "East"), ("west", "West")],
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        string="Status",
        selection=[("new", "New"), ("offer_received", "Offer received"), ("offer_accepted", "Offer accepted"),
                   ("sold", "Sold"), ("cancel", "Cancelled")],
        copy=False,
        default="new",
    )
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False, default=False)
    seller_id = fields.Many2one("res.partner", string="Seller", default=lambda self: self.env.user)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    best_price = fields.Float(compute="_compute_best_price", store=True, string="Best offer price")

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = 0.0 if not record.offer_ids else max(record.offer_ids.mapped("price"))

    @api.onchange("garden")
    def _onchange_garden(self):
        self.garden_area = 10 if self.garden else None
        self.garden_orientation = "north" if self.garden else None

    def unlink(self):
        if self.state in ["new", "cancel"]:
            raise UserError("Only new and canceled properties can be deleted.")
        return super().unlink()

    def action_sold(self):
        for record in self:
            if record.state == "cancel":
                raise UserError("You cannot sell a property that is cancelled.", "Error!")
            record.state = "sold"
            record.selling_price = record.best_price
            record.buyer_id = record.offer_ids.filtered(lambda offer: offer.price == record.best_price).partner_id
            record.offer_ids.write({"status": "refused"})
            record.offer_ids.filtered(lambda t: t.price == record.best_price).write({"status": "accepted"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise ValidationError("You cannot cancel a property that is sold.")
            self.state = "cancel"
            self.buyer_id = False
            self.selling_price = 0.0
            self.offer_ids.write({"status": "refused"})
        return True

    @api.constrains("expected_price", "selling_price")
    def _check_price(self):
        for record in self:
            if 0 < record.best_price <= (record.expected_price * 0.8):
                raise ValidationError("The price must be positive.")


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Real Estate Property Type"
    _order = "sequence, name"
    _sql_constraints = [
        ("check_name", "UNIQUE(name)", "The name must be unique"),
    ]

    name = fields.Char(required=True)
    sequence = fields.Integer("Sequence", default=10)

    property_ids = fields.One2many("estate.property", "property_type_id", string="Properties")

class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Real Estate Property Tag"
    _order = "name"
    _sql_constraints = [
        ("check_name", "UNIQUE(name)", "The name must be unique"),
    ]

    name = fields.Char(required=True)
    color = fields.Integer()
    property_ids = fields.Many2many("estate.property", string="Properties")


class PropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Property Offer"
    _order = "price desc"
    _sql_constraints = [
        ("check_price", "CHECK(price > 0)", "The price must be strictly positive"),
    ]

    create_date = fields.Datetime(default=fields.Datetime.now)
    price = fields.Float(required=True)
    status = fields.Selection(
        string="Status",
        selection=[("accepted", "Accepted"), ("refused", "Refused")],
        default=False,
    )
    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Datetime(string="Deadline",
                                    compute="_compute_date_deadline",
                                    inverse="_inverse_date_deadline",
                                    store=True)
    partner_id = fields.Many2one("res.partner", required=True, string="Partner")
    property_id = fields.Many2one("estate.property", required=True)

    def action_accept(self):
        if "accepted" in self.mapped("property_id.offer_ids.state"):
            raise UserError("An offer as already been accepted.")
        for record in self:
            record.status = "accepted"
            record.property_id.state = "offer_accepted"
        return True

    def action_refuse(self):
        for record in self:
            record.status = "refused"
        return True

    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date + relativedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.date_deadline:
                record.validity = (record.date_deadline - record.create_date).days + 1
