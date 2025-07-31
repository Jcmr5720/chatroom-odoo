odoo.define('whatsapp_connector.google_search', function (require) {
    'use strict';

    $(document).ready(function () {
        var $form = $('.o_GoogleSearchForm');
        if (!$form.length) {
            return;
        }
        var $iframe = $('<iframe>', {
            class: 'o_GoogleResultsIframe',
            style: 'display:none;width:100%;height:600px;border:none;'
        });
        $form.after($iframe);

        $form.on('submit', function (ev) {
            ev.preventDefault();
            var query = $(this).find('input[name="q"]').val();
            var type = $(this).find('select[name="search_type"]').val() || 'web';
            var url = 'https://www.google.com/search?q=' + encodeURIComponent(query);
            if (type === 'images') {
                url = 'https://www.google.com/search?tbm=isch&q=' + encodeURIComponent(query);
            }
            if (window.open) {
                window.open(url, '_blank', 'noopener');
            }
            if ($iframe.length) {
                try {
                    $iframe.attr('src', url).show();
                } catch (e) {
                    console.warn('Could not load results in iframe:', e);
                }
            }
        });
    });
});
