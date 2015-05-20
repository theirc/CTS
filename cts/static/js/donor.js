$(document).ready(function() {
  // DATATABLES
  var table = $('#donors-table-1').DataTable({
    "searching": false,  /* must be true to use search even from the API */
    "dom": "lrtip",  /* don't show datatables' searchbox */
    "orderClasses": false,
    "paging": false,
    "stateSave": true  // so we keep the same filters and sorting from last time
  });

  $('.donor-edit-pencil').on('click', function(){
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'donor_edit_modal', 'submit-edit-donor-button',
            'edit_donor_form', submit_url);
      }
    });
  });

  $('#new-donor-button').on('click', function() {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new_donor_modal', 'submit-new-donor-button',
            'new_donor_form', submit_url);
      }
    });
  });

  // now that we're done messing with the table, render it once
  $('#donors-table-1').removeClass('hidden');
});
