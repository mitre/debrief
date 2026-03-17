<script setup>
import { inject, ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";

const $api = inject("$api");

onMounted(async () => {
  let d3Script = document.createElement("script");
  d3Script.setAttribute(
    "src",
    "/debrief/js/d3.v4.min.js"
  );
  let d4Script = document.createElement("script");
  d4Script.setAttribute(
    "src",
    "/debrief/js/d3-zoom.v1.min.js"
  );
  let graphScript = document.createElement("script");
  graphScript.setAttribute(
    "src",
    "/debrief/js/graph.js"
  );
  document.head.appendChild(d3Script);
  document.head.appendChild(d4Script);
  document.head.appendChild(graphScript);
});
</script>

<style scoped>
caption {
    display: none;
}

svg {
    width: 100%;
    height: 100%;
}

#debrief-graph {
    position: relative;
    background-color: black;
    width: 100% !important;
    height: 400px;
    border-radius: 4px;
}

#fact-graph {
    position: relative;
    margin: auto;
    background-color: black;
    border-radius: 4px;
    width: 100%;
    max-width: 100%;
    height: 600px;
}

#fact-limit {
    width: 100%;
    margin: auto;
}

#select-operation {
    max-width: 100%;
    margin: 0 auto;
}

#tactic-section {
    width: 100%;
    max-width: 100%;
    margin: auto;
}

div.d3-tooltip {
    position: absolute;
    text-align: left;
    width: auto;
    height: auto;
    padding: 5px;
    font: 12px sans-serif;
    background: #750b20;
    border: 0px;
    border-radius: 4px;
    pointer-events: none;
}

.graph-controls {
    position: absolute;
}

#tactic-section > .card {
    background-color: #121212;
}

/* ==================== TOPOLOGY REPLAY ==================== */

.topo-wrapper {
    width: 100%;
}

.topo-controls {
    padding: 8px 0 2px;
}

.topo-split {
    display: flex;
    gap: 0;
    min-height: 450px;
}

.topo-canvas {
    flex: 1;
    background: #121212;
    border-radius: 6px;
    overflow: auto;
    min-height: 400px;
    border: 1px solid #2a2a3e;
}

.topo-svg {
    width: 100%;
    height: 100%;
    min-height: 400px;
}

/* Zone bands */
.topo-zone {
    stroke: #333;
    stroke-width: 1;
}

.topo-zone-label {
    fill: #666;
    font-size: 11px;
    font-family: monospace;
}

/* Edges */
.topo-edge {
    stroke: #444;
    stroke-width: 1.5;
    stroke-dasharray: 6 4;
    transition: stroke 0.3s;
}

.topo-edge.is-active {
    stroke: #cc3311;
    stroke-width: 2.5;
    stroke-dasharray: none;
    filter: drop-shadow(0 0 4px rgba(204, 51, 17, 0.5));
}

.topo-edge.is-lateral {
    stroke-dasharray: 8 4;
}

/* Host nodes */
.topo-host {
    cursor: pointer;
    transition: opacity 0.3s;
}

.topo-host.is-discovered {
    opacity: 0.3;
}

.topo-host.is-discovered:hover {
    opacity: 0.6;
}

.topo-host-bg {
    fill: #1a1a2e;
    stroke: #555;
    stroke-width: 1.5;
    transition: all 0.3s;
}

.topo-host.is-compromised .topo-host-bg {
    fill: #1e1e32;
    stroke: #888;
}

.topo-host.is-active .topo-host-bg {
    stroke: #cc3311;
    stroke-width: 2.5;
}

.topo-host.is-visited .topo-host-bg {
    stroke: #750b20;
    stroke-width: 2;
}

.topo-host.is-discovered .topo-host-bg {
    stroke-dasharray: 4 3;
    stroke: #555;
}

.topo-glow {
    fill: none;
    stroke: #cc3311;
    stroke-width: 2;
    opacity: 0.5;
    animation: topoGlow 1.2s ease-in-out infinite alternate;
}

@keyframes topoGlow {
    from { opacity: 0.3; r: 26; }
    to { opacity: 0.7; r: 30; }
}

.topo-host-icon {
    pointer-events: none;
}

.topo-host.is-discovered .topo-host-icon {
    opacity: 0.4;
}

.topo-host-label {
    fill: #aaa;
    font-size: 9px;
    pointer-events: none;
}

.topo-badge circle {
    transition: fill 0.2s;
}

.topo-tooltip rect {
    pointer-events: none;
}

.topo-tooltip text {
    pointer-events: none;
}

/* Slide-out detail panel */
.topo-detail {
    width: 320px;
    flex-shrink: 0;
    background: #1a1a2e;
    border-left: 1px solid #333;
    border-radius: 0 6px 6px 0;
    padding: 12px;
    overflow-y: auto;
    max-height: 500px;
}

.topo-detail-header {
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid #333;
}

.topo-detail-section {
    margin-top: 10px;
}

.topo-step {
    padding: 4px 8px;
    margin-bottom: 2px;
    border-radius: 4px;
    background: #121212;
    cursor: pointer;
    transition: background 0.15s;
}

.topo-step:hover {
    background: #1e1e32;
}

.topo-step-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

.topo-step-dot.is-success { background: #44AA99; }
.topo-step-dot.is-danger { background: #CC3311; }
.topo-step-dot.is-info { background: cornflowerblue; }
.topo-step-dot.is-dark { background: #333; }
.topo-step-dot.is-warning { background: #FFB000; }

.topo-step-detail {
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px solid #222;
}

.topo-intel {
    padding: 2px 0;
}

.replay-pre {
    background: #0d0d1a;
    color: #ccc;
    font-size: 0.7rem;
    padding: 6px 10px;
    border-radius: 4px;
    max-height: 150px;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-all;
}
</style>

<script>
import { toast } from "bulma-toast";
import { b64DecodeUnicode } from "@/utils/utils";
export default {
  inject: ["$api"],
  data() {
    return {
        operations: [],
        selectedOperationId: '',
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
        reportSections: [],
        activeReportSections: [],
        useCustomLogo: false,
        logoFilename: '',
        logos: [],

        selectedGraphType: 'attackpath',
        nodesOrderedByTime: {},
        showGraphLegend: true,
        isGraphPlaying: false,
        graphInterval: null,

        // Replay tab
        replayCursor: -1,
        replayPlaying: false,
        replaySpeed: 1000,
        replayInterval: null,
        replayExpandedIdx: -1,
        replayHoverIdx: -1,

        // Topology
        topoData: null,
        topoSelectedHost: null,
        topoHoverHost: null,
        topoActiveHost: null,
        topoVisitedHosts: new Set(),
        topoExpandedStep: null,
        topoActiveEdge: -1,
    };
  },
  created() {
    this.initPage();
  },
  methods: {
    initPage() {
            this.$api.get('/plugin/debrief/sections').then((data) => {
                this.reportSections = data.data.report_sections;
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error getting report sections",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
            this.$api.get('/api/v2/operations').then((operations) => {
                this.operations = operations.data;
                this.initReportSections();
                return this.$api.get('/plugin/debrief/logos');
            }).then(async (data) => {
                this.logos = data.data.logos;
                if (typeof moveLegend !== 'undefined') {
                  window.addEventListener('resize', moveLegend);
                }

                // While the debrief tab is open, keep checking for new/killed agents
                setInterval(async () => {
                  this.refreshOperations();
                }, "3000");
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error getting operations",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

        refreshOperations() {
          this.$api.get('/api/v2/operations').then((operations) => {
                this.operations = operations.data;
            }).catch((error) => {
                console.error(error);
          toast({
            message:
            "Error refreshing operations",
            type: "is-danger",
            dismissible: true,
            pauseOnHover: true,
            duration: 2000,
            position: "bottom-right",
          });
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
            if (!this.selectedOperationId.length) return;
            this.$api.post('/plugin/debrief/report', { operations: [this.selectedOperationId] }).then((data) => {
                data = data.data;
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

                updateReportGraph([this.selectedOperationId]);
            }).catch((error) => {
                toast({
                  message:
                  "Error loading operation",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
                console.error(error);
            })
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
                if (data.data) {
                    try {
                        this.command = data.data.link.command;
                        this.commandOutput = JSON.parse(b64DecodeUnicode(data.data.output));
                    } catch (error) { // occurs when data is not JSON
                        this.commandOutput = '';
                        console.error(error);
                        toast({
                          message:
                          "Error getting command and/or command results.",
                          type: "is-danger",
                          dismissible: true,
                          pauseOnHover: true,
                          duration: 2000,
                          position: "bottom-right",
                        });
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
            if (el.target.files.length === 0) return;

            let formData = new FormData()
            formData.append('header-logo', el.target.files[0])
            this.$api.post('/plugin/debrief/logo', formData, false).then((data) => {
                data = data.data;
                this.logos.push(data.filename);
                this.logoFilename = data.filename;
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error uploading file",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

        downloadPDF() {
            let requestBody = {
                'operations': [this.selectedOperationId],
                'graphs': this.getGraphData(),
                'report-sections': this.activeReportSections,
                'header-logo': this.logoFilename
            };
            this.$api.post('/plugin/debrief/pdf', requestBody, true).then((data) => {
                data = data.data;
                let dataStr = URL.createObjectURL(new Blob([data["pdf_bytes"]], { type: "application/pdf" }));
                let downloadAnchorNode = document.createElement("a");
                downloadAnchorNode.setAttribute("href", dataStr);
                downloadAnchorNode.setAttribute("download", data.filename);
                document.body.appendChild(downloadAnchorNode);
                downloadAnchorNode.click();
                downloadAnchorNode.remove();
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error downloading PDF report",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

        downloadJSON() {
          this.$api.post('/plugin/debrief/json', { 'operations': [this.selectedOperationId] }).then((data) => {
                data = data.data;
                this.downloadJson(data.filename, data);
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error downloading JSON report",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

         downloadJson(filename, data) {
            let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
            let downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", filename + ".json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        },

        getGraphData() {
            let encodedGraphs = {}

            document.querySelectorAll('.debrief-svg').forEach((svg) => {
                let newSvg = svg.cloneNode(true);
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
            let id = `debrief-${this.selectedGraphType}-svg`;

            if (this.isGraphPlaying) {
                if (!this.nodesOrderedByTime[id].find(node => node.style.display == "none")) {
                    this.visualizeBeginning();
                }

                while (this.isGraphPlaying) {
                    await this.sleep(1000);
                    if (this.isGraphPlaying) {
                        this.visualizeStepForward();
                    }
                }
            }
        },

       sleep(ms) {
          return new Promise((resolve) => setTimeout(resolve, ms));
      },
        visualizeBeginning() {
            let id = `debrief-${this.selectedGraphType}-svg`;
            document.querySelectorAll(`#${id} .node:not(.c2)`).forEach((node) => node.style.display = 'none');
            document.querySelectorAll(`#${id} polyline`).forEach((node) => node.style.display = 'none');
        },

        visualizeEnd() {
            let id = `debrief-${this.selectedGraphType}-svg`;
            document.querySelectorAll(`#${id} .node`).forEach((node) => node.style.display = 'block');
            document.querySelectorAll(`#${id} polyline`).forEach((node) => node.style.display = 'block');
        },

        visualizeStepForward() {
            this.getNodesOrderedByTime();
            let id = `debrief-${this.selectedGraphType}-svg`;

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
            let id = `debrief-${this.selectedGraphType}-svg`;

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
        useCustomLogoChange () {
            if (!this.useCustomLogo) this.logoFilename = '';
        },

        // ==================== REPLAY METHODS ====================

        initReplay() {
            this.replayPause();
            this.replayCursor = this.replaySteps.length ? this.replaySteps.length - 1 : -1;
            this.replayExpandedIdx = -1;
            this.topoSelectedHost = null;
            this.topoVisitedHosts = new Set();
            this.topoActiveHost = null;
            this.topoActiveEdge = -1;
            // Fetch topology data
            if (this.selectedOperationId.length) {
                this.$api.get(`/plugin/debrief/topology?operations=${this.selectedOperationId}`).then((data) => {
                    this.topoData = data.data;
                }).catch((err) => {
                    console.error('Topology fetch failed:', err);
                    this.topoData = null;
                });
            }
        },

        replayPlay() {
            if (!this.replaySteps.length) return;
            this.replayPlaying = true;
            if (this.replayCursor >= this.replaySteps.length - 1) {
                this.replayCursor = -1;
                this.topoVisitedHosts = new Set();
                this.topoActiveHost = null;
            }
            this.replayInterval = setInterval(() => {
                if (this.replayCursor < this.replaySteps.length - 1) {
                    this.replayCursor++;
                    this.replayUpdateTopo();
                } else {
                    this.replayPause();
                }
            }, this.replaySpeed);
        },

        replayPause() {
            this.replayPlaying = false;
            if (this.replayInterval) {
                clearInterval(this.replayInterval);
                this.replayInterval = null;
            }
        },

        replayStepForward() {
            if (this.replayCursor < this.replaySteps.length - 1) {
                this.replayCursor++;
                this.replayScrollToActive();
            }
        },

        replayStepBack() {
            if (this.replayCursor > 0) {
                this.replayCursor--;
                this.replayScrollToActive();
            }
        },

        replayJumpToStart() {
            this.replayPause();
            this.replayCursor = 0;
        },

        replayJumpToEnd() {
            this.replayPause();
            this.replayCursor = this.replaySteps.length - 1;
        },

        replayScrollToActive() {
            this.$nextTick(() => {
                const feed = this.$refs.replayFeed;
                if (!feed) return;
                const cards = feed.querySelectorAll('.replay-card');
                const active = cards[this.replayCursor];
                if (active) {
                    active.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        },

        replayMarkerPct(idx) {
            if (this.replaySteps.length <= 1) return 50;
            return (idx / (this.replaySteps.length - 1)) * 100;
        },

        replayMarkerClass(idx) {
            return {
                'is-active': idx === this.replayCursor,
                'is-past': idx < this.replayCursor,
                'is-future': idx > this.replayCursor,
            };
        },

        replayDotClass(status) {
            return {
                'is-success': status === 0,
                'is-danger': status === 1,
                'is-info': status === 124,
                'is-dark': status === -2,
                'is-warning': status === -3,
                'is-light': status === -4,
            };
        },

        replayStatusTagClass(status) {
            if (status === 0) return 'is-success';
            if (status === 1) return 'is-danger';
            if (status === 124) return 'is-info';
            if (status === -2) return 'is-dark';
            if (status === -3) return 'is-warning';
            if (status === -4) return 'is-light';
            if (status === -5) return 'is-link';
            return 'is-dark';
        },

        replayPlatformIcon(step) {
            // Find the agent's platform from loaded agents
            const agent = this.agents.find(a => a.paw === step.paw);
            if (agent) {
                if (agent.platform === 'windows') return 'fab fa-windows';
                if (agent.platform === 'linux') return 'fab fa-linux';
                if (agent.platform === 'darwin') return 'fab fa-apple';
            }
            return 'fas fa-desktop';
        },

        replayDecodeCommand(step) {
            try {
                return atob(step.command);
            } catch {
                return step.command || 'N/A';
            }
        },

        // ==================== TOPOLOGY METHODS ====================

        replayUpdateTopo() {
            if (!this.topoData || this.replayCursor < 0) return;
            const step = this.replaySteps[this.replayCursor];
            if (!step) return;
            const paw = step.paw;
            this.topoActiveHost = paw;
            this.topoVisitedHosts.add(paw);
            // Find edge that leads to this host's agent
            const edgeIdx = (this.topoData.edges || []).findIndex(e => e.target === paw);
            this.topoActiveEdge = edgeIdx >= 0 ? edgeIdx : -1;
        },

        topoSelectHost(host) {
            this.topoSelectedHost = host.compromised ? this.topoData.hosts[host.id] : host;
        },

        topoEdgeActive(edgeIdx) {
            return this.topoActiveEdge === edgeIdx;
        },

        topoPlatformSvg(platform) {
            const map = {
                linux: '/debrief/img/linux.svg',
                windows: '/debrief/img/windows.svg',
                darwin: '/debrief/img/darwin.svg',
                server: '/debrief/img/cloud.svg',
            };
            return map[platform] || '/debrief/img/unknown.svg';
        },

        topoZoneColor(index) {
            const colors = [
                'rgba(117, 11, 32, 0.10)',
                'rgba(30, 30, 100, 0.12)',
                'rgba(30, 100, 30, 0.10)',
                'rgba(100, 80, 20, 0.10)',
                'rgba(60, 60, 60, 0.12)',
            ];
            return colors[index % colors.length];
        },
  },
  computed: {
        topoSubnets() {
            if (!this.topoData) return [];
            const subnets = this.topoData.subnets || [];
            const padding = 30;
            const bandH = 80;
            const hostSpacing = 100;
            const c2Height = 70; // space reserved for C2 node above bands
            return subnets.map((s, si) => {
                const hostCount = Math.max(s.hosts.length, 1);
                const w = Math.max(hostCount * hostSpacing + 80, 250);
                return {
                    cidr: s.cidr,
                    x: padding,
                    y: c2Height + padding + si * (bandH + 16),
                    w: w,
                    h: bandH,
                    hosts: s.hosts,
                };
            });
        },

        topoHosts() {
            if (!this.topoData) return [];
            const hosts = this.topoData.hosts || {};
            const result = [];
            const hostSpacing = 100;
            // Position hosts centered within their subnet bands
            const hostPositions = {};
            this.topoSubnets.forEach((subnet) => {
                const totalW = subnet.hosts.length * hostSpacing;
                const startX = subnet.x + (subnet.w - totalW) / 2 + hostSpacing / 2;
                subnet.hosts.forEach((hid, hi) => {
                    hostPositions[hid] = {
                        x: startX + hi * hostSpacing,
                        y: subnet.y + subnet.h / 2,
                    };
                });
            });
            // C2 node centered above all bands
            const svgW = this.topoSvgWidth;
            hostPositions['c2'] = { x: svgW / 2, y: 35 };

            Object.entries(hosts).forEach(([id, host]) => {
                const pos = hostPositions[id] || { x: svgW / 2, y: 35 };
                result.push({ ...host, x: pos.x, y: pos.y });
            });
            return result;
        },

        topoEdges() {
            if (!this.topoData) return [];
            const edges = this.topoData.edges || [];
            const hostMap = {};
            this.topoHosts.forEach(h => { hostMap[h.id] = h; });
            return edges.map(e => {
                const src = hostMap[e.source];
                const tgt = hostMap[e.target];
                if (!src || !tgt) return { ...e, path: '' };
                // Gentle curve — control point offset perpendicular to the line
                const mx = (src.x + tgt.x) / 2;
                const my = (src.y + tgt.y) / 2;
                const dx = tgt.x - src.x;
                const curveOffset = Math.min(Math.abs(dx) * 0.2, 30);
                const path = `M ${src.x} ${src.y} Q ${mx + curveOffset} ${my} ${tgt.x} ${tgt.y}`;
                return { ...e, path };
            });
        },

        topoViewBox() {
            const w = this.topoSvgWidth;
            const subnets = this.topoSubnets;
            const lastSubnet = subnets[subnets.length - 1];
            const h = lastSubnet ? lastSubnet.y + lastSubnet.h + 30 : 200;
            return `0 0 ${w} ${Math.max(h, 180)}`;
        },

        topoSvgWidth() {
            if (!this.topoData) return 600;
            const subnets = this.topoSubnets;
            const maxW = subnets.reduce((max, s) => Math.max(max, s.x + s.w + 30), 0);
            return Math.max(maxW, 400);
        },

        topoHostSteps() {
            if (!this.topoSelectedHost || !this.topoData) return [];
            const paw = this.topoSelectedHost.agent_paw || this.topoSelectedHost.id;
            return (this.topoData.steps_by_host || {})[paw] || [];
        },

        replaySteps() {
            if (!this.steps || !this.steps.length) return [];
            return [...this.steps].sort((a, b) => {
                const ta = a.finish || a.decide || '';
                const tb = b.finish || b.decide || '';
                return ta.localeCompare(tb);
            });
        },

        replayProgressPct() {
            if (this.replaySteps.length <= 1) return this.replayCursor >= 0 ? 100 : 0;
            if (this.replayCursor < 0) return 0;
            return (this.replayCursor / (this.replaySteps.length - 1)) * 100;
        },
  },
};
</script>

<template lang="pug">
div
  h2 Debrief
  p
    strong Campaign Analytics.
    |  Debrief gathers overall campaign information and analytics for operations.
    |  It provides a centralized view of operation metadata, graphical displays of
    |  the operation, the techniques and tactics used, and the facts discovered by the operation.

hr

div
  .buttons
    button.button.is-primary.is-small(:disabled="!selectedOperationId.length", @click="showGraphSettingsModal = true")
      span.icon.is-small
        font-awesome-icon(icon="fas fa-cog")
      span Graph Settings
    button.button.is-primary.is-small(:disabled="!selectedOperationId.length", @click="showReportModal = true")
      span.icon.is-small
        font-awesome-icon(icon="fas fa-download")
      span Download PDF Report
    button.button.is-primary.is-small(:disabled="!selectedOperationId.length", @click="downloadJSON")
      span.icon.is-small
        font-awesome-icon(icon="fas fa-download")
      span Download Operation JSON

  .columns.mb-4.is-variable.is-1
    .column.is-2
      form
        .field
          .control.mr-2
            .select.is-fullwidth
              select.has-text-centered(v-model="selectedOperationId", @change="loadOperation")
                option(disabled selected value="") Select an operation
                template(v-for="operation in operations", :key="operation.id")
                  option(:value="operation.id") {{ operation.name }}
    .column.is-10.is-flex.is-justify-content-center.m-0
      #images(style="display: none")
      #copy
      #debrief-graph.svg-container(v-show="1")
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
            span.icon.is-small
              font-awesome-icon(icon="fas fa-fast-backward")
          button.button.is-small(@click="visualizeStepBack")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-backward")
          button.button.is-small(v-show="isGraphPlaying", @click="visualizePlayPause")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-pause")
          button.button.is-small(v-show="!isGraphPlaying", @click="visualizePlayPause")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-play")
          button.button.is-small(@click="visualizeStepForward")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-forward")
          button.button.is-small(@click="visualizeEnd")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-fast-forward")

  .tabs.is-centered(v-show="selectedOperationId.length")
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
      li(:class="{ 'is-active': activeTab === 'replay' }", @click="activeTab = 'replay'; initReplay()")
        a
          span.icon.is-small
            font-awesome-icon(icon="fas fa-play-circle")
          span Replay

  div(v-show="selectedOperationId.length")
    div(v-show="activeTab === 'stats'")
      table.table.is-striped.is-fullwidth
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

    div(v-show="activeTab === 'agents'")
      table.table.is-striped.is-fullwidth
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

    div(v-show="activeTab === 'steps'")
      table.table.is-striped.is-fullwidth
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

    div(v-show="activeTab === 'facts'")
      #fact-graph
        svg#debrief-fact-svg.debrief-svg
        .d3-tooltip#fact-tooltip(style="opacity: 0")
      article#fact-limit.message.is-info
        #fact-limit-msg.message-body

    //- ==================== REPLAY TAB ====================
    div(v-show="activeTab === 'replay'")
      .topo-wrapper

        //- PLAYBACK CONTROLS
        .topo-controls
          .buttons.has-addons.is-centered.mb-0
            button.button.is-small.is-dark(@click="replayJumpToStart", :disabled="!replaySteps.length")
              span.icon
                font-awesome-icon(icon="fas fa-fast-backward")
            button.button.is-small.is-dark(@click="replayStepBack", :disabled="!replaySteps.length")
              span.icon
                font-awesome-icon(icon="fas fa-backward")
            button.button.is-small.is-dark(v-if="!replayPlaying", @click="replayPlay", :disabled="!replaySteps.length")
              span.icon
                font-awesome-icon(icon="fas fa-play")
            button.button.is-small.is-dark(v-else, @click="replayPause")
              span.icon
                font-awesome-icon(icon="fas fa-pause")
            button.button.is-small.is-dark(@click="replayStepForward", :disabled="!replaySteps.length")
              span.icon
                font-awesome-icon(icon="fas fa-forward")
            button.button.is-small.is-dark(@click="replayJumpToEnd", :disabled="!replaySteps.length")
              span.icon
                font-awesome-icon(icon="fas fa-fast-forward")
          .is-flex.is-justify-content-center.is-align-items-center.mt-1.mb-2
            span.is-size-7.has-text-grey.mr-3 Speed:
            .buttons.has-addons.mb-0
              button.button.is-tiny(:class="replaySpeed === 500 ? 'is-primary' : 'is-dark'", @click="replaySpeed = 500", style="font-size:0.65rem;padding:2px 8px;height:22px") 2x
              button.button.is-tiny(:class="replaySpeed === 1000 ? 'is-primary' : 'is-dark'", @click="replaySpeed = 1000", style="font-size:0.65rem;padding:2px 8px;height:22px") 1x
              button.button.is-tiny(:class="replaySpeed === 2000 ? 'is-primary' : 'is-dark'", @click="replaySpeed = 2000", style="font-size:0.65rem;padding:2px 8px;height:22px") 0.5x
            span.is-size-7.has-text-grey.ml-3 Step {{ replayCursor + 1 }} / {{ replaySteps.length }}

        //- TOPOLOGY CANVAS + DETAIL PANEL
        .topo-split
          //- SVG CANVAS
          .topo-canvas(ref="topoCanvas")
            svg.topo-svg(
              v-if="topoData",
              :viewBox="topoViewBox",
              preserveAspectRatio="xMidYMid meet",
              xmlns="http://www.w3.org/2000/svg"
            )
              //- Subnet zone bands
              g.topo-subnets
                template(v-for="(subnet, si) in topoSubnets", :key="si")
                  rect.topo-zone(
                    :x="subnet.x", :y="subnet.y",
                    :width="subnet.w", :height="subnet.h",
                    :fill="topoZoneColor(si)", rx="8"
                  )
                  text.topo-zone-label(:x="subnet.x + 12", :y="subnet.y + 18") {{ subnet.cidr }}

              //- Connection edges (curved dotted)
              g.topo-edges
                template(v-for="(edge, ei) in topoEdges", :key="ei")
                  path.topo-edge(
                    :d="edge.path",
                    :class="{ 'is-active': topoEdgeActive(ei), 'is-lateral': edge.type === 'lateral_movement' }",
                    fill="none"
                  )
                  //- Animated pulse circle
                  circle.topo-pulse(
                    v-if="topoEdgeActive(ei)",
                    r="4", fill="#cc3311"
                  )
                    animateMotion(dur="0.8s", repeatCount="1", :path="edge.path")

              //- Host icons
              g.topo-hosts
                template(v-for="host in topoHosts", :key="host.id")
                  g.topo-host(
                    :transform="`translate(${host.x}, ${host.y})`",
                    :class="{ 'is-compromised': host.compromised, 'is-discovered': !host.compromised, 'is-active': topoActiveHost === host.id, 'is-visited': topoVisitedHosts.has(host.id) }",
                    @click="topoSelectHost(host)",
                    @mouseenter="topoHoverHost = host.id",
                    @mouseleave="topoHoverHost = null"
                  )
                    //- Glow ring for active host
                    circle.topo-glow(r="28", v-if="topoActiveHost === host.id")
                    //- Host circle background
                    circle.topo-host-bg(r="20")
                    //- Platform icon (SVG image from debrief static assets)
                    image.topo-host-icon(
                      :href="topoPlatformSvg(host.platform)",
                      x="-12", y="-12", width="24", height="24"
                    )
                    //- Hostname label
                    text.topo-host-label(y="32", text-anchor="middle") {{ host.hostname }}
                    //- Step count badge
                    g.topo-badge(v-if="host.compromised && host.step_count > 0")
                      circle(cx="16", cy="-16", r="8", fill="#750b20")
                      text(x="16", y="-16", text-anchor="middle", dominant-baseline="central", fill="white", font-size="9") {{ host.step_count }}
                    //- Hover tooltip
                    g.topo-tooltip(v-if="topoHoverHost === host.id")
                      rect(x="-80", y="-60", width="160", height="40", rx="4", fill="#1a1a2e", stroke="#555")
                      text(x="0", y="-46", text-anchor="middle", fill="#aaa", font-size="10") {{ host.ips.join(', ') || 'No IP' }}
                      text(x="0", y="-32", text-anchor="middle", fill="#ccc", font-size="10") {{ host.platform }} | {{ host.compromised ? host.privilege || 'agent' : 'discovered' }}

            //- Empty state
            .has-text-centered.py-6(v-if="!topoData")
              p.has-text-grey Select an operation to see the topology

          //- SLIDE-OUT DETAIL PANEL
          .topo-detail(v-if="topoSelectedHost")
            .topo-detail-header
              .is-flex.is-align-items-center.is-justify-content-space-between
                strong {{ topoSelectedHost.hostname }}
                button.delete.is-small(@click="topoSelectedHost = null")
              p.is-size-7.has-text-grey {{ topoSelectedHost.ips.join(', ') }}
              .tags.mt-1
                span.tag.is-small(:class="topoSelectedHost.compromised ? 'is-danger' : 'is-dark'") {{ topoSelectedHost.compromised ? 'Compromised' : 'Discovered' }}
                span.tag.is-small(v-if="topoSelectedHost.platform !== 'unknown'") {{ topoSelectedHost.platform }}
                span.tag.is-small(v-if="topoSelectedHost.privilege") {{ topoSelectedHost.privilege }}

            //- Steps on this host
            .topo-detail-section(v-if="topoSelectedHost.compromised && topoHostSteps.length")
              p.is-size-7.has-text-weight-bold.mb-1 Steps ({{ topoHostSteps.length }})
              .topo-step(v-for="step in topoHostSteps", :key="step.id", @click="topoExpandedStep = (topoExpandedStep === step.id ? null : step.id)")
                .is-flex.is-align-items-center
                  span.topo-step-dot(:class="replayStatusTagClass(step.status)")
                  span.is-size-7.ml-2 {{ step.ability_name }}
                  span.has-text-grey.ml-auto(style="font-size:0.6rem") {{ step.tactic }}
                .topo-step-detail(v-if="topoExpandedStep === step.id")
                  p.is-size-7.has-text-grey {{ step.technique_id }} {{ step.technique_name }}
                  pre.replay-pre(v-if="step.command") {{ replayDecodeCommand({ command: step.command }) }}

            //- Intel for discovered hosts
            .topo-detail-section(v-if="!topoSelectedHost.compromised && topoSelectedHost.intel && topoSelectedHost.intel.length")
              p.is-size-7.has-text-weight-bold.mb-1 Gathered Intel
              .topo-intel(v-for="item in topoSelectedHost.intel", :key="item.trait + item.value")
                span.is-size-7.has-text-grey {{ item.trait }}:
                span.is-size-7.ml-1 {{ item.value }}

            .topo-detail-section(v-if="!topoSelectedHost.compromised && (!topoSelectedHost.intel || !topoSelectedHost.intel.length)")
              p.is-size-7.has-text-grey No intel gathered

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
            input(type="checkbox", v-model="useCustomLogo", @change="useCustomLogoChange")
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
                    input.file-input(type="file", name="userLogo", accept="image/*", v-on:change="uploadLogo", ref="fileInput")
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
</template>

