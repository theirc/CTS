$(document).ready(function() {
  // DATATABLES
  var table = $('#users-table-1').DataTable({
    "searching": false,  /* must be true to use search even from the API */
    "dom": "lrtip",  /* don't show datatables' searchbox */
    "orderClasses": false,
    "paging": false,
    "stateSave": true  // so we keep the same filters and sorting from last time
  });

  $('.cts-user-edit-pencil').on('click', function(){
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'cts_user_edit_modal', 'submit-edit-user-button',
            'edit_user_form', submit_url);
      }
    });
  });

  $('#new-user-button').on('click', function() {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new_cts_user_modal', 'submit-new-user-button',
            'new_user_form', submit_url);
      }
    });
  });

  // now that we're done messing with the table, render it once
  $('#users-table-1').removeClass('hidden');
});
