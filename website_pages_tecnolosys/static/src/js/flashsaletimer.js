odoo.define('website_pages_tecnolosys.flashsaletimer', function (require) {
    'use strict';

    $(document).ready(function () {

        var flashDateRecover = $('#flashDate').val();
        if (!flashDateRecover) {
            return; 
        }
        var flashDateConvert = flashDateRecover.replace(' ', 'T');
        var flashEnd = new Date(flashDateConvert);

        function timer() {
            var flasVar1 = new Date();
            var flashLimitTime = Math.floor((flashEnd - flasVar1) / 1000);

            if (flashLimitTime <= 0) {
                clearInterval(countTime);
                $('.container-products3').hide();
                console.log('f_limit');
            } else {
                var flashDays = Math.floor(flashLimitTime / (24 * 3600));
                var flashHours = Math.floor((flashLimitTime % (24 * 3600)) / 3600);
                var flashMinutes = Math.floor((flashLimitTime % 3600) / 60);
                var flashSeconds = flashLimitTime % 60;
                var timeText =
                    String(flashDays).padStart(2, '0') + 'd : ' +
                    String(flashHours).padStart(2, '0') + 'h : ' +
                    String(flashMinutes).padStart(2, '0') + 'm : ' +
                    String(flashSeconds).padStart(2, '0') + 's';

                $('#container-products3-main-time-h2').text(timeText);
                console.log('f_count');
            }
        }

        timer();
        var countTime = setInterval(timer, 1000);
    });
});
