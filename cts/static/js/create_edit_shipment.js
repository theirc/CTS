/*global $, ajax_alert, clear_ajax_alerts, report_ajax_error, fill_item_modal */
$(document).ready(function () {
  $('#shipment_selector').on('change', function () {

    var url = $('#shipment_selector option:selected').attr('data-url');

    if (url === undefined) {
      return;
    }

    /* Unset dirty on this form only, so session_security won't warn user that
     they're leaving an unsaved form if this is the only change.
     */
    $('form#select_shipment_form').removeAttr('data-dirty');

    document.location = url;

    /* If we let the change continue to be processed, this form will
     get marked dirty, which we don't want.
     */
    return false;
  });

  var get_selected_package_pk = function () {
    return sessionStorage.getItem('package_pk');
  };

  var get_pkg_name = function (pk) {
    /* Get name of specified pkg by querying the text in the select control */
    var selected_link = $('.pkg_selection_link[data-pk="' + pk + '"]');
    return selected_link.html();
  };

  /* Select the package with the specified PK */
  var select_package = function (pk) {
    // Is the pk valid?
    var matching_links = $('.pkg_selection_link[data-pk="' + pk + '"]');
    if (matching_links.length === 0) {
      return;
    }

    // Mark the selected package row
    $('tr.package-row.selected').removeClass('selected');
    $('tr#package-row-' + pk).addClass('selected');

    sessionStorage.setItem('package_pk', pk);
    $('#select-pkg-dropdown').html(get_pkg_name(pk));

    /* update the item table */
    var url = window.location.href.replace(/shipments.*/, 'shipments/package/items/' + pk + '/');

    $.ajax({
      url: url,
      dataType: 'HTML',
      success: function (data) {
        $('#selected_package_table_div').addClass('hidden');
        if ($.fn.dataTable.isDataTable('#items-table-1')) {
          $('#items-table-1').DataTable().destroy();
        }
        // Remove any existing body and footer
        $('#items-table-1 tbody').remove();
        $('#items-table-1 tfoot').remove();

        // add the new body and footer to the DOM after the head
        $('#items-table-1 thead').after($(data));


        $('#items-table-1').DataTable({
          "dom": "lrtip",  /* don't show datatables' searchbox */
          "paging": false,
          "stateSave": true,  // so we keep the same sorting from last time
          "columnDefs": [{    // first column, last 2 columns not sortable
            'orderable': false,
            'targets': [0, -1, -2]
          }]
        });
        $('#selected_package_table_div').removeClass('hidden');
      }
    });
  };

  $('#package_item_all_or_none_checkbox').on('change', function () {
    $('input[name="package_item"]').prop('checked', $(this).prop('checked'));
  });

  $('#bulk_button').on('click', function () {
    var selected_items = $('input[name="package_item"]:checked');
    if (selected_items.length === 0) {
      ajax_alert("warning", "Please select at least one package item to bulk edit.");
      return;
    }
    var item_pks = $.map(selected_items, function (item) { return $(item).attr('value'); });
    item_pks = item_pks.join(",");
    var url = $(this).attr('data-url');
    $.ajax({
      url: url,
      dataType: 'HTML',
      data: {
        'selected_items': item_pks
      },
      success: function (data) {
        fill_item_modal(
          data,
          'bulk-edit-package-items-modal',
          'submit-bulk-edit-package-items-button',
          'bulk-edit-package-items-form',
          url
        );
      },
      error: report_ajax_error
    });
  });

  $('#create_package_from_kit_button').on('click', function () {
    var submit_url = $(this).attr('data-url'),
        form_id = 'new_pkg_from_kit_form';
    var new_pkg_success = function (rsp_data) {
      var pkg_pk = rsp_data;
      // change selected package upon reload:
      sessionStorage.setItem('package_pk', pkg_pk);
      /* Tell session_security that the form is no longer dirty */
      $('#' + form_id).removeAttr('data-dirty');
      /* Reload the page to show the change */
      window.location.reload(true);
    };
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new-package-from-kit-modal', 'submit-new-pkg-button',
            form_id, submit_url, new_pkg_success);
      },
      error: report_ajax_error
    });
  });

  $('#create_package_button').on('click', function () {
    var submit_url = $(this).attr('data-url');
    var modal_id = "new-package-modal";
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, modal_id, 'submit-new-pkg-button',
            'new_pkg_form', submit_url);
      },
      error: report_ajax_error
    });
  });

  $('#add_item_to_package_button').on('click', function () {
    var base_url = $(this).data('url');
    var submit_url = base_url.replace('9999', get_selected_package_pk());
    var modal_id = 'new-package-modal';
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, modal_id, 'add-package-item-button',
            'create-package-item-form', submit_url);
      },
      error: report_ajax_error
    });
  });

  $('#edit_package_details_button').on('click', function () {
    clear_ajax_alerts();
    var base_url = $(this).attr('data-url');
    var submit_url = base_url.replace('9999', get_selected_package_pk());
    var modal_id = "edit-package-details-modal";
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, modal_id, 'submit-new-pkg-button',
            'new_pkg_form', submit_url);
      },
      error: report_ajax_error
    });
  });

  $('#items-table-1').delegate('.edit-package-item-button', 'click', function () {
    clear_ajax_alerts();
    var url = $(this).attr('data-url');
    var modal_id = 'edit-package-item-modal';
    $.ajax({
      url: url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, modal_id, 'submit-package-item-button',
                        'edit-package-item-form', url);
      },
      error: report_ajax_error
    });
  });

  $('#items-table-1').DataTable({
    "paging": false
  });
  $('#more-actions-button').popover({
    html: true,
    content: function () {
      return $('#more-actions-popover').html();
    },
    trigger: 'focus'
  });

  /* Load data for the packages table */
  var $packages_table = $('tbody#packages_rows');
  $packages_table.load(
    $packages_table.attr('data-url'),
    function() {
      $('.pkg_selection_link, tr.package-row').on('click', function () {
        var pk = $(this).attr('data-pk');
        select_package(pk);
      });

      /* On page load, if package was selected before, select it again */
      if (get_selected_package_pk()) {
        select_package(get_selected_package_pk());
      }
    }
  );

  /* No forms can be dirty yet, but session_security might have marked some dirty
     while select.js was changing things around.
   */
  $('form[data-dirty=true]').removeAttr('data-dirty');
});
