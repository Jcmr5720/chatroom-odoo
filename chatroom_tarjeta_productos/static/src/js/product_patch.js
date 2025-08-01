odoo.define('chatroom_tarjeta_productos.product_patch', async function (require) {
    'use strict';
    let __exports = {};
    const { patch } = require('@web/core/utils/patch');
    const { ProductModel } = require('@a57f7a72eb29be2e68a9675edd680394d67e2ecd8df85dc2c38e83822c8551e8');

    const productPatch = {
        constructor() {
            this._super(...arguments);
            this.qtySan = 0.0;
            this.qtyTul = 0.0;
            this.qtyNeu = 0.0;
        },
        updateFromJson(base) {
            this._super(base);
            if ('quantity_in_location' in base) {
                this.qtySan = base.quantity_in_location;
            }
            if ('quantity_in_tulipanes' in base) {
                this.qtyTul = base.quantity_in_tulipanes;
            }
            if ('quantity_in_neutron' in base) {
                this.qtyNeu = base.quantity_in_neutron;
            }
        },
    };
    patch(ProductModel.prototype, 'chatroom_tarjeta_productos', productPatch);
    return __exports;
});

