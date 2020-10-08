function appendOnLoad(handler) { window[ addEventListener ? 'addEventListener' : 'attachEvent' ]( addEventListener ? 'load' : 'onload', handler ) }

function toggleDisplay(id) {
  var el = d3.select("#"+id)
  var visible = el.style("display") != "none";
  el.style("display", visible ? "none" : "inline");
}

function getDateTime(relativeToStartMs) {
  var since = startDateEpoch + relativeToStartMs;
  return new Date(since);
}

function getWH(el) {
  var node = el.node();
  var styl = window.getComputedStyle(node)
  var ret = {
    width: styl.width,
    height: styl.height
  }
  ret.width = parseInt(ret.width == null || ret.width < 10 ? 200 : ret.width);
  ret.height = parseInt(ret.height == null || ret.height < 10 ? 200 : ret.height);
  return ret;
}

function plotSVG(divParent, specs) {
  specs = Array.isArray(specs) ? specs : [specs]
  if(!specs.every(d => typeof(d.data)!='undefined' && typeof(d.xPlot)!='undefined' && typeof(d.yPlot)!='undefined'))
    throw "plotSVG was provided data incompatible with use"

  specs.forEach(function(spec) {
    spec.typX = spec.data.length > 0 ? getTypeName(spec.xPlot(spec.data[0])) : "number";
    spec.typY = spec.data.length > 0 ? getTypeName(spec.yPlot(spec.data[0])) : "number";
  })

  for(spec of specs) {
    spec.title = typeof(spec.title)!='undefined' ? spec.title : "Unknown";
    spec.color = typeof(spec.color)!='undefined' ? spec.color : "gray";
  }

  var specs_y_axis = specs.filter(spec => !(spec.typY == "number" && d3.max(spec.data, spec.yPlot)==0))

  var legend_cols = 4
  var legend = addLegend(divParent, specs,legend_cols)

  var parentBox = getWH(divParent);

  var legend_height = Math.round(specs.length / 3) * 20;
  var h_padding_per = 40
  var h_total_padding = Math.round(specs.length / 2) * h_padding_per;

  // set the dimensions and margins of the graph
  var margin = {top: 10, right: 60, bottom: 30, left: 60},
      width = parentBox.width - margin.left - margin.right - h_total_padding,
      height = parentBox.height - legend_height - margin.top - margin.bottom;

  // append the svg object to the body of the page
  var svg = divParent
    .append("svg")
      .attr("width", width + margin.left + margin.right + h_total_padding * 2)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + (margin.left + (h_total_padding/2)) + "," + margin.top + ")");

  var all_x_are_dates = specs.every(spec => getTypeName(spec.xPlot(spec.data[0])) === "Date")
  var all_x = null;
  var is_y_axis_left = true;

  for(var i=0; i<specs.length; i++) {
    var spec = specs[i];

    // Add X axis --> it is a date format
    var x = getD3scalerForType(spec.typX, spec.data, spec.xPlot)
      .range([ 0, width ]);
    if(all_x_are_dates) {
      if(all_x == null) {
        all_x = x;
        svg.append("g")
          .attr("transform", "translate(0," + height + ")")
          .call(d3.axisBottom(x));
      }
      x = all_x;
    }

    if(specs_y_axis.some(s => spec.title === s.title)) {
      // Add Y axis
      var y = getD3scalerForType(spec.typY, spec.data, spec.yPlot)
        .range([ height, 0 ]);
      var y_axis = is_y_axis_left ? d3.axisLeft(y) : d3.axisRight(y)
      var rightTransform = is_y_axis_left ? 0 : width
      var h_offset = Math.floor(i / 2) * h_padding_per * (is_y_axis_left ? -1 : 1)
      is_y_axis_left = !is_y_axis_left;
      svg.append("g")
        .attr("stroke", spec.color)
        .attr("transform", "translate(" + (rightTransform + h_offset) + ",0)")
        .call(y_axis);
    }

    var path = svg.append("path")
          .datum(spec.data)
          .attr("fill", "none")
          .attr("stroke", spec.color)
          .attr("stroke-width", 1.5)
          .attr("d", d3.line()
            .x(function(d) { return x(spec.xPlot(d)) })
            .y(function(d) { return y(spec.yPlot(d)) })
          )
  }

  divParent.append(() => legend.node());
  legend.style("width",getWH(divParent).width / 2)
  legend.attr("transform", "translate(0," + (-margin.bottom) + ")")
  var whLegend = getWH(legend)
  divParent.style("height", getWH(divParent).height + whLegend.height)
}

function getTypeName(obj) {
  if(obj == null) return "string";
  if(Object.prototype.toString.call(obj) === '[object Date]')
    return "Date";
  else
    return typeof(obj);
}

function getD3scalerForType(typeName, data, plot) {
  if(typeName == "Date")
    return d3.scaleTime()
      .domain(d3.extent(data, plot))
  else
    return d3.scaleLinear()
      .domain([0, Math.max(1,d3.max(data, plot))])
}

function addLegend(divParent, specs, cols_per) {
  var rows = []
  for(var i=0; i<specs.length; i+=cols_per) {
    var row = specs.slice(i, i+cols_per)
    rows.push(row)
  }
  var legend = d3.create("table")
                .attr("class","legend")
  var tablebody = legend.append("tbody");
        rows = tablebody
                .selectAll("tr")
                .data(rows)
                .enter()
                .append("tr");
        cells = rows.selectAll("td")
                .data(function(d) {
                  return d;
                })
                .enter()
                .append("td")
                .style("color",d => d.color)
                .text(d => d.title + (typeof(d.units)!='undefined'?" (" + d.units + ")":""));
  return legend
}

function specTimeLine(title, units, color, data, l_time_field, l_num_field) {
  var ret = {
      title: title,
      data: data,
      xPlot: d => getDateTime(l_time_field(d)),
      yPlot: l_num_field
    }
  if(units != null && typeof(units)!='undefined')
    ret.units = units
  ret.color = (color != null && typeof(color)!='undefined') ? color : "gray"
  return ret
}

function createSpecsTable(specs) {
  var table = d3.create("table")
  var header = table.append("thead").append("tr");
      header.selectAll("th")
            .data(["Color", "Scale", "Measurement", "Min", "Avg", "Max", "Med", "Std. Dev."])
            .enter()
            .append("th")
            .text(function(d) { return d; });
  var tablebody = table.append("tbody");
        rows = tablebody
                .selectAll("tr")
                .data(specs)
                .enter()
                .append("tr");
        cells = rows.selectAll("td")
                .data(function(d) {
                  var commons = getMinMaxAvgMedianStdDev(d.data, d.yPlot)
                  var arr = [
                    { text: ".", background_color: d.color },
                    //{ text: d.title + (typeof(d.units)!='undefined'?" (" + d.units + ")":"") },
                    { text: (typeof(d.units)!='undefined'?" (" + d.units + ")":""), },
                    { text: d.title, },
                    { text: commons.minimum },
                    { text: commons.mean },
                    { text: commons.maximum },
                    { text: commons.median },
                    { text: commons.deviation },
                  ];
                  arr.forEach(a => a.__data__ = d)
                  return arr
                })
                .enter()
                .append("td")
                .style("background-color", d => (typeof(d.background_color!='undefined') ? d.background_color : "transparent"))
                .style("color", d => (typeof(d.__data__.color!='undefined') ? d.__data__.color : "black"))
                .text(d => d.text);
  return table
}

function getMinMaxAvgMedianStdDev(data, plot) {
  // if "number"
  var vals = data.map(d => plot(d));
  return {
    minimum: d3.min(vals),
    maximum: d3.max(vals),
    mean: d3.mean(vals),
    median: d3.median(vals),
    variance: d3.variance(vals),
    deviation: d3.deviation(vals)
  }
}
