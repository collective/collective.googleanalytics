jq(function () {
    var draw_visualization = function () {
        var data = new google.visualization.DataTable();
        data.addColumn("string", "Day");
        data.addColumn("number", "Visits");
        data.addRows([
            ["18", 648],
            ["19", 449],
            ["20", 385],
            ["21", 182],
            ["22", 210],
            ["23", 466],
            ["24", 561],
            ["25", 348],
            ["26", 188],
            ["27", 180],
            ["28", 163],
            ["29", 181],
            ["30", 521],
            ["01", 485],
            ["02", 523],
            ["03", 419],
            ["04", 320],
            ["05", 160],
            ["06", 195],
            ["07", 469],
            ["08", 488],
            ["09", 479],
            ["10", 520],
            ["11", 423],
            ["12", 198],
            ["13", 265],
            ["14", 615],
            ["15", 478],
            ["16", 401],
            ["17", 412],
            ["18", 228]
        ]);

        var container_width = getAnalyticsContainerWidth(jq('#${id}'));

        var chart = new google.visualization.LineChart(document.getElementById('${id}'));
        chart.draw(data, {title: "Site Visits", titleX: "Day", titleY: "Visits", axisFontSize: 10, legend: "none", height: 250, width: container_width});
    };
    setTimeout(draw_visualization, 1);
});