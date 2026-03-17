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
    width: 80% !important;
    height: 400px;
    border-radius: 4px;
}

#fact-graph {
    position: relative;
    margin: auto;
    background-color: black;
    border-radius: 4px;
    width: 800px;
    height: 600px;
}

#fact-limit {
    width: 800px;
    margin: auto;
}

#select-operation {
    max-width: 800px;
    margin: 0 auto;
}

#tactic-section {
    width: 600px;
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

/* ==================== REPLAY TAB ==================== */

.replay-container {
    max-width: 900px;
    margin: 0 auto;
}

.replay-controls {
    padding: 12px 0 4px;
}

/* Timeline strip */
.replay-timeline {
    position: relative;
    padding: 0 24px 20px;
}

.replay-timeline-track {
    position: relative;
    height: 4px;
    background: #363636;
    border-radius: 2px;
    margin: 30px 0 0;
}

.replay-timeline-progress {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(90deg, #750b20, #cc3311);
    border-radius: 2px;
    transition: width 0.3s ease;
}

.replay-timeline-marker {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    cursor: pointer;
    z-index: 2;
}

.replay-marker-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #555;
    border: 2px solid #363636;
    transition: all 0.3s ease;
}

.replay-timeline-marker.is-past .replay-marker-dot {
    background: #750b20;
    border-color: #750b20;
}

.replay-timeline-marker.is-active .replay-marker-dot {
    background: #cc3311;
    border-color: #fff;
    width: 16px;
    height: 16px;
    box-shadow: 0 0 8px rgba(204, 51, 17, 0.6);
}

.replay-marker-label {
    display: none;
    position: absolute;
    bottom: 18px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.6rem;
    white-space: nowrap;
    color: #aaa;
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.replay-timeline-marker.is-active .replay-marker-label,
.replay-timeline-marker:hover .replay-marker-label {
    display: block;
    color: #fff;
}

/* Hover popover */
.replay-popover {
    position: absolute;
    bottom: 28px;
    left: 50%;
    transform: translateX(-50%);
    background: #1a1a2e;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 10px 14px;
    min-width: 220px;
    max-width: 320px;
    z-index: 100;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    pointer-events: none;
}

.replay-popover-header {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    padding-bottom: 6px;
    border-bottom: 1px solid #333;
}

.replay-popover-body p {
    margin: 2px 0;
}

/* Event feed */
.replay-feed {
    max-height: 500px;
    overflow-y: auto;
    padding: 8px 0;
    scroll-behavior: smooth;
}

.replay-card {
    display: flex;
    margin-bottom: 2px;
    opacity: 0;
    transform: translateY(10px);
    animation: replayFadeIn 0.35s ease forwards;
    cursor: pointer;
    transition: opacity 0.2s;
}

.replay-card.is-past {
    opacity: 0.55;
}

.replay-card.is-active {
    opacity: 1;
}

@keyframes replayFadeIn {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.replay-card.is-past {
    animation: none;
    opacity: 0.55;
    transform: none;
}

/* Timeline dots on cards */
.replay-card-timeline {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 32px;
    flex-shrink: 0;
    padding-top: 14px;
}

.replay-card-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #555;
    flex-shrink: 0;
}

.replay-card-dot.is-success { background: #44AA99; }
.replay-card-dot.is-danger { background: #CC3311; }
.replay-card-dot.is-info { background: cornflowerblue; }
.replay-card-dot.is-dark { background: #333; }
.replay-card-dot.is-warning { background: #FFB000; }
.replay-card-dot.is-light { background: #ddd; }

.replay-card-line {
    width: 2px;
    flex-grow: 1;
    background: #363636;
    min-height: 12px;
}

/* Card content */
.replay-card-content {
    flex: 1;
    background: #1a1a2e;
    border-radius: 6px;
    padding: 10px 14px;
    margin-left: 8px;
    border: 1px solid transparent;
    transition: border-color 0.2s, background 0.2s;
}

.replay-card.is-active .replay-card-content {
    border-color: #750b20;
    background: #1e1e32;
}

.replay-card:hover .replay-card-content {
    border-color: #555;
}

.replay-card-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.replay-card-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
}

.replay-agent-badge {
    font-size: 0.75rem;
    color: #aaa;
    background: #2a2a3e;
    padding: 1px 8px;
    border-radius: 4px;
}

.replay-card-title {
    font-size: 0.9rem;
}

.replay-card-detail {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #333;
}

.replay-pre {
    background: #0d0d1a;
    color: #ccc;
    font-size: 0.75rem;
    padding: 8px 12px;
    border-radius: 4px;
    max-height: 200px;
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
        },

        replayPlay() {
            if (!this.replaySteps.length) return;
            this.replayPlaying = true;
            if (this.replayCursor >= this.replaySteps.length - 1) {
                this.replayCursor = -1;
            }
            this.replayInterval = setInterval(() => {
                if (this.replayCursor < this.replaySteps.length - 1) {
                    this.replayCursor++;
                    this.replayScrollToActive();
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
  },
  computed: {
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

  .columns.mb-6
    .column.is-3
      form
        .field
          .control.mr-2
            .select.is-fullwidth
              select.has-text-centered(v-model="selectedOperationId", @change="loadOperation")
                option(disabled selected value="") Select an operation
                template(v-for="operation in operations", :key="operation.id")
                  option(:value="operation.id") {{ operation.name }}
    .column.is-9.is-flex.is-justify-content-center.m-0
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
      .replay-container

        //- PLAYBACK CONTROLS
        .replay-controls
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
          .is-flex.is-justify-content-center.is-align-items-center.mt-1.mb-3
            span.is-size-7.has-text-grey.mr-3 Speed:
            .buttons.has-addons.mb-0
              button.button.is-tiny(:class="replaySpeed === 500 ? 'is-primary' : 'is-dark'", @click="replaySpeed = 500", style="font-size:0.65rem;padding:2px 8px;height:22px") 2x
              button.button.is-tiny(:class="replaySpeed === 1000 ? 'is-primary' : 'is-dark'", @click="replaySpeed = 1000", style="font-size:0.65rem;padding:2px 8px;height:22px") 1x
              button.button.is-tiny(:class="replaySpeed === 2000 ? 'is-primary' : 'is-dark'", @click="replaySpeed = 2000", style="font-size:0.65rem;padding:2px 8px;height:22px") 0.5x
            span.is-size-7.has-text-grey.ml-3 Step {{ replayCursor + 1 }} / {{ replaySteps.length }}

        //- TIMELINE STRIP
        .replay-timeline(v-if="replaySteps.length")
          .replay-timeline-track
            .replay-timeline-progress(:style="{ width: replayProgressPct + '%' }")
            .replay-timeline-marker(
              v-for="(step, idx) in replaySteps",
              :key="idx",
              :style="{ left: replayMarkerPct(idx) + '%' }",
              :class="replayMarkerClass(idx)",
              @click="replayCursor = idx",
              @mouseenter="replayHoverIdx = idx",
              @mouseleave="replayHoverIdx = -1"
            )
              .replay-marker-dot
              .replay-marker-label {{ step.ability.name }}
              //- Hover popover
              .replay-popover(v-if="replayHoverIdx === idx")
                .replay-popover-header
                  span.tag.is-small(:class="replayStatusTagClass(step.status)") {{ getStatusName(step.status) }}
                  strong.ml-2 {{ step.ability.name }}
                .replay-popover-body
                  p.is-size-7
                    span.has-text-grey Agent:
                    |  {{ step.paw }}
                  p.is-size-7(v-if="step.ability.tactic")
                    span.has-text-grey Tactic:
                    |  {{ step.ability.tactic }}
                  p.is-size-7(v-if="step.ability.technique_name")
                    span.has-text-grey Technique:
                    |  {{ step.ability.technique_name }}
                  p.is-size-7(v-if="step.finish")
                    span.has-text-grey Time:
                    |  {{ step.finish }}

        //- EVENT FEED
        .replay-feed(ref="replayFeed")
          template(v-for="(step, idx) in replaySteps", :key="idx")
            .replay-card(
              v-show="idx <= replayCursor",
              :class="{ 'is-active': idx === replayCursor, 'is-past': idx < replayCursor }",
              @click="replayExpandedIdx = (replayExpandedIdx === idx ? -1 : idx)"
            )
              .replay-card-timeline
                .replay-card-dot(:class="replayDotClass(step.status)")
                .replay-card-line(v-if="idx < replaySteps.length - 1")
              .replay-card-content
                .replay-card-header
                  .replay-card-meta
                    span.tag.is-small(:class="replayStatusTagClass(step.status)") {{ getStatusName(step.status) }}
                    span.replay-agent-badge.ml-2
                      font-awesome-icon.mr-1(:icon="replayPlatformIcon(step)")
                      | {{ step.paw }}
                    span.has-text-grey.ml-2.is-size-7(v-if="step.finish") {{ step.finish }}
                  .replay-card-title
                    strong {{ step.ability.name }}
                    span.has-text-grey.ml-2.is-size-7(v-if="step.ability.tactic") {{ step.ability.tactic }}
                    span.has-text-grey.is-size-7(v-if="step.ability.technique_name")  / {{ step.ability.technique_name }}

                //- EXPANDED DETAIL
                .replay-card-detail(v-if="replayExpandedIdx === idx")
                  .columns.is-multiline.mt-1
                    .column.is-12(v-if="step.ability.description")
                      p.is-size-7.has-text-grey {{ step.ability.description }}
                    .column.is-12
                      p.is-size-7.has-text-weight-bold Command
                      pre.replay-pre {{ replayDecodeCommand(step) }}
                    .column.is-12
                      button.button.is-small.is-outlined(@click.stop="showCommand(step.id, step.command, step.ability.name)") View Output
                    .column.is-12(v-if="step.facts && step.facts.length")
                      p.is-size-7.has-text-weight-bold.mb-1 Facts Discovered
                      .tags
                        span.tag.is-info.is-light(v-for="fact in step.facts", :key="fact.trait") {{ fact.trait }}: {{ fact.value ? fact.value.substring(0, 40) : '' }}

          //- Empty state
          .has-text-centered.py-6(v-if="!replaySteps.length")
            p.has-text-grey Select an operation to see the replay

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

