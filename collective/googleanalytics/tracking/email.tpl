<script type="text/javascript">
    jq(function() {
        jq('a[href^="mailto"]').click(function () {
            var email = jq(this).attr('href').replace('mailto:', '');
            _gaq.push(['_trackEvent', 'External', 'E-mail', email, '${relative_url}']);
        });
    });
</script>