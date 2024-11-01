$(document).ready(function() {

    //Category Select 2
    $('.size-color').select2();

    //Append Value for remove post
    $('.remove-post-key').click(function() {
        var postId = $(this).attr('data-value');
        $('#remove-val').val(postId);
    })

});