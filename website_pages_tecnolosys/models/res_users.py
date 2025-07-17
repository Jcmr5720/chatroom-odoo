# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    pqr_ids = fields.One2many('web.pqr','cliente_id', string="PQRS" )
