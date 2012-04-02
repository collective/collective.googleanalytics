(function ($) {
    getAnalyticsContainerWidth = function(container) {
        var container_width;
        // If we're displaying the report in an expanding dl, we need to expand it
        // before we can get the width.
        if ($(container).parents('dl.collapsedBlockCollapsible').length > 0) {
            var dl_parent = $(container).parents('dl.collapsedBlockCollapsible').eq(0);
            dl_parent.removeClass('collapsedBlockCollapsible').addClass('expandedBlockCollapsible');
            container_width = $(container).innerWidth();
            dl_parent.removeClass('expandedBlockCollapsible').addClass('collapsedBlockCollapsible');
        // Otherwise, we can just get the width.
        } else {
            container_width = $(container).innerWidth();
        }
        return container_width;
    }; 
}(jQuery));
