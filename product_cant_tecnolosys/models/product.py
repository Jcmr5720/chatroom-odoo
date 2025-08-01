from odoo import api,fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

     # Campo de relación para vincular product.template con stock.quant
    quant_ids = fields.One2many('stock.quant', 'product_tmpl_id', string='Ubicaciones')

    # Campo computado para mostrar la cantidad de productos en la ubicación específica (ubicación con ID 1)
    quantity_in_location = fields.Float(string='Unidades en SAndresito', compute='_compute_quantity_in_location')
    quantity_in_tulipanes = fields.Float(string='Unidades en Tulipanes', compute='_compute_quantity_in_tulipanes')
    quantity_in_neutron = fields.Float(string='Unidades en Neutron', compute='_compute_quantity_in_neutron')
    quantity_total =  fields.Float(string='Unidades Totales', compute='_compute_quantity_in_totales',store=True)

                

    @api.depends(
        'product_variant_ids.qty_available',
        'product_variant_ids.virtual_available',
        'product_variant_ids.incoming_qty',
        'product_variant_ids.outgoing_qty',
        'quantity_in_tulipanes',
        'quantity_in_neutron',
        'quantity_in_location'
    )
    def _compute_quantity_in_totales(self):
        for product_template in self:
            location_ids = [78,70,118]  # ID de las ubicaciones que se desea obtener la cantidad de productos
            products=product_template.product_variant_ids
    
            if products:
                quants_in_location = self.env['stock.quant'].search([
                ('product_id', 'in', products.ids),
                ('location_id', 'in', location_ids),
                ('product_id.active', '=', True)
            ])
                product_template.quantity_total = sum(quants_in_location.mapped('available_quantity'))
            else:
                product_template.quantity_total = 0


    @api.depends('quant_ids')
    def _compute_quantity_in_neutron(self):
        for product_template in self:
            location_ids = [118]  # ID de las ubicaciones que se desea obtener la cantidad de productos
            products=product_template.product_variant_ids
    
            if products:
                quants_in_location = self.env['stock.quant'].search([
                ('product_id', 'in', products.ids),
                ('location_id', 'in', location_ids),
                ('product_id.active', '=', True)
            ])
                product_template.quantity_in_neutron = sum(quants_in_location.mapped('available_quantity'))
            else:
                product_template.quantity_in_neutron = 0

    @api.depends('quant_ids')
    def _compute_quantity_in_location(self):
        for product_template in self:
            location_ids = [78]  # ID de las ubicaciones que se desea obtener la cantidad de productos
            products=product_template.product_variant_ids
    
            if products:
                quants_in_location = self.env['stock.quant'].search([
                ('product_id', 'in', products.ids),
                ('location_id', 'in', location_ids),
                ('product_id.active', '=', True)
            ])
                product_template.quantity_in_location = sum(quants_in_location.mapped('available_quantity'))
            else:
                product_template.quantity_in_location = 0

    
    @api.depends('quant_ids')
    def _compute_quantity_in_tulipanes(self):
        for product_template in self:
            location_ids = [70]  # ID de las ubicaciones que se desea obtener la cantidad de productos
            products=product_template.product_variant_ids
    
            if products:
                quants_in_location = self.env['stock.quant'].search([
                ('product_id', 'in', products.ids),
                ('location_id', 'in', location_ids),
                ('product_id.active', '=', True)
            ])
                product_template.quantity_in_tulipanes = sum(quants_in_location.mapped('available_quantity'))
            else:
                product_template.quantity_in_tulipanes = 0