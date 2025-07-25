# -*- coding: utf-8 -*-
import logging
import json
import werkzeug
from odoo import http, _, SUPERUSER_ID
from odoo.http import request, Response
from odoo.exceptions import UserError
from odoo.addons.base.models.ir_qweb import QWebException
from psycopg2 import OperationalError
from psycopg2.extensions import TransactionRollbackError
_logger = logging.getLogger(__name__)


def log_request(req):
    pass


def acrux_allowed_models():
    return ['product.template', 'product.product', 'acrux.chat.new.group.wizard', 'acrux.chat.conversation']


class WebhookController(http.Controller):

    @http.route('/acrux_webhook/test', auth='public', type='http')
    def acrux_webhook_test(self, **post):
        return Response(status=200)

    @http.route('/acrux_webhook/whatsapp_connector/<string:connector_uuid>',
                auth='public', type='json', methods=['POST'])
    def acrux_webhook(self, connector_uuid, **post):
        ''' Keeping URLs secret. '''
        try:
            if not post:
                return Response(status=403)  # Forbidden
            log_request(request)

            updates = post.get('updates', [])
            events = post.get('events', [])
            messages = post.get('messages', [])
            if not updates and not events and not messages:
                return Response(status=403)  # Forbidden

            Connector = request.env['acrux.chat.connector'].with_user(SUPERUSER_ID).sudo()
            connector_id = Connector.search([('uuid', '=', connector_uuid)], limit=1)
            if not connector_id or not connector_uuid:
                return Response(status=403)  # Forbidden
            ctx = {
                'tz': connector_id.tz,
                'lang': connector_id.company_id.partner_id.lang,
                'allowed_company_ids': [connector_id.company_id.id],
                'from_webhook': True
            }
            connector_id = connector_id.with_context(ctx)
            Conversation = request.env['acrux.chat.conversation'].with_user(SUPERUSER_ID).sudo().\
                with_context(ctx)

            for contact in updates:
                contact = Conversation.parse_contact_receive(connector_id, contact)
                Conversation.contact_update(connector_id, contact)

            for event in events:
                event = Conversation.parse_event_receive(connector_id, event)
                Conversation.new_webhook_event(connector_id, event)

            for mess in messages:
                data = Conversation.parse_message_receive(connector_id, mess)
                if data['conv_type'] != 'none':
                    Conversation.new_message(data)
                else:
                    _logger.warning(f'message {data.get("number")} ignored')

            return Response(status=200)
        except (TransactionRollbackError, OperationalError, QWebException) as e:
            raise e
        except Exception:
            request._cr.rollback()
            _logger.error('Error', exc_info=True)
            return Response(status=500)  # Internal Server Error

    def chek_error(self, status, content, headers):
        if status == 304:
            return Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        if not content:
            return Response(status=404)

    @http.route(['/web/chatresource/<int:id>/<string:access_token>',
                 '/web/static/chatresource/<string:model>/<string:id>/<string:field>'],
                type='http', auth='public', sitemap=False)
    def acrux_web_content(self, id=None, model=None, field=None, access_token=None):
        '''
        /web/chatresource/...        -> for attachment
        /web/static/chatresource/... -> for product image
        :param field: field (binary image, PNG or JPG) name in model. Only support 'image'.
        '''

        IrBinary = request.env['ir.binary'].sudo()
        try:
            if id and access_token and not model and not field:
                record = IrBinary._find_record(res_id=int(id), access_token=access_token)
                stream = IrBinary._get_stream_from(record)
            else:
                if not id or not field.startswith('image') or model not in acrux_allowed_models():
                    return Response(status=404)

                id, sep, unique = id.partition('_')
                record = IrBinary._find_record(res_model=model, res_id=int(id))
                stream = IrBinary._get_image_stream_from(record, field_name=field,
                                                         placeholder='web/static/img/XXXXX.png')
        except Exception:
            return Response(status=404)

        response = stream.get_response()
        return response


class Binary(http.Controller):

    @http.route('/web/binary/upload_attachment_chat', methods=['POST'], type='http', auth='user')
    def mail_attachment_upload(self, ufile, thread_id, thread_model, is_pending=False, **kwargs):
        ''' Source: web.controllers.discuss.DiscussController.upload_attachment '''
        try:
            limit = int(request.env['ir.config_parameter'].sudo().get_param('acrux_max_weight_kb') or '0')
            Attach = request.env['ir.attachment']
            datas = ufile.read()
            if len(datas) > limit * 1024:
                raise UserError(_('Too big, max. %s (%s)') % ('%sMb' % int(limit / 1000), ufile.filename))
            vals = {
                'name': ufile.filename,
                'raw': datas,
                'res_id': 0,
                'res_model': 'acrux.chat.message',
                'delete_old': True,
                'public': True
            }
            if is_pending and is_pending != 'false':
                # Add this point, the message related to the uploaded file does
                # not exist yet, so we use those placeholder values instead.
                vals.update({
                    'res_id': 0,
                    'res_model': 'acrux.chat.message',
                })
            vals['access_token'] = Attach._generate_access_token()
            attachment = Attach.create(vals)
            if ufile.mimetype:
                attachment.mimetype = ufile.mimetype
            attachment._post_add_create()
            attachmentData = {
                'filename': ufile.filename,
                'id': attachment.id,
                'mimetype': attachment.mimetype,
                'name': attachment.name,
                'size': attachment.file_size,
                'isAcrux': True,
            }
            if attachment.access_token:
                attachmentData['accessToken'] = attachment.access_token
        except UserError as e:
            attachmentData = {'error': e.args[0], 'filename': ufile.filename}
            _logger.exception("Fail to upload attachment %s" % ufile.filename)
        except Exception:
            attachmentData = {'error': _("Something horrible happened"), 'filename': ufile.filename}
            _logger.exception("Fail to upload attachment %s" % ufile.filename)
        return request.make_response(
            data=json.dumps(attachmentData),
            headers=[('Content-Type', 'application/json')]
        )
