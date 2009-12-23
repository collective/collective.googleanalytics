// Load the Visualization API and the piechart package.
google.load('visualization', '1', {'packages':['${package_name}']});

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(drawChart);

// Callback that creates and populates a data table, 
// instantiates the pie chart, passes in the data and
// draws it.
function drawChart() {

// Create our data table.

  var data = new google.visualization.DataTable();
  ${columns}
  data.addRows(${data});


  // Instantiate and draw our chart, passing in some options.
  var chart = new google.visualization.${chart_type}(document.getElementById('${id}'));
  chart.draw(data, ${options});
}