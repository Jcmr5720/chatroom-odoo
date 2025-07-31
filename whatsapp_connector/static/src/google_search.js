odoo.define('whatsapp_connector.google_search', function (require) {
    'use strict';
    var $ = require('jquery');
    $(document).on('submit', '.o_GoogleSearchForm', function (ev) {
        ev.preventDefault();
        var $form = $(this);
        var query = $form.find('input[name="q"]').val();
        var type = $form.find('select[name="tb"]').val();
        var url = 'https://www.google.com/search?q=' + encodeURIComponent(query);
        if (type) {
            url += '&tb=' + encodeURIComponent(type);
        }
        $form.closest('.o_GoogleSearchTab').find('.o_GoogleSearchResult').attr('src', url);
    });
});
