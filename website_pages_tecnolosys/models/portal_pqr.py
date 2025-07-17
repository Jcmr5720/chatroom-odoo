from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging
import base64

_logger = logging.getLogger(__name__)

class PortalPqr(CustomerPortal):

    def _get_pqr_data(self, sortby='date'):
        website_user = request.env.user.id
        website_name = request.env.user.display_name
        sort_mapping = {
            'date': 'write_date desc',
            'id': 'id desc',
            'name': 'display_name asc',
        }
        order = sort_mapping.get(sortby, 'write_date desc')

        pqr_records = request.env['web.pqr'].search(
            [('cliente_id', '=', website_user)],
            order=order
        )

        pqrDates = []
        for var in pqr_records:
            images = []
            for dates in var.message_ids:
                if dates.attachment_ids:
                    images.append(dates.attachment_ids('utf-8') if isinstance(dates.attachment_ids, bytes) else dates.attachment_ids)

            description = ''
            if var.message_ids:
                description = var.message_ids[-2].body or ''

            pqrDates.append({
                'varId': var.id,
                'varName': var.name,
                'varWriteOn': var.write_date,
                'varDisplayName': website_name,
                'varPriority': var.priority,
                'varDescription': description,
                'varCategory': var.categoria.name if var.categoria else '',
                'varImages': images,
                'varUrl': f"/my/pqrs/{var.id}",
            })

        return {
            'pqrDates': pqrDates,
            'websiteUser': website_user,
        }

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'pqrCount' in counters:
            website_user = self._get_pqr_data()['websiteUser']
            count = request.env['web.pqr'].search_count([('cliente_id', '=', website_user)])
            values['pqrCount'] = count
        return values

    @http.route(['/my/pqrs'], type='http', auth="user", website=True)
    def portal_my_pqrs(self, **kw):

        searchbar_sortings = {
            'date': {'label': 'Más reciente', 'order': 'write_date desc'},
            'id': {'label': 'Id', 'order': 'id desc'},
            'name': {'label': 'Nombre', 'order': 'display_name asc'},
        }
        sortby = kw.get('sortby', 'date')

        values = self._get_pqr_data(sortby=sortby)
        values.update({
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        _logger.info("PÁGINA PQRS (/) = OK => VALORES: %s", values)
        return request.render('website_pages_tecnolosys.portal_pqr_table', values)

    @http.route(['/my/pqrs/crear'], type='http', auth="user", website=True, methods=['GET'])
    def portal_create_pqr_form(self, **kw):
        categories = request.env['web.pqr.category'].sudo().search([])
        priorities = request.env['web.pqr'].fields_get(['priority'])['priority']['selection']
        canales = request.env['web.pqr'].fields_get(['canal_de_ventas'])['canal_de_ventas']['selection']
        ventas_records = request.env['sale.order'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id)
        ], order='date_order desc')
        ventas = [so.name for so in ventas_records]
        return request.render('website_pages_tecnolosys.portal_pqr_form', {
            'categories': categories,
            'priorities': priorities,
            'canales': canales,
            'ventas': ventas,
        })


    @http.route(['/my/pqrs/crear'], type='http', auth="user", website=True, methods=['POST'])
    def portal_create_pqr_submit(self, **post):
        user = self._get_pqr_data()['websiteUser']
        categoria = post.get('categoria')
        message_body = post.get('message_body')
        canal_venta = post.get('canal_de_ventas')
        venta_relation = post.get('venta_relation')

        image_files = request.httprequest.files.getlist('imagenes')
        images_data = []

        for img_file in image_files[:5]:
            if img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                images_data.append({
                    'nombre': img_file.filename,
                    'mimetype': img_file.content_type,
                    'datas': img_base64
                })
        

        venta_odo = request.env['sale.order'].search([('name', '=', venta_relation)]).id
        
        request.env['web.pqr'].sudo().create({
            'cliente_id': user,
            'categoria': categoria,
            'canal_de_ventas': canal_venta,
            'description': message_body,
            'venta_relation': venta_odo,
            'attachments': images_data,
            'desde_web': True,
        })

        return request.redirect('/my/pqrs')

    @http.route(['/pqrs/crear'], type='http', auth="public", website=True, methods=['GET'])
    def public_create_pqr_form(self, **kw):
        categories = request.env['web.pqr.category'].sudo().search([])
        canales = request.env['web.pqr'].fields_get(['canal_de_ventas'])['canal_de_ventas']['selection']
        return request.render('website_pages_tecnolosys.portal_pqr_public_form', {
            'categories': categories,
            'canales': canales,
        })

    @http.route(['/pqrs/crear'], type='http', auth="public", website=True, methods=['POST'])
    def public_create_pqr_submit(self, **post):
        categoria = post.get('categoria')
        message_body = post.get('message_body')
        canal_venta = post.get('canal_de_ventas')
        venta_string = post.get('venta_string')
        nombre_public = post.get('nombre_public')
        cel_public = post.get('cel_public')
        email_public = post.get('email_public')
        identificacion_public = post.get('identificacion_public')

        image_files = request.httprequest.files.getlist('imagenes')
        images_data = []

        for img_file in image_files[:5]:
            if img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                images_data.append({
                    'nombre': img_file.filename,
                    'mimetype': img_file.content_type,
                    'datas': img_base64
                })

        request.env['web.pqr'].sudo().create({
            'categoria': categoria,
            'canal_de_ventas': canal_venta,
            'description': message_body,
            'venta_string': venta_string,
            'nombre_public': nombre_public,
            'cel_public': cel_public,
            'email_public': email_public,
            'identificacion_public': identificacion_public,
            'attachments': images_data,
            'desde_web': True,
        })

        return request.redirect('/')

    @http.route(['/my/pqrs/<int:pqr_id>'], type='http', auth="public", website=True)
    def portal_show_pqr(self, pqr_id, access_token=None, **kw):
        pqr_record = request.env['web.pqr'].browse(pqr_id)
        if not pqr_record.exists():
            raise http.NotFound()

        if access_token and access_token != pqr_record.access_token:
            raise http.AccessError()
        if not access_token and request.env.user != pqr_record.cliente_id:
            raise http.AccessError()

        website_name = pqr_record.cliente_id.display_name
        images = []
        other_files = []
        for message in pqr_record.message_ids:
            if message.attachment_ids:
                for att in message.attachment_ids:
                    data = att.datas.decode('utf-8') if isinstance(att.datas, bytes) else att.datas
                    file_info = {
                        'id': att.id,
                        'name': att.name,
                        'mimetype': att.mimetype,
                        'datas': data,
                    }
                    if att.mimetype in ('image/png', 'image/jpeg', 'image/jpg'):
                        images.append(file_info)
                    else:
                        other_files.append(file_info)
        only_images = not other_files

        pqr = request.env['web.pqr'].sudo().browse(pqr_id)

        description = ''
        if pqr_record.message_ids:
            description = pqr_record.message_ids[-2].body or ''

        values = {
            'varId': pqr_record.id,
            'varName': pqr_record.name,
            'varWriteOn': pqr_record.write_date,
            'varDisplayName': website_name,
            'varCanalVentas': pqr_record.canal_de_ventas,
            'varVentaString' : pqr_record.venta_relation.name,
            'varDescription': description,
            'varCategory': pqr_record.categoria.name if pqr_record.categoria else '',
            'varImages': images,
            'varFiles': other_files,
            'onlyImages': only_images,
            'pqrObject': pqr,
        }

        return request.render('website_pages_tecnolosys.portal_pqr_page', values)