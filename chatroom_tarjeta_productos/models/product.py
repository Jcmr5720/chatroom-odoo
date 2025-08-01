from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    quantity_in_location = fields.Float(
        related='product_tmpl_id.quantity_in_location',
        readonly=True,
    )
    quantity_in_tulipanes = fields.Float(
        related='product_tmpl_id.quantity_in_tulipanes',
        readonly=True,
    )
    quantity_in_neutron = fields.Float(
        related='product_tmpl_id.quantity_in_neutron',
        readonly=True,
    )
    quantity_total = fields.Float(
        related='product_tmpl_id.quantity_total',
        readonly=True,
    )
