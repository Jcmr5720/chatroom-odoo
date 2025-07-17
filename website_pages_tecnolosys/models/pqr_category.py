# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class WebPqrCategory(models.Model):

    _name = 'web.pqr.category'
    _description = 'Categoría de PQR Web'

    code = fields.Char(string="Código",required= True)

    name = fields.Char(string="Tipo de consulta")

    motivo = fields.One2many("web.pqr.motivo","categoria",string="Motivos")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            code = vals.get('code')
            name = vals.get('name', code)

            if code:
                self.env['ir.sequence'].create({
                    'name': f'Referencia PQR {name}',
                    'code': f'pqr.referencia.{code}',
                    'prefix': f'{code}-',
                    'padding': 5,
                    'number_next': 1,
                    'number_increment': 1,
                    'implementation': 'standard'
                })

        return super().create(vals_list)


    def unlink(self):
        sequence_obj = self.env['ir.sequence']

        for categoria in self:
            sequence_code = f'pqr.referencia.{categoria.code}'
            sequence = sequence_obj.search([('code', '=', sequence_code)], limit=1)
            if sequence:
                sequence.unlink()

        return super().unlink()
