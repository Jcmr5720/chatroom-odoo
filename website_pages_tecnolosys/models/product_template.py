# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from datetime import date

_logger = logging.getLogger(__name__)

class ProductoTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.model
    def time_current(self):
        return date.today()

    def fPromeCode(self):
        promeCode = []
        promeCodes = []
        promeRewards = []
        websiteIdSearch = self.env.ref('website.default_website')
        websiteId = websiteIdSearch.company_id.id
        promeCodeSearch = self.env['loyalty.program'].sudo().search([
            ('program_type', '=', 'promo_code'),
            ('company_id', '=', websiteId)
        ])

        if promeCodeSearch:
            for promeX in promeCodeSearch.rule_ids:
                if promeX.code:
                    promeCodes.append(promeX.code)
                    
            for promeY in promeCodeSearch.reward_ids:
                if promeY.discount_product_category_id:
                    promeRewards.append(promeY.discount_product_category_id.id)
            
            promeCode.append({
                'var1': promeCodes,
                'var2': promeRewards
            })
        else:
            promeCode = []
        
        return {
            'promeCode': promeCode
        }
    
    def fProductPromo(self):
        res = self.fPromeCode()
        promeCode = res['promeCode']
        promo_codes_to_show = []
        
        if promeCode:
            categorias = promeCode[0]['var2']
            codigos = promeCode[0]['var1']
            
            if self.categ_id.id in categorias:
                promo_codes_to_show = codigos
                
        return promo_codes_to_show