# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class WebPqrMotivo(models.Model):

    _name = 'web.pqr.motivo'
    _description = 'motivo de PQR Web'

    name = fields.Char(string="Tipo de consulta")

    categoria = fields.Many2one("web.pqr.category",string="Categoría PQR")

    required_sale = fields.Boolean(string="Requiere Venta",default=False)
