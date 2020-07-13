$( document ).ready(function() {
    $('#debrief-download-raw').click(function () {
        let operations = $('#debrief-operation-list').val();
        operations.forEach(function (op_id, index) {
            let postData = op_id ? {
                'index': 'operation_report',
                'op_id': op_id,
                'agent_output': Number(1)
            } : null;
            // TODO: add filename = operation name, agent output selection
            downloadReport('/api/rest', "operation", postData);
        })
    });

    $('#debrief-operation-list').change(function (e){
        clearReport();
        let operations = $(e.target).val();
        updateReportGraph(operations);
        restRequest('POST', {'operations': operations}, displayReport, '/plugin/debrief/report');
    });

    function clearReport(){
        $("#report-operations tbody tr").remove();
        $("#report-steps tbody tr").remove();
    }

    function displayReport(data){
        let operations = data['operations'];
        operations.forEach(function (op, index) {
            updateOperationTable(op);
            updateStepTable(op);
        })
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

function downloadPDF() {
    function callback(data) {
        if (typeof data == 'string') {
            stream('Select a single operation to generate a PDF report');
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
    restRequest('POST', {'operation_id': $('#debrief-operation-list').val()}, callback, '/plugin/debrief/pdf');
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