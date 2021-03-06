$(function() {
  window.chartCount = 0;

  $('#print').click(function() {

    var printUrl = $(this).attr('data-url-print') + '?prepareCharts=true';
    //window.print(printUrl);
    window.open(printUrl, 'print-report', 'width=980,height=980'); //,resizable=no,toolbar=no,menubar=no,status=no
  });

  window.ChartDrawer = {
    drawPie: function(pieData, pieId, legendId) {
      var drawFn = drawPie.bind(this, pieData, pieId, legendId);
      drawOnScroll(pieId, drawFn);
    },
    drawSurveysAveragePie: function(pieData, pieId, legendId) {
      var drawFn = drawSurveysAveragePie.bind(this, pieData, pieId, legendId);
      drawOnScroll(pieId, drawFn);
    },
    drawVerticalBarChart: function(chartContainerId, chartId, labelsId, data) {
      var drawFn = drawVerticalBarChart.bind(this, chartId, labelsId, data);
      drawOnScroll(chartContainerId, drawFn);
    },
    drawHorizontalBarChart: function (chartId, chartData) {
      var drawFn = drawHorizontalBarChart.bind(this, chartId, chartData);
      drawOnScroll(chartId, drawFn);
    },
    drawDistributionChart: function(chartContainerId, chartId, labelsId, data) {
      var drawFn = drawDistributionChart.bind(this, chartId, labelsId, data);
      drawOnScroll(chartContainerId, drawFn);
    }
  };

  function drawPie(pieData, pieId, legendId) {
    _drawPie(pieData, pieId, legendId, _pieLabelCallback)
  }

  function drawSurveysAveragePie(pieData, pieId, legendId) {
    var pieSurveysAverageCallback = _genPieSurveysAverageCallback(pieData.surveys);
    _drawPie(pieData, pieId, legendId, pieSurveysAverageCallback)
  }

  function _drawPie(pieData, pieId, legendId, pieLabelCallback) {
    var $pieCtx = $(pieId).get(0).getContext("2d");
    var $pieLegend = $(legendId);
    var chartOptions = {
      type: 'pie',
      data: pieData,
      responsive: true,
      options: {
        legend: false,
        tooltips: {
          enabled: false,
          callbacks: {
            label: pieLabelCallback
          }
        }
      }
    };
    if (window.prepareCharts) {
      chartOptions.options.animation = {
        duration: 0,
        onComplete: function() {
          chartCount -= 1;
        }
      };
      chartOptions.options.responsive = true;
      chartOptions.options.maintainAspectRatio = false;

    }

    var pie = new Chart($pieCtx, chartOptions);

    $pieLegend.html(pie.generateLegend());
    $pieLegend.find('li span').each(function() {
      var backgroundColor = $(this).css('background-color');
      $(this).attr('style', 'background-color: ' + backgroundColor +' !important;');
    })
    _filterLegend();

    function _filterLegend() {
      var $lis = $pieLegend.find('ul > li');

      !pieData.showZerosInLegend && $lis.each(function(index, li) {
        if (pieData.datasets[0].data[index] == 0) {
          $(li).empty();
        }
      });

      if (pieData.hideLastLegendItem) {
        $lis.last().empty();
      }
    }
  }

  function _pieLabelCallback(tooltipItems, data) {
    var recordsNum = data.datasets[tooltipItems.datasetIndex].data[tooltipItems.index];
    var totalNum = data.datasets[tooltipItems.datasetIndex].data.reduce(function(a,b) {return a + b});
    var percentage = Math.round(recordsNum/totalNum*100);

    return tooltipItems.yLabel = data.labels[tooltipItems.index] + '\n' +
      'Entries: ' + recordsNum + '\n' +
      'Percent: ' + percentage + '%';
  }

  function _genPieSurveysAverageCallback(surveys) {
    return function(tooltipItems, data) {
      var surveysNum = surveys[tooltipItems.index];
      var percentage = data.datasets[tooltipItems.datasetIndex].data[tooltipItems.index];

      return tooltipItems.yLabel = data.labels[tooltipItems.index] + '\n' +
        'Entries: ' + surveysNum + '\n' +
        'Percent: ' + percentage + '%';
    }
  }

  function drawOnScroll(elemId, drawFn) {
    var inView = false;
    var wasShown = false;
    chartCount += 1;
    function isScrolledIntoView(elemId)
    {
      var $elemContainer = $(elemId).closest('.report-card');
      var docViewTop = $(window).scrollTop();
      var docViewBottom = docViewTop + $(window).height();

      var heightModificator = $elemContainer.outerHeight() * 0.4;

      var elemTop = $elemContainer.offset().top + heightModificator;
      var elemBottom = elemTop + $elemContainer.outerHeight() - heightModificator;

      return ((elemTop <= docViewBottom) && (elemBottom >= docViewTop));
    }

    function show() {
      if (isScrolledIntoView(elemId)) {
        if (inView || wasShown) {
          return;
        }
        inView = true;
        wasShown = true;
        setTimeout(drawFn, 0);
      }
    }

    if (window.prepareCharts) {
      drawFn();
    } else {
      $(document).ready(show);
      $(window).scroll(show);
    }
  }

  function drawHorizontalBarChart(chartId, chartData) {
    var $horizontalBarChart = $(chartId);

    drawYLabels($horizontalBarChart, chartData);
    drawBars($horizontalBarChart, chartData);
    adjustXLabels($horizontalBarChart, chartData);
    initTooltips($horizontalBarChart);
    animateBars($horizontalBarChart);
    animateLabels($horizontalBarChart);
    --chartCount;

    function drawBars($chart, data) {
      var $bars = $chart.find('.horizontal-bars');

      data.forEach(function (item) {
        if (item.positiveNum !== -1 && item.negativeNum !== -1) {
          _drawNonEmptyBar($bars, item);
        } else {
          _drawEmptyBar($bars, item);
        }
      });
    }

    function drawYLabels($chart, data) {
      var $yLabels = $chart.find('.y-labels');

      data.forEach(function (item) {
        var $label = $('<div class="h-chart-y-label">' + item.label + '</div>');
        $yLabels.append($label);
      });
    }

    function adjustXLabels($chart, data) {
      var $xLabels = $chart.find('.x-labels');
      var xLabelsPaddingLeft = $chart.find('.y-labels').outerWidth();

      $xLabels.css('padding-left', xLabelsPaddingLeft);
    }

    function initTooltips($chart) {
      $chart.find('[data-toggle="tooltip"]').tooltip()
    }

    function _drawNonEmptyBar($bars, item) {
      var $bar = $('<div class="bar"></div>');

      var $positivePortionText = $('<span>' + item.positiveNum + '</span>');
      var $negativePortionText = $('<span>' + item.negativeNum + '</span>');

      var percentages = _getPercentages(item);

      var $positivePortion = $(
        '<div class="portion positive" ' +
        'data-toggle="tooltip" ' +
        'data-placement="top"' +
        ' title="' + percentages.positive + '">' +
        '</div>'
      ).html($positivePortionText);

      var $negativePortion = $(
        '<div class="portion negative" ' +
        'data-toggle="tooltip" ' +
        'data-placement="top"' +
        ' title="' + percentages.negative + '">' +
        '</div>'
      ).html($negativePortionText);

      var positiveWidth = _calcPositiveWidth(item);
      var negativeWidth = 100 - positiveWidth;

      $negativePortion.css('width', negativeWidth + '%');
      $positivePortion.css('width', positiveWidth + '%');

      $bar.append($positivePortion);
      $bar.append($negativePortion);
      $bars.append($bar);

      _hideTextIfOverflows($negativePortion, $negativePortionText);
      _hideTextIfOverflows($positivePortion, $positivePortionText);
    }

    function _drawEmptyBar($bars, item) {
      var $bar = $('<div class="bar"></div>');

      var $emptyPortion = $(
        '<div class="portion empty" ' +
        'data-toggle="tooltip" ' +
        'data-placement="top"' +
        ' title="n/a">' +
        '</div>'
      ).html('n/a');

      $bar.append($emptyPortion);
      $bars.append($bar);
    }

    function _hideTextIfOverflows($container, $text) {
      if (!_isEnoughSpaceForText($container, $text)) {
        $container.empty();
      }
    }

    function _isEnoughSpaceForText($container, $text) {
      return $container.outerWidth() > $text.outerWidth();
    }

    function _calcPositiveWidth(item) {
      var MIN_WIDTH = 1;
      var MAX_WIDTH = 99;

      var positiveWidth = item.positiveNum / (item.positiveNum + item.negativeNum) * 100;
      if (positiveWidth > MAX_WIDTH) {
        positiveWidth = MAX_WIDTH;
      } else if (positiveWidth < MIN_WIDTH) {
        positiveWidth = MIN_WIDTH;
      }

      return positiveWidth;
    }

    function _getPercentages(item) {
      var positivePercentage = item.positiveNum / (item.positiveNum + item.negativeNum) * 100;
      var negativePercentage = 100 - positivePercentage;

      return {
        positive: _getPercentageString(positivePercentage),
        negative: _getPercentageString(negativePercentage)
      }
    }

    function _getPercentageString(percentage) {
      var percentageStr = Math.round(percentage) + '%';

      if (percentage > 0 && percentage < 1) {
        percentageStr = '< 1%';
      } else if (percentage > 99 && percentage < 100) {
        percentageStr = '> 99%';
      }

      return percentageStr;
    }

    function animateBars($chart) {
      var $barItems = $chart.find('.horizontal-bars .bar');
      $barItems.css('width', '0');

      setTimeout(function() {
        $barItems.css('transition', 'width 1s ease');
        $barItems.css('width', '100%')
      });
    }

    function animateLabels($chart) {
      var $labels = $chart.find('.h-chart-x-label, .h-chart-y-label');
      $labels.addClass('animated');
    }
  }

  function getBarChartPlugins() {
    var plugins = [
      Chartist.plugins.tooltip({
        tooltipFnc: function (surveysNum, percentage) {
          return 'Entries: ' + surveysNum;
        },
        anchorToPoint: true
      })
    ];
    if (!window.prepareCharts) {
      plugins.push(
        Chartist.plugins.barAnimation({
          duration: 2000
        })
      );
    }
    return plugins;
  }

  function genTicks(low, high) {
    var step = (high - low) / 4;
    var rv = [];
    while (low <= (high - step)) {
      rv.push(low)
      low += step;
    }
    rv.push(high);
    return rv;
  }

  function drawVerticalBarChart(chartId, labelsId, data) {
    var wasDrawn = false;
    var unit = data.unit;
    var low = data.lowest;
    var high = data.highest;

    var barChart = new Chartist.Bar(chartId, {
      labels: data.labels,
      series: [data.series]
    }, {
      stackBars: false,
      high: high,
      low: low,
      axisY: {
        type: Chartist.FixedScaleAxis,
        ticks: genTicks(low, high),
        labelInterpolationFnc: setYAxisLabels
      },
      axisX: {
        showGrid: false
      },
      plugins: getBarChartPlugins()
    })
      .on('draw',setBarTitle)
      .on('draw', setBarWidth)
      .on('created', drawBarLabels)
      .on('created', animateAdditionalElements);

    $(document).on('resize', drawBarLabels);

    function setBarWidth(data) {
      if (data.type === "bar") {
        data.element.attr({
          style: 'stroke-width: 22px'
        });
      }
    }

    function setBarTitle(data) {
      if (data.type === "bar") {
        var barHorizontalCenter, barVerticalCenter, label, value;
        barHorizontalCenter = data.x1 + (data.element.width() * .5);
        barVerticalCenter = data.y1 + (data.element.height() * -1) - 10;
        value = data.element.attr('ct:value');
        label = new Chartist.Svg('text');
        if (value == '-1') {
          label.text('n/a');
        } else {
          label.text(value + unit);
        }
        label.addClass("ct-bar-title");
        label.attr({
          x: barHorizontalCenter,
          y: barVerticalCenter,
          'text-anchor': 'middle'
        });
        return data.group.append(label);
      }
    }

    function setYAxisLabels(value) {
      if (unit === '%') {
        return value % 50 == 0 ? value + '%' : '';
      } else {
        return `${value}${unit}`;
      }
    }

    function drawBarLabels() {
      var $barChartContainer = $(chartId);
      var barChartContainerPosition = $barChartContainer.offset();
      var $labels = $(labelsId);
      var $bars = $barChartContainer.find('.ct-bar');

      $labels.empty();

      $bars.each(function(i, bar) {
        var $bar = $(bar);
        var barPosition = $bar.offset();
        var $label = $('<div class="ct-bar-label">' + barChart.data.labels[i] + '</div>');
        $labels.append($label);
        var barHeight = bar.getBBox().height;
        var barWidth = bar.getBBox().width;
        var labelTop = barPosition.top - barChartContainerPosition.top + barHeight + 10;
        var labelLeft = barPosition.left - barChartContainerPosition.left + barWidth/2 - $label.width()/2;
        $label.css('top', labelTop);
        $label.css('left', labelLeft);
        $label.css('height', $label.width());
      });
    }

    function animateAdditionalElements() {
      animateTitles();
      animateGrid();
      animateLabels(chartId, '.ct-label');
      animateLabels(labelsId, '.ct-bar-label');
      wasDrawn = true;
      --chartCount;
    }

    function animateGrid() {
      var $barChartContainer = $(chartId);
      var $grid = $barChartContainer.find('.ct-grid');

      if (wasDrawn) {
        $grid.css('transition', 'none');
      }

      $grid.each(function (index, elt) {  //Jquery cannot set stroke-opacity via css() method
        elt.style.strokeOpacity = 1;
      });
    }

    function animateTitles() {
      var $barChartContainer = $(chartId);
      var $percentages = $barChartContainer.find('.ct-bar-title');

      if (wasDrawn) {
        $percentages.css('transition', 'none')
      }

      $percentages.css('fill-opacity', 1);
    }

    function animateLabels(containerId, labelsSelector) {
      var $container = $(containerId);
      var $labels = $container.find(labelsSelector);

      if (wasDrawn) {
        $labels.css('transition', 'none')
      }

      $labels.addClass('animated');
    }
  }

  function drawDistributionChart(chartId, labelsId, data) {
    var wasDrawn = false;

    var maxVal = findMaxValue();
    var tick = calcTick();
    var maxY = findMaxY();

    var barChart = new Chartist.Bar(chartId, {
      labels: data.labels,
      series: [data.series]
    }, {
      stackBars: false,
      high: maxY,
      low: 0,
      axisY: {
        type: Chartist.FixedScaleAxis,
        ticks: genTicks()
      },
      axisX: {
        showGrid: false
      },
      plugins: getBarChartPlugins()
    })
      .on('draw',setBarTitle)
      .on('draw', setBarWidth)
      .on('draw', setBarColor)
      .on('created', drawBarLabels)
      .on('created', animateAdditionalElements);

    $(document).on('resize', drawBarLabels);

    function setBarWidth(data) {
      if (data.type === "bar") {
        var windowWidth = $(window).width();
        var strokeWidth = 22;

        if (windowWidth < 450 && windowWidth >= 375) {
          strokeWidth = 15;
        } else if (windowWidth < 375) {
          strokeWidth = 10
        }

        data.element.attr({
          style: 'stroke-width: ' + strokeWidth + 'px;'
        });
      }
    }

    function setBarColor(data) {
      if (data.type === "bar") {
        var maxBarRelation = data.series[data.index].value/maxVal;
        var colorClass = 'highest';

        if (maxBarRelation >= 0.5 && maxBarRelation < 1) {
          colorClass = 'medium'
        } else if (maxBarRelation < 0.5) {
          colorClass = 'lower'
        }
        data.element._node.className.baseVal += ' ' + colorClass;
        data.element._node.className.animVal += ' ' + colorClass;
      }
    }

    function setBarTitle(data) {
      if (data.type === "bar") {
        var barHorizontalCenter, barVerticalCenter, label, value, meta;
        meta = data.element.attr('ct:meta');
        value = data.element.attr('ct:value');
        barHorizontalCenter = data.x1 + (data.element.width() * .5);
        barVerticalCenter = data.y1 + (data.element.height() * -1) - 10;
        label = new Chartist.Svg('text');
        if (value != '-1' && value != '0') {
          label.text(meta + '%');
        }
        label.addClass("ct-bar-title");
        label.attr({
          x: barHorizontalCenter,
          y: barVerticalCenter,
          'text-anchor': 'middle'
        });
        return data.group.append(label);
      }
    }

    function drawBarLabels() {
      var $barChartContainer = $(chartId);
      var barChartContainerPosition = $barChartContainer.offset();
      var $labels = $(labelsId);
      var $bars = $barChartContainer.find('.ct-bar');

      $labels.empty();

      $bars.each(function(i, bar) {
        var $bar = $(bar);
        var barPosition = $bar.offset();
        var $label = $('<div class="ct-bar-label">' + barChart.data.labels[i] + '</div>');
        $labels.append($label);
        var barHeight = bar.getBBox().height;
        var barWidth = bar.getBBox().width;
        var labelTop = barPosition.top - barChartContainerPosition.top + barHeight + 10;
        var labelLeft = barPosition.left - barChartContainerPosition.left + barWidth/2 - $label.width()/2;
        $label.css('top', labelTop);
        $label.css('left', labelLeft);
        $label.css('height', $label.width());
      });
    }

    function animateAdditionalElements() {
      animateTitles();
      animateGrid();
      animateLabels(chartId, '.ct-label');
      animateLabels(labelsId, '.ct-bar-label');
      wasDrawn = true;
      --chartCount;
    }

    function animateGrid() {
      var $barChartContainer = $(chartId);
      var $grid = $barChartContainer.find('.ct-grid');

      if (wasDrawn) {
        $grid.css('transition', 'none');
      }

      $grid.each(function (index, elt) {  //Jquery cannot set stroke-opacity via css() method
        elt.style.strokeOpacity = 1;
      });
    }

    function animateTitles() {
      var $barChartContainer = $(chartId);
      var $percentages = $barChartContainer.find('.ct-bar-title');

      if (wasDrawn) {
        $percentages.css('transition', 'none')
      }

      $percentages.css('fill-opacity', 1);
    }

    function animateLabels(containerId, labelsSelector) {
      var $container = $(containerId);
      var $labels = $container.find(labelsSelector);

      if (wasDrawn) {
        $labels.css('transition', 'none')
      }

      $labels.addClass('animated');
    }

    function findMaxValue() {
      return Math.max.apply( Math, data.series.map(function(item) {return item.value}) );
    }

    function findMaxY() {
      return (Math.floor(maxVal/tick) + 1)*tick;
    }

    function genTicks() {
      var ticksNum = Math.round(maxY/tick);
      var ticks = [];
      for (var i = 0; i <=ticksNum; i+=1) {
        ticks.push(i*tick);
      }

      return ticks;
    }

    function calcTick() {
      tick = Math.round(maxVal/3/10)*10;
      if (!tick) {
        tick = 5;
      }
      return tick;
    }
  }

});
