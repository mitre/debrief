let colors = d3.scaleOrdinal(d3.schemeCategory10);

let graph_svg = d3.select("#debrief-graph-svg"),
    fact_svg = d3.select("#debrief-fact-svg"),
    width = +graph_svg.attr("width"),
    height = +graph_svg.attr("height");

let graph_simulation = createForceSimulation();
let fact_simulation = createForceSimulation();
let simulationDict = {"graph": graph_simulation, "facts": fact_simulation}

let tooltip = d3.select('#tooltip');

function createForceSimulation() {
    return d3.forceSimulation()
            .force("link", d3.forceLink().id(function(d) { return d.id; }))
                .force('charge', d3.forceManyBody()
              .strength(-200)
              .theta(0.8)
              .distanceMax(150)
            )
            .force("center", d3.forceCenter(width / 2, height / 2));
}

async function updateReportGraph(operations){
    $('#debrief-graph-svg').innerHTML = "";
    $('#debrief-fact-svg').innerHTML = "";
    d3.selectAll("svg > *").remove();
    await buildGraph(graph_svg, 'graph', operations);
    await buildGraph(fact_svg, 'facts', operations);
}

async function buildGraph(svg, graphUrl, operations) {
    let url = "/plugin/debrief/" + graphUrl + "?operations=" + operations.join();
    console.log(operations, url);
    d3.json(url, function (error, graph) {
        console.log(graph);
        if (error) throw error;
        writeGraph(graph, svg, graphUrl);
    });
}

function writeGraph(graph, svg, type) {

  var link = svg.append("g")
                .style("stroke", "#aaa")
                .selectAll("line")
                .data(graph.links)
                .enter().append("line");

  var node = svg.append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(graph.nodes)
      .enter()
      .append("circle")
        .attr("r", 16)
        .style("fill", "#efefef")
        .style("stroke", "#424242")
        .style("stroke-width", "1px")
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended));

  var label = svg.append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(graph.nodes)
      .enter().append("text")
        .attr("class", "label")
        .text(function(d) { return d.type + ':' + d.name; });

  let simulation = simulationDict[type];

  simulation
      .nodes(graph.nodes)
      .on("tick", ticked);

  simulation.force("link")
      .links(graph.links);

  function ticked() {
    link
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node
         .attr("r", 16)
         .style("fill", "#efefef")
         .style("stroke", "#424242")
         .style("stroke-width", "1px")
         .attr("cx", function (d) { return d.x+5; })
         .attr("cy", function(d) { return d.y-3; })
         .on("mouseover", function(d) {
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip.html(generateTooltipHTML(d))
                .style("left", d.x+48 + "px")
                .style("top", d.y-40 + "px");
            })
        .on("mouseout", function(d) {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0)
            });

    label
    		.attr("x", function(d) { return d.x; })
            .attr("y", function (d) { return d.y; })
            .style("font-size", "10px").style("fill", "#333");
  }

  function dragstarted(d) {
      if (!d3.event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
  }

  function dragged(d) {
      d.fx = d3.event.x
      d.fy = d3.event.y
  }

  function dragended(d) {
      d.fx = d3.event.x
      d.fy = d3.event.y
      if (!d3.event.active) simulation.alphaTarget(0);
  }
}

function generateTooltipHTML(d) {
    let props = ['type', 'name', 'score', 'collected_by', 'technique_id'];
    let ret = "";
    props.forEach(function(prop) {
        if (d[prop]) {
            if (prop == 'type') {
                ret += 'trait: ' + d[prop] + '<br/>';
            }
            else if (prop == 'name') {
                ret += 'value: ' + d[prop] + '<br/>';
            }
            else {
                ret += prop + ": " + d[prop] + '<br/>';
            }
        }
    })
    return ret
}
