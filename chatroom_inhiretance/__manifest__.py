{
    'name': 'ChatRoom Inhiretance',
    'version': '16.0.1.0.0',
    'summary': 'Customization for ChatRoom AI settings',
    'author': 'Chatroom',
    'license': 'OPL-1',
    'category': 'Discuss',
    'depends': ['whatsapp_connector'],
    'data': [
        'data/ai_config_data.xml',
        'views/include_template.xml',
    ],
    'qweb': [
        'static/src/xml/tabs_extension.xml',
    ],
    'installable': True,
    'application': False,
}
