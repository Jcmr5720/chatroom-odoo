from odoo import fields, models, api
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class AcruxChatConversation(models.Model):
    _inherit = 'acrux.chat.conversation'

    @api.model
    def get_product_fields_to_read(self):
        fields_search = [
            'id', 'display_name', 'lst_price', 'uom_id',
            'write_date', 'product_tmpl_id', 'name', 'type', 'default_code'
        ]
        if 'quantity_total' in self.env['product.product']._fields:
            fields_search.append('quantity_total')
        if 'quantity_in_location' in self.env['product.product']._fields:
            fields_search.append('quantity_in_location')
        if 'quantity_in_tulipanes' in self.env['product.product']._fields:
            fields_search.append('quantity_in_tulipanes')
        if 'quantity_in_neutron' in self.env['product.product']._fields:
            fields_search.append('quantity_in_neutron')
        return fields_search

    @api.model
    def search_product(self, string, filters=None):
        products = super().search_product(string, filters=filters)

        if 'quantity_total' in self.env['product.product']._fields:
            stock_filter = (filters or {}).get('stock_filter', 'positive')
            if stock_filter == 'positive':
                products = [p for p in products if p.get('quantity_total', 0) > 0]
            elif stock_filter == 'negative':
                products = [p for p in products if p.get('quantity_total', 0) < 0]
        return products

    @api.model
    def get_config_parameters(self):
        """Return ChatRoom configuration values.

        This method is expected by the JS client when loading the chatroom.
        Some deployments were missing it, which raised an AttributeError during
        startup.  By defining it here we ensure the required configuration is
        always available.
        """
        Config = self.env['ir.config_parameter'].sudo()
        return {
            'chatroom_tab_orientation': Config.get_param('chatroom_tab_orientation')
        }
