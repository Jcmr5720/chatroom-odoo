odoo.define('website_pages_tecnolosys.popupmodal', function (require) {
    'use strict';

    $(document).ready(function () {

        var modalKey = 'reset_modal_time';
        var modalBack = Math.floor(Date.now() / 1000);
        var modalTimeReset = 1 * 24 * 60 * 60;
        var modalReset = Number(localStorage.getItem(modalKey));

        if (!modalReset || modalReset < Number(modalBack)) {
            $('#myModal').modal('show');
            modalReset = modalBack + modalTimeReset;
            localStorage.setItem(modalKey, modalReset);

            $('#myBtnClose, .close').click(function () {
                console.log('save_modal');
                $('#myModal').modal('hide');
            });
        } else {
            console.log('run_modal');
        }


    });
});
