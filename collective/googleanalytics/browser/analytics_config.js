jq(function () {
    getAnalyticsContainerWidth = function(container) {
        // If we're displaying the report in an expanding dl, we need to expand it
        // before we can get the width.
        if (jq(container).parents('dl.collapsedBlockCollapsible').length > 0) {
            var dl_parent = jq(container).parents('dl.collapsedBlockCollapsible').eq(0);
            dl_parent.removeClass('collapsedBlockCollapsible').addClass('expandedBlockCollapsible');
            var container_width = jq(container).innerWidth();
            dl_parent.removeClass('expandedBlockCollapsible').addClass('collapsedBlockCollapsible');
        // Otherwise, we can just get the width.
        } else {
            var container_width = jq(container).innerWidth();
        }
        return container_width;
    }; 
});