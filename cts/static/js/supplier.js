$(document).ready(function() {
  // DATATABLES
  var table = $('#suppliers-table-1').DataTable({
    "searching": false,  /* must be true to use search even from the API */
    "dom": "lrtip",  /* don't show datatables' searchbox */
    "orderClasses": false,
    "paging": false,
    "stateSave": true  // so we keep the same filters and sorting from last time
  });

  $('.supplier-edit-pencil').on('click', function(){
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'supplier_edit_modal', 'submit-edit-supplier-button',
            'edit_supplier_form', submit_url);
      }
    });
  });

  $('#new-supplier-button').on('click', function() {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new_supplier_modal', 'submit-new-supplier-button',
            'new_supplier_form', submit_url);
      }
    });
  });

  // now that we're done messing with the table, render it once
  $('#suppliers-table-1').removeClass('hidden');
});
