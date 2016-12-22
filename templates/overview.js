//document ready function - happens on page load
$(function() {

  var sbs_click = 'NS0030';
  $('#overview_table tr').click(function () {
    // get sbs by click, change the graph on the right side to show the relevant data
    sbs_click = $(this).closest("tr").find("td:eq(0)").text();
    console.log(sbs_click);
    var data2 = google.visualization.arrayToDataTable([
    ['sbs', 'Samples', 'Mean coverage'],
      {% for item in coverage_data %}
      ['{{ item[0] }}', '{{ item[3] }}', {{ item[2] }}],
      {% endfor %}
      ]);
      var view = new google.visualization.DataView(data2);
      view.setRows(view.getFilteredRows([{column: 0, value: sbs_click }]))
      view.setColumns([1,2]);
    //console.log(google.visualization.dataTableToCsv(data2));
      var options2 = {
      title: 'Samples vs. Mean coverage comparison for SBS321',
      hAxis: {title: '', minValue: 0, maxValue: 15, slantedText: true, slantedTextAngle: 315},
      vAxis: {title: 'Mean coverage', minValue: 0, maxValue: 15},
      legend: 'none'
    };

    // Data for pie chart
    var data_pie = google.visualization.arrayToDataTable([
        ['Class', 'Number'],
        ['1',     11],
        ['2',      2],
        ['3',  2],
        ['4', 2],
        ['5',    7]
      ]);
    var chart2 = new google.visualization.ScatterChart(document.getElementById('chart_div2'));
    chart2.draw(view, options2);

  });

      google.charts.load('current', {'packages':['corechart']});
      google.charts.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = google.visualization.arrayToDataTable([
        ['Samples', 'Mean coverage'],
          [ '8',      12],
          [ '4',      5.5],
          [ '11',     14],
          [ '42',      5],
          [ '3',      3.5],
          [ '6.5',    7]
          ]);

        var options = {
          title: 'Samples vs. Mean coverage comparison',
          hAxis: {title: 'Samples', minValue: 0, maxValue: 15},
          vAxis: {title: 'Mean coverage', minValue: 0, maxValue: 15},
          legend: 'none'
        };

        var data2 = google.visualization.arrayToDataTable([
        ['sbs', 'Samples', 'Mean coverage'],
          {% for item in coverage_data %}
          ['{{ item[0] }}', '{{ item[3] }}', {{ item[2] }}],
          {% endfor %}
          ]);
          var view = new google.visualization.DataView(data2);
          view.setRows(view.getFilteredRows([{column: 0, value: sbs_click }]))
          view.setColumns([1,2]);
        //console.log(google.visualization.dataTableToCsv(data2));
          var options2 = {
          title: 'Samples vs. Mean coverage comparison for SBS321',
          hAxis: {title: '', minValue: 0, maxValue: 15, slantedText: true, slantedTextAngle: 315},
          vAxis: {title: 'Mean coverage', minValue: 0, maxValue: 15},
          legend: 'none'
        };

        // Data for pie chart
        var data_pie = google.visualization.arrayToDataTable([
            ['Class', 'Number'],
            ['1',     11],
            ['2',      2],
            ['3',  2],
            ['4', 2],
            ['5',    7]
          ]);

          var options_pie = {
              title: 'Number of mutations of each class'
            };


        var chart = new google.visualization.ScatterChart(document.getElementById('chart_div'));
        chart.draw(data, options);
        var chart2 = new google.visualization.ScatterChart(document.getElementById('chart_div2'));
        chart2.draw(view, options2);
        // paichart:
        var chart3 = new google.visualization.PieChart(document.getElementById('chart_pie'));
        chart3.draw(data_pie, options_pie);
      }


    // On click of table, get SBS in alert box
























});
