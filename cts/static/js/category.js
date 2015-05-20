$(document).ready(function() {
  // DATATABLES
  var table = $('#categories-table-1').DataTable({
    "searching": false,  /* must be true to use search even from the API */
    "dom": "lrtip",  /* don't show datatables' searchbox */
    "orderClasses": false,
    "paging": false,
    "stateSave": true  // so we keep the same filters and sorting from last time
  });

  $('.category-edit-pencil').on('click', function(){
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'category_edit_modal', 'submit-edit-category-button',
            'edit_category_form', submit_url);
      }
    });
  });

  $('#new-category-button').on('click', function() {
    var submit_url = $(this).attr('data-url');
    $.ajax({
      url: submit_url,
      dataType: 'HTML',
      success: function (data) {
        fill_item_modal(data, 'new_category_modal', 'submit-new-category-button',
            'new_category_form', submit_url);
      }
    });
  });

  // now that we're done messing with the table, render it once
  $('#categories-table-1').removeClass('hidden');
});
