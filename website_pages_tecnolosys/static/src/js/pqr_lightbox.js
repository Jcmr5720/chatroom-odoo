odoo.define('website_pages_tecnolosys.pqr_lightbox', function (require) {
    'use strict';

    $(document).on('click', '.pqr-image-wrapper', function (ev) {
        ev.preventDefault();
        var imgSrc = $(this).data('img-src');
        if (!imgSrc) {
            imgSrc = $(this).find('img').attr('src');
        }
        var $overlay = $('<div class="pqr-lightbox-overlay"><span class="close-lightbox">&times;</span><img src="' + imgSrc + '"/></div>');
        $('body').append($overlay);
        $overlay.css('display', 'flex').hide().fadeIn('fast');

        $overlay.on('click', '.close-lightbox', function (e) {
            e.stopPropagation();
            $overlay.fadeOut('fast', function () { $(this).remove(); });
        });

        $overlay.on('click', function () {
            $overlay.fadeOut('fast', function () { $(this).remove(); });
        });
    });
});
