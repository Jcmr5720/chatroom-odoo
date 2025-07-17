{
    'name': 'website_pages_tecnolosys',
    'summary': 'Modulo encargado de personalizar el sitio web tecnolosys como paginas nuevas, estilos y scripts.',
    'version': '1.0',
    'author': 'Juan Camilo Muñoz',
    'category': 'Tools',
    'depends': [
        'loyalty',
        'website',
        'web',
        'web_editor',
        'portal',
        'sale',
        'website_sale',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/templates_test.xml',

        'views/test/test.xml',

        'views/home/gtm.xml',
        'views/home/modal.xml',
        'views/home/container_promo.xml',
        'views/home/container1.xml',
        'views/home/container2.xml',
        'views/home/container3.xml',

        'views/snippets/s_dynamic_snippet3.xml',
        'views/snippets/s_dynamic_snippet4.xml',
        'views/snippets/s_dynamic_snippet5.xml',
        'views/snippets/s_dynamic_snippet6.xml',

        'views/products/product_views.xml',

        'views/portal/web_pqr.xml',
        'views/portal/web_pqr_category.xml',
        'views/portal/web_pqr_motivo.xml',
        'views/portal/menu.xml',
        'views/portal/portal_pqr_inherit.xml',
        'views/portal/portal_pqr_table.xml',
        'views/portal/portal_pqr_form.xml',
        'views/portal/portal_pqr_public_form.xml',
        'views/portal/portal_pqr_page.xml',

        'views/website/custom_header_templates.xml',

        'data/data_website.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            ('include', 'web._assets_bootstrap'),
            'website_pages_tecnolosys/static/src/scss/container_promo.scss',
            'website_pages_tecnolosys/static/src/scss/container1.scss',
            'website_pages_tecnolosys/static/src/scss/container2.scss',
            'website_pages_tecnolosys/static/src/scss/container3.scss',

            'website_pages_tecnolosys/static/src/scss/snippet1.scss',
            'website_pages_tecnolosys/static/src/scss/snippet2.scss',
            'website_pages_tecnolosys/static/src/scss/snippet3.scss',
            'website_pages_tecnolosys/static/src/scss/snippet4.scss',

            'website_pages_tecnolosys/static/src/scss/popupmodal.scss',

            'website_pages_tecnolosys/static/src/js/pqr_lightbox.js',
            'website_pages_tecnolosys/static/src/js/modal.js',
            'website_pages_tecnolosys/static/src/js/flashsaletimer.js',

            'website_pages_tecnolosys/static/src/scss/product_views.scss',
            'website_pages_tecnolosys/static/src/scss/custom_header.scss',

            'website_pages_tecnolosys/static/src/scss/main.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'GPL-3'
}