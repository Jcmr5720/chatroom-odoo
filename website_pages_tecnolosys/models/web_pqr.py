# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class WebPqr(models.Model):

    _name = 'web.pqr'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'PQR Web'

    name = fields.Char(string="Referencia",readonly=True, default = "Nuevo",copy=False)


    usuario_asignado = fields.Many2one("res.users",string="Usuario Asignado",domain=[('share', '=', False)])


    canal_de_ventas = fields.Selection([('vitrina','Tienda física'),('chatroom','WhatsApp'),('website','Página web'),('ml','Mercado Libre'),('others','Otros')],default='chatroom',string="Canal de venta")

    cliente_id = fields.Many2one('res.users',string="Usuario")

    priority =  fields.Selection([('high','Alta'),('medium','Media'),('low','Baja')],default='low',string="Prioridad",store=True)

    categoria = fields.Many2one("web.pqr.category",string="Tipo de consulta",readonly=True)

    actividad_estado = fields.Selection([('overdue','Sin iniciar'),('today','Tomado'),('success','Terminado')],default='overdue',string="Estado", store=True, tracking=True)

    venta_relation =  fields.Many2one("sale.order", string="Venta")
    venta_string = fields.Char(string="Venta")
    
    nombre_public = fields.Char(string="Nombre usuario público")
    cel_public = fields.Char(string="Celular usuario público", store=False)
    email_public = fields.Char(string="Email usuario público")
    identificacion_public = fields.Char(string="Identificación usiario público")




    def tomar_caso(self):
        usuario_id = self.env.user.id

        self.usuario_asignado = usuario_id
        self.actividad_estado = 'today'

    def finalizar(self):
        self.actividad_estado = 'success'

        

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            categoria_id = vals.get('categoria')
            if not categoria_id:
                raise ValidationError("Debe seleccionar una categoría para generar la referencia.")

            categoria = self.env['web.pqr.category'].search(['|',('id','=',categoria_id),('name','=',categoria_id)])
            if not categoria.exists():
                raise ValidationError("La categoría seleccionada no existe.")

            sequence_code = f'pqr.referencia.{categoria.code}'

            # Obtener siguiente número de la secuencia
            secuencia = self.env['ir.sequence'].next_by_code(sequence_code)
            if not secuencia:
                secuencia = '/'

            # Asignar nombre formateado
            vals['name'] = f"{secuencia}"

        message_body = vals.pop('description', '')
        binary_files = vals.pop('attachments', [])
        web = vals.pop('desde_web',False)
        
        pqr =  super(WebPqr, self).create(vals)


        if web:
            attachment_ids = []
            for file_data in binary_files:
                if not file_data.get('datas'):
                    continue
                attachment = self.env['ir.attachment'].create({
                    'name': file_data.get('name', 'Adjunto'),
                    'type': 'binary',
                    'datas': file_data['datas'],
                    'res_model': 'web.pqr',
                    'res_id': pqr.id,
                    'mimetype': file_data.get('mimetype', 'application/octet-stream'),
                })
                attachment_ids.append(attachment.id)

            if message_body or attachment_ids:
                pqr.message_post(
                    body=message_body or "Adjuntos del cliente.",
                    attachment_ids=attachment_ids
                )



        return pqr
