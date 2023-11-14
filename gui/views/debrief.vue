<script setup>
import { inject, ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";

const $api = inject("$api");

onMounted(async () => {});
</script>

<script>
import '/debrief/js/d3.v4.min.js';
import '/assets/d3-zoom.v1.min.js';
import '/assets/graph.js';
</script>

<style scoped>
@import "/debrief/css/debrief.css";
</style>

<script>
export default {
  inject: ["$api"],
  data() {
    return {
        operations: [],
        selectedOperationIds: [],
        activeTab: 'stats',

        stats: [],
        agents: [],
        steps: [],
        tacticsAndTechniques: [],

        showCommandModal: false,
        command: '',
        commandOutput: '',
        commandAbilityName: '',

        showGraphSettingsModal: false,
        graphOptionLabels: true,
        graphOptionIcons: true,
        graphOptionSteps: true,

        showReportModal: false,
        reportSections: JSON.parse(`{{ report_sections | tojson }}`),
        activeReportSections: [],
        useCustomLogo: false,
        logoFilename: '',
        logos: [],

        selectedGraphType: 'attackpath',
        nodesOrderedByTime: {},
        showGraphLegend: true,
        isGraphPlaying: false,
        graphInterval: null,
    };
  },
  created() {
    this.initDebrief();
  },
  methods: {
    initPage() {
            this.$api.get('/api/v2/operations').then((operations) => {
                this.operations = operations;
                this.initReportSections();
                return this.$api.get('/plugin/debrief/logos');
            }).then(async (data) => {
                this.logos = data.logos;
                window.addEventListener('resize', moveLegend);

                // While the debrief tab is open, keep checking for new/killed agents
                while (this.$refs.debriefHeader) {
                    await sleep(3000);
                    this.refreshOperations();
                }
            }).catch((error) => {
                console.error(error);
                toast('Error getting operations');
            });
        },

        refreshOperations() {
          this.$api.get('/api/v2/operations').then((operations) => {
                this.operations = operations;
            }).catch((error) => {
                console.error(error);
                toast('Error refreshing operations');
            });
        },

        initReportSections() {
            const BASE_ORDERING = [ 
                "main-summary",
                "statistics",
                "agents",
                "attackpath-graph",
                "steps-graph",
                "tactic-graph",
                "technique-graph",
                "fact-graph",
                "tactic-technique-table",
                "steps-table",
                "facts-table"
            ];
            this.reportSections.sort((a, b) => {
                let aIndex = BASE_ORDERING.indexOf(a.key);
                let bIndex = BASE_ORDERING.indexOf(b.key);
                return aIndex - bIndex;
            });
            this.activeReportSections = this.reportSections.map((section) => section.key);
        },

        loadOperation() {
            if (!this.selectedOperationIds.length) return;
            this.$api.post('/plugin/debrief/report', { operations: this.selectedOperationIds }).then((data) => {
                this.stats = data.operations;
                this.agents = data.operations.map((o) => o.host_group).flat();

                this.steps = [];
                this.stats.forEach((stat) => {
                    stat.chain.forEach((c) => {
                        this.steps.push({ ...c, operation_name: stat.name });
                    });
                });

                Object.keys(data.ttps).forEach((tactic) => {
                    data.ttps[tactic].steps = Object.keys(data.ttps[tactic].steps).map((op) => {
                        return {
                            operation: op,
                            abilities: data.ttps[tactic].steps[op]
                        }
                    })
                })
                this.tacticsAndTechniques = data.ttps;

                updateReportGraph(this.selectedOperationIds);
            }).catch((error) => {
                toast('Error loading operation', false);
                console.error(error);
            })
        },

        operationSelectMousedown(el) {
            // An override to the select field so users don't need to hold CMD or Ctrl while selecting multiple op's
            el.selected = !el.selected;
            this.selectedOperationIds = Array.from(el.parentNode.childNodes)
                .filter((node) => node.localName === 'option' && node.selected)
                .map((node) => node.value);
            this.loadOperation();
        },
        
        getStatusName(status) {
            if (status === 0) {
                return 'success';
            } else if (status === -2) {
                return 'discarded';
            } else if (status === 1) {
                return 'failure';
            } else if (status === 124) {
                return 'timeout';
            } else if (status === -3) {
                return 'collected';
            } else if (status === -4) {
                return 'untrusted';
            } else if (status === -5) {
                return 'visibility';
            }
            return 'queued';
        },

        showCommand(id, command, abilityName) {
            this.commandAbilityName = abilityName;
            let requestBody = {
                index: 'result',
                link_id: id
            };
            this.$api.post('/api/rest', requestBody).then((data) => {
                if (data) {
                    try {
                        this.command = b64DecodeUnicode(data.link.command);
                        this.commandOutput = JSON.parse(b64DecodeUnicode(data.output));
                    } catch (error) { // occurs when data is not JSON
                        this.commandOutput = '';
                        console.error(error);
                        toast('Error getting command and/or command results.');
                    }
                } else {
                    this.command = 'No command to display';
                    this.commandOutput = '';
                }
                this.showCommandModal = true;
            });
        },

        moveReportSectionOrder(index, toIndex) {
            if (toIndex < 0 || toIndex >= this.reportSections.length) return;

            let temp = this.reportSections[index];
            this.reportSections[index] = this.reportSections[toIndex];
            this.reportSections[toIndex] = temp;

            let sortedActiveSections = this.activeReportSections;
            this.activeReportSections = this.reportSections.map((section) => section.key).filter((section) => sortedActiveSections.includes(section));
        },

        toggleReportSection(section) {
            let index = this.activeReportSections.indexOf(section);
            index >= 0 ? this.activeReportSections.splice(index, 1) : this.activeReportSections.push(section);
        },

        toggleLegend() {
            this.showGraphLegend = !this.showGraphLegend;
            document.querySelectorAll('.legend').forEach((legend) => {
                legend.style.display = (this.showGraphLegend ? 'block' : 'none');
            });
        },
        
        uploadLogo(el) {
            if (el.files.length === 0) return;

            let formData = new FormData()
            formData.append('header-logo', el.files[0])
            this.$api.post('/plugin/debrief/logo', formData, false).then((data) => {
                this.logos.push(data.filename);
                this.logoFilename = data.filename;
            }).catch((error) => {
                console.error(error);
                toast('Error uploading file', false);
            });
        },

        downloadPDF() {
            let requestBody = {
                'operations': this.selectedOperationIds,
                'graphs': this.getGraphData(),
                'report-sections': this.activeReportSections,
                'header-logo': this.logoFilename
            };
            this.$api.post('/plugin/debrief/pdf', requestBody, true).then((data) => {
                let dataStr = URL.createObjectURL(new Blob([data["pdf_bytes"]], { type: "application/pdf" }));
                let downloadAnchorNode = document.createElement("a");
                downloadAnchorNode.setAttribute("href", dataStr);
                downloadAnchorNode.setAttribute("download", data.filename);
                document.body.appendChild(downloadAnchorNode);
                downloadAnchorNode.click();
                downloadAnchorNode.remove();
            }).catch((error) => {
                console.error(error);
                toast('Error downloading PDF report', false);
            });
        },

        downloadJSON() {
          this.$api.post('/plugin/debrief/json', { 'operations': this.selectedOperationIds }).then((data) => {
                downloadJson(data.filename, data);
            }).catch((error) => {
                console.error(error);
                toast('Error downloading JSON report', false);
            });
        },

        getGraphData() {
            let encodedGraphs = {}

            document.querySelectorAll('.debrief-svg').forEach((svg) => {
                newSvg = svg.cloneNode(true);
                newSvg.setAttribute('id', 'copy-svg');
                document.getElementById('copy').appendChild(newSvg)
                document.querySelectorAll('#copy-svg .container').forEach((container) => container.setAttribute('transform', 'scale(5)'))

                // resize svg viewBox to fit content
                var copy = document.getElementById('copy-svg');
                if (copy.style.display == "none") {
                    copy.style.display = "";
                }
                var bbox = copy.getBBox();
                var viewBox = [bbox.x - 10, bbox.y - 10, bbox.width + 20, bbox.height + 20].join(" ");
                copy.setAttribute("viewBox", viewBox);

                // re-enable any hidden nodes
                document.querySelectorAll('#copy-svg .link').forEach((el) => el.style.display = '');
                document.querySelectorAll('#copy-svg polyline').forEach((el) => el.style.display = '');
                document.querySelectorAll('#copy-svg .link .icons').forEach((el) => {
                    Array.from(el.children).forEach((child) => { 
                        if (child.getAttribute('class').includes('svg-icon')) {
                            child.style.display = '';
                        }
                    })
                })
                document.querySelectorAll('#copy-svg .link .icons').forEach((el) => {
                    Array.from(el.children).forEach((child) => { 
                        if (child.getAttribute('class').includes('hidden')) {
                            child.remove();
                        }
                    })
                })
                document.querySelectorAll('#copy-svg text').forEach((el) => el.style.display = '');
                document.querySelectorAll('#copy-svg text').forEach((el) => el.style.fill = '#333');

                let serializedSvg = new XMLSerializer().serializeToString(document.getElementById('copy-svg'));
                let encodedData = window.btoa(serializedSvg);
                let graphKey = svg.id.split("-")[1];
                encodedGraphs[graphKey] = encodedData;
                document.getElementById('copy').innerHTML = '';
            })

            return encodedGraphs
        },

        toggleLabels() {
            if (this.graphOptionLabels) {
                document.querySelectorAll('#debrief-graph .label').forEach((el) => el.style.display = '');
            } else {
                document.querySelectorAll('#debrief-graph .label').forEach((el) => el.style.display = 'none');
            }
        },

        toggleIcons() {
            if (this.graphOptionIcons) {
                document.querySelectorAll('#debrief-graph .svg-icon:not(.hidden)').forEach((el) => el.style.display = '');
            } else {
                document.querySelectorAll('#debrief-graph .svg-icon:not(.hidden)').forEach((el) => el.style.display = 'none');
            }
        },

        toggleSteps() {
            if (this.graphOptionSteps) {
                document.querySelectorAll('#debrief-graph .link').forEach((el) => el.style.display = '');
                document.querySelectorAll('#debrief-steps-svg .next_link').forEach((el) => el.style.display = '');
            } else {
                document.querySelectorAll('#debrief-graph .link').forEach((el) => el.style.display = 'none');
                document.querySelectorAll('#debrief-steps-svg .next_link').forEach((el) => el.style.display = 'none');
            }
        },

        toggleTactics() {
            let showing = [];
            document.querySelectorAll('#debrief-graph .link .icons').forEach((el) => {
                Array.from(el.children).forEach((child) => { 
                    if (child.classList.contains('svg-icon') && !child.classList.contains('hidden')) showing.push(child);
                });
            });
            let hidden = [];
            document.querySelectorAll('#debrief-graph .link .icons').forEach((el) => {
                Array.from(el.children).forEach((child) => { 
                    if (child.classList.contains('hidden')) hidden.push(child);
                });
            });

            showing.forEach((child) => {
                child.style.display = 'none';
                child.classList.add('hidden');
            });
            hidden.forEach((child) => {
                child.style.display = '';
                child.classList.remove('hidden');
            });
        },

        // Graph functions

        getNodesOrderedByTime() {
            function compareTimestamp(a, b) {
                if (Date.parse(a.dataset.timestamp) < Date.parse(b.dataset.timestamp)) {
                    return -1;
                }
                if (Date.parse(a.dataset.timestamp) > Date.parse(b.dataset.timestamp)) {
                    return 1;
                }
                return 0;
            }
            function getSortedNodes(id) {
                return Array.from(document.querySelectorAll(`#${id} .node`)).sort(compareTimestamp);
            }
            
            this.nodesOrderedByTime = {};
            this.nodesOrderedByTime["debrief-steps-svg"] = getSortedNodes("debrief-steps-svg");
            this.nodesOrderedByTime["debrief-attackpath-svg"] = getSortedNodes("debrief-attackpath-svg");
            this.nodesOrderedByTime["debrief-tactic-svg"] = getSortedNodes("debrief-tactic-svg");
            this.nodesOrderedByTime["debrief-technique-svg"] = getSortedNodes("debrief-technique-svg");
        },

        async visualizePlayPause() {
            this.getNodesOrderedByTime();
            this.isGraphPlaying = !this.isGraphPlaying;
            let id = this.$refs[this.selectedGraphType].id;

            if (this.isGraphPlaying) {
                if (!this.nodesOrderedByTime[id].find(node => node.style.display == "none")) {
                    this.visualizeBeginning();
                }

                while (this.isGraphPlaying) {
                    await sleep(1000);
                    if (this.isGraphPlaying) {
                        this.visualizeStepForward();
                    }
                }
            }
        },

        visualizeBeginning() {
            let id = this.$refs[this.selectedGraphType].id;
            document.querySelectorAll(`#${id} .node:not(.c2)`).forEach((node) => node.style.display = 'none');
            document.querySelectorAll(`#${id} polyline`).forEach((node) => node.style.display = 'none');
        },

        visualizeEnd() {
            let id = this.$refs[this.selectedGraphType].id;
            document.querySelectorAll(`#${id} .node`).forEach((node) => node.style.display = 'block');
            document.querySelectorAll(`#${id} polyline`).forEach((node) => node.style.display = 'block');
        },

        visualizeStepForward() {
            this.getNodesOrderedByTime();
            let id = this.$refs[this.selectedGraphType].id;

            let nextNode = this.nodesOrderedByTime[id].find(node => node.style.display == "none");
            if (nextNode) {
                nextNode.style.display = 'block';

                let showingNodesIds = this.nodesOrderedByTime[id].filter(node => node.style.display !== "none").map(node => node.id);
                document.querySelectorAll(`#${id} polyline`).forEach((line) => {
                    if (showingNodesIds.includes(`node-${line.getAttribute('data-target')}`) && showingNodesIds.includes(`node-${line.getAttribute('data-source')}`)) {
                        line.style.display = "block";
                    }
                })
            }

            if (!this.nodesOrderedByTime[id].find(node => node.style.display == "none")) {
                this.isGraphPlaying = false;
            }
        },

        visualizeStepBack() {
            this.getNodesOrderedByTime();
            let id = this.$refs[this.selectedGraphType].id;

            let prevNode = this.nodesOrderedByTime[id].slice().reverse().find(node => node.style.display != "none");

            if (prevNode.id !== "node-0") {
                prevNode.style.display = 'none';

                let showingNodesIds = this.nodesOrderedByTime[id].filter(node => node.style.display != "none").map(node => node.id);
                document.querySelectorAll(`#${id} polyline`).forEach((line) => {
                    if (!showingNodesIds.includes(`node-${line.getAttribute('data-target')}`) || !showingNodesIds.includes(`node-${line.getAttribute('data-source')}`)) {
                        line.style.display = 'none';
                    }
                });
            }
        },
  },
};
</script>

<template lang="pug">
div(v-bind:ref="debriefHeader")
  h2 Debrief
  p
    strong Campaign Analytics.
    |  Debrief gathers overall campaign information and analytics for a selected 
    |  set of operations. It provides a centralized view of operation metadata, graphical displays of 
    |  the operations, the techniques and tactics used, and the facts discovered by the operations.

hr

div
  .buttons
    button.button.is-primary.is-small(:disabled="!selectedOperationIds.length", @click="showGraphSettingsModal = true")
      span.icon
        em.fas.fa-cog
      span Graph Settings
    button.button.is-primary.is-small(:disabled="!selectedOperationIds.length", @click="showReportModal = true")
      span.icon
        em.fas.fa-file-pdf
      span Download PDF Report
    button.button.is-primary.is-small(:disabled="!selectedOperationIds.length", @click="downloadJSON")
      span.icon
        em.fas.fa-file-code
      span Download Operation JSON

  .columns.mb-6
    .column.is-3
      form
        .field
          label.label Select one or more operations
          .control.is-expanded
            .select.is-small.is-fullwidth.is-multiple
              select(size="10", multiple, v-model="selectedOperationIds", @change="loadOperation")
                template(v-for="operation in operations", :key="operation.id")
                  option(:value="operation.id") {{ operation.name }}
    .column.is-9.is-flex.is-justify-content-center.m-0
      #images(style="display: none")
      #copy
      #debrief-graph.svg-container(v-show="selectedOperationIds.length")
        .d3-tooltip#op-tooltip(style="opacity: 0")
        .is-flex.graph-controls.m-2
          .select.is-small.mr-2
            select(v-model="selectedGraphType")
              option(value="attackpath") Attack Path
              option(value="steps") Steps
              option(value="tactic") Tactic
              option(value="technique") Technique
          button.button.is-small(@click="toggleLegend") {{ showGraphLegend ? 'Hide' : 'Show' }} Legend
        svg#debrief-steps-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'steps'")
        svg#debrief-attackpath-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'attackpath'")
        svg#debrief-tactic-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'tactic'")
        svg#debrief-technique-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'technique'")
        .buttons.is-justify-content-center.mt-2
          button.button.is-small(@click="visualizeBeginning")
            span.icon
              em.fas.fa-fast-backward
          button.button.is-small(@click="visualizeStepBack")
            span.icon
              em.fas.fa-backward
          button.button.is-small(v-show="isGraphPlaying", @click="visualizePlayPause")
            span.icon
              em.fas.fa-pause
          button.button.is-small(v-show="!isGraphPlaying", @click="visualizePlayPause")
            span.icon
              em.fas.fa-play
          button.button.is-small(@click="visualizeStepForward")
            span.icon
              em.fas.fa-forward
          button.button.is-small(@click="visualizeEnd")
            span.icon
              em.fas.fa-fast-forward

  .tabs.is-centered(v-show="selectedOperationIds.length")
    ul.ml-0
      li(:class="{ 'is-active': activeTab === 'stats' }", @click="activeTab = 'stats'")
        a Stats
      li(:class="{ 'is-active': activeTab === 'agents' }", @click="activeTab = 'agents'")
        a Agents
      li(:class="{ 'is-active': activeTab === 'steps' }", @click="activeTab = 'steps'")
        a Steps
      li(:class="{ 'is-active': activeTab === 'tactics' }", @click="activeTab = 'tactics'")
        a Tactics & Techniques
      li(:class="{ 'is-active': activeTab === 'facts' }", @click="activeTab = 'facts'")
        a Fact Graph

  div(v-show="selectedOperationIds.length")
    //- Stats Tab Content
    div(v-show="activeTab === 'stats'")
      table.table.is-striped
        caption Operation Statistics
        thead
          tr
            th Name
            th State
            th Planner
            th Objective
            th Time
        tbody
          template(v-for="stat in stats")
            tr
              td {{ stat.name }}
              td {{ stat.state.toUpperCase() }}
              td {{ stat.planner.name }}
              td {{ stat.objective.name }}
              td {{ stat.start }}

    //- Agents Tab Content
    div(v-show="activeTab === 'agents'")
      table.table.is-striped
        caption Operation Agents
        thead
          tr
            th Paw
            th Host
            th Platform
            th Username
            th Privilege
            th Executable
        tbody
          template(v-for="agent in agents")
            tr
              td {{ agent.paw }}
              td {{ agent.host }}
              td {{ agent.platform }}
              td {{ agent.username }}
              td {{ agent.privilege }}
              td {{ agent.exe_name }}

    //- Steps Tab Content
    div(v-show="activeTab === 'steps'")
      table.table.is-striped
        caption Operation Steps
        thead
          tr
            th Status
            th Time
            th Name
            th Agent
            th Operation
            th Command
        tbody
          template(v-for="step in steps")
            tr
              td {{ getStatusName(step.status) }}
              td {{ step.finish }}
              td {{ step.ability.name }}
              td {{ step.paw }}
              td {{ step.operation_name }}
              td
                button.button.is-small(@click="showCommand(step.id, step.command, step.ability.name)") Show Command

    //- Tactics & Techniques Tab Content
    div(v-show="activeTab === 'tactics'")
      template(v-for="tactic in tacticsAndTechniques")
        .card.mb-4
          header.card-header
            p.card-header-title.is-size-5 {{ tactic.name }}
          .card-content
            .content
              p.has-text-centered
                strong Techniques
              ul
                template(v-for="technique in Object.keys(tactic.techniques)")
                  li {{ `${tactic.techniques[technique]} | ${technique}` }}
              p.has-text-centered
                strong Steps
              template(v-for="step in tactic.steps")
                .block
                  p {{ step.operation }}
                  ul
                    template(v-for="ability in step.abilities")
                      li {{ ability }}

    //- Facts Tab Content
    div(v-show="activeTab === 'facts'")
      #fact-graph
        svg#debrief-fact-svg.debrief-svg
        .d3-tooltip#fact-tooltip(style="opacity: 0")
      article#fact-limit.message.is-info
        #fact-limit-msg.message-body

  //- Graph Settings Modal
  .modal(v-bind:class="{ 'is-active': showGraphSettingsModal }")
    .modal-background(@click="showGraphSettingsModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title Graph Settings
      section.modal-card-body
        p
          strong Display Options
        form
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionLabels", @change="toggleLabels")
                |  Show labels
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionIcons", @change="toggleIcons")
                |  Show icons
        p
          strong Data Options
        form
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionSteps", @change="toggleSteps")
                |  Show operation steps
          .field
            .control
              label.checkbox
                input(type="checkbox", @change="toggleTactics")
                |  Show steps as tactics
      footer.modal-card-foot
        nav.level
          .level-left
          .level-right
            .level-item
              button.button.is-small(@click="showGraphSettingsModal = false") Close

  //- Command Modal
  .modal(v-bind:class="{ 'is-active': showCommandModal }")
    .modal-background(@click="showCommandModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title {{ `Step: ${commandAbilityName}` }}
      section.modal-card-body
        p Command
        pre {{ command }}
        p {{ `Standard Output${commandOutput.stdout ? '' : ': Nothing to show'}` }}
        template(v-if="commandOutput != '' && commandOutput.stdout !== ''")
          pre.has-text-left.white-space-pre-line {{ commandOutput.stdout }}
        p {{ `Standard Error${commandOutput.stderr ? '' : ': Nothing to show'}` }}
        template(v-if="commandOutput != '' && commandOutput.stderr !== ''")
          pre.has-text-left.white-space-pre-line.has-text-danger {{ commandOutput.stderr }}
      footer.modal-card-foot
        nav.level
          .level-left
          .level-right
            .level-item
              button.button.is-small(@click="showCommandModal = false") Close

  //- Report Modal
  .modal(v-bind:class="{ 'is-active': showReportModal }")
    .modal-background(@click="showReportModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title Download Report as PDF
      section.modal-card-body.content.mb-0
        h5 Report Header Logo
        p.help Select a logo to appear in the top right corner of each page.
        form
          label.checkbox
            input(type="checkbox", v-model="useCustomLogo", @change="if (!useCustomLogo) logoFilename = ''")
            | Use custom logo
        .mt-3
        .columns(v-show="useCustomLogo")
          .column.is-6.m-0
            form
              .field
                label.label Select a logo
                .control
                  .select.is-small.is-fullwidth
                    select(v-model="logoFilename")
                      option(default, disabled, value="") Select a logo
                      template(v-for="logo in logos", :key="logo")
                        option(v-bind:value="logo") {{ logo }}
              .field
                .file.is-dark.is-small.is-fullwidth
                  label.file-label
                    input.file-input(type="file", name="userLogo", accept="image/*", v-on:change="uploadLogo($el)", ref="fileInput")
                    span.file-cta
                      span.file-icon
                        i.fas.fa-upload
                      span.file-label Upload new logo…
          .column.is-6.m-0.is-flex.is-align-items-center.is-justify-content-center
            template(v-if="logoFilename")
              img(:alt="'Logo to use for report header'", :src="`/logodebrief/header-logos/${logoFilename}`")
            p(v-else) Select a logo to see preview
        h5 Report Sections
        p.help Sections that are checked will be displayed in the report in order as shown in the list below.
        table
          caption Sections to display in report
          thead
            tr
              th(scope="col")
              th(scope="col")
              th(scope="col")
          tbody
            template(v-for="(section, index) in reportSections", :key="section.key")
              tr
                td.is-flex.is-flex-direction-column.is-align-items-center.is-justify-content-center
                  span.icon.is-small(@click="moveReportSectionOrder(index, index - 1)")
                    i(v-show="index", class="fas fa-sort-up")
                  span.icon.is-small(@click="moveReportSectionOrder(index, index + 1)")
                    i(v-show="index < reportSections.length - 1", class="fas fa-sort-down")
                td
                  .is-flex.is-align-items-center
                    input(type="checkbox", v-bind:checked="activeReportSections.includes(section.key)", v-on:change="toggleReportSection(section.key)")
                td {{ section.name }}

      footer.modal-card-foot
        nav.level
          .level-left
            .level-item
              button.button.is-small(@click="showReportModal = false") Close
          .level-right
            .level-item
              button.button.is-small.is-primary(@click="downloadPDF") Download

  .modal(v-bind:class="{ 'is-active': showCommandModal }")
    .modal-background(@click="showCommandModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title {{ `Step: ${commandAbilityName}` }}
      section.modal-card-body
        p Command
        pre {{ command }}
        p {{ `Standard Output${commandOutput.stdout ? '' : ': Nothing to show'}` }}
        template(v-if="commandOutput && commandOutput.stdout")
          pre.has-text-left.white-space-pre-line {{ commandOutput.stdout }}
        p {{ `Standard Error${commandOutput.stderr ? '' : ': Nothing to show'}` }}
        template(v-if="commandOutput && commandOutput.stderr")
          pre.has-text-left.white-space-pre-line.has-text-danger {{ commandOutput.stderr }}

      footer.modal-card-foot
        nav.level
          .level-left
          .level-right
            .level-item
              button.button.is-small(@click="showCommandModal = false") Close

  .modal(v-bind:class="{ 'is-active': showGraphSettingsModal }")
    .modal-background(@click="showGraphSettingsModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title Graph Settings
      section.modal-card-body
        p
          strong Display Options
        form
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionLabels", v-on:change="toggleLabels")
                | Show labels
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionIcons", v-on:change="toggleIcons")
                | Show icons
        p
          strong Data Options
        form
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionSteps", v-on:change="toggleSteps")
                | Show operation steps
          .field
            .control
              label.checkbox
                input(type="checkbox", v-on:change="toggleTactics")
                | Show steps as tactics

      footer.modal-card-foot
        nav.level
          .level-left
            .level-item
              button.button.is-small(@click="showReportModal = false") Close
          .level-right
            .level-item
              button.button.is-small.is-primary(@click="downloadPDF") Download
</template>