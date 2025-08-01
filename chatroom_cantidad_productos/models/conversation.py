from odoo import fields, models,api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class AcruxChatConversation(models.Model):
    _inherit = 'acrux.chat.conversation'

    @api.model
    def get_product_fields_to_read(self):
        fields_search = ['id', 'display_name', 'lst_price', 'uom_id',
                         'write_date', 'product_tmpl_id', 'name', 'type', 'default_code']
        if 'quantity_in_location' in self.env['product.product']._fields:
            fields_search.append('quantity_total')
        return fields_search

    @api.model
    def search_product(self, string):

        if not string:
            return []
        ProductProduct = self.env['product.product']
        domain = [('sale_ok', '=', True)]
        if string:
            if string.startswith('/cat '):
                domain += [('categ_id.complete_name', 'ilike', string[5:].strip())]
            else:
                domain += ['|', ('name', 'ilike', string), ('default_code', 'ilike', string)]
        fields_search = self.get_product_fields_to_read()
        out = ProductProduct.search_read(domain, fields_search, order='name, list_price')

        
        # Filtrar los diccionarios que cumplen con la condición quantity_in_location > 0
        out_filtered = [product_dict for product_dict in out if product_dict.get('quantity_total', 0) > 0]
        
        return out_filtered