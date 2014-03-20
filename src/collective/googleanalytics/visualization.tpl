<div id="${id}"></div>
<script type="text/javascript" charset="utf-8">
	jq(function () {
	    var draw_visualization = function () {
	        var data = new google.visualization.DataTable();
	        ${columns}
	        data.addRows(${data});

	        var container_width = getAnalyticsContainerWidth(jq('#${id}'));

	        var chart = new google.visualization.${chart_type}(document.getElementById('${id}'));
	        chart.draw(data, ${options});
	    };
	    setTimeout(draw_visualization, 1);
	});
</script>


