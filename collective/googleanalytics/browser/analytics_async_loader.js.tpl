google.load('visualization', '1', {'packages':${visualization_packages}});
jq(function () {
    jq('#${container_id}').css({
        'background-image': 'url(${portal_url}/++resource++analytics_images/loading.gif)',
        'background-position': 'center center',
        'background-repeat': 'no-repeat',
        'height': '50px'
    });
    jq('#${container_id}').load('@@analytics_async', {
       'report_ids': ${report_ids},
       'profile_id': '${profile_id}',
       'request_url': '${request_url}',
       'date_range': '${date_range}'
    }, function () {
        jq('#${container_id}').css({
	          'background-image': 'none',
	          'height': 'auto'
	      });
    }); 
});