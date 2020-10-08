var nodesOrderedByTime;
var visualizeInterval;

$( document ).ready(function() {
    $('#debrief-download-raw').click(function () {
        let operations = $('#debrief-operation-list').val();
        if (operations) {
            operations.forEach(function (op_id, index) {
                let postData = op_id ? {
                    'index': 'operation_report',
                    'op_id': op_id,
                    'agent_output': Number(1)
                } : null;
                let time = new Date().toISOString().split('.')[0].replaceAll(':', '-');
                let opName = $("#debrief-operation-list option[value='" + op_id + "']").text();
                downloadReport('/api/rest', 'debrief_' + opName + '_' + time, postData);
            })
        }
        else {
            stream('Select at least one operation to generate the JSON report');
        }
    });

    $('#debrief-operation-list').change(function (e){
        clearReport();
        let operations = $(e.target).val();
        if (operations) {
            updateReportGraph(operations);
            $('.debrief-display-opt').prop("checked", true);
            $("#show-tactic-icons").prop("checked", false);
            $("#fact-limit-msg").hide();
            $("#fact-limit-msg p").html();
            restRequest('POST', {'operations': operations}, displayReport, '/plugin/debrief/report');
        }
    });

    function clearReport(){
        $("#report-operations tbody tr").remove();
        $("#report-steps tbody tr").remove();
        $("#report-agents tbody tr").remove();
        $("#report-tactics-techniques tbody tr").remove();
    }

    function displayReport(data){
        let operations = data['operations'];
        operations.forEach(function (op, index) {
            updateOperationTable(op);
            updateStepTable(op);
        })
        updateAgentTable(data['agents']);
        updateTacticTechniqueTable(data['ttps']);
        nodesOrderedByTime = getNodesOrderedByTime();
    }

    function updateOperationTable(op){
        $("#report-operations tbody").append("<tr>" +
            "<td>"+op.name+"</td>" +
            "<td style='text-transform: capitalize;'>"+op.state+"</td>" +
            "<td>"+op.planner.name+"</td>" +
            "<td>"+op.objective.name+"</td>" +
            "<td>"+op.start+"</td>" +
            "</tr>");
    }

    function updateStepTable(op){
        op.chain.forEach(function (step, index) {
            $("#report-steps tbody").append("<tr>" +
                "<td>"+statusName(step.status) +"</td>" +  //
                "<td>"+step.finish+"</td>" +  //
                "<td>"+step.ability.name+"</td>" +
                "<td>"+step.paw+"</td>" +
                "<td>"+op.name+"</td>" +  //
                "<td><button data-encoded-cmd='"+step.command +"' onclick='findResults(this,"+step.id+")'>Show" +
                " Command</button></td>" +
                "</tr>");
        })
    }

    function updateTacticTechniqueTable(ttps) {
        function generateList(objList, innerList) {
            let ret = innerList ? "<ul>" : "<ul style='padding: 0px'>";
            objList.forEach(function(obj) {
                ret += "<li>" + obj + "</li>"
            })
            ret += "</ul>"
            return ret;
        }
        function generateTechniqueList(techniques) {
            let arr = [];
            for (let name in techniques) {
                arr.push(techniques[name] + ": " + name);
            }
            return generateList(arr, false);
        }
        function generateStepList(steps) {
            let ret = "<ul style='padding: 0px'>"
            for (let opName in steps) {
                ret += "<li style='color: grey'>" + opName + "</li>";
                ret += generateList(steps[opName], true);
            }
            ret += "</ul>"
            return ret;
        }
        for (let key in ttps) {
            let tactic = ttps[key];
            $("#report-tactics-techniques tbody").append("<tr>" +
                "<td style='text-transform: capitalize;'>" + tactic.name + "</td>" +
                "<td>" + generateTechniqueList(tactic.techniques) + "</td>" +
                "<td>" + generateStepList(tactic.steps) + "</td>" +
                "</tr");
        }
    }

    function updateAgentTable(agents) {
        agents.forEach(function(agent) {
            $("#report-agents tbody").append("<tr>" +
                "<td>" + agent.paw + "</td>" +
                "<td>" + agent.host + "</td>" +
                "<td>" + agent.platform + "</td>" +
                "<td>" + agent.username + "</td>" +
                "<td>" + agent.privilege + "</td>" +
                "<td>" + agent.exe_name + "</td>" +
                "</tr>"
            );
        })
    }

    function statusName(status) {
        if (status === 0) {
            return 'success';
        } else if (status === -2) {
            return 'discarded';
        } else if (status === 1) {
            return 'failure';
        } else if (status === 124) {
            return 'timeout';
        } else if (status === -3) { // && chain.collect) {
            return 'collected';
        } else if (status === -4) {
            return 'untrusted';
        } else if (status === -5) {
            return 'visibility';
        }
        return 'queued';
    }
});

function switchGraphView(btn) {
    $(".op-svg").hide();
    $(".graph-switch").attr("disabled", false);
    $("#graph-switch-" + $(btn).val()).attr("disabled", true);
    $("#debrief-" + $(btn).val() + "-svg").show();
}

function downloadPDF() {
    function callback(data) {
        if (typeof data == 'string') {
            stream('Select at least one operation to generate a PDF report');
        }
        else {
            stream('Downloading PDF report: '+ data['filename'] + '.pdf');

            let file = new Blob([data['pdf_bytes']], { type: 'application/pdf' });
            let fileURL = URL.createObjectURL(file);

            let downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute('href', fileURL);
            downloadAnchorNode.setAttribute('download', data['filename'] + '.pdf');
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        }
    }
    restRequest('POST', {'operations': $('#debrief-operation-list').val(), 'graphs': getGraphData()}, callback, '/plugin/debrief/pdf');
}

function findResults(elem, lnk){
    function loadResults(data){
        if (data) {
            let res = atob(data.output);
            $.each(data.link.facts, function (k, v) {
                let regex = new RegExp(String.raw`${v.value}`, "g");
                res = res.replace(regex, "<span class='highlight'>" + v.value + "</span>");
            });
            $('#debrief-step-modal-view').html(res);
        }
    }
    document.getElementById('debrief-step-modal').style.display='block';
    $('#debrief-step-modal-cmd').html(atob($(elem).attr('data-encoded-cmd')));
    restRequest('POST', {'index':'result','link_id':lnk}, loadResults);
}

function resetDebriefStepModal() {
    let modal = $('#debrief-step-modal');
    modal.hide();
    modal.find('#debrief-step-modal-cmd').text('');
    modal.find('#debrief-step-modal-view').text('');
}

function getGraphData() {
    let encodedGraphs = {}

    $(".debrief-svg").each(function(idx, svg) {
        $("#copy").append($(svg).clone().prop("id", "copy-svg"))
        $("#copy-svg .container").attr("transform", "scale(5)")

//        resize svg viewBox to fit content
        var copy = $("#copy-svg")[0];
        if (copy.style.display == "none") {
            copy.style.display = "";
        }
        var bbox = copy.getBBox();
        var viewBox = [bbox.x - 10, bbox.y - 10, bbox.width + 20, bbox.height + 20].join(" ");
        copy.setAttribute("viewBox", viewBox);

//        re-enable any hidden nodes
        $("#copy-svg .link").show()
        $("#copy-svg .next_link").show()
        $("#copy-svg .link .icons").children('.svg-icon').show();
        $("#copy-svg .link .icons").children('.hidden').remove();
        $("#copy-svg text").show();
        $("#copy-svg text").css("fill", "#333");

        let serializedSvg = new XMLSerializer().serializeToString($("#copy-svg")[0])
        let encodedData = window.btoa(serializedSvg);
        let graphKey = $(svg).attr("id").split("-")[1]
        encodedGraphs[graphKey] = encodedData
        $("#copy").html("")
    })

    return encodedGraphs
}

function toggleLabels(input) {
    if($(input).prop("checked")) {
        $("#debrief-graph text").show();
    }
    else {
        $("#debrief-graph text").hide();
    }
}

function toggleSteps(input) {
    if($(input).prop("checked")) {
        $("#debrief-graph .link").show()
        $("#debrief-graph-svg .next_link").show()
    }
    else {
        $("#debrief-graph .link").hide()
        $("#debrief-graph-svg .next_link").hide()
    }
}

function toggleTacticIcons(input) {
    let showing = $("#debrief-graph .link .icons").children(".svg-icon:not(hidden)");
    let hidden = $("#debrief-graph .link .icons").children(".hidden");
    showing.hide();
    hidden.show();
    showing.addClass("hidden");
    hidden.removeClass("hidden");
}

function toggleIcons(input) {
    if($(input).prop("checked")) {
        $("#debrief-graph .svg-icon:not(.hidden)").show();
    }
    else {
        $("#debrief-graph .svg-icon:not(.hidden)").hide();
    }
}

function visualizeTogglePlay() {
    if ($("#graph-media-play").hasClass("paused")) {
        if (!nodesOrderedByTime.find(node => node.style.display == "none")) {
            visualizeBeginning();
        }
        $("#graph-media-play").removeClass("paused");
        $("#graph-media-play").html("||");
        visualizeInterval = setInterval(visualizeStepForward, 1000);
    }
    else {
        $("#graph-media-play").html("&#x25B6;");
        $("#graph-media-play").addClass("paused");
        clearInterval(visualizeInterval);
    }
}

function visualizeStepForward() {
    let nextNode = nodesOrderedByTime.find(node => node.style.display == "none");
    if (nextNode) {
        $(nextNode).show();

        let showingNodesIds = nodesOrderedByTime.filter(node => node.style.display != "none").map(node => node.id);
        let relatedLines = $("#debrief-graph-svg line").filter(function(idx, line) {
            return showingNodesIds.includes("node-" + $(line).data("target")) && showingNodesIds.includes("node-" + $(line).data("source"))
        })
        relatedLines.show();
    }

    if (!$("#graph-media-play").hasClass("paused") && !nodesOrderedByTime.find(node => node.style.display == "none")) {
        $("#graph-media-play").addClass("paused");
        $("#graph-media-play").html("&#x25B6;");
        clearInterval(visualizeInterval);
    }
}

function visualizeStepBack() {
    let prevNode = $(nodesOrderedByTime.slice().reverse().find(node => node.style.display != "none"));

    if (prevNode.attr("id") != "#node-0") {
        prevNode.hide();

        let showingNodesIds = nodesOrderedByTime.filter(node => node.style.display != "none").map(node => node.id);
        let relatedLines = $("#debrief-graph-svg line").filter(function(idx, line) {
            return !(showingNodesIds.includes("node-" + $(line).data("target")) && showingNodesIds.includes("node-" + $(line).data("source")))
        })
        relatedLines.hide();
    }

}

function visualizeBeginning() {
    $("#debrief-graph-svg .node:not(.c2)").hide();
    $("#debrief-graph-svg line").hide();
}

function visualizeEnd() {
    $("#debrief-graph-svg .node").show();
    $("#debrief-graph-svg line").show();
}

function getNodesOrderedByTime() {
    function compareTimestamp(a, b) {
        if (Date.parse(a.dataset.timestamp) < Date.parse(b.dataset.timestamp)) {
            return -1;
        }
        if (Date.parse(a.dataset.timestamp) > Date.parse(b.dataset.timestamp)) {
            return 1;
        }
        return 0;
    }
    return $("#debrief-graph-svg .node").toArray().sort(compareTimestamp);
}
