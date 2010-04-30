<div id="${id}"></div>
<script type="text/javascript" charset="utf-8">
	jq(function () {
	    var draw_visualization = function () {
	        var data = new google.visualization.DataTable();
	        data.addColumn("string", "Day");
data.addColumn("number", "Visits");
	        data.addRows([["1", 458], ["2", 274], ["3", 150], ["4", 160], ["5", 376], ["6", 453], ["7", 579], ["8", 520], ["9", 369], ["10", 161], ["11", 205], ["12", 482], ["13", 539], ["14", 473], ["15", 485], ["16", 317], ["17", 157], ["18", 206], ["19", 446], ["20", 517], ["21", 439], ["22", 436], ["23", 365], ["24", 153], ["25", 183], ["26", 441], ["27", 668], ["28", 493], ["29", 455], ["30", 192]]);

	        var container_width = getAnalyticsContainerWidth(jq('#${id}'));

	        var chart = new google.visualization.LineChart(document.getElementById('${id}'));
	        chart.draw(data, {"width": container_width, "title": "Site Visits", "titleX": "Day", "titleY": "Visits", "axisFontSize": 10, "legend": "none", "height": 250});
	    };
	    setTimeout(draw_visualization, 1);
	});
</script>




<p>
<strong>11152</strong> total visits in the last
30 days
</p>
<p>
<strong>371</strong>
average visits per day
</p>
