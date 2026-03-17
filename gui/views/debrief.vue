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
    background: #4c0089;
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

.topo-main-canvas {
    width: 100%;
}

.topo-canvas {
    background: #121212;
    border-radius: 6px;
    overflow: auto;
    min-height: 250px;
    border: 1px solid #2a2a3e;
    position: relative;
    flex: 1;
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
    fill: #555;
    font-size: 9px;
    font-family: monospace;
}

/* Edges */
.topo-edge {
    stroke: #444;
    stroke-width: 1.5;
    stroke-dasharray: 6 4;
    transition: stroke 0.3s;
}

.topo-edge.is-newest {
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
    from { opacity: 0.3; r: 22; }
    to { opacity: 0.7; r: 26; }
}

.topo-beacon-trail {
    pointer-events: none;
}

/* Legend as HTML outside SVG */
.topo-legend-box {
    display: flex;
    gap: 16px;
    padding: 6px 12px;
    background: #1a1a2e;
    border: 1px solid #333;
    border-radius: 4px;
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 10;
}

.topo-legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    color: #888;
}

.topo-legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
}

.topo-legend-filled {
    border: none !important;
}

.topo-beacon {
    filter: drop-shadow(0 0 4px rgba(68, 170, 153, 0.8));
}

.topo-beacon-dot {
    filter: drop-shadow(0 0 6px rgba(68, 170, 153, 0.9));
    pointer-events: none;
}

/* Legend row above canvas */
.topo-legend-row {
    display: flex;
    justify-content: flex-end;
    gap: 16px;
    padding: 6px 12px;
    margin-bottom: 4px;
}

.topo-legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: #aaa;
}

.topo-legend-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    display: inline-block;
}

.topo-legend-filled {
    border: none !important;
}

.topo-pivot-ring {
    pointer-events: none;
}

.topo-pivot-label {
    pointer-events: none;
}

.topo-host-icon {
    pointer-events: none;
    filter: invert(1) brightness(2);  /* make black SVGs white */
}

.topo-host.is-discovered .topo-host-icon {
    opacity: 0.4;
    filter: invert(1) brightness(1.5);
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

/* ==================== REDESIGNED TABS & TABLES ==================== */

.debrief-tabs ul {
    border-bottom-color: #333;
}

.debrief-tabs li a {
    color: #888;
    border-bottom-color: transparent;
    transition: color 0.2s;
}

.debrief-tabs li a:hover {
    color: #ccc;
    border-bottom-color: #555;
}

.debrief-tabs li.is-active a {
    color: #fff;
    border-bottom-color: #8b00ff;
}

.debrief-tab-content {
    padding: 12px 0;
}

/* Custom dark table */
.debrief-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.85rem;
    border-radius: 6px;
    overflow: hidden;
}

.debrief-table thead th {
    background: #4c0089;
    color: #fff;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 12px;
    border: none;
}

.debrief-table tbody tr {
    background: #1a1a2e;
    transition: background 0.15s;
}

.debrief-table tbody tr:nth-child(even) {
    background: #16162a;
}

.debrief-table tbody tr:hover {
    background: #252540;
}

.debrief-table td {
    padding: 6px 12px;
    border: none;
    border-bottom: 1px solid #222;
    color: #ccc;
    vertical-align: middle;
}

/* TTP Cards Grid */
.debrief-ttp-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
}

.debrief-ttp-card {
    background: #1a1a2e;
    border-radius: 6px;
    border: 1px solid #2a2a3e;
    overflow: hidden;
}

.debrief-ttp-header {
    background: #4c0089;
    color: #fff;
    padding: 8px 12px;
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: capitalize;
}

.debrief-ttp-body {
    padding: 10px 12px;
}

.debrief-ttp-section {
    margin-bottom: 8px;
}

.debrief-ttp-section:last-child {
    margin-bottom: 0;
}

.debrief-ttp-label {
    font-size: 0.7rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.debrief-ttp-item {
    font-size: 0.8rem;
    padding: 2px 0;
    color: #ccc;
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
        replaySpeed: 2000,
        replayInterval: null,
        replayExpandedIdx: -1,
        replayHoverIdx: -1,

        // Topology
        topoData: null,
        topoSelectedHost: null,
        topoHoverHost: null,
        topoActiveHost: null,
        topoVisitedHosts: new Set(),
        topoRevealedHosts: new Set(),
        topoNewestEdge: -1,
        topoBeaconEdge: -1,
        topoBeaconEdges: new Set(),
        topoBeaconDotT: {},  // edgeIdx -> t value (0=source, 1=target)
        topoExpandedStep: null,
        topoStepCounts: {},
        topoShowAll: false,    // true = static full view, false = progressive replay
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

                // Refresh operations periodically, with backoff on failure
                if (!this._refreshTimer) {
                  this._refreshFailCount = 0;
                  this._refreshTimer = setInterval(() => {
                    this.refreshOperations();
                  }, 5000);
                }
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
                this._refreshFailCount = 0;
            }).catch(() => {
                this._refreshFailCount = (this._refreshFailCount || 0) + 1;
                if (this._refreshFailCount > 3 && this._refreshTimer) {
                    clearInterval(this._refreshTimer);
                    this._refreshTimer = null;
                }
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

                // Load topology data — start with only C2 visible
                this.topoSelectedHost = null;
                this.topoRevealedHosts = new Set(['c2']);
                this.topoVisitedHosts = new Set();
                this.topoActiveHost = null;
                this.topoNewestEdge = -1;
                this.topoBeaconEdge = -1;
                this.topoStepCounts = {};
                this.topoShowAll = false;
                this.replayCursor = -1;
                this.$api.get(`/plugin/debrief/topology?operations=${this.selectedOperationId}`).then((topo) => {
                    this.topoData = topo.data;
                    // Only C2 visible — press play to start revealing
                }).catch((err) => console.error('Topology load failed:', err));

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
            this.replayCursor = -1;
            this.replayExpandedIdx = -1;
            this.topoSelectedHost = null;
            this.topoActiveHost = null;
            this.topoNewestEdge = -1;
            this.topoBeaconEdge = -1;
            this.topoStepCounts = {};
            this.topoShowAll = false;
            // Reset to C2 only — progressive reveal starts from here
            this.topoRevealedHosts = new Set(['c2']);
            this.topoVisitedHosts = new Set();
        },

        async replayPlay() {
            if (!this.replaySteps.length) return;
            if (this.replayCursor >= this.replaySteps.length - 1) {
                // Restart from beginning
                this.replayCursor = -1;
                this.topoRevealedHosts = new Set(['c2']);
                this.topoVisitedHosts = new Set();
                this.topoActiveHost = null;
                this.topoNewestEdge = -1;
                this.topoBeaconEdge = -1;
                this.topoStepCounts = {};
            }
            this.replayPlaying = true;
            while (this.replayPlaying && this.replayCursor < this.replaySteps.length - 1) {
                this.replayCursor++;
                const prevRevealed = new Set(this.topoRevealedHosts);
                this.replayUpdateTopo();
                // Check if a new host was just revealed
                const seq = this.topoData.replay_sequence || [];
                const item = seq[this.replayCursor];
                const paw = item ? item.paw : null;
                const isNewHost = paw && !prevRevealed.has(paw);
                if (isNewHost && this.replayPlaying) {
                    // Wait a moment to show the host, then beacon back to C2
                    await this.sleep(400);
                    if (this.replayPlaying) {
                        await this.replayBeaconToC2(paw);
                    }
                }
                // Wait between steps
                if (this.replayPlaying) {
                    await this.sleep(this.replaySpeed);
                }
            }
            this.replayPlaying = false;
        },

        replayPause() {
            this.replayPlaying = false;
        },

        replayStepForward() {
            if (this.replayCursor < this.replaySteps.length - 1) {
                this.replayCursor++;
                this.replayUpdateTopo();
            }
        },

        replayStepBack() {
            // Can't easily undo progressive reveal, just go back one cursor
            if (this.replayCursor > 0) {
                this.replayCursor--;
            }
        },

        replayJumpToStart() {
            this.replayPause();
            this.replayCursor = -1;
            this.topoRevealedHosts = new Set(['c2']);
            this.topoVisitedHosts = new Set();
            this.topoActiveHost = null;
            this.topoNewestEdge = -1;
            this.topoBeaconEdge = -1;
            this.topoStepCounts = {};
        },

        replayJumpToEnd() {
            this.replayPause();
            this.topoRevealAll();
            this.replayCursor = this.replaySteps.length - 1;
        },

        topoRevealAll() {
            if (!this.topoData) return;
            const allHosts = new Set(Object.keys(this.topoData.hosts || {}));
            allHosts.add('c2');
            this.topoRevealedHosts = allHosts;
            this.topoVisitedHosts = new Set(allHosts);
            this.topoActiveHost = null;
            this.topoNewestEdge = -1;
            this.topoBeaconEdge = -1;
            this.topoStepCounts = {};
            for (const [paw, steps] of Object.entries(this.topoData.steps_by_host || {})) {
                this.topoStepCounts[paw] = steps.length;
            }
            this.topoShowAll = true;
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
            const seq = this.topoData.replay_sequence || [];
            const item = seq[this.replayCursor];
            if (!item) return;

            const paw = item.paw;
            const wasRevealed = this.topoRevealedHosts.has(paw);

            // Reveal this host
            this.topoRevealedHosts = new Set(this.topoRevealedHosts);
            this.topoRevealedHosts.add(paw);
            this.topoActiveHost = paw;
            this.topoVisitedHosts = new Set(this.topoVisitedHosts);
            this.topoVisitedHosts.add(paw);

            // Update step count for this host
            this.topoStepCounts = { ...this.topoStepCounts };
            this.topoStepCounts[paw] = (this.topoStepCounts[paw] || 0) + 1;

            // If this is a newly revealed host, show the edge
            this.topoNewestEdge = -1;
            this.topoBeaconEdge = -1;
            if (!wasRevealed) {
                const edgeIdx = this.topoEdges.findIndex(e => e.target === paw);
                if (edgeIdx >= 0) {
                    this.topoRevealedHosts.add(this.topoEdges[edgeIdx].source);
                    this.topoNewestEdge = edgeIdx;
                }
            }
        },

        // Compute position of green dot along an edge
        topoBeaconDotPos(edgeIdx) {
            const t = this.topoBeaconDotT[edgeIdx] || 0;
            const edge = this.topoEdges[edgeIdx];
            if (!edge) return { x: 0, y: 0 };
            const hostMap = {};
            this.topoHosts.forEach(h => { hostMap[h.id] = h; });
            const src = hostMap[edge.source];
            const tgt = hostMap[edge.target];
            if (!src || !tgt) return { x: 0, y: 0 };
            // Interpolate along the edge (target→source direction, so t=0 is target, t=1 is source)
            return {
                x: tgt.x + (src.x - tgt.x) * t,
                y: tgt.y + (src.y - tgt.y) * t,
            };
        },

        // Animate green dot hopping along each edge from new host back to C2
        async replayBeaconToC2(paw) {
            if (!this.topoData || !this.topoData.path_to_c2) return;
            const pathHosts = this.topoData.path_to_c2[paw];
            if (!pathHosts || pathHosts.length < 2) return;

            for (let i = 0; i < pathHosts.length - 1; i++) {
                if (!this.replayPlaying && i > 0) break;
                const from = pathHosts[i];
                const to = pathHosts[i + 1];

                const edgeIdx = this.topoEdges.findIndex(e =>
                    (e.source === to && e.target === from) || (e.source === from && e.target === to)
                );
                if (edgeIdx < 0) continue;

                // Show dot on this edge and animate t from 0 to 1
                this.topoBeaconEdges = new Set(this.topoBeaconEdges);
                this.topoBeaconEdges.add(edgeIdx);
                this.topoBeaconDotT = { ...this.topoBeaconDotT, [edgeIdx]: 0 };

                // Animate in steps for visible hopping
                const steps = 14;
                for (let s = 0; s <= steps; s++) {
                    this.topoBeaconDotT = { ...this.topoBeaconDotT, [edgeIdx]: s / steps };
                    await this.sleep(45);
                }

                // Remove dot from this edge
                this.topoBeaconEdges = new Set(this.topoBeaconEdges);
                this.topoBeaconEdges.delete(edgeIdx);
            }
        },

        topoSelectHost(host) {
            this.topoSelectedHost = host.compromised ? this.topoData.hosts[host.id] : host;
        },

        topoHostCurrentSteps(hostId) {
            return this.topoStepCounts[hostId] || 0;
        },

        topoSubnetRevealed(subnet) {
            return subnet.hosts.some(hid => this.topoRevealedHosts.has(hid));
        },

        topoSubnetVisible(subnet) {
            // Show if it has a revealed host
            if (subnet.hosts.some(hid => this.topoRevealedHosts.has(hid))) return true;
            // Show empty subnets only when an agent that can see that network is revealed
            if (subnet.hosts.length === 0 && this.topoData) {
                // Check if any revealed agent has an IP in this subnet
                for (const [hid, host] of Object.entries(this.topoData.hosts || {})) {
                    if (!this.topoRevealedHosts.has(hid)) continue;
                    for (const ip of (host.ips || [])) {
                        const parts = ip.split('.');
                        if (parts.length === 4) {
                            const cidr = `${parts[0]}.${parts[1]}.${parts[2]}.0/24`;
                            if (cidr === subnet.cidr) return true;
                        }
                    }
                }
            }
            return false;
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
            const padding = 16;
            const bandW = 140;
            const hostSpacing = 80;
            const c2Width = 70;
            return subnets.map((s, si) => {
                const hosts_data = this.topoData.hosts || {};
                const comp = s.hosts.filter(h => hosts_data[h] && hosts_data[h].compromised);
                const disc = s.hosts.filter(h => hosts_data[h] && !hosts_data[h].compromised);
                const discSpacing = disc.length > 5 ? 20 : hostSpacing * 0.6;
                const h = Math.max(
                    comp.length * hostSpacing + disc.length * discSpacing + 50,
                    hostSpacing + 40
                );
                return {
                    cidr: s.cidr,
                    x: c2Width + padding + si * (bandW + 12),
                    y: padding,
                    w: bandW,
                    h: h,
                    hosts: s.hosts,
                };
            });
        },

        topoHosts() {
            if (!this.topoData) return [];
            const hosts = this.topoData.hosts || {};
            const result = [];
            const hostSpacing = 80;
            const stackSpacing = 20;  // tight spacing for stacked discovered hosts
            const hostPositions = {};

            this.topoSubnets.forEach((subnet) => {
                // Separate compromised and discovered hosts
                const compromised = subnet.hosts.filter(hid => hosts[hid] && hosts[hid].compromised);
                const discovered = subnet.hosts.filter(hid => hosts[hid] && !hosts[hid].compromised);

                // Position compromised hosts with full spacing
                const compH = compromised.length * hostSpacing;
                const compStartY = subnet.y + 24;
                compromised.forEach((hid, hi) => {
                    hostPositions[hid] = {
                        x: subnet.x + subnet.w / 2,
                        y: compStartY + hi * hostSpacing + hostSpacing / 2,
                    };
                });

                // Position discovered hosts — stacked tightly below compromised
                const discStartY = compStartY + compH + (compromised.length ? 10 : 0);
                const discSpacing = discovered.length > 5 ? stackSpacing : hostSpacing * 0.6;
                discovered.forEach((hid, hi) => {
                    // Offset x slightly for stacking effect when >5
                    const xOff = discovered.length > 5 ? (hi % 2 === 0 ? -8 : 8) : 0;
                    hostPositions[hid] = {
                        x: subnet.x + subnet.w / 2 + xOff,
                        y: discStartY + hi * discSpacing + discSpacing / 2,
                    };
                });
            });

            // C2 node on the left
            const svgH = this.topoSvgHeight;
            hostPositions['c2'] = { x: 30, y: svgH / 2 };

            Object.entries(hosts).forEach(([id, host]) => {
                const pos = hostPositions[id] || { x: 50, y: svgH / 2 };
                const isPivot = host.is_pivot || false;
                result.push({ ...host, x: pos.x, y: pos.y, isPivot });
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
                if (!src || !tgt) return { ...e, path: '', reversePath: '' };
                const mx = (src.x + tgt.x) / 2;
                const my = (src.y + tgt.y) / 2;
                const dx = tgt.x - src.x;
                const curveOffset = Math.min(Math.abs(dx) * 0.2, 30);
                const path = `M ${src.x} ${src.y} Q ${mx + curveOffset} ${my} ${tgt.x} ${tgt.y}`;
                // Reverse path for beacon traveling back to C2
                const reversePath = `M ${tgt.x} ${tgt.y} Q ${mx + curveOffset} ${my} ${src.x} ${src.y}`;
                return { ...e, path, reversePath };
            });
        },

        topoViewBox() {
            const w = this.topoSvgWidth;
            const h = this.topoSvgHeight;
            return `0 0 ${w} ${h}`;
        },

        // Dynamic icon scale
        topoIconRadius() {
            if (!this.topoData) return 28;
            const hostCount = Object.keys(this.topoData.hosts || {}).length;
            if (hostCount <= 3) return 28;
            if (hostCount <= 6) return 28;
            if (hostCount <= 12) return 26;
            if (hostCount <= 20) return 24;
            return 22;
        },

        topoIconImgSize() {
            return Math.round(this.topoIconRadius * 1.3);
        },

        topoSvgWidth() {
            if (!this.topoData) return 800;
            const subnets = this.topoSubnets;
            const lastSubnet = subnets[subnets.length - 1];
            const w = lastSubnet ? lastSubnet.x + lastSubnet.w + 20 : 500;
            return Math.max(w, 600);  // minimum width prevents huge icons
        },

        topoSvgHeight() {
            if (!this.topoData) return 300;
            const subnets = this.topoSubnets;
            const maxH = subnets.reduce((max, s) => Math.max(max, s.y + s.h + 20), 0);
            return Math.max(maxH, 250);  // minimum height
        },

        topoOperationName() {
            if (!this.selectedOperationId || !this.operations) return '';
            const op = this.operations.find(o => o.id === this.selectedOperationId);
            return op ? op.name : '';
        },

        topoHostSteps() {
            if (!this.topoSelectedHost || !this.topoData) return [];
            const paw = this.topoSelectedHost.agent_paw || this.topoSelectedHost.id;
            return (this.topoData.steps_by_host || {})[paw] || [];
        },

        replaySteps() {
            // Use topology replay_sequence if available (preferred — has correct ordering)
            if (this.topoData && this.topoData.replay_sequence && this.topoData.replay_sequence.length) {
                return this.topoData.replay_sequence;
            }
            // Fallback to operation steps
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

  //- Hidden elements needed for PDF graph export
  #images(style="display: none")
  #copy
  #debrief-graph(style="display:none")
    .d3-tooltip#op-tooltip(style="opacity: 0")
    svg#debrief-steps-svg.op-svg.debrief-svg
    svg#debrief-attackpath-svg.op-svg.debrief-svg
    svg#debrief-tactic-svg.op-svg.debrief-svg
    svg#debrief-technique-svg.op-svg.debrief-svg

  .is-flex.is-align-items-center.mb-3(style="gap:12px")
    .select.is-small
      select(v-model="selectedOperationId", @change="loadOperation")
        option(disabled selected value="") Select an operation
        template(v-for="operation in operations", :key="operation.id")
          option(:value="operation.id") {{ operation.name }}

  //- TOPOLOGY VIEW — full width
  .topo-main-canvas(v-show="selectedOperationId.length")
        //- Operation title
        .has-text-centered.mb-2(v-if="selectedOperationId.length")
          strong.has-text-grey {{ topoOperationName }}

        //- Replay controls (integrated here, not in a separate tab)
        .topo-controls.mb-2
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
          .has-text-centered.mt-1
            span.is-size-7.has-text-grey Step {{ Math.max(replayCursor + 1, 0) }} / {{ replaySteps.length }}

        //- Legend (outside canvas)
        .topo-legend-row(v-if="topoData")
          span.topo-legend-item
            span.topo-legend-dot(style="border: 2px solid #cc3311")
            span Path
          span.topo-legend-item
            span.topo-legend-dot(style="border: 2px dashed #FFB000")
            span Pivot
          span.topo-legend-item
            span.topo-legend-dot.topo-legend-filled(style="background:#44AA99")
            span Beacon

        //- Topology canvas + slide-out
        .topo-split
          .topo-canvas(ref="topoMainCanvas")
            svg.topo-svg(
              v-if="topoData",
              :viewBox="topoViewBox",
              preserveAspectRatio="xMidYMid meet",
              xmlns="http://www.w3.org/2000/svg"
            )
              //- Subnet zone bands — only show when a host in the subnet is revealed
              //- Empty subnets (networks seen but no agents) appear when their parent agent is revealed
              g.topo-subnets
                template(v-for="(subnet, si) in topoSubnets", :key="si")
                  template(v-if="topoSubnetVisible(subnet)")
                    rect.topo-zone(
                      :x="subnet.x", :y="subnet.y",
                      :width="subnet.w", :height="subnet.h",
                      :fill="topoZoneColor(si)", rx="6"
                    )
                    text.topo-zone-label(:x="subnet.x + subnet.w / 2", :y="subnet.y + 14", text-anchor="middle") {{ subnet.cidr }}
              //- Edges
              g.topo-edges
                template(v-for="(edge, ei) in topoEdges", :key="ei")
                  template(v-if="topoRevealedHosts.has(edge.source) && topoRevealedHosts.has(edge.target)")
                    path.topo-edge(
                      :id="'topo-path-' + ei",
                      :d="edge.path",
                      :class="{ 'is-newest': topoNewestEdge === ei }",
                      fill="none"
                    )
                    //- Green beacon — a single green dot that hops along the dashed path
                    circle.topo-beacon-dot(
                      v-if="topoBeaconEdges.has(ei)",
                      r="4", fill="#44AA99",
                      :cx="topoBeaconDotPos(ei).x",
                      :cy="topoBeaconDotPos(ei).y"
                    )
                    //- Red pulse: edge appearing (forward direction)
                    circle.topo-pulse(v-if="topoNewestEdge === ei", r="2", fill="#cc3311")
                      animateMotion(dur="0.5s", repeatCount="1", :path="edge.path")
              //- Host icons
              g.topo-hosts
                template(v-for="host in topoHosts", :key="host.id")
                  g.topo-host(
                    v-show="topoRevealedHosts.has(host.id)",
                    :transform="`translate(${host.x}, ${host.y})`",
                    :class="{ 'is-compromised': host.compromised, 'is-discovered': !host.compromised, 'is-active': topoActiveHost === host.id, 'is-visited': topoVisitedHosts.has(host.id) }",
                    @click="topoSelectHost(host)",
                    @mouseenter="topoHoverHost = host.id",
                    @mouseleave="topoHoverHost = null"
                  )
                    circle.topo-glow(:r="topoIconRadius + 6", v-if="topoActiveHost === host.id")
                    circle.topo-host-bg(:r="topoIconRadius")
                    image.topo-host-icon(:href="topoPlatformSvg(host.platform)", :x="-topoIconImgSize/2", :y="-topoIconImgSize/2", :width="topoIconImgSize", :height="topoIconImgSize")
                    //- Pivot indicator: dashed orange ring
                    circle.topo-pivot-ring(v-if="host.isPivot", :r="topoIconRadius + 4", fill="none", stroke="#FFB000", stroke-width="1.5", stroke-dasharray="4 3")
                    text.topo-host-label(:y="topoIconRadius + 18", text-anchor="middle") {{ host.hostname }}
                    g.topo-badge(v-if="host.compromised && topoHostCurrentSteps(host.id) > 0")
                      circle(:cx="topoIconRadius - 4", :cy="-topoIconRadius + 4", r="7", fill="#4c0089")
                      text(:x="topoIconRadius - 4", :y="-topoIconRadius + 4", text-anchor="middle", dominant-baseline="central", fill="white", font-size="8") {{ topoHostCurrentSteps(host.id) }}
                    g.topo-tooltip(v-if="topoHoverHost === host.id")
                      rect(x="-60", y="-36", width="120", height="24", rx="3", fill="#1a1a2e", stroke="#555")
                      text(x="0", y="-28", text-anchor="middle", fill="#aaa", font-size="8") {{ host.ips.join(', ') || 'No IP' }}
                      text(x="0", y="-18", text-anchor="middle", fill="#ccc", font-size="8") {{ host.platform }}

              //- (beacon dots rendered per-edge above)

            .has-text-centered.py-4(v-if="!topoData && selectedOperationId.length")
              p.has-text-grey.is-size-7 Loading topology...

          //- (legend moved outside topo-split)

          //- Slide-out detail panel (click a host)
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
            .topo-detail-section(v-if="!topoSelectedHost.compromised && topoSelectedHost.intel && topoSelectedHost.intel.length")
              p.is-size-7.has-text-weight-bold.mb-1 Gathered Intel
              .topo-intel(v-for="item in topoSelectedHost.intel", :key="item.trait + item.value")
                span.is-size-7.has-text-grey {{ item.trait }}:
                span.is-size-7.ml-1 {{ item.value }}
            .topo-detail-section(v-if="!topoSelectedHost.compromised && (!topoSelectedHost.intel || !topoSelectedHost.intel.length)")
              p.is-size-7.has-text-grey No intel gathered

  .tabs.is-centered.debrief-tabs(v-show="selectedOperationId.length")
    ul.ml-0
      li(:class="{ 'is-active': activeTab === 'stats' }", @click="activeTab = 'stats'")
        a
          span.icon.is-small
            font-awesome-icon(icon="fas fa-chart-bar")
          span Stats
      li(:class="{ 'is-active': activeTab === 'agents' }", @click="activeTab = 'agents'")
        a
          span.icon.is-small
            font-awesome-icon(icon="fas fa-user-secret")
          span Agents
      li(:class="{ 'is-active': activeTab === 'tactics' }", @click="activeTab = 'tactics'")
        a
          span.icon.is-small
            font-awesome-icon(icon="fas fa-crosshairs")
          span TTPs

  div.debrief-tab-content(v-show="selectedOperationId.length")
    //- STATS TABLE
    div(v-show="activeTab === 'stats'")
      table.debrief-table
        thead
          tr
            th Name
            th State
            th Planner
            th Objective
            th Started
        tbody
          template(v-for="stat in stats", :key="stat.name")
            tr
              td.has-text-weight-bold {{ stat.name }}
              td
                span.tag.is-small(:class="stat.state === 'finished' ? 'is-success' : 'is-warning'") {{ stat.state.toUpperCase() }}
              td {{ stat.planner.name }}
              td {{ stat.objective.name }}
              td.has-text-grey {{ stat.start }}

    //- AGENTS TABLE
    div(v-show="activeTab === 'agents'")
      table.debrief-table
        thead
          tr
            th
            th Paw
            th Host
            th Platform
            th Username
            th Privilege
            th Executable
        tbody
          template(v-for="agent in agents", :key="agent.paw")
            tr
              td
                image(:src="agent.platform === 'windows' ? '/debrief/img/windows.svg' : agent.platform === 'darwin' ? '/debrief/img/darwin.svg' : '/debrief/img/linux.svg'", style="width:16px;height:16px;vertical-align:middle")
              td.has-text-weight-bold {{ agent.paw }}
              td {{ agent.host }}
              td {{ agent.platform }}
              td {{ agent.username }}
              td
                span.tag.is-small(:class="agent.privilege === 'Elevated' ? 'is-danger' : 'is-dark'") {{ agent.privilege }}
              td.has-text-grey {{ agent.exe_name }}

    //- TTPs — TACTICS & TECHNIQUES
    div(v-show="activeTab === 'tactics'")
      .has-text-centered.py-4(v-if="!tacticsAndTechniques || Object.keys(tacticsAndTechniques).length === 0")
        p.has-text-grey No TTPs data available for this operation
        p.is-size-7.has-text-grey.mt-1 TTPs are populated when abilities are executed during an operation
      .debrief-ttp-grid(v-else)
        template(v-for="tactic in tacticsAndTechniques", :key="tactic.name")
          .debrief-ttp-card
            .debrief-ttp-header {{ tactic.name }}
            .debrief-ttp-body
              .debrief-ttp-section
                .debrief-ttp-label Techniques
                template(v-for="technique in Object.keys(tactic.techniques)", :key="technique")
                  .debrief-ttp-item
                    span.tag.is-small.is-dark.mr-1 {{ tactic.techniques[technique] }}
                    span {{ technique }}
              .debrief-ttp-section(v-if="tactic.steps && tactic.steps.length")
                .debrief-ttp-label Abilities
                template(v-for="step in tactic.steps", :key="step.operation")
                  template(v-for="ability in step.abilities", :key="ability")
                    .debrief-ttp-item.has-text-grey {{ ability }}

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

