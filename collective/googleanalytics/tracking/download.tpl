<script type="text/javascript">
    jq(function() {
        var extensions = ${file_extensions};
        for (var i=0;i<extensions.length;i++) {
            jq('a[href$$=".' + extensions[i] + '"]').click(function () {
                _gaq.push(['_trackEvent', 'File', 'Download', jq(this).attr('href'), '${relative_url}']);
            });
        }
    });
</script>