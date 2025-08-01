odoo.define('chatroom_inhiretance.calculator', function (require) {
    'use strict';

    $(document).ready(function () {
        var $calc = $('.o_Calculator');
        if (!$calc.length) {
            return;
        }
        var $display = $calc.find('.o_CalcDisplay input');
        $calc.on('click', '.o_CalcButton', function () {
            var val = $(this).data('value');
            if (val === 'C') {
                $display.val('');
            } else if (val === '=') {
                try {
                    var result = eval($display.val() || '0');
                    $display.val(result);
                } catch (e) {
                    $display.val('Error');
                }
            } else {
                $display.val($display.val() + val);
            }
        });
    });
});
