# -*- coding: utf-8 -*-
import logging
from typing import List
from time import sleep
from psycopg2 import IntegrityError, errorcodes
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from odoo.tools import formatLang
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, date
from ..tools import DEFAULT_IMAGE_URL
from ..tools import get_image_url, get_image_from_url, get_binary_attach
from ..tools import date_timedelta, date2sure_write
_logger = logging.getLogger(__name__)

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class AcruxChatConversation(models.Model):
    _name = 'acrux.chat.conversation'
    _description = 'Chat Conversation'
    _order = 'last_activity desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
    number = fields.Char('Base number', required=True, index=True)
    number_format = fields.Char('Number', compute='_compute_number_format',
                                store=True, readonly=True)
    conv_type = fields.Selection([('none', 'None'), ('normal', 'Normal'), ('private', 'Private')], readonly=False,
                                 string='Conversation Type', required=True, default='normal')
    image_128 = fields.Image('Avatar', max_width=128, max_height=128)
    image_url = fields.Char('Avatar Url', compute='_image_update', store=True,
                            default=DEFAULT_IMAGE_URL, required=True)
    connector_id = fields.Many2one('acrux.chat.connector', 'Connector', required=True,
                                   ondelete='cascade')
    res_partner_id = fields.Many2one('res.partner', 'Client', ondelete='set null')
    status = fields.Selection([('new', 'New'),
                               ('current', 'Current'),
                               ('done', 'Done')], 'Status', required=True,
                              default='new')
    chat_message_ids = fields.One2many('acrux.chat.message', 'contact_id', 'Chat Messages')
    agent_id = fields.Many2one('res.users', 'Agent', ondelete='set null',
                               domain="[('company_id', 'in', [company_id, False]), ('is_chatroom_group','=',True)]")
    last_activity = fields.Datetime('Last activity', required=True, store=True,
                                    default=fields.Datetime.now)
    last_sent = fields.Datetime('Last sent', help='Last message sent to the partner.')
    last_received = fields.Datetime('Last Received', help='To prevent send message with extra fee.')
    last_received_first = fields.Datetime('First Unanswered', help='First unanswered message.')
    company_id = fields.Many2one('res.company', related='connector_id.company_id', string='Company',
                                 store=True, readonly=True)
    team_id = fields.Many2one('crm.team', string='Team',
                              domain="[('company_id', 'in', [company_id, False])]",
                              ondelete='set null')
    border_color = fields.Char(related='connector_id.border_color', store=False)
    desk_notify = fields.Selection(related='connector_id.desk_notify', store=False)
    connector_type = fields.Selection(related='connector_id.connector_type', store=False)
    show_icon = fields.Boolean(related='connector_id.show_icon', store=False)
    allow_signing = fields.Boolean(related='connector_id.allow_signing', store=False)
    valid_number = fields.Selection([('yes', 'Yes'),
                                     ('no', 'No')], string='Valid', default=False, help='Exists in WhatsApp')
    tmp_agent_id = fields.Many2one('res.users', 'Assign to', ondelete='set null',
                                   domain="[('company_id', 'in', [company_id, False]), ('is_chatroom_group','=',True)]")
    is_waba_opt_in = fields.Boolean('Opt-in', default=True)
    sent_opt_in = fields.Boolean('Opt-in already requested', default=True)
    mute_opt_in = fields.Boolean()
    stage_id = fields.Many2one('acrux.chat.conversation.stage', string='Stage', index=True,
                               tracking=True, copy=False,
                               group_expand='_read_group_stage_ids')
    kanban_state = fields.Selection([('grey', 'No next activity planned'),
                                     ('red', 'Next activity late'),
                                     ('green', 'Next activity is planned')],
                                    string='Kanban State', compute='_compute_kanban_state')
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority',
                                index=True, default=AVAILABLE_PRIORITIES[0][0])
    color = fields.Integer('Color Index', default=0)
    tag_ids = fields.Many2many('acrux.chat.conversation.tag', string='Tags')
    note = fields.Text('Note', help='Internal note.')
    is_odoo_created = fields.Boolean('Is odoo created?', default=False)
    description = fields.Text('Description', help='Conversation description. '
                              'May be synchronized with external connector.')
    allowed_lang_ids = fields.Many2many(related='connector_id.allowed_lang_ids')

    _sql_constraints = [
        ('number_connector_uniq', 'unique (number, conv_type, connector_id)', _('Number in connector has to be unique'))
    ]

    def is_private(self):
        return self.conv_type == 'private'

    @api.constrains('status', 'agent_id')
    def _constrain_status(self):
        for r in self:
            if r.status == 'current' and not r.agent_id:
                raise ValidationError(_('Have to set agent to set conversation to "current"'))

    @api.constrains('number', 'connector_id', 'conv_type')
    def _constrain_number(self):
        for r in self.filtered(lambda conv: conv.connector_id and conv.number and not conv.is_private()):
            r.connector_id.assert_id(r.number)

    @api.onchange('number', 'connector_id', 'conv_type')
    def _onchange_number(self):
        for r in self.filtered(lambda conv: conv.connector_id and conv.number and not conv.is_private()):
            r.number = r.connector_id.clean_id(r.number)

    @api.onchange('res_partner_id')
    def onchange_res_partner_id(self):
        if self.res_partner_id and self.env.context.get('set_default'):
            self.name = self.res_partner_id.name
            number = self.res_partner_id.mobile or self.res_partner_id.phone
            self.number = self.connector_id.clean_id(number) if number else False

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AcruxChatConversation, self).create(vals_list)
        for ret in res:
            if (self.env.context.get('is_from_wizard') or self.env.context.get('is_acrux_chat_room')) \
                    and not self.env.context.get('not_check_is_valid') \
                    and ret.connector_id.check_is_valid_active() and not ret.valid_number:
                ret.connector_id.check_is_valid_whatsapp_number(ret, raise_error=False)
                if ret.valid_number == 'no':
                    error = _('Number not exist in WhatsApp (%s)') % ret.number
                    raise ValidationError(error)
                elif not ret.valid_number and ret.connector_id.valid_restriction:
                    error = _('The number could not be verified (%s)') % ret.number
                    raise ValidationError(error)
            ret.update_conversation()
        return res

    def action_check_is_valid(self):
        recs = dict()
        for rec in self:
            if rec.connector_id.connector_type == 'apichat.io' and rec.connector_id.auto_valid_number:
                if rec.connector_id.id not in recs:
                    recs[rec.connector_id.id] = {'conv_ids': self.env['acrux.chat.conversation'],
                                                 'conn_id': rec.connector_id}
                recs[rec.connector_id.id]['conv_ids'] |= rec
        for conn in recs.values():
            # raise if expired or reached
            conn['conn_id'].check_is_valid_whatsapp_number(conn['conv_ids'])

    def update_conversation(self):
        self.ensure_one()
        if self.env.context.get('not_download_profile_picture'):
            return
        if self.connector_id.connector_type in ['apichat.io', 'chatapi']:
            params = {'chatId': self.get_chat_id()}
            self._update_conversation(params, timeout=5)

    def get_chat_id(self):
        self.ensure_one()
        out = self.number
        if self.connector_id.connector_type in ['apichat.io', 'chatapi']:
            if self.conv_type == 'normal':
                out = f'{self.number}@c.us'
            elif self.conv_type == 'private':
                out = f'{self.number}@l.us'
        return out

    def _update_conversation(self, params, timeout):
        self.ensure_one()
        try:
            data = self.connector_id.ca_request('contact_get', params=params,
                                                timeout=timeout)
            name = data.get('name')
            if name:
                self.name = name.strip()
            image_url = data.get('image')
            if image_url and image_url.startswith('http'):
                raw = get_image_from_url(image_url)
                if raw:
                    self.image_128 = raw
        except Exception:
            pass

    def write(self, vals):
        if vals.get('status') and self.env.context.get('please_log_event'):
            event = {'new': 'to_new',
                     'done': 'to_done',
                     'current': 'to_curr'}
            self.event_create(event.get(vals['status']))
        return super(AcruxChatConversation, self).write(vals)

    def event_create(self, event, user_id=False, text=False):
        if not self.env.context.get('not_log_event'):
            if not user_id:
                user_id = self.env.user
            Message = self.env['acrux.chat.message']
            for rec in self:
                txt = text or dict(Message._fields['event'].selection).get(event)
                data = {'ttype': 'info',
                        'from_me': True,  # By convention
                        'contact_id': rec.id,
                        'event': event,
                        'user_id': user_id.id,
                        'text': '%s (%s)' % (txt, user_id.name)}
                Message.create(data)

    @api.depends('last_sent', 'last_received')
    def _last_activity(self):
        for rec in self:
            exist = rec.last_sent or rec.last_received
            if exist:
                last = max(rec.last_sent or exist, rec.last_received or exist)
            else:
                last = fields.Datetime.now()
            rec.last_activity = last

    @api.depends('image_128', 'res_partner_id.image_128')
    def _image_update(self):
        for rec in self:
            if rec.image_128 and rec.write_date:
                rec.image_url = get_image_url(self, rec, rec.image_128)
            elif rec.res_partner_id.image_128:
                rec.image_url = get_image_url(self, rec.res_partner_id, rec.res_partner_id.image_128)
            else:
                rec.image_url = DEFAULT_IMAGE_URL

    @api.depends('number', 'connector_id', 'conv_type')
    def _compute_number_format(self):
        to_process = self.filtered(lambda conv: conv.connector_id and conv.number and not conv.is_private())
        for rec in to_process:
            rec.number_format = rec.connector_id.format_id(rec.number)
        for rec in self - to_process:
            rec.number_format = rec.number

    @api.depends('name', 'number_format')
    def name_get(self):
        result = []
        full_name = self.env.context.get('full_name')
        for conv in self:
            if full_name:
                result.append((conv.id, _('To: %s (%s) | From: %s') %
                               (conv.name, conv.number_format, conv.connector_id.name)))
            else:
                result.append((conv.id, '%s (%s)' % (conv.name, conv.number_format)))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', 'ilike', name), ('number', 'ilike', name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    def get_to_done(self):
        self.ensure_one()
        return {'status': 'done',
                'agent_id': False}

    def get_to_current(self):
        self.ensure_one()
        return {'agent_id': self.env.user.id,
                'status': 'current'}

    def get_to_new(self):
        self.ensure_one()
        return {'status': 'new',
                'agent_id': False}

    def set_to_done(self):
        for r in self:
            r.event_create('to_done')
            r.write(r.get_to_done())

    def set_to_current(self):
        for r in self:
            r.event_create('to_curr')
            r.write(r.get_to_current())

    def set_to_new(self):
        for r in self:
            r.write(r.get_to_new())

    @api.model
    def new_message(self, data):
        '''
        Processes received message (WebHook).
        :param data:
            ttype:
            connector_id:
            name:
            number:
            message:
        :return: objetc message_id
        '''
        Messages = self.env['acrux.chat.message']
        Connector = self.env['acrux.chat.connector']

        conn_id = Connector.browse(data['connector_id'])
        conn_id.assert_id(data['number'])

        conversation = self.create_conversation_from_message_dict(data)
        last_sent = conversation.last_sent
        message_id = Messages.create({
            'text': data['message'],
            'contact_id': conversation.id,
            'ttype': data['ttype'],
            'msgid': data['msgid'],
            'date_message': date2sure_write(data['time']),
            'from_me': data.get('from_me', False)
        })
        message_id.post_create_from_json(data)
        limit = conversation.decide_first_status()
        limit, send_bus = self.new_message_hook(message_id, limit, data, last_sent)
        if conversation.env.context.get('downl_later'):
            self.env.cr.commit()
            conversation.with_context(not_download_profile_picture=False).update_conversation()
        if send_bus:
            data_to_send = conversation.build_dict(limit)
            conversation._sendone(conversation.get_bus_channel(), 'new_messages', data_to_send)
        return message_id

    @api.model
    def create_conversation_from_message_dict(self, data):
        conversation = self.env['acrux.chat.conversation']
        max_tries = 0
        please_set_to_new = False
        while max_tries < 3:
            max_tries += 1
            conversation = self.search([('number', '=', data['number']),
                                        ('conv_type', '=', data['conv_type']),
                                        ('connector_id', '=', data['connector_id'])])
            if conversation:
                if conversation.valid_number != 'yes':
                    conversation.valid_number = 'yes'
                if not conversation.is_waba_opt_in:
                    conversation.is_waba_opt_in = True
            if not conversation:
                try:
                    vals = self.create_conversation_from_message_dict_vals(data)
                    conversation = self.with_context(not_download_profile_picture=True, downl_later=True).create(vals)
                    self.env.cr.commit()
                    please_set_to_new = True
                except IntegrityError as e:
                    if e.pgcode == errorcodes.UNIQUE_VIOLATION:
                        self.env.cr.rollback()
                        sleep(1)
                        continue
                # conversation.set_to_new()
            if not conversation.res_partner_id and conversation.status in ['new', 'done']:
                partner_id = self.search_partner_from_number(conversation)
                if partner_id:
                    conversation.res_partner_id = partner_id[0]
            if please_set_to_new:
                conversation.set_to_new()
            break
        return conversation

    @api.model
    def create_conversation_from_message_dict_vals(self, data):
        return {
            'name': data['name'] or data['number'],
            'connector_id': data['connector_id'],
            'valid_number': 'yes',
            'is_waba_opt_in': True,
            'number': data['number'],
            'conv_type': data['conv_type'],
        }

    def decide_first_status(self):
        self.ensure_one()
        limit = 1
        if self.status == 'done':
            self.set_to_new()
            limit = 22
        elif self.status == 'current':
            if (self.connector_id.reassign_current_conversation and
                    not self.agent_id.chatroom_active()):
                self.with_context(force_reassign=True).set_to_new()
                limit = 22
            else:
                limit = 1
        else:
            limit = 1
        return limit

    def new_message_hook(self, message_id, limit, data, last_sent):
        return limit, True

    def get_channel_to_many(self):
        self.ensure_one()
        return self.env.cr.dbname, self._name, self.connector_id.company_id.id, self.connector_id.id

    def get_channel_to_one(self, user_id=None):
        self.ensure_one()
        if not user_id:
            user_id = self.agent_id
        # Add user at the end
        return self.env.cr.dbname, self._name, 'private', self.connector_id.company_id.id, user_id.id

    def get_bus_channel(self):
        self.ensure_one()
        channel = None
        if self.agent_id and self.status == 'current':
            channel = self.get_channel_to_one()
        else:
            channel = self.get_channel_to_many()
        return channel

    @api.model
    def parse_notification(self, datas):
        return datas

    def filter_notification(self, datas):
        '''
            Esta funcion deberia ser model pero se usa los registros en self
            en las herencias
        '''
        return datas

    def _sendmany(self, datas):
        notifications = self.parse_notification(self.filter_notification(datas))
        if notifications:
            self.env['bus.bus']._sendmany(notifications)

    def _sendone(self, channel, notification_type, message):
        self._sendmany([[channel, notification_type, message]])

    def update_conversation_bus(self):
        data_to_send = self.build_dict(limit=0)
        self._sendone(self.get_channel_to_many(), 'update_conversation', data_to_send)

    @api.model
    def new_message_event(self, connector_id, msgid, data):
        Messages = self.env['acrux.chat.message']
        message_id = Messages.search([('connector_id', '=', connector_id.id),
                                      ('msgid', '=', msgid)], limit=1)
        if message_id:
            message_id.process_message_event(data)
            if not message_id.mute_notify:
                conv_id = message_id.contact_id
                data_to_send = conv_id.build_dict(limit=0)
                data_to_send[0]['messages'] = message_id.get_js_dict()
                if data['type'] == 'failed':
                    conv_id._sendone(conv_id.get_bus_channel(), 'error_messages', data_to_send)
                else:
                    conv_id._sendone(conv_id.get_channel_to_many(), 'update_conversation', data_to_send)
        return message_id

    def get_product_caption(self, product_id):
        self.ensure_one()
        if not product_id:
            raise ValidationError('Product is required.')
        text = ''
        product_caption = (self.connector_id.product_caption or '').strip()
        if product_caption:
            def format_price(price):
                return formatLang(self.env, price, currency_obj=self.env.company.currency_id)
            local_dict = {
                'env': self.env,
                'format_price': format_price,
                'product_id': product_id,
                'conversation_id': self,
                'text': ''
            }
            safe_eval(product_caption, locals_dict=local_dict, mode='exec', nocopy=True)
            text = local_dict.get('text', '') or ''
        return (text or '').strip()

    def send_message(self, msg_data, check_access=True):
        self.ensure_one()
        if check_access:
            if self.status != 'current':
                raise ValidationError(_('You can\'t write in this conversation, please refresh the screen.'))
            if self.agent_id != self.env.user:
                raise ValidationError(_('This conversation is no longer attended to by you.'))
        AcruxChatMessages = self.env['acrux.chat.message']
        js_id = msg_data['id'] if 'id' in msg_data and msg_data['id'] < 0 else None
        msg_data['contact_id'] = self.id
        msg_data = self.split_complex_message(msg_data)
        if msg_data.get('chat_list_id'):
            ListModel = self.env['acrux.chat.message.list']
            msg_data['chat_list_id'] = ListModel.browse(msg_data['chat_list_id']).copy({'active': False}).id
        message_obj = AcruxChatMessages.create(msg_data)
        message_obj.message_send()
        data_to_send = self.build_dict(limit=0)
        data_to_send[0]['messages'] = message_obj.get_js_dict()
        data_to_send[0]['messages'][0]['js_id'] = js_id
        self._sendone(self.get_channel_to_many(), 'update_conversation', data_to_send)
        return message_obj.get_js_dict()

    def send_message_product(self, prod_id):
        self.ensure_one()
        product_id = self.env['product.product'].browse(prod_id)
        attach = get_binary_attach(self.env, 'product.product', prod_id, 'image_512',
                                   fields_ret=['id'], product_id=product_id)
        if attach:
            msg_data = {
                'text': self.get_product_caption(product_id),
                'from_me': True,
                'is_product': True,
                'ttype': 'image',
                'res_model': 'ir.attachment',
                'res_id': attach.get('id'),
            }
        else:
            msg_data = {
                'text': self.get_product_caption(product_id) or product_id.display_name.strip(),
                'from_me': True,
                'ttype': 'text',
            }
        self.send_message_bus_release(msg_data, self.status)

    def split_complex_message(self, msg_data):
        return msg_data

    def send_message_bus_release(self, msg_data, back_status, check_access=True):
        ''' msg_data = {
                'ttype': 'info',
                'from_me': True,
                'contact_id': self.conversation_id,
                'res_model': False,
                'res_id': False,
                'text': 'un texto',
            }
        '''
        self.ensure_one()
        conv_id = self
        result = conv_id.send_message(msg_data, check_access)
        to_bus = False
        data_to_send = []
        if back_status == 'new':
            conv_id.set_to_new()
            to_bus = True
            message_id = self.env['acrux.chat.message'].browse([result[0]['id']])
            data_to_send = conv_id.build_dict(limit=0)
            data_to_send[0]['messages'] = message_id.get_js_dict()
        elif back_status == 'current':
            to_bus = True
            message_id = self.env['acrux.chat.message'].browse([result[0]['id']])
            data_to_send = conv_id.build_dict(limit=0)
            data_to_send[0]['messages'] = message_id.get_js_dict()
        elif back_status == 'done':
            conv_id.set_to_done()
        if to_bus:
            conv_id._sendone(conv_id.get_bus_channel(), 'new_messages', data_to_send)

    @api.model
    def get_fields_to_read(self):
        return ['id', 'name', 'number', 'agent_id', 'status', 'team_id', 'image_url',
                'number_format', 'border_color', 'res_partner_id', 'connector_id',
                'last_activity', 'desk_notify', 'connector_type', 'show_icon', 'allow_signing',
                'tag_ids', 'note', 'allowed_lang_ids', 'conv_type']

    def build_dict(self, limit, offset=0, field_names: List[str] = None):
        AcruxChatMessages = self.env['acrux.chat.message']
        Tags = self.env['acrux.chat.conversation.tag']
        if not field_names:
            field_names = self.get_fields_to_read()
        conversations = self.read(field_names)
        if limit > 0:
            for conv in conversations:
                message_id = AcruxChatMessages.search([('contact_id', '=', conv['id'])],
                                                      limit=limit, offset=offset)
                message = message_id.get_js_dict()
                message.reverse()
                conv['messages'] = message
        for conv in conversations:
            if conv['tag_ids']:
                conv['tag_ids'] = Tags.browse(conv['tag_ids']).read(['id', 'name', 'color'])
            message_id = AcruxChatMessages.search([('contact_id', '=', conv['id']),
                                                   ('ttype', 'not like', 'info%')], limit=1)
            if message_id:
                conv['last_activity'] = message_id.date_message
        return conversations

    @api.model
    def search_active_conversation(self):
        ''' For present user '''
        domain = ['|', ('status', '=', 'new'),
                  '&', ('status', '=', 'current'),
                       ('agent_id', '=', self.env.user.id)]
        conversations = self.search(domain)
        return conversations.ids

    @api.model
    def search_partner_from_number(self, conv_id):
        ResPartner = self.env['res.partner']
        domain = [('company_id', 'in', [conv_id.connector_id.company_id.id, False]),
                  ('conv_standard_numbers', 'like', conv_id.number)]
        return ResPartner.search(domain)

    @api.model
    def search_conversation_by_partner_domain(self, partner_id):
        return [('res_partner_id', '=', partner_id),
                ('company_id', '=', self.env.company.id)]

    @api.model
    def search_conversation_by_partner(self, partner_id, limit):
        self = self.with_context(acrux_from_chatter=True)
        conversations = self.search(self.search_conversation_by_partner_domain(partner_id))
        return conversations.build_dict(limit)

    def conversation_send_read(self):
        ''' Send notification of read message. '''
        for conv_id in self:
            conn_id = conv_id.connector_id
            if conn_id.ca_status and conn_id.connector_type in ['apichat.io', 'chatapi']:
                conv_id.mark_conversation_read({'phone': conv_id.number, 'chat_type': conv_id.conv_type})

    def mark_conversation_read(self, data, timeout=5):
        self.ensure_one()
        try:
            self.env.cr.execute('''
                UPDATE acrux_chat_message
                SET read_date = now()
                WHERE read_date IS NULL
                    AND contact_id IN %(conv_id)s
            ''', {'conv_id': tuple(self.ids)})
            if bool(self.env.cr.rowcount):
                self.env.cr.commit()
                self.connector_id.ca_request('msg_set_read', data, timeout=timeout, ignore_exception=True)
        except Exception as _e:
            print(_e)

    def conversation_verify_to_new(self, conn_id):
        if conn_id.time_to_reasign:
            date_to_news = date_timedelta(minutes=-conn_id.time_to_reasign)
            return self.filtered(lambda x: x.status == 'current' and
                                 x.last_received_first and
                                 x.write_date < date_to_news)
        else:
            return self.env['acrux.chat.conversation']

    def conversation_verify_to_done(self, conn_id):
        if conn_id.time_to_done:
            date_to_done = date_timedelta(days=-conn_id.time_to_done)
            ret = self.filtered(lambda x: x.write_date < date_to_done)
            return ret
        else:
            return self.env['acrux.chat.conversation']

    @api.model
    def conversation_verify(self):
        ''' Call from cron or direct '''
        Connector = self.env['acrux.chat.connector'].sudo()
        to_done_ids = to_news_ids = self.env['acrux.chat.conversation']
        for conn_id in Connector.search([]):
            sctx = self.sudo().with_context(tz=conn_id.tz,
                                            lang=conn_id.company_id.partner_id.lang,
                                            allowed_company_ids=[conn_id.company_id.id])
            add_ids = sctx.search([('connector_id', '=', conn_id.id),
                                   ('status', '!=', 'done')])
            to_news = add_ids.conversation_verify_to_new(conn_id)
            to_done = (add_ids - to_news).conversation_verify_to_done(conn_id)
            to_done_ids |= to_done
            to_news_ids |= to_news
            all_ids = to_done | to_news
            if len(all_ids):
                conv_delete_ids = all_ids.read(['id', 'agent_id'])
                for to_x in all_ids:
                    to_x.event_create('unanswered', user_id=to_x.agent_id)
                to_done.set_to_done()
                to_news.set_to_new()
                notifications = []
                notifications.append((all_ids[0].get_channel_to_many(), 'delete_taken_conversation', conv_delete_ids))
                notifications.append((all_ids[0].get_channel_to_many(), 'delete_conversation', conv_delete_ids))
                all_ids._sendmany(notifications)
                to_news._sendone(all_ids[0].get_channel_to_many(), 'new_messages', to_news.build_dict(22))
        _logger.info('________ | conversation_verify: %s to new, %s to done' % (len(to_news_ids), len(to_done_ids)))
        self.env.cr.commit()

    def block_conversation(self):
        self.ensure_one()
        if self.status in ['new', 'done']:
            back_status = self.status
            channel = self.get_bus_channel()
            self.set_to_current()
            data_to_send = {'id': self.id, 'agent_id': [self.env.user.id, self.env.user.name]}
            if back_status == 'new':
                self._sendone(channel, 'delete_conversation', [data_to_send])
        else:
            if self.agent_id.id != self.env.user.id:
                raise ValidationError(_('Customer is already being served for %s') % self.agent_id.name)
        return self.build_dict(2)

    def release_conversation(self):
        self.set_to_done()

    @api.model
    def get_message_fields_to_read(self):
        return self.env['acrux.chat.message'].get_fields_to_read()

    @api.model
    def get_attachment_fields_to_read(self):
        return ['id', 'checksum', 'mimetype', 'display_name', 'url', 'name',
                'res_model', 'res_field', 'res_id']

    @api.model
    def get_product_fields_to_read(self):
        fields_search = [
            'id', 'display_name', 'lst_price', 'uom_id',
            'write_date', 'product_tmpl_id', 'name', 'type', 'default_code',
        ]
        if 'qty_available' in self.env['product.product']._fields:
            fields_search.append('qty_available')
        if 'quantity_total' in self.env['product.product']._fields:
            fields_search.append('quantity_total')
        return fields_search

    @api.model
    def search_product(self, string, filters=None):
        ProductProduct = self.env['product.product']
        domain = [('sale_ok', '=', True)]
        filters = filters or {}
        stock_filter = filters.get('stock_filter')
        if not stock_filter and filters.get('available'):
            stock_filter = 'positive'
        if stock_filter and 'qty_available' in ProductProduct._fields:
            if stock_filter == 'positive':
                domain.append(('qty_available', '>', 0))
            elif stock_filter == 'negative':
                domain.append(('qty_available', '<=', 0))
        if string:
            if string.startswith('/cat '):
                domain += [('categ_id.complete_name', 'ilike', string[5:].strip())]
            else:
                search_name = filters.get('search_name')
                search_description = filters.get('search_description')
                if search_name or search_description:
                    if search_name and search_description:
                        domain += ['|',
                                   ('product_tmpl_id.name', 'ilike', string),
                                   ('product_tmpl_id.description', 'ilike', string)]
                    elif search_name:
                        domain.append(('product_tmpl_id.name', 'ilike', string))
                    else:
                        domain.append(('product_tmpl_id.description', 'ilike', string))
                else:
                    domain += ['|', ('name', 'ilike', string), ('default_code', 'ilike', string)]
        fields_search = self.get_product_fields_to_read()
        out = ProductProduct.search_read(domain, fields_search, order='name, list_price', limit=32)
        return out

    def init_and_notify(self):
        self.ensure_one()
        self.block_conversation()
        data_to_send = self.build_dict(22)
        channel = self.get_channel_to_one()
        self._sendone(channel, 'init_conversation', data_to_send)

    def open_conversation(self):
        '''
            Permite abrir una conversacion en chatroom.
            No importa el estado en que este la conversacion.
        '''
        self.ensure_one()
        if self.status in ['new', 'done']:
            self.init_and_notify()
        else:  # es current
            if self.agent_id == self.env.user:
                self.init_and_notify()
            else:
                self._sendone(self.get_channel_to_many(), 'init_conversation', self.build_dict(22))

    @api.model
    def conversation_create(self, partner_id, connector_id, number):
        Connector = self.env['acrux.chat.connector']
        if connector_id:
            connector_id = Connector.browse(connector_id)
        else:
            connector_id = Connector.search([], limit=1)
        number = connector_id.clean_id(number)
        connector_id.assert_id(number)
        vals = {
            'name': number,
            'number': number,
            'connector_id': connector_id.id,
            'status': 'done'
        }
        if partner_id:
            vals['name'] = partner_id.name
            vals['res_partner_id'] = partner_id.id
        conv_id = self.create(vals)
        return conv_id

    @api.model
    def contact_update(self, connector_id, data):
        number = data.get('number', '')
        image_url = data.get('image_url') or ''
        if number and image_url:
            conv_id = self.search([('number', '=', number),
                                   ('connector_id', '=', connector_id.id)])
            if conv_id:
                if image_url and image_url.startswith('http'):
                    raw_image = get_image_from_url(image_url)
                    conv_id.image_128 = raw_image

    @api.model
    def _get_message_allowed_types(self):
        return ['text', 'image', 'audio', 'video', 'file', 'location', 'sticker']

    @api.model
    def parse_message_receive(self, connector_id, message):
        ttype = message.get('type')
        text = message.get('txt')
        text = text or ''
        if ttype not in self._get_message_allowed_types():
            text = text or 'Message type Not allowed (%s).' % ttype
            ttype = 'text'
        if message.get('time'):
            date_msg = datetime.fromtimestamp(message.get('time'))
        else:
            date_msg = fields.Datetime.now()
        out = {
            'ttype': ttype,
            'connector_id': connector_id.id,
            'name': message.get('name'),
            'msgid': message.get('id', False),
            'number': connector_id.clean_id(message.get('number', '')),
            'message': text.strip(),
            'filename': message.get('filename', ''),
            'url': message.get('url', ''),
            'time': date_msg,
            'conv_type': 'none',
        }
        if message.get('metadata'):
            out['metadata'] = message['metadata']
        if message.get('id'):
            if connector_id.connector_type in ['apichat.io', 'chatapi']:
                out['from_me'] = message['id'].split('_')[0] == 'true'
                if '@l.us' in message.get('id'):
                    out['conv_type'] = 'private'
                    out['number'] = message.get('number', '')
                elif '@c.us' in message.get('id'):
                    out['conv_type'] = 'normal'
            else:
                out['conv_type'] = 'normal'
        return out

    @api.model
    def parse_contact_receive(self, connector_id, data):
        data['number'] = connector_id.clean_id(data.get('number', ''))
        return data

    @api.model
    def parse_event_receive(self, connector_id, event):
        if event.get('type') == 'failed':
            out = {
                'type': event.get('type'),
                'msgid': event.get('msgid'),
                'reason': event.get('txt'),
            }
        elif event.get('type') == 'phone-status':
            out = event
        else:
            out = event
        return out

    @api.model
    def new_webhook_event(self, connector_id, event):
        ttype = event.get('type')
        if ttype == 'failed':
            if event['msgid'] and event['reason']:
                self.new_message_event(connector_id, event['msgid'], event)
            _logger.warning(event)
        elif ttype == 'phone-status':
            connector_id.ca_status_change(event.get('status'))
        elif ttype == 'pending' and connector_id.connector_type == 'gupshup':
            if event.get('msgid') and event.get('wa_id'):
                message_id = self.env['acrux.chat.message'].search(
                    [('msgid', '=', event['msgid']), ('connector_id.connector_type', '=', 'gupshup')],
                    limit=1)
                message_id.msgid = event['wa_id']
        elif event.get('type') == 'opt_update' and connector_id.connector_type == 'gupshup':
            self.update_opt_in(connector_id, event)

    @api.model
    def check_object_reference(self, postfix, view):
        return self.sudo().env['ir.model.data'].check_object_reference('whatsapp_connector%s' % (postfix or ''), view)

    def delegate_conversation(self):
        self.ensure_one()
        conv_delete_ids = self.read(['id', 'agent_id'])
        if self.status != 'new':
            self.with_context(ignore_agent_id=True).set_to_new()
        if self.tmp_agent_id:
            self.with_user(self.tmp_agent_id).set_to_current()
        notifications = []
        notifications.append((self.get_channel_to_many(), 'delete_taken_conversation', conv_delete_ids))
        notifications.append((self.get_channel_to_many(), 'delete_conversation', conv_delete_ids))
        data = self.build_dict(22)
        if self.tmp_agent_id:
            self.tmp_agent_id = False
            for r in data:
                r['assigned'] = True
            notifications.append((self.get_channel_to_one(), 'assign_conversation', data))
        else:
            notifications.append((self.get_channel_to_many(), 'new_messages', data))
        self._sendmany(notifications)

    def toggle_opt_in(self):
        self.ensure_one()
        self.sent_opt_in = True
        self.is_waba_opt_in = not self.is_waba_opt_in
        if not self.mute_opt_in and not self.is_waba_opt_in:
            data_to_send = {
                'conv': self.id,
                'name': self.name_get()[0][1],
                'opt_in': self.is_waba_opt_in
            }
            self._sendone(self.get_channel_to_many(), 'opt_in', data_to_send)
        # opt-in is removed from gupshup
        # data = {
        #     'number': self.number,
        #     'opt_in': not self.is_waba_opt_in
        # }
        # self.connector_id.ca_request('opt_in', data)

    @api.model
    def update_opt_in(self, connector_id, event):
        conv = self.search([('connector_id', '=', connector_id.id),
                            ('number', '=', connector_id.clean_id(event['number']))], limit=1)
        if conv:
            conv.is_waba_opt_in = event['opt_in']
            if not conv.mute_opt_in and not conv.is_waba_opt_in:
                data_to_send = {
                    'conv': conv.id,
                    'name': conv.name_get()[0][1],
                    'opt_in': event['opt_in']
                }
                conv._sendone(conv.get_channel_to_many(), 'opt_in', data_to_send)

    @api.model
    def fix_message_read_date(self):
        '''
            To execute after install
        '''
        self.env.cr.execute('''UPDATE acrux_chat_message SET read_date = date_message WHERE read_date IS NULL''')

    def refresh_api_data(self):
        self.ensure_one()
        self.update_conversation()
        self.update_conversation_bus()

    @api.depends('activity_date_deadline')
    def _compute_kanban_state(self):
        today = date.today()
        for conv in self:
            kanban_state = 'grey'
            if conv.activity_date_deadline:
                lead_date = fields.Date.from_string(conv.activity_date_deadline)
                if lead_date >= today:
                    kanban_state = 'green'
                else:
                    kanban_state = 'red'
            conv.kanban_state = kanban_state

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Always display all stages """
        return stages.search([], order=order)

    @api.model
    def fix_opt_in_to_true(self):
        '''
            To execute after update
        '''
        conv_ids = self.search([('sent_opt_in', '=', False), ('is_waba_opt_in', '=', False)])
        conv_ids.write({'sent_opt_in': True, 'is_waba_opt_in': True})

    def close_from_ui(self):
        self.ensure_one()
        if self.status == 'new' or (self.status == 'current' and self.agent_id == self.env.user):
            self.release_conversation()

    @api.model
    def web_read_group(self, domain, fields, groupby, limit=None, offset=0, orderby=False,
                       lazy=True, expand=False, expand_limit=None, expand_orderby=False):
        out = super(AcruxChatConversation, self).web_read_group(domain, fields, groupby, limit, offset, orderby,
                                                                lazy, expand, expand_limit, expand_orderby)
        if self.env.context.get('chatroom_fold_null_group') and out.get('length') > 0:
            for group in out['groups']:
                if group.get('stage_id', None) is False:
                    group['__fold'] = True
        return out

    @api.model
    def get_config_parameters(self):
        Config = self.env['ir.config_parameter'].sudo()
        return {
            'chatroom_tab_orientation': Config.get_param('chatroom_tab_orientation')
        }
