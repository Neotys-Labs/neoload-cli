function shuffleArray(array) {
  var copy = array.slice(0,array.length)
    for (var i = copy.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = copy[i];
        copy[i] = copy[j];
        copy[j] = temp;
    }
  return copy;
}

function graphTrends(el, data, subgroup_colors, fGroupName, fGroupChildren, fChildName, fChildValue) {
  // set the dimensions and margins of the graph
  var margin = {top: 10, right: 30, bottom: 20, left: 50},
      width = getWH(el).width - margin.left - margin.right,
      height = getWH(el).height - margin.top - margin.bottom;

  // append the svg object to the body of the page
  var svg = el
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

  var groups = data.map(fGroupName);
  var all_subgroup_names = []
  var all_values = []
  data.forEach(d => {
    var children = fGroupChildren(d)
    var mine = children.map(group => fChildName(group))
    var vals = children.map(group => parseFloat(fChildValue(group)));
    all_values = all_values.concat(vals)
    all_subgroup_names = all_subgroup_names.concat(mine)
  })
  var colors = subgroup_colors.map(g => g.color)
  var subgroups = all_subgroup_names.filter( onlyUnique );

  var max_y_value = Math.max.apply(Math, all_values);

  var x = d3.scaleBand()
      .domain(groups)
      .range([0, width])
      .padding([0.2])
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x).tickSize(0));

    // Add Y axis
   var y = d3.scaleLinear()
     .domain([0, max_y_value])
     .range([ height, 0 ]);
   svg.append("g")
     .call(d3.axisLeft(y));

   // Another scale for subgroup position?
   var xSubgroup = d3.scaleBand()
     .domain(subgroups)
     .range([0, x.bandwidth()])
     .padding([0.05])

   // color palette = one color per subgroup
   var color = d3.scaleOrdinal()
     .domain(subgroups)
     .range(colors)

  var getSubgroupValue = function(this_group_data, bar_name) {
    var children = fGroupChildren(this_group_data)
    var results = children.filter(child => fChildName(child) === bar_name)
    var value = fChildValue(results[0])
    return value
  }
  var setupBarData = function(d) {
    return subgroups.map(function(key) {
      return {
        key: key,
        data: d,
        value: getSubgroupValue(d,key)
      };
    });
  }

   var gs = svg.append("g")
     .selectAll("g")
     // Enter in data = loop group per group
     .data(data)
     .enter()
     .append("g")
       .attr("transform", function(d) { return "translate(" + x(fGroupName(d)) + ",0)"; })
       .text(function(d) { return fGroupName(d) })
   gs
     .selectAll("rect")
     .data(setupBarData)
     .enter()
     .append("rect")
       .attr("x", function(d) { return xSubgroup(d.key); })
       .attr("y", function(d) { return y(d.value); })
       .attr("width", xSubgroup.bandwidth())
       .attr("height", function(d) { return height - y(d.value); })
       .attr("fill", function(d) { return color(d.key); })
       .on("mouseover", handleMouseOverBar)
       .on("mouseout", handleMouseOutBar);
   gs
   .selectAll("text")
   .data(setupBarData)
   .enter()
   .append("text")
     .attr("x", function(d) { return xSubgroup(d.key); })
     .attr("y", function(d) { return getWH(el).height-70 }) //y(d.value); })
     .attr("width", xSubgroup.bandwidth())
     .attr("dx", ".75em")
     .attr("dy", "1.75em")
     .style("text-align","center")
     .text(function(d) { return subgroup_colors.filter(g => g.name===d.key).map(g => g.index)[0] })

}

function onlyUnique(value, index, self) {
    return self.indexOf(value) === index;
}

function getCell(d,i) {
  var barName = d.key;
  var index = window.results_colors.filter(r => r.name === barName)[0].index;
  var groupName = d.data.name;
  return d3.selectAll('*[data-transaction-name = "'+groupName+'"][data-result-name = "'+barName+'"]')
}
function handleMouseOverBar(d, i) {
  var cell = getCell(d,i)
  cell.style("background-color","yellow")
}
function handleMouseOutBar(d, i) {
  var cell = getCell(d,i)
  cell.style("background-color","transparent")
}
