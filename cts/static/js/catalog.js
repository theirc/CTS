/*global $, report_ajax_error, fill_item_modal, ajax_alert, clear_ajax_alerts */
$(document).ready(function () {
  //
  // CATALOG ITEMS
  var table = $('#items-table-1').DataTable({
    "searching": true,  /* must be true to use search even from the API */
    "dom": "lrtip",  /* don't show datatables' searchbox */
    "orderClasses": false,
    "paging": false,
    "stateSave": true  // so we keep the same filters and sorting from last time
  });

  $('.item-edit-pencil').on('click', function () {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'catalog_item_edit_modal', 'submit-edit-item-button',
            'edit_item_form', submit_url);
      },
      error: report_ajax_error
    });
  });

  $('#new-item-button').on('click', function () {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new_catalog_item_modal', 'submit-new-item-button',
            'new_item_form', submit_url);
      },
      error: report_ajax_error
    });
  });

  $('#reset-quantities').on('click', function () {
    $('input.item-quantity-field').val('');
  });

  //
  // KITS
  //
  /* Select kit */
  var get_selected_kit_pk = function () {
    return sessionStorage.getItem('kit_pk');
  };

  var get_selected_kit_name = function () {
    /* Get name of selected kit by querying the text in the select control */
    var selected_link = $('.kit_selection_link[data-pk="' + get_selected_kit_pk() + '"]');
    return selected_link.html();
  };

  var clear_item_quantities = function() {
    $('.item-quantity-field').val('');
  };

  var change_selected_kit = function (kit_pk) {
    // Change the selected kit.
    // make sure the pk is valid
    if ($('.kit_selection_link[data-pk="' + kit_pk + '"]').length === 0) {
      return;
    }
    // Is it a change?
    var was_changed = (kit_pk !== get_selected_kit_pk());
    sessionStorage.setItem('kit_pk', kit_pk);
    $('input[name=selected_kit]').val(kit_pk);
    /* display the parts of the page that are only displayed if a kit has been selected */
    $('.hide_if_no_kit_selected').removeClass('hidden');
    $('a#select-kit-dropdown').html(get_selected_kit_name());
    $('#edit_kit_button').html("View Kit");
    $('#edit_kit_button').parent().removeClass('hidden');
    clear_ajax_alerts();
    clear_item_quantities();
    if (was_changed) {
      ajax_alert("info", "You've selected the <b>" + get_selected_kit_name() +
        "</b> kit. When you use the '+' button next to an item, the " +
        "quantity you specify will be added to this kit.");
    }
  };

  $('.kit_selection_link').on('click', function () {
    var pk = $(this).attr('data-pk');
    if (pk) {
      change_selected_kit(pk);
    }
  });

  /* New kit */
  $('#new-kit-button').on('click', function () {
    var submit_url = $(this).attr('data-url');
    var modal_id = 'new_kit_modal';
    var on_success = function (data) {
      jsonData = JSON.parse(data);
      var new_kit_pk = jsonData.kit_pk;
      /* Add a new option to the selector */
      var menuitem = $('<a>').addClass("kit_selection_link").attr({
        role: "menuitem",
        tabindex: "-1",
        "data-pk": new_kit_pk
      }).html(jsonData.name);
      var new_option = $('<li>').attr({role: "presentation"}).append(menuitem);
      $('#select-kit-dropdown').next().append(new_option);

      $('#' + modal_id).modal('hide');
      change_selected_kit(new_kit_pk);
      ajax_alert('success', 'A new kit, ' + get_selected_kit_name() + ', has ' +
                 'been created.');
    };
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, modal_id, 'submit-new-kit-button',
                        'new_kit_form', submit_url, on_success);
      }
    });
  });
  /* Edit kit */

  /* view/edit kit */
  $('#edit_kit_button').on('click', function () {
    clear_ajax_alerts();
    var kit_pk = get_selected_kit_pk();
    var url = get_kit_edit_url(kit_pk);
    var modal_id = 'edit_kit_modal';
    var on_success = function (data) {
      // Called if the changes are successfully submitted
      // Update name of kit in the selector
      var option = $('a.kit_selection_link[data-pk="' + kit_pk + '"]');
      var name = $.parseJSON(data).name;
      option.html(name);
      clear_ajax_alerts();
      $('#' + modal_id).modal('hide');
      change_selected_kit(kit_pk);
      ajax_alert('success', 'Changes have been saved');
    };
    $.ajax({
      url: url,
      dataType: 'HTML',
      type: 'GET',
      success: function (data) {
        fill_item_modal(data, modal_id, 'submit_edit_kit_button',
                        'edit_kit_form', url, on_success);
      },
      error: function (jqXHR) {
        report_ajax_error(jqXHR);
      }
    });
  });

  $('#edit_kit_modal').delegate('.kit_item_delete_button', 'click', function () {
    var item_pk = $(this).attr('data-pk');
    $('input[data-pk="' + item_pk + '"').val(0);
  });

  $('#items-table-1').delegate('.item-quantity-field', 'focus', function () {
    // Removes the error highlight from the field when the user edits it.
    $(this).parent().removeClass('has-error');
  });

  /* Add items to kit, one item type at a time */
  $('#items-table-1').delegate('.add-to-kit-circle', 'click', function () {
    var kit_pk = get_selected_kit_pk();
    var item_pk = $(this).data("pk");
    var qty_field = $('#id_quantity-' + item_pk);
    var quantity = parseInt(qty_field.val(), 10);
    var result_field = $('#result-' + item_pk);

    clear_ajax_alerts();

    if (isNaN(quantity) || quantity <= 0) {
      qty_field.parent().addClass('has-error');
      ajax_alert("error", "To add an item to this kit, provide an integer " +
                 "quantity greater than zero.");
    } else {
      qty_field.parent().removeClass('has-error');
      var url = $(this).attr('data-url').replace('8888', kit_pk).replace('9999', quantity);
      $.ajax({
        url: url,
        dataType: 'text',
        type: 'POST'
      }).success(function (data) {
        /* data is a message about what happened */
        ajax_alert('success', data);
        qty_field.val('');
        result_field.html('');
      }.bind(this)).fail(function (jqXHR) {
        result_field.html(jqXHR.responseText);
      });
    }
  });

  $('#import-button').on('click', function () {
    var modal_id = 'import_modal';
    var on_success = function (data) {
      clear_ajax_alerts();
      $('#' + modal_id).modal('hide');
      ajax_alert('success', 'Items imported');
    };
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'import_modal', 'submit-import-button',
                        'import_form', submit_url, on_success);
      }
    });
  });

  //
  // FILTERING
  //
  function set_catalog_filter(names) {
    // names = an array of category names to display
    // if the array is empty, display them all
    if (names.length === 0) {
      // turn off search
      table.column($('#category-column')).search('').draw();
    } else {
      var regex = '^' + names.join('$|^') + '$';
      table.column($('#category-column')).search(regex, true, false).draw();
    }
    if (get_selected_kit_pk()) {
      $('.hide_if_no_kit_selected').removeClass('hidden');
    }
  }
  $('.filter-checkbox').on('change', function () {
    // If select-all is checked and we just turned off another checkbox,
    // then turn off select-all too.
    if (!$(this).prop('checked') && $('#filter-select-all').prop('checked')) {
      $('#filter-select-all').prop('checked', false);
    }
    // collect selected categories, then filter
    var search_categories = [];
    $('.filter-checkbox').each(function () {
      if ($(this).prop('checked')) {
        search_categories.push($(this).attr('data-name'));
      }
    });
    set_catalog_filter(search_categories);
  });

  $('#filter-select-all').on('change', function () {
    // make all the other checkboxes the same as the select-all checkbox
    var checked = $(this).prop('checked');
    $('.filter-checkbox').prop('checked', checked);
    // turn off search - whether they're all on or all off, we show all the items
    set_catalog_filter([]);
  });

  // If there were already filters in effect,
  // initialize the checkboxes to reflect the filtering.
  var current_search = table.column($('#category-column')).search();
  if (current_search !== undefined) {
    var search_string = current_search[0];
    if (search_string !== '') {
      var regexes = search_string.split('|');
      var regex, name;
      while (regexes.length > 0) {
        regex = regexes.pop();
        name = regex.substring(1, regex.length - 1);
        $('.filter-checkbox[data-name="' + name + '"]').prop('checked', true);
      }
      $('div#collapseOne').collapse('show');  // show the filters
    }
  }
  // now that we're done messing with the table, render it once
  $('#items-table-1').removeClass('hidden');

  /* If a kit was previously selected, make it selected again */
  var kit_pk = get_selected_kit_pk();
  if (kit_pk) {
    change_selected_kit(kit_pk);
  }

  // Initialize tooltips
  $('button#reset-quantities, button#add-items-to-kit-button').tooltip();
});
