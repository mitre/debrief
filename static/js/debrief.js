
$('#debrief-operation-list').change(function (e){
    let operations = $(e.target).val();
    restRequest('POST', {'operations': operations}, displayReport, '/plugin/debrief/report');
    console.log(operations);
});

function displayReport(data){
    console.log(data);
    let op = data[0];
    $('#report-name').html(op.name);
    $('#report-name-duration').html("The operation lasted " + reportDuration(op) + " with a random "+op.jitter + " second pause between steps");
    $('#report-adversary').html(op.adversary.name);
    $('#report-adversary-desc').html(op.adversary.description);
    $('#report-group').html(op.host_group[0]['group']);
    $('#report-group-cnt').html(op.host_group.length + ' agents were included');
    addSteps(op.chain);
    addFacts(op.chain);
}

function reportDuration(data) {
    if(data.state === 'finished') {
        let finish = reportFinished(data.chain);
        let operationInSeconds = Math.abs(finish - new Date(data.start)) / 1000;
        let operationInMinutes = Math.floor(operationInSeconds / 60) % 60;
        operationInSeconds -= operationInMinutes * 60;
        let secondsRemainder = operationInSeconds % 60;
        return operationInMinutes + 'min ' + secondsRemainder + 'sec';
    }
    return "(not finished yet)"
}

 function reportFinished(steps) {
    let latest = d = new Date(0);
    steps.forEach(s => {
        let d = new Date(s.finish);
        if(d > latest) {
            latest = d;
        }
    });
    return latest;
}

 function reportStepLength(steps) {
    let step_len = 0;
    step_len += steps.length;
    return step_len;
}

 function reportScore(steps) {
    let failed = 0;
    steps.forEach(s => {
        if(s.status > 0) {
            failed += 1;
        }
    });
    return parseInt(100 - (failed/reportStepLength(steps) * 100)) + '%';
}

 function reportAllFacts(steps) {
    var facts = []
    steps.forEach(s => {
        facts = facts.concat(s.facts);
    });
    return facts;
}

 function addSteps(steps) {
    $("#report-steps").find("tr:gt(0)").remove();
    steps.forEach(s => {
        $("#report-steps tbody").append("<tr><td>"+statusName(s.status)+"</td><td>"+s.host+"</td><td>"+s.ability.name+"</td><td>"+s.ability.technique_name+"</td></tr>");
    });
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
    } else if (status === -3 && chain.collect) {
        return 'collected';
    } else if (status === -4) {
        return 'untrusted';
    } else if (status === -5) {
        return 'visibility';
    }
    return 'queued';
}

 function addFacts(steps){
    $("#report-facts").find("tr:gt(0)").remove();
    let factsList = reportAllFacts(steps);
    let facts = {};
    factsList.forEach(f => {
        if (!(f.trait in facts)) {
            facts[f.trait] = [f.value];
        } else {
            facts[f.trait].push(f.value);
        }
    });
    console.log(factsList);
    console.log(facts);
    $.each(facts, function( key, value ) {
      let factData = "<td>";
      $.each(value, function( index, fact ) {
        factData += fact+"<br/>"
      });

       factData += "</td>";
      let result = "<tr><td>"+key+"</td>"+factData+"</tr>";
      $("#report-facts").append(result);
    });
}