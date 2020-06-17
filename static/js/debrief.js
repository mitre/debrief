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
        restRequest('POST', {'operations': operations}, displayReport, '/plugin/debrief/report');
    });

    function clearReport(){
        $("#report-operations tbody tr").remove();
        $("#report-steps tbody tr").remove();
    }

    function displayReport(data){
        let operations = data['operations'];
        updateReportGraph(operations);
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
                "<td><button>Show Command</button></td>" +
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