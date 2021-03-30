var factDisplayLimit = 15;

class Graph {
    constructor(id, type, tooltip) {
        this.id = id;
        this.type = type;
        this.svg = d3.select(id);
        this.tooltip = tooltip;
        this.simulation = createForceSimulation();
    }
}

var width = $("#debrief-graph").width(),
    height = $("#debrief-graph").height()

$('svg').width('100%')
$('svg').height('100%')

var link_lengths = {'agent_contact': 100, 'next_link': 50, 'has_agent': 50, 'relationship': 100};
var node_charges = {'c2': -200, 'operation': -100, 'agent': -200, 'link': -150, 'fact': -50, 'tactic': -200, 'technique_name': -200}

var graphSvg = new Graph("#debrief-graph-svg", "graph", d3.select("#op-tooltip")),
    attackPathSvg = new Graph("#debrief-attackpath-svg", "attackpath", d3.select("#op-tooltip")),
    tacticSvg = new Graph("#debrief-tactic-svg", "tactic", d3.select('#op-tooltip')),
    techniqueSvg = new Graph("#debrief-technique-svg", "technique", d3.select('#op-tooltip')),
    factSvg = new Graph("#debrief-fact-svg", "fact", d3.select('#fact-tooltip'))

var graphs = [graphSvg, attackPathSvg, factSvg, tacticSvg, techniqueSvg];

var imgs = {
    "server": "debrief/img/cloud.svg",
    "operation": "debrief/img/operation.svg",
    "link": "debrief/img/link.svg",
    "fact": "debrief/img/star.svg",
    "darwin": "debrief/img/darwin.svg",
    "windows": "debrief/img/windows.svg",
    "linux": "debrief/img/linux.svg",
    "tactic": "debrief/img/tactic.svg",
    "technique_name": "debrief/img/technique.svg",
    "collection": "debrief/img/collection.svg",
    "credential-access": "debrief/img/credaccess.svg",
    "defense-evasion": "debrief/img/defevasion.svg",
    "discovery": "debrief/img/discovery.svg",
    "execution": "debrief/img/execution.svg",
    "exfiltration": "debrief/img/exfil.svg",
    "impact": "debrief/img/impact.svg",
    "lateral-movement": "debrief/img/latmove.svg",
    "persistence": "debrief/img/persistence.svg",
    "privilege-escalation": "debrief/img/privesc.svg",
    "initial-access": "debrief/img/access.svg",
    "command-and-control": "debrief/img/commandcontrol.svg",
    "unknown" : "debrief/img/unknown.svg"
    };

for (var key in imgs) {
    getImage(key, imgs[key])
}

function getImage(i, value) {
    $.get(value, function(data) {
        data.documentElement.id = i + "-img"
        data.documentElement.classList.add("svg-icon")
        $('#images').append(data.documentElement);
    })
}

var colors = d3.scaleOrdinal(d3.schemeCategory10);

function createForceSimulation() {
    return d3.forceSimulation()
            .force("link", d3.forceLink().id(function(d) { return d.id; }))
            .force('charge', d3.forceManyBody()
                .strength(function(d) { return node_charges.hasOwnProperty(d.type) ? node_charges[d.type] : -200 })
                .theta(0.8)
                .distanceMax(100))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(16));
}

function updateReportGraph(operations){
    $('.debrief-svg').innerHTML = "";
    d3.selectAll(".debrief-svg > *").remove();

    graphs.forEach(function(graphObj) {
        buildGraph(graphObj, operations)
        graphObj.simulation.alpha(1).restart();
        graphObj.svg.call(d3.zoom().scaleExtent([0.5, 5]).on("zoom", function() {
            d3.select(graphObj.id + " .graphContainer")
                .attr("transform", "translate(" + d3.event.transform.x + "," + d3.event.transform.y + ")scale(" + d3.event.transform.k + ")");
        }));
    });
}

function buildGraph(graphObj, operations) {
    let url = "/plugin/debrief/graph?type=" + graphObj.type + "&operations=" + operations.join();
    d3.json(url, function (error, graph) {
        if (error) throw error;
        writeGraph(graph, graphObj);
        if (graphObj.type == "fact") {
            limitFactsDisplayed(operations);
        }
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

    var container = graphObj.svg.append("g")
                        .attr("class", "container")
                        .attr("width", "100%")
                        .attr("height", "100%")

    var graphContainer = container.append("g")
                        .attr("class", "graphContainer")

    var arrows = graphContainer.append("g")
                .style("stroke", "#aaa")
                .style("fill", "#aaa")
                .selectAll("polyline")
                .data(graph.links)
                .enter().append("polyline")
                .attr("data-source", function(d) { return d.source })
                .attr("data-target", function(d) { return d.target })
                .attr("class", function(d) { return d.type;})
                .attr("stroke-linecap", "round");

    container.selectAll('g.nodes').remove();
    var nodes = graphContainer.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(graph.nodes)
        .enter().append("g")
            .attr("data-op", function(d) { return d.operation })
            .attr("id", function(d) { return "node-" + d.id })
            .attr("class", function(d) { return "node " + d.type; })
            .attr("data-timestamp", function(d) { return d.timestamp; })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

    nodes.append("circle")
        .attr("r", 16)
        .style("fill", function(d) {
            if (d.status || d.status == 0) {
                return statusColor(d.status);
            }
            else {
                return "#efefef";
            }
        })
        .style("stroke", "#424242")
        .style("stroke-width", "1px")

    nodes.append("text")
        .attr("class", "label")
        .attr("x", "18")
        .attr("y", "8")
        .style("font-size", "12px").style("fill", "white")
        .text(function(d) {
            if (d.type != 'link') {
                return d.name;
            }
        });

    nodes.append("g")
        .attr("class", "icons")
        .html(function(d) {
            let c = updateIconAttr(cloneImgIcon(d), d.status);
            let l = "";
            if (d.type == "link") {
                l = $("#link-img")[0].cloneNode(true);
                l = updateIconAttr(l, d.status);
                $(c).addClass("hidden");
                $(c).hide();
            }
            return c.outerHTML + l.outerHTML;
        })

    var legend = container.append("g")
	    .attr("class", "legend")

	legend.append("rect")
	    .attr("id", "legend-rect-" + graphObj.type)
	    .attr("x", width - 185)
	    .attr("y", 20)
	    .attr("rx", 6)
	    .attr("width", 183)
	    .attr("height", 50)
	    .style("fill", "rgba(170, 170, 170, 0.5)")

	legend.append("text")
	    .attr("x", width - 120)
	    .attr("y", 45)
	    .style("font-weight", "bold")
	    .style("fill", "white")
	    .text("Legend")

	var entry = legend.selectAll("g")
	    .data(graph.nodes.filter(isUniqueImg).concat(addLinkImg(graphObj.type)))
	    .enter()
	    .append("g")

    let lineHeight = 30;
    let upperPadding = 60;

    entry.append("svg")
        .attr("x", width - 170)
        .attr("y", function(d, i){
            $("#legend-rect-" + graphObj.type).attr("height", parseInt($("#legend-rect-" + graphObj.type).attr("height")) + lineHeight);
            let yVal = i * lineHeight + upperPadding;
            if (yVal > height - 90) {
                $("#debrief-graph").height(height + lineHeight);
                height = $("#debrief-graph").height();
            }
            return yVal})
        .attr("width", 20)
        .attr("height", 20)
        .html(function(d) {
            let clone = cloneImgIcon(d);
            this.id = clone.id + "-legend";
            this.setAttribute("viewBox", clone.getAttribute("viewBox"));
            this.setAttribute("preserveAspectRatio", "xMidYMid meet");
            this.setAttribute("xmlns", "http://www.w3.org/2000/svg");
            this.setAttribute("version", "1.0");
            return clone.innerHTML;
        })

    entry.append("text")
        .attr("x", width - 135)
        .attr("y", function(d, i){ return i *  lineHeight + upperPadding + lineHeight/2;})
        .style("fill", "white")
        .style("font-size", 13)
        .style("text-transform", "capitalize")
        .text(function(d) {
            return d.img.indexOf(" ") == -1 ? d.img : d.type;
        });

    if (graphObj.type == "fact") {
        let legendHeight = 50 + parseInt($("#legend-rect-" + graphObj.type).attr("height"));

        var factCountTable  = legend.append("g")
            .attr("class", "fact-count")

        var factEntry = factCountTable.selectAll("g")
            .data(graph.nodes.filter(x => x.type == "fact").filter(isUniqueFactTrait))
            .enter()
            .append("g")

        factEntry.append("text")
            .attr("x", width - 170)
            .attr("y", function(d, i) { return legendHeight + i * 20;})
            .style("fill", "white")
            .style("font-size", 13)
            .text(function(d) {
                return graph.nodes.filter(x => x.name == d.name).length;
            })

        factEntry.append("text")
            .attr("x", width - 135)
            .attr("y", function(d, i) { return legendHeight + i * 20; })
            .style("fill", "white")
            .style("font-size", 13)
            .style("font-weight", "normal")
            .text(function(d) { return d.name; })
    }

    let simulation = graphObj.simulation;

    simulation
        .nodes(graph.nodes)
        .on("tick", ticked)
        .force('link')
        .links(graph.links)
        .distance(function(d) {return link_lengths[d.type];});

    function ticked() {

        arrows
            .attr("points", function(d) { return getPolylineCoords(d.source.x, d.source.y, d.target.x, d.target.y) })
            .attr("transform", function(d) { return rotateArrow(d.source.x, d.source.y, d.target.x, d.target.y) });

        nodes
            .attr('transform', function(d) {return 'translate(' + d.x + ',' + d.y + ')';})
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
        switch (d["type"]) {
            case "operation":
                ret += "name: " + d["name"] + "<br/>";
                ret += "op_id: " + d["id"] + "<br/>";
                ret += "created: " + d["timestamp"] + "<br/>";
                break;
            case "tactic":
            case "technique_name":
                let p = d["attrs"][d["type"]]
                ret += d["type"] + ": " + p + "<br/>";
                ret += "created: " + d["timestamp"] + "<br/>";
                for (let attr in d["attrs"]) {
                    if (attr != d["type"]) {
                        ret += attr + ": " + d["attrs"][attr] + "<br/>";
                    }
                }
                break;
            default:
                ret += d["timestamp"] ? "created: " + d["timestamp"] + "<br/>" : "";
                for (let attr in d["attrs"]) {
                    if (d["attrs"][attr] != null) {
                        ret += attr + ": ";
                        ret += attr == "status" ? statusName(d["attrs"][attr]) : d["attrs"][attr];
                        ret += "<br/>";
                    }
                }
        }
        return ret;
    }

    function getPolylineCoords(x1, y1, x2, y2) {
        let p1 = `${x1} ${y1}`;
        let x = x1 - Math.hypot(x2-x1, y2-y1) + 17;
        let p2 = `${x} ${y1}`;
        let p3 = `${x + 7.5} ${y1 + 4}`;
        let p4 = `${x + 7.5} ${y1 - 4}`;
        let p5 = p2;
        return `${p1}, ${p2}, ${p3}, ${p4}, ${p5}`;
    }

    function rotateArrow(x1, y1, x2, y2) {
      let deltaX = x2 - x1;
      let deltaY = y2 - y1;
      let angleDeg = Math.atan2(deltaY, deltaX) * 180 / Math.PI + 180;
      return `rotate(${angleDeg}, ${x1}, ${y1})`;
    }
}

function cloneImgIcon(d) {
    let c;
    try {
        if (d.img.indexOf(" ") == -1 && $("#" + d.img + "-img").length > 0) {
            c = $("#" + d.img + "-img")[0].cloneNode(true);
        }
        else {
            c = $("#" + d.type + "-img")[0].cloneNode(true);
        }
    }
    catch {
        c = $("#unknown-img")[0].cloneNode(true);
    }
    return c;
}

function updateIconAttr(svg, status) {
    $(svg).removeAttr("id");
    $(svg).attr("width", 32);
    $(svg).attr("height", 16);
    $(svg).attr("x", "-16");
    $(svg).attr("y", "-8");
    if (status && status == -2) {
        $($(svg).children()[0]).attr("fill", "white");
    }
    return svg;
}

function statusColor(status) {
    if (status === 0) {
        return '#44AA99';
    } else if (status === -2) {
        return 'black';
    } else if (status === 1) {
        return '#CC3311';
    } else if (status === 124) {
        return 'cornflowerblue';
    } else if (status === -3) {
        return '#FFB000';
    } else if (status === -4) {
        return 'white';
    } else if (status === -5) {
        return '#EE3377';
    }
    return '#555555';
}

function limitFactsDisplayed(operations) {
    let hasOverFactLimit = operations.some(function(op) { return $("#debrief-fact-svg g.fact[data-op='" + op + "']").slice(factDisplayLimit).length > 0 })
    if (hasOverFactLimit) {
        $("#fact-limit-msg p").html("More than " + factDisplayLimit + " facts found in the operation(s) selected. For readability, only the first " + factDisplayLimit + " facts of each operation are displayed.");
        $("#fact-limit-msg").show();
        operations.forEach(function(opId) {
            let nodesToRemove = $("#debrief-fact-svg g.fact[data-op='" + opId + "']").splice(factDisplayLimit);
            nodesToRemove.forEach(function(node) {
                let nodeId = node.id.split("node-")[1];
                $("#debrief-fact-svg polyline.relationship[data-source='" + nodeId + "']").remove();
                $("#debrief-fact-svg polyline.relationship[data-target='" + nodeId + "']").remove();
                node.remove();
            })
        })
    }
}

function isUniqueImg(value, index, self) {
    let arr = Array.from(self, x => x.img.indexOf(" ") == -1 ? x.img : x.type);
    let v = value.img.indexOf(" ") == -1 ? value.img : value.type;
    return arr.indexOf(v) === index;
}

function addLinkImg(graphType) {
    return graphType == "graph" ? [{"name": "link-image", "img": "link"}] : [];
}

function isUniqueFactTrait(value, index, self) {
    let arr = Array.from(self, x => x.name);
    return arr.indexOf(value.name) == index;
}
