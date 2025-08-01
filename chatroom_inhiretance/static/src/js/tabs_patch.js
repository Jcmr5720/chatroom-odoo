odoo.define('chatroom_inhiretance.tabs_patch', function (require) {
    'use strict';
    const { patch } = require('@web/core/utils/patch');
    const { TabsContainer } = require('@af0df1a5affde864bfaca0edba19137ac4e7199f2cb7ae310c45d7b47aaac68b');

    patch(TabsContainer.prototype, 'chatroom_inhiretance.tabs_patch', {
        get titles() {
            const base = this._super();
            return Object.assign({}, base, { tab_calculator: this.env._t('Calculator') });
        },
    });
});
