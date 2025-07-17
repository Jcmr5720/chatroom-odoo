# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.tools.translate import html_translate
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class snippetClass(models.Model):
    _inherit = 'website.page'
    
    @api.model
    def fTest(self):
        valuesTest = {
            'codigo': 123456789,
            'status_check': "OK"
        }
        return valuesTest
        
    def fSnippetCommon(self, snippet_x, snippet_y):
        snippetModelo = self.env['loyalty.reward']
        snippetFiltro = [
            ('reward_type', '=', 'discount'),
            ('discount', '>', 0),
            ('program_id.program_type', '=', 'promotion')
        ]
        snippetSearchDescuento = snippetModelo.sudo().search(snippetFiltro)

        snippetTamañoTotalSearch = len(snippet_x)
        snippetCantidadPaginasCarrousel = range((snippetTamañoTotalSearch + snippet_y - 1) // snippet_y)
        snippetVectorItems = []

        for snippetAnchoVectorItem in snippetCantidadPaginasCarrousel:
            snippetAnchoVectorItemsIn = snippetAnchoVectorItem * snippet_y
            snippetAnchoVectorItemsOut = (snippetAnchoVectorItem + 1) * snippet_y
            snippetVectorItems.append(snippet_x[snippetAnchoVectorItemsIn:snippetAnchoVectorItemsOut])

        snippetDatos = []
        for snippetVar_1 in snippet_x:
            snippetArray_1 = []
            snippetDescuentoProducto = 0
            snippetDescuentoCateg = 0
            snippetDescuento = 0

            for snippetVar_2 in snippetSearchDescuento:
                snippetArray_1 = snippetVar_2.discount_product_ids.mapped('product_tmpl_id').ids

                if snippetVar_2.discount_product_ids and snippetVar_1.id in snippetArray_1:
                    snippetDescuentoProducto = snippetVar_2.discount

                if snippetVar_2.discount_product_category_id in snippetVar_1.categ_id:
                    snippetDescuentoCateg = snippetVar_2.discount

            if snippetDescuentoProducto > 0 and snippetDescuentoCateg > 0:
                snippetDescuento = snippetDescuentoProducto + snippetDescuentoCateg
            elif snippetDescuentoProducto > 0:
                snippetDescuento = snippetDescuentoProducto
            elif snippetDescuentoCateg > 0:
                snippetDescuento = snippetDescuentoCateg

            snippetDatos.append({
                'v_1': snippetVar_1.id,
                'v_2': snippetDescuento
            })

        return {
            'snippetCantidadPaginasCarrousel': snippetCantidadPaginasCarrousel,
            'snippetVectorItems': snippetVectorItems,
            'snippetDatos': snippetDatos,
            'snippetSearchProductos_id': snippet_x
        }
        
    # s_dynamic_snippet3  
    def fSnippet3(self):
        snippetCategoriaSearch3 = 45
        snippetModelo3 = self.env['product.template']
        snippetCampo3 = 'website_sequence asc'
        snippetFiltro3 = [
            ('website_published', '=', True),
            ('public_categ_ids.id', '=', snippetCategoriaSearch3),
            ('quantity_total', '>', 0)
        ]
             
        snippetAlcance3 = 30
        snippetSearchProductos_id = snippetModelo3.sudo().search(snippetFiltro3 , order = snippetCampo3, limit = snippetAlcance3)
        
        snippetCantidadItemsCarrousel = 6

        snippetCommonData = self.fSnippetCommon(snippetSearchProductos_id, snippetCantidadItemsCarrousel)

        return {
            'snippetDatos': snippetCommonData['snippetDatos'],
            'snippetVectorItems': snippetCommonData['snippetVectorItems'],
            'snippetSearchProductos_id': snippetSearchProductos_id,
            'snippetCantidadPaginasCarrousel': snippetCommonData['snippetCantidadPaginasCarrousel'],
            'snippetCantidadItemsCarrousel': snippetCantidadItemsCarrousel
        }

    # s_dynamic_snippet4
    def fSnippet4_1(self):
        snippetCheck4_1 = self.env['loyalty.program'].sudo().search([('name', '=', 'day_sale')], limit=1)
        if not snippetCheck4_1:
            
            return{
                'snippetProductoDiaSearch': False,
                'snippetProductoDia': None
            }
            
        snippetModelo4_1 = self.env['loyalty.reward']
        snippetFiltro4_1 = [
            ('program_id.name', '=', 'day_sale'),
            ('reward_type', '=', 'discount'),
            ('discount', '>', 0)
        ]
        snippetAlcance4_1 = 1
        snippetProductoDiaSearch = snippetModelo4_1.sudo().search(snippetFiltro4_1 , limit= snippetAlcance4_1)

        if snippetProductoDiaSearch and snippetProductoDiaSearch.discount_product_ids:
            snippetProductoDia = snippetProductoDiaSearch.discount_product_ids[0].product_tmpl_id
        else:
            snippetProductoDia = None

        return {
            'snippetProductoDiaSearch': snippetProductoDiaSearch,
            'snippetProductoDia': snippetProductoDia
        }

    def fSnippet4_2(self):
        snippetModelo4_2 = self.env['product.template']
        snippetCampo4_2 = 'create_date desc'
        snippetFiltro4_2 = [
            ('website_published', '=', True),
            ('quantity_total', '>', 0)
        ]
        snippetAlcance4_2 = 10
        snippetSearchProductosId4_2 = snippetModelo4_2.sudo().search(snippetFiltro4_2 , order = snippetCampo4_2, limit = snippetAlcance4_2)
        
        return snippetSearchProductosId4_2

    def fSnippet5(self):
        snippetCheck5 = self.env['loyalty.program'].sudo().search([('name', '=', 'flash_sale'),], limit=1)
        if not snippetCheck5:
            
            return{
                'snippetFlashSale' : None,
                'snippetFlashSaleSearch' : False,
                'snippetFlashDate' : False
            }
            
        snippetModelo5 = self.env['loyalty.reward']
        snippetFiltro5 = [
            ('program_id.name', '=', 'flash_sale'),
            ('reward_type', '=', 'discount'),
            ('discount', '>', 0)
        ]
        snippetAlcance5 = 12
        snippetFlashSaleSearch = snippetModelo5.sudo().search(snippetFiltro5, limit=snippetAlcance5)
        snippetFlashSale = []
        
        snippetModelo5_2 = self.env['loyalty.program']
        snippetFiltro5_2 = [
            ('name', '=', 'flash_sale'),
        ]
        snippetFlashSaleSearch2 = snippetModelo5_2.sudo().search(snippetFiltro5_2, limit=1)
        
        if snippetFlashSaleSearch:
            snippetArrayF5 = snippetFlashSaleSearch.mapped('discount_product_ids.product_tmpl_id')
            snippetFiltroQty = [
                ('id', 'in', snippetArrayF5.ids),
                ('quantity_total', '>', 0)
            ]
            snippetFlashSale = snippetArrayF5.sudo().search(snippetFiltroQty, limit=snippetAlcance5)
            
            if snippetFlashSaleSearch2:
                snippetFlashDate = snippetFlashSaleSearch2.date_to
            else:
                snippetFlashDate = False
                
        else:
            snippetFlashSale = []
        
        return {
            'snippetFlashSale' : snippetFlashSale,
            'snippetFlashSaleSearch' : snippetFlashSaleSearch,
            'snippetFlashDate' : snippetFlashDate
        }
        
    def fSnippet6(self):
        snippetModelo6 = self.env['product.template']
        snippetFiltro6 = [
            ('website_published', '=', True),
            ('quantity_total', '>', 0)
        ]
        snippetAlcance6 = 100
        snippetSearch4_2 = snippetModelo6.sudo().search(snippetFiltro6)
        snippetSearchProductosId6 = sorted(snippetSearch4_2, key=lambda x: x.sales_count)
        snippetSearchProductosId6 = snippetSearchProductosId6[-10:]
        
        snippetCommonData = self.fSnippetCommon(snippetSearchProductosId6, snippetAlcance6)
        
        return {
            'snippetDatos': snippetCommonData['snippetDatos'],
            'snippetSearchProductosId6' : snippetSearchProductosId6 
        }
        
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
                promeCodes.append(promeX.code)
                
            for promeY in promeCodeSearch.reward_ids:
                promeRewards.append(promeY.discount_product_category_id.name)
                
            promeCode.append({
                'var1': promeCodes,
                'var2' : promeRewards
                })
        
        else:
            promeCode = None
            
        return {
            'promeCode': promeCode
        }