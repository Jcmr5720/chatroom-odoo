from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from odoo.exceptions import AccessError
from werkzeug.exceptions import NotFound

import logging

_logger = logging.getLogger(__name__)

class WebsitePagesTecnolosys(Website):
    
    def paginaValores(self):
        valuesTest = request.env['website.page'].fTest()
        valuesPromeCode = request.env['website.page'].fPromeCode()
        valuesSnippet3 = request.env['website.page'].fSnippet3()
        valuesSnippet4_1 = request.env['website.page'].fSnippet4_1()
        valuesSnippet4_2 = request.env['website.page'].fSnippet4_2()
        valuesSnippet5 = request.env['website.page'].fSnippet5()
        valuesSnippet6 = request.env['website.page'].fSnippet6()
        
        values={
            #test
            'codigo': valuesTest['codigo'],
            'status_check': valuesTest['status_check'],
            #prome_code
            'promeCodeDatos' : valuesPromeCode['promeCode'],
            #s_dynamic_snippet3
            'snippetSearchProductos_id' :  valuesSnippet3['snippetSearchProductos_id'],
            'snippetCantidadPaginasCarrousel_3': valuesSnippet3['snippetCantidadPaginasCarrousel'],
            'snippetVectorItems_3': valuesSnippet3['snippetVectorItems'],
            'snippetDatos_3': valuesSnippet3['snippetDatos'],
            #s_dynamic_snippet4
            'snippetProductoDiaSearch' : valuesSnippet4_1['snippetProductoDiaSearch'],
            'snippetProductoDia' : valuesSnippet4_1['snippetProductoDia'],
            'snippetSearchProductosId4_2': valuesSnippet4_2,
            #s_dynamic_snippet5
            'snippetFlashSaleSearch' : valuesSnippet5['snippetFlashSaleSearch'],
            'snippetFlashSale' : valuesSnippet5['snippetFlashSale'],
            'snippetFlashDate' : valuesSnippet5['snippetFlashDate'],
            #s_dynamic_snippet6
            'snippetDatos6': valuesSnippet6['snippetDatos'],
            'snippetSearchProductosId6' : valuesSnippet6['snippetSearchProductosId6'],           
        }
    
        return values

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        """Este controlador utiliza la clase Website, importada desde el módulo website. 
        Actualmente, está siendo sobrescrito para permitir que el módulo website_pages_tecnolosys 
        pueda renderizar su propio contenido sin generar conflictos con el controlador original"""
        
        homepage_url = request.website._get_cached('homepage_url')
        if homepage_url and homepage_url != '/':
            request.env['ir.http'].reroute(homepage_url)

        website_page = request.env['ir.http']._serve_page()
        if website_page:
            values = self.paginaValores()
            _logger.info("PÁGINA HOME (/) = OK => VALORES: %s", values)
            return request.render('website_pages_tecnolosys.homepage_test', values)

        if homepage_url and homepage_url != '/':
            try:
                return request._serve_ir_http()
            except (AccessError, NotFound, SessionExpiredException):
                pass
    
    @http.route('/pqr', type='http', auth='public', website=True, sitemap=False)
    def pages(self, **kw):
        values = self.paginaValores()
        _logger.info("PÁGINA TEST = OK => VALORES: %s", values)
        return request.render('website_pages_tecnolosys.page_test', values)