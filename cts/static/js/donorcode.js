$(document).ready(function() {
  // DATATABLES
  var table = $('#donorcodes-table-1').DataTable({
    "searching": false,  /* must be true to use search even from the API */
    "dom": "lrtip",  /* don't show datatables' searchbox */
    "orderClasses": false,
    "paging": false,
    "stateSave": true  // so we keep the same filters and sorting from last time
  });

  $('.donorcode-edit-pencil').on('click', function(){
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'donorcode_edit_modal', 'submit-edit-donorcode-button',
            'edit_donorcode_form', submit_url);
      }
    });
  });

  $('#new-donorcode-button').on('click', function() {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new_donorcode_modal', 'submit-new-donorcode-button',
            'new_donorcode_form', submit_url);
      }
    });
  });

  // now that we're done messing with the table, render it once
  $('#donorcode-table-1').removeClass('hidden');
});
