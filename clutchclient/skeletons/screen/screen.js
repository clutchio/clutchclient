Clutch.Core.init(function() {

$('#example-form').bind('submit', function(e) {
    // Get the value in the search input box
    var search = $('#search-input').val();
    // Clear the search input box
    this.reset();
    // Make sure the keyboard goes away
    $('#search-input').blur();
    
    // Add the value that was entered into the list below
    $('#searches').append('<li>' + search + '</li>');
    
    // If there are too many entries in the search list, delete the oldest
    if($('#searches li').length > 3) {
        $('#searches li').first().remove();
    }
    
    // Call the clickHereTapped method on iOS and pass the search term as a value
    Clutch.Core.callMethod('clickHereTapped', {value: search});
    
    return false;
});

// Ensure that when the search input is focused, it is not obscured by the iOS Keyboard
$('#search-input').bind('focus', function(e) {
    window.scrollTo(0, 300);
});

});