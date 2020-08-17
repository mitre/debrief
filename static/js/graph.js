class Graph {
    constructor(type, svg, tooltip) {
        this.type = type;
        this.svg = svg;
        this.tooltip = tooltip;
        this.simulation = createForceSimulation(1200, 400);
    }
}

let graphSvg = new Graph("graph", d3.select("#debrief-graph-svg"), null),
    tacticSvg = new Graph("tactic", d3.select("#debrief-tactic-svg"), d3.select('#op-tooltip')),
    techniqueSvg = new Graph("technique", d3.select("#debrief-technique-svg"), d3.select('#op-tooltip')),
    factSvg = new Graph("fact", d3.select("#debrief-fact-svg"), d3.select('#fact-tooltip'))

let graphs = [graphSvg, factSvg, tacticSvg, techniqueSvg];

let colors = d3.scaleOrdinal(d3.schemeCategory10);

function createForceSimulation(width, height) {
    return d3.forceSimulation()
            .force("link", d3.forceLink().id(function(d) { return d.id; }))
                .force('charge', d3.forceManyBody()
              .strength(-200)
              .theta(0.8)
              .distanceMax(150)
            )
            .force("center", d3.forceCenter(width / 2, height / 2));
}

function updateReportGraph(operations){
    $('.debrief-svg').innerHTML = "";
    d3.selectAll("svg > *").remove();

    graphs.forEach(function(graphObj) {
        buildGraph(graphObj, operations)
    });
}

function buildGraph(graphObj, operations) {
    let url = "/plugin/debrief/graph?type=" + graphObj.type + "&operations=" + operations.join();
    d3.json(url, function (error, graph) {
        if (error) throw error;
        writeGraph(graph, graphObj);
    });
}

function writeGraph(graph, graphObj) {

  graphObj.svg.append('defs').append('marker')
        .attrs({'id':'arrowhead'+graphObj.type,
            'viewBox':'-0 -5 10 10',
            'refX':30,
            'refY':0,
            'orient':'auto',
            'markerWidth':8,
            'markerHeight':8,
            'xoverflow':'visible'})
        .append('svg:path')
        .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
        .attr('fill', '#999')
        .style('stroke','none');

  var link = graphObj.svg.append("g")
                .style("stroke", "#aaa")
                .selectAll("line")
                .data(graph.links)
                .enter().append("line")
                .attr('marker-end','url(#arrowhead' + graphObj.type + ')');

  var node = graphObj.svg.append("g")
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

  var label = graphObj.svg.append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(graph.nodes)
      .enter().append("text")
        .attr("class", "label")
        .text(function(d) { return d.type + ':' + d.name; });

  let simulation = graphObj.simulation;

  simulation
      .nodes(graph.nodes)
      .on("tick", ticked);

  simulation.force("link")
      .links(graph.links)
      .distance(50)

  function ticked() {
    link
        .attr("x1", function(d) { return d.source.x+6; })
        .attr("y1", function(d) { return d.source.y-2; })
        .attr("x2", function(d) { return d.target.x+6; })
        .attr("y2", function(d) { return d.target.y-2; });


    node
         .attr("r", 16)
         .style("fill", "#efefef")
         .style("stroke", "#424242")
         .style("stroke-width", "1px")
         .attr("cx", function (d) { return d.x+5; })
         .attr("cy", function(d) { return d.y-3; })
         .on("mouseover", function(d) {
            if (graphObj.tooltip) {
                graphObj.tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                graphObj.tooltip.html(generateTooltipHTML(d))
                    .style("left", d.x+50 + "px")
                    .style("top", d.y + "px");
            }
        })
        .on("mouseout", function(d) {
            if (graphObj.tooltip) {
                graphObj.tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            }
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

  function generateTooltipHTML(d) {
    let ret = "";
    if (d["type"] == "operation") {
        ret += "name: " + d["name"] + "<br/>";
        ret += "op_id: " + d["id"] + "<br/>";
    }
    else if (d["type"] == "tactic" || d["type"] == "technique_name") {
        let p = d["attrs"][d["type"]]
        ret += d["type"] + ": " + p + "<br/>";
        for (let key in d["attrs"]) {
            if (key != d["type"]) {
                ret += key + ": " + d["attrs"][key] + "<br/>";
            }
        }
    }
    else {
        for (let key in d["attrs"]) {
            if (d["attrs"][key]) {
                ret += key + ": " + d["attrs"][key] + "<br/>";
            }
        }
    }
    return ret
  }
}
