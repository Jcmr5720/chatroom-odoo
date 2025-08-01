from odoo import models, api


class AcruxChatConversation(models.Model):
    _inherit = 'acrux.chat.conversation'

    @api.model
    def get_product_fields_to_read(self):
        fields_search = super().get_product_fields_to_read()
        Product = self.env['product.product']
        if 'quantity_in_location' in Product._fields:
            extra = [
                'quantity_in_location',
                'quantity_in_tulipanes',
                'quantity_in_neutron',
            ]
            for field in extra:
                if field not in fields_search:
                    fields_search.append(field)
        return fields_search

    @api.model
    def search_product(self, string, filters=None):
        products = super().search_product(string, filters=filters)
        Product = self.env['product.product']
        if 'quantity_in_location' in Product._fields:
            stock_filter = (filters or {}).get('stock_filter', 'positive')
            if stock_filter == 'positive':
                products = [p for p in products if p.get('quantity_total', 0) > 0]
            elif stock_filter == 'negative':
                products = [p for p in products if p.get('quantity_total', 0) < 0]
        return products
