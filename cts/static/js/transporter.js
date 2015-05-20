$(document).ready(function() {
  // DATATABLES
  var table = $('#transporters-table-1').DataTable({
    "searching": false,  /* must be true to use search even from the API */
    "dom": "lrtip",  /* don't show datatables' searchbox */
    "orderClasses": false,
    "paging": false,
    "stateSave": true  // so we keep the same filters and sorting from last time
  });

  $('.transporter-edit-pencil').on('click', function(){
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'transporter_edit_modal', 'submit-edit-transporter-button',
            'edit_transporter_form', submit_url);
      }
    });
  });

  $('#new-transporter-button').on('click', function() {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new_transporter_modal', 'submit-new-transporter-button',
            'new_transporter_form', submit_url);
      }
    });
  });

  // now that we're done messing with the table, render it once
  $('#transporters-table-1').removeClass('hidden');
});
