{
    'name': 'Tarjeta de Productos Chatroom',
    'summary': 'Muestra cantidades por bodega en tarjetas de productos',
    'version': '1.0',
    'author': 'Juan José Gamboa Ortiz',
    'depends': ['whatsapp_connector', 'product_cant_tecnolosys', 'chatroom_cantidad_productos'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'chatroom_tarjeta_productos/static/src/components/*/*.xml',
            'chatroom_tarjeta_productos/static/src/components/*/*.scss',
            'chatroom_tarjeta_productos/static/src/js/product_patch.js',
        ],
    },
    'installable': True,
    'license': 'GPL-3',
}
