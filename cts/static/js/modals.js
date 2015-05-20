/* Common code for popping up modals */

function ajax_alert(level, message) {
  /* Add an alert to the top of the page.
  level=alert levels from bootstrap, e.g. success, info, warning, or danger.
  message is a text message.
   */
  var template = $('#ajax_alert_template').html();
  var new_html = template.replace('MESSAGE', message).replace('ALERT_LEVEL', level);
  $('#ajax_alert_container').html($('#ajax_alert_container').html() + new_html);
}

function clear_ajax_alerts() {
  /* Clear any existing alerts */
  $('#ajax_alert_container').html('');
}

function report_ajax_error(jqXHR) {
  var msg = 'Sorry, there was an error contacting the server';
  if (jqXHR.status > 0 || jqXHR.statusText !== '') {
    msg = msg + ':';
    if (jqXHR.status > 0) {
      msg = msg + ' ' + jqXHR.status;
    }
    if (jqXHR.statusText !== '') {
      msg = msg + ' ' + jqXHR.statusText;
    }
  }
  ajax_alert('danger', msg);
}


// ADD OR EDIT ITEM
function fill_item_modal(data, modal_id, button_id, form_id, submit_url, on_success, show_modal) {
  // on_success: optional callback when form is submitted successfully
  // show_modal: if false, don't show the modal; use this if the modal is already visible
  //             because jquery doesn't handle showing an already-visible modal well.
  $('#' + button_id).off();
  $('#' + modal_id + ' div.modal-content').html(data);
  $('#' + button_id).on('click', function () {
    var options = {
      url: submit_url,
      type: 'POST',
      complete: function (jqXHR, status) {
        /* 'complete' gets called no matter what the response, so we can divide
         * up the cases to handle it however we want.
         */
        var rsp_data = jqXHR.responseText;
        if (status === 'success') {
          if (on_success) {
            on_success(rsp_data);
          } else {
            /* Tell session_security that the form is no longer dirty */
            $('#' + form_id).removeAttr('data-dirty');
            /* Default is to reload the page to show the change */
            window.location.reload(true);
          }
        } else if (jqXHR.status === 400) {
          // whoops, some error in the form
          fill_item_modal(rsp_data, modal_id, button_id, form_id, submit_url,
                          on_success, false);
        } else {
          report_ajax_error(jqXHR);
        }
      }
    };
    $('#' + form_id).ajaxSubmit(options);
  });
  /* Tell session_security that the form is no longer dirty */
  $('#' + form_id).removeAttr('data-dirty');
  if (show_modal !== false) {
    $('#' + modal_id).modal('show');
  }
  return false;
}
