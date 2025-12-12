# pytest tests

import pytest
import json

import attack_mapper

@pytest.fixture
def example_data_comp_by_id():
    return json.loads(
'''
{
    "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077": {
        "type": "x-mitre-data-component",
        "spec_version": "2.1",
        "id": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
        "created": "2021-10-20T15:05:19.272Z",
        "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
        "revoked": false,
        "external_references": [
            {
                "source_name": "mitre-attack",
                "url": "https://attack.mitre.org/datacomponents/DC0032",
                "external_id": "DC0032"
            }
        ],
        "object_marking_refs": [
            "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
        ],
        "modified": "2025-11-12T22:03:39.105Z",
        "name": "Process Creation",
        "description": "Refers to the event in which a new process (executable) is initialized by an operating system. This can involve parent-child process relationships, process arguments, and environmental variables. Monitoring process creation is crucial for detecting malicious behaviors, such as execution of unauthorized binaries, scripting abuse, or privilege escalation attempts.. ",
        "x_mitre_data_source_ref": "",
        "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
        "x_mitre_deprecated": false,
        "x_mitre_domains": [
            "ics-attack",
            "mobile-attack",
            "enterprise-attack"
        ],
        "x_mitre_version": "2.0",
        "x_mitre_attack_spec_version": "3.3.0",
        "x_mitre_log_sources": [
            {
                "name": "Process",
                "channel": "None"
            },
            {
                "name": "auditd:SYSCALL",
                "channel": "execve"
            }
        ]
    },
    "x-mitre-data-component--685f917a-e95e-4ba0-ade1-c7d354dae6e0": {
        "type": "x-mitre-data-component",
        "spec_version": "2.1",
        "id": "x-mitre-data-component--685f917a-e95e-4ba0-ade1-c7d354dae6e0",
        "created": "2021-10-20T15:05:19.273Z",
        "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
        "revoked": false,
        "external_references": [
            {
                "source_name": "mitre-attack",
                "url": "https://attack.mitre.org/datacomponents/DC0064",
                "external_id": "DC0064"
            }
        ],
        "object_marking_refs": [
            "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
        ],
        "modified": "2025-11-12T22:03:39.105Z",
        "name": "Command Execution",
        "description": "test desc",
        "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
        "x_mitre_deprecated": false,
        "x_mitre_domains": [
            "ics-attack",
            "mobile-attack",
            "enterprise-attack"
        ],
        "x_mitre_version": "2.0",
        "x_mitre_attack_spec_version": "3.3.0",
        "x_mitre_log_sources": [
            {
                "name": "Command",
                "channel": "None"
            },
            {
                "name": "auditd:SYSCALL",
                "channel": "execution of realmd, samba-tool, or ldapmodify with user-related arguments"
            },
            {
                "name": "macos:unifiedlog",
                "channel": "dsconfigad or dscl with create or append options for AD-bound users"
            }
        ]
    }
}
''')

@pytest.fixture
def example_analytic():
    return json.loads(
'''
{
    "type": "x-mitre-analytic",
    "spec_version": "2.1",
    "id": "x-mitre-analytic--2385f397-5d17-4b37-ba07-bb52a52ff66c",
    "created": "2025-10-21T15:10:28.402Z",
    "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
    "external_references": [
        {
            "source_name": "mitre-attack",
            "url": "https://attack.mitre.org/detectionstrategies/DET0360#AN1025",
            "external_id": "AN1025"
        }
    ],
    "object_marking_refs": [
        "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
    ],
    "modified": "2025-11-12T22:03:39.105Z",
    "name": "Analytic 1025",
    "description": "test analytic description",
    "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
    "x_mitre_deprecated": false,
    "x_mitre_version": "1.0",
    "x_mitre_attack_spec_version": "3.3.0",
    "x_mitre_domains": [
        "enterprise-attack"
    ],
    "x_mitre_platforms": [
        "Windows"
    ],
    "x_mitre_log_source_references": [
        {
            "x_mitre_data_component_ref": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
            "name": "WinEventLog:Security",
            "channel": "EventCode=4688"
        },
        {
            "x_mitre_data_component_ref": "x-mitre-data-component--685f917a-e95e-4ba0-ade1-c7d354dae6e0",
            "name": "WinEventLog:PowerShell",
            "channel": "EventCode=4103, 4104, 4105, 4106"
        }
    ],
    "x_mitre_mutable_elements": [
        {
            "field": "TimeWindow",
            "description": "Adjustable window to track chained discovery activity (e.g., 5-10 minutes)."
        },
        {
            "field": "UserContext",
            "description": "Tune to focus on non-admin users or service accounts performing enumeration."
        },
        {
            "field": "ProcessLineageDepth",
            "description": "How far back the parent-child process chain is correlated."
        }
    ]
}
''')

@pytest.fixture
def example_analytics_by_tid():
    return {
        'T1053.005': [{
            'an_id': 'AN1221',
            'id': 'x-mitre-analytic--4959f750-78db-4b4c-8d91-23027b386c2b',
            'name': 'Analytic 1221',
            'platform': 'windows',
            'platforms': ['windows'],
            'statement': 'test description 1221',
            'tunables': [
                {
                    "field": "TimeWindow",
                    "description": "Defines threshold for grouping task creation and associated execution within suspicious time proximity."
                },
                {
                    "field": "UserContext",
                    "description": "Filters based on non-standard user accounts or execution under SYSTEM when not typical for the environment."
                },
                {
                    "field": "TaskNamePattern",
                    "description": "Allows defenders to flag obfuscated, randomized, or suspicious task names outside normal conventions."
                },
                {
                    "field": "CommandLineEntropyThreshold",
                    "description": "Flags tasks executing heavily obfuscated PowerShell or binary blobs via base64 or encoding."
                }
            ],
            'det_id': 'DET0441',
            'dc_elements': [
                {
                    "data_component": "Scheduled Job Creation",
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4698"
                },
                {
                    "data_component": "Scheduled Job Modification",
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4702"
                },
                {
                    "data_component": "Process Creation",
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=1"
                },
                {
                    "data_component": "File Creation",
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=11"
                },
                {
                    "data_component": "Windows Registry Key Modification",
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=13, 14"
                }
            ]
        }],
        'T1083': [
            {
                'an_id': 'AN1040',
                'id': 'x-mitre-analytic--69d9d158-aa43-4b73-b9a4-f1a2dc6c13c1',
                'name': 'Analytic 1040',
                'platform': 'windows',
                'platforms': ['windows'],
                'statement': 'test description 1040',
                'tunables': [
                    {
                        "field": "CommandLineRegex",
                        "description": "Allows tuning based on tools/scripts used for enumeration (e.g., tree, dir /s /b)"
                    },
                    {
                        "field": "UserContext",
                        "description": "Scoping for standard vs elevated or service accounts"
                    },
                    {
                        "field": "TimeWindow",
                        "description": "Defines burst activity over short periods (e.g., >50 directory queries in 30s)"
                    }
                ],
                'det_id': 'DET0370',
                'dc_elements': [
                    {
                        "data_component": "Process Creation",
                        "name": "WinEventLog:Security",
                        "channel": "EventCode=4688"
                    },
                    {
                        "data_component": "File Creation",
                        "name": "WinEventLog:Sysmon",
                        "channel": "EventCode=11"
                    }
                ]
            },
            {
                'an_id': 'AN1041',
                'id': 'x-mitre-analytic--b50bf863-644a-48c2-85a3-2c633f135650',
                'name': 'Analytic 1041',
                'platform': 'linux',
                'platforms': ['linux'],
                'statement': 'test description 1041',
                'tunables': [
                    {
                        "field": "FilePathDepth",
                        "description": "Max depth of recursive access to tune noise vs anomaly"
                    },
                    {
                        "field": "UserContext",
                        "description": "Helpful to exclude known scripts or automation accounts"
                    }
                ],
                'det_id': 'DET0370',
                'dc_elements': [
                    {
                        "data_component": "Process Creation",
                        "name": "auditd:SYSCALL",
                        "channel": "execve"
                    },
                    {
                        "data_component": "File Access",
                        "name": "auditd:PATH",
                        "channel": "PATH"
                    }
                ]
            },
            {
                'an_id': 'AN1042',
                'id': 'x-mitre-analytic--42683860-d6df-4585-af65-31f783269f8f',
                'name': 'Analytic 1042',
                'platform': 'macos',
                'platforms': ['macos'],
                'statement': 'test description 1042',
                'tunables': [
                    {
                        "field": "PredicateScope",
                        "description": "Adjust macOS unified log filter to include/exclude system paths"
                    },
                    {
                        "field": "TimeWindow",
                        "description": "Tune based on burst access patterns"
                    }
                ],
                'det_id': 'DET0370',
                'dc_elements': [
                    {
                        "data_component": "Process Creation",
                        "name": "macos:unifiedlog",
                        "channel": "log collect --predicate"
                    },
                    {
                        "data_component": "File Access",
                        "name": "fs:fsusage",
                        "channel": "Filesystem Call Monitoring"
                    }
                ]
            },
            {
                'an_id': 'AN1043',
                'id': 'x-mitre-analytic--aaddc766-52bb-428b-98c4-3a742d10befa',
                'name': 'Analytic 1043',
                'platform': 'esxi',
                'platforms': ['esxi'],
                'statement': 'test description 1043',
                'tunables': [
                    {
                        "field": "CLICommandPattern",
                        "description": "Match on esxcli storage|filesystem commands"
                    },
                    {
                        "field": "AccessSource",
                        "description": "Limit alerting to non-vCenter or remote IPs"
                    }
                ],
                'det_id': 'DET0370',
                'dc_elements': [
                    {
                        "data_component": "Command Execution",
                        "name": "esxi:shell",
                        "channel": "Shell Access/Command Execution"
                    },
                    {
                        "data_component": "File Access",
                        "name": "esxi:hostd",
                        "channel": "vSphere File API Access"
                    }
                ]
            },
            {
                'an_id': 'AN1044',
                'id': 'x-mitre-analytic--be6e5f23-0e29-430f-83f7-d76c58de3a2d',
                'name': 'Analytic 1044',
                'platform': 'network devices',
                'platforms': ['network devices'],
                'statement': 'test description 1044',
                'tunables': [
                    {
                        "field": "CommandWhitelist",
                        "description": "Filter allowed commands by account or IP"
                    },
                    {
                        "field": "SessionOrigin",
                        "description": "Tunable to restrict detection to remote terminal or Telnet/SSH"
                    }
                ],
                'det_id': 'DET0370',
                'dc_elements': [
                    {
                        "data_component": "Command Execution",
                        "name": "networkdevice:syslog",
                        "channel": "CLI Command Logging"
                    }
                ]
            }
        ]
    }

@pytest.fixture
def example_techniques_by_id():
    return {
        'T1053.005': {
            'technique_id': 'T1053.005',
            'name': 'Scheduled Task',
            'ap_id': 'attack-pattern--005a06c6-14bf-4118-afa0-ebcd8aebb0c9'
        },
        'T1083': {
            'technique_id': 'T1083',
            'name': 'File and Directory Discovery',
            'ap_id': 'attack-pattern--7bc57495-ea59-4380-be31-a64af124ef18'
        },
    }

@pytest.fixture
def example_strategies_by_tid():
    return {
        'T1053.005': [{
            'id': 'x-mitre-detection-strategy--c7bdd7d7-19dc-4042-8565-5e0cf4656102',
            'name': 'Detection of Suspicious Scheduled Task Creation and Execution on Windows',
            'external_references': [
                {
                    'source_name': 'mitre-attack',
                    'url': 'https://attack.mitre.org/detectionstrategies/DET0441',
                    'external_id': 'DET0441'
                }
            ],
            'det_id': 'DET0441',
        }],
        'T1083': [{
            'id': 'x-mitre-detection-strategy--33ab9d0c-5671-48e6-8465-f80560909c65',
            'name': 'Recursive Enumeration of Files and Directories Across Privilege Contexts',
            'external_references': [
                {
                    'source_name': 'mitre-attack',
                    'url': 'https://attack.mitre.org/detectionstrategies/DET0370',
                    'external_id': 'DET0370'
                }
            ],
            'det_id': 'DET0370',
        }]
    }

@pytest.fixture
def example_bundle_v18():
    return json.loads(
'''
{
    "type": "bundle",
    "id": "bundle--1bcaeeb8-0f66-41e3-aa08-441688cda580",
    "objects": [
        {
            "type": "attack-pattern",
            "spec_version": "2.1",
            "id": "attack-pattern--005a06c6-14bf-4118-afa0-ebcd8aebb0c9",
            "created": "2019-11-27T14:58:00.429Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/techniques/T1053/005",
                    "external_id": "T1053.005"
                },
                {
                    "source_name": "ProofPoint Serpent",
                    "description": "Campbell, B. et al. (2022, March 21). Serpent, No Swiping! New Backdoor Targets French Entities with Unique Attack Chain. Retrieved April 11, 2022.",
                    "url": "https://www.proofpoint.com/us/blog/threat-insight/serpent-no-swiping-new-backdoor-targets-french-entities-unique-attack-chain"
                },
                {
                    "source_name": "Defending Against Scheduled Task Attacks in Windows Environments",
                    "description": "Harshal Tupsamudre. (2022, June 20). Defending Against Scheduled Tasks. Retrieved July 5, 2022.",
                    "url": "https://blog.qualys.com/vulnerabilities-threat-research/2022/06/20/defending-against-scheduled-task-attacks-in-windows-environments"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-24T17:48:19.176Z",
            "name": "Scheduled Task",
            "description": "test desc sch task",
            "kill_chain_phases": [
                {
                    "kill_chain_name": "mitre-attack",
                    "phase_name": "execution"
                },
                {
                    "kill_chain_name": "mitre-attack",
                    "phase_name": "persistence"
                },
                {
                    "kill_chain_name": "mitre-attack",
                    "phase_name": "privilege-escalation"
                }
            ],
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_contributors": [
                "Andrew Northern, @ex_raritas",
                "Bryan Campbell, @bry_campbell",
                "Selena Larson, @selenalarson",
                "Sittikorn Sangrattanapitak",
                "Zachary Abzug, @ZackDoesML"
            ],
            "x_mitre_deprecated": false,
            "x_mitre_detection": "",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_is_subtechnique": true,
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_platforms": [
                "Windows"
            ],
            "x_mitre_version": "1.8",
            "x_mitre_remote_support": false
        },
        {
            "type": "attack-pattern",
            "spec_version": "2.1",
            "id": "attack-pattern--7bc57495-ea59-4380-be31-a64af124ef18",
            "created": "2017-05-31T21:31:04.710Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/techniques/T1083",
                    "external_id": "T1083"
                },
                {
                    "source_name": "Windows Commands JPCERT",
                    "description": "Tomonaga, S. (2016, January 26). Windows Commands Abused by Attackers. Retrieved February 2, 2016.",
                    "url": "https://blogs.jpcert.or.jp/en/2016/01/windows-commands-abused-by-attackers.html"
                },
                {
                    "source_name": "US-CERT-TA18-106A",
                    "description": "US-CERT. (2018, April 20). Alert (TA18-106A) Russian State-Sponsored Cyber Actors Targeting Network Infrastructure Devices. Retrieved October 19, 2020.",
                    "url": "https://www.us-cert.gov/ncas/alerts/TA18-106A"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-24T17:49:00.036Z",
            "name": "File and Directory Discovery",
            "description": "test desc",
            "kill_chain_phases": [
                {
                    "kill_chain_name": "mitre-attack",
                    "phase_name": "discovery"
                }
            ],
            "x_mitre_attack_spec_version": "3.2.0",
            "x_mitre_contributors": [
                "Austin Clark, @c2defense"
            ],
            "x_mitre_deprecated": false,
            "x_mitre_detection": "",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_is_subtechnique": false,
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_platforms": [
                "ESXi",
                "Linux",
                "macOS",
                "Network Devices",
                "Windows"
            ],
            "x_mitre_version": "1.7"
        },
        {
            "type": "attack-pattern",
            "spec_version": "2.1",
            "id": "attack-pattern--00d0b012-8a03-410e-95de-5826bf542de6",
            "created": "2017-05-31T21:30:54.176Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": true,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/techniques/T1066",
                    "external_id": "T1066"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-24T17:48:19.377Z",
            "name": "Indicator Removal from Tools",
            "description": "test desc",
            "kill_chain_phases": [
                {
                    "kill_chain_name": "mitre-attack",
                    "phase_name": "defense-evasion"
                }
            ],
            "x_mitre_attack_spec_version": "3.2.0",
            "x_mitre_deprecated": false,
            "x_mitre_detection": "",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_is_subtechnique": false,
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_platforms": [
                "Linux",
                "macOS",
                "Windows"
            ],
            "x_mitre_version": "1.1"
        },
        {
            "type": "x-mitre-detection-strategy",
            "spec_version": "2.1",
            "id": "x-mitre-detection-strategy--c7bdd7d7-19dc-4042-8565-5e0cf4656102",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0441",
                    "external_id": "DET0441"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Detection of Suspicious Scheduled Task Creation and Execution on Windows",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_analytic_refs": [
                "x-mitre-analytic--4959f750-78db-4b4c-8d91-23027b386c2b"
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-detection-strategy",
            "spec_version": "2.1",
            "id": "x-mitre-detection-strategy--deb0a989-7d09-4403-b1a1-8658e36a0f9a",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0816",
                    "external_id": "DET0816"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Detection of Threat Intel Vendors",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_analytic_refs": [
                "x-mitre-analytic--23855fa6-f6d6-4a9c-a270-ea1f2830ef60"
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-detection-strategy",
            "spec_version": "2.1",
            "id": "x-mitre-detection-strategy--33ab9d0c-5671-48e6-8465-f80560909c65",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0370",
                    "external_id": "DET0370"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Recursive Enumeration of Files and Directories Across Privilege Contexts",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_analytic_refs": [
                "x-mitre-analytic--69d9d158-aa43-4b73-b9a4-f1a2dc6c13c1",
                "x-mitre-analytic--b50bf863-644a-48c2-85a3-2c633f135650",
                "x-mitre-analytic--42683860-d6df-4585-af65-31f783269f8f",
                "x-mitre-analytic--aaddc766-52bb-428b-98c4-3a742d10befa",
                "x-mitre-analytic--be6e5f23-0e29-430f-83f7-d76c58de3a2d"
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "relationship",
            "spec_version": "2.1",
            "id": "relationship--a6822af7-4da4-42c4-8649-2789a4127950",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "description": "",
            "relationship_type": "detects",
            "source_ref": "x-mitre-detection-strategy--33ab9d0c-5671-48e6-8465-f80560909c65",
            "target_ref": "attack-pattern--7bc57495-ea59-4380-be31-a64af124ef18",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_attack_spec_version": "3.3.0"
        },
        {
            "type": "relationship",
            "spec_version": "2.1",
            "id": "relationship--45c4401a-c104-4f80-93e1-bf8d64ed9711",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "description": "",
            "relationship_type": "detects",
            "source_ref": "x-mitre-detection-strategy--deb0a989-7d09-4403-b1a1-8658e36a0f9a",
            "target_ref": "attack-pattern--51e54974-a541-4fb6-a61b-0518e4c6de41",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_attack_spec_version": "3.3.0"
        },
        {
            "type": "relationship",
            "spec_version": "2.1",
            "id": "relationship--44fe6cf4-fdb3-4fa9-9855-14f3b59dc984",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "description": "",
            "relationship_type": "detects",
            "source_ref": "x-mitre-detection-strategy--c7bdd7d7-19dc-4042-8565-5e0cf4656102",
            "target_ref": "attack-pattern--005a06c6-14bf-4118-afa0-ebcd8aebb0c9",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_attack_spec_version": "3.3.0"
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--4959f750-78db-4b4c-8d91-23027b386c2b",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0441#AN1221",
                    "external_id": "AN1221"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "Analytic 1221",
            "description": "test description 1221",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "Windows"
            ],
            "x_mitre_log_source_references": [
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--f42df6f0-6395-4f0c-9376-525a031f00c3",
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4698"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--faa34cf6-cf32-4dc9-bd6a-8f7a606ff65b",
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4702"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=1"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--2b3bfe19-d59a-460d-93bb-2f546adc2d2c",
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=11"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--da85d358-741a-410d-9433-20d6269a6170",
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=13, 14"
                }
            ],
            "x_mitre_mutable_elements": [
                {
                    "field": "TimeWindow",
                    "description": "Defines threshold for grouping task creation and associated execution within suspicious time proximity."
                },
                {
                    "field": "UserContext",
                    "description": "Filters based on non-standard user accounts or execution under SYSTEM when not typical for the environment."
                },
                {
                    "field": "TaskNamePattern",
                    "description": "Allows defenders to flag obfuscated, randomized, or suspicious task names outside normal conventions."
                },
                {
                    "field": "CommandLineEntropyThreshold",
                    "description": "Flags tasks executing heavily obfuscated PowerShell or binary blobs via base64 or encoding."
                }
            ]
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--23855fa6-f6d6-4a9c-a270-ea1f2830ef60",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0816#AN1948",
                    "external_id": "AN1948"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Analytic 1948",
            "description": "test description 1948",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "PRE"
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--2385f397-5d17-4b37-ba07-bb52a52ff66c",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0360#AN1025",
                    "external_id": "AN1025"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "Analytic 1025",
            "description": "Detection of domain group enumeration through command-line utilities such as 'net group /domain' or PowerShell cmdlets, followed by suspicious access to API calls or LSASS memory.",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "Windows"
            ],
            "x_mitre_log_source_references": [
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4688"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--685f917a-e95e-4ba0-ade1-c7d354dae6e0",
                    "name": "WinEventLog:PowerShell",
                    "channel": "EventCode=4103, 4104, 4105, 4106"
                }
            ],
            "x_mitre_mutable_elements": [
                {
                    "field": "TimeWindow",
                    "description": "Adjustable window to track chained discovery activity (e.g., 5-10 minutes)."
                },
                {
                    "field": "UserContext",
                    "description": "Tune to focus on non-admin users or service accounts performing enumeration."
                },
                {
                    "field": "ProcessLineageDepth",
                    "description": "How far back the parent-child process chain is correlated."
                }
            ]
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--69d9d158-aa43-4b73-b9a4-f1a2dc6c13c1",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0370#AN1040",
                    "external_id": "AN1040"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Analytic 1040",
            "description": "test description 1040",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "Windows"
            ],
            "x_mitre_log_source_references": [
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4688"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--2b3bfe19-d59a-460d-93bb-2f546adc2d2c",
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=11"
                }
            ],
            "x_mitre_mutable_elements": [
                {
                    "field": "CommandLineRegex",
                    "description": "Allows tuning based on tools/scripts used for enumeration (e.g., tree, dir /s /b)"
                },
                {
                    "field": "UserContext",
                    "description": "Scoping for standard vs elevated or service accounts"
                },
                {
                    "field": "TimeWindow",
                    "description": "Defines burst activity over short periods (e.g., >50 directory queries in 30s)"
                }
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--b50bf863-644a-48c2-85a3-2c633f135650",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0370#AN1041",
                    "external_id": "AN1041"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Analytic 1041",
            "description": "test description 1041",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "Linux"
            ],
            "x_mitre_log_source_references": [
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
                    "name": "auditd:SYSCALL",
                    "channel": "execve"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--235b7491-2d2b-4617-9a52-3c0783680f71",
                    "name": "auditd:PATH",
                    "channel": "PATH"
                }
            ],
            "x_mitre_mutable_elements": [
                {
                    "field": "FilePathDepth",
                    "description": "Max depth of recursive access to tune noise vs anomaly"
                },
                {
                    "field": "UserContext",
                    "description": "Helpful to exclude known scripts or automation accounts"
                }
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--42683860-d6df-4585-af65-31f783269f8f",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0370#AN1042",
                    "external_id": "AN1042"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Analytic 1042",
            "description": "test description 1042",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "macOS"
            ],
            "x_mitre_log_source_references": [
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
                    "name": "macos:unifiedlog",
                    "channel": "log collect --predicate"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--235b7491-2d2b-4617-9a52-3c0783680f71",
                    "name": "fs:fsusage",
                    "channel": "Filesystem Call Monitoring"
                }
            ],
            "x_mitre_mutable_elements": [
                {
                    "field": "PredicateScope",
                    "description": "Adjust macOS unified log filter to include/exclude system paths"
                },
                {
                    "field": "TimeWindow",
                    "description": "Tune based on burst access patterns"
                }
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--aaddc766-52bb-428b-98c4-3a742d10befa",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0370#AN1043",
                    "external_id": "AN1043"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Analytic 1043",
            "description": "test description 1043",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "ESXi"
            ],
            "x_mitre_log_source_references": [
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--685f917a-e95e-4ba0-ade1-c7d354dae6e0",
                    "name": "esxi:shell",
                    "channel": "Shell Access/Command Execution"
                },
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--235b7491-2d2b-4617-9a52-3c0783680f71",
                    "name": "esxi:hostd",
                    "channel": "vSphere File API Access"
                }
            ],
            "x_mitre_mutable_elements": [
                {
                    "field": "CLICommandPattern",
                    "description": "Match on esxcli storage|filesystem commands"
                },
                {
                    "field": "AccessSource",
                    "description": "Limit alerting to non-vCenter or remote IPs"
                }
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-analytic",
            "spec_version": "2.1",
            "id": "x-mitre-analytic--be6e5f23-0e29-430f-83f7-d76c58de3a2d",
            "created": "2025-10-21T15:10:28.402Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/detectionstrategies/DET0370#AN1044",
                    "external_id": "AN1044"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:10:28.402Z",
            "name": "Analytic 1044",
            "description": "test description 1044",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_version": "1.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_domains": [
                "enterprise-attack"
            ],
            "x_mitre_platforms": [
                "Network Devices"
            ],
            "x_mitre_log_source_references": [
                {
                    "x_mitre_data_component_ref": "x-mitre-data-component--685f917a-e95e-4ba0-ade1-c7d354dae6e0",
                    "name": "networkdevice:syslog",
                    "channel": "CLI Command Logging"
                }
            ],
            "x_mitre_mutable_elements": [
                {
                    "field": "CommandWhitelist",
                    "description": "Filter allowed commands by account or IP"
                },
                {
                    "field": "SessionOrigin",
                    "description": "Tunable to restrict detection to remote terminal or Telnet/SSH"
                }
            ],
            "x_mitre_deprecated": false
        },
        {
            "type": "x-mitre-data-component",
            "spec_version": "2.1",
            "id": "x-mitre-data-component--f42df6f0-6395-4f0c-9376-525a031f00c3",
            "created": "2021-10-20T15:05:19.271Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/datacomponents/DC0001",
                    "external_id": "DC0001"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "Scheduled Job Creation",
            "description": "The establishment of a task or job that will execute at a predefined time or based on specific triggers.",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_domains": [
                "ics-attack",
                "enterprise-attack"
            ],
            "x_mitre_version": "2.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_log_sources": [
                {
                    "name": "Scheduled Job",
                    "channel": "None"
                },
                {
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4698"
                },
                {
                    "name": "linux:syslog",
                    "channel": "Execution of non-standard script or binary by cron"
                },
                {
                    "name": "WinEventLog:TaskScheduler",
                    "channel": "EventCode=106"
                }
            ]
        },
        {
            "type": "x-mitre-data-component",
            "spec_version": "2.1",
            "id": "x-mitre-data-component--faa34cf6-cf32-4dc9-bd6a-8f7a606ff65b",
            "created": "2021-10-20T15:05:19.271Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/datacomponents/DC0012",
                    "external_id": "DC0012"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-10-21T15:14:38.292Z",
            "name": "Scheduled Job Modification",
            "description": "Changes made to an existing scheduled job, including modifications to its execution parameters, command payload, or execution timing.",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_domains": [
                "ics-attack",
                "enterprise-attack"
            ],
            "x_mitre_version": "2.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_log_sources": [
                {
                    "name": "Scheduled Job",
                    "channel": "None"
                },
                {
                    "name": "auditd:CONFIG_CHANGE",
                    "channel": "/var/log/audit/audit.log"
                },
                {
                    "name": "m365:exchange",
                    "channel": "Remove-InboxRule, Clear-Mailbox"
                },
                {
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4702"
                }
            ]
        },
        {
            "type": "x-mitre-data-component",
            "spec_version": "2.1",
            "id": "x-mitre-data-component--3d20385b-24ef-40e1-9f56-f39750379077",
            "created": "2021-10-20T15:05:19.272Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/datacomponents/DC0032",
                    "external_id": "DC0032"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "Process Creation",
            "description": "Refers to the event in which a new process (executable) is initialized by an operating system. This can involve parent-child process relationships, process arguments, and environmental variables. Monitoring process creation is crucial for detecting malicious behaviors, such as execution of unauthorized binaries, scripting abuse, or privilege escalation attempts.. ",
            "x_mitre_data_source_ref": "",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_domains": [
                "ics-attack",
                "mobile-attack",
                "enterprise-attack"
            ],
            "x_mitre_version": "2.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_log_sources": [
                {
                    "name": "Process",
                    "channel": "None"
                },
                {
                    "name": "auditd:SYSCALL",
                    "channel": "execve"
                }
            ]
        },
        {
            "type": "x-mitre-data-component",
            "spec_version": "2.1",
            "id": "x-mitre-data-component--2b3bfe19-d59a-460d-93bb-2f546adc2d2c",
            "created": "2021-10-20T15:05:19.273Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/datacomponents/DC0039",
                    "external_id": "DC0039"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "File Creation",
            "description": "A new file is created on a system or network storage. This action often signifies an operation such as saving a document, writing data, or deploying a file. Logging these events helps identify legitimate or potentially malicious file creation activities. Examples include logging file creation events (e.g., Sysmon Event ID 11 or Linux auditd logs). ",
            "x_mitre_data_source_ref": "",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_domains": [
                "ics-attack",
                "enterprise-attack"
            ],
            "x_mitre_version": "2.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_log_sources": [
                {
                    "name": "File",
                    "channel": "None"
                },
                {
                    "name": "WinEventLog:Sysmon",
                    "channel": "EventCode=11"
                },
                {
                    "name": "auditd:SYSCALL",
                    "channel": "creat"
                }
            ]
        },
        {
            "type": "x-mitre-data-component",
            "spec_version": "2.1",
            "id": "x-mitre-data-component--da85d358-741a-410d-9433-20d6269a6170",
            "created": "2021-10-20T15:05:19.273Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/datacomponents/DC0063",
                    "external_id": "DC0063"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "Windows Registry Key Modification",
            "description": "test description",
            "x_mitre_data_source_ref": "",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_domains": [
                "ics-attack",
                "enterprise-attack"
            ],
            "x_mitre_version": "2.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_log_sources": [
                {
                    "name": "Windows Registry",
                    "channel": "None"
                },
                {
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4657"
                },
                {
                    "name": "WinEventLog:Security",
                    "channel": "EventCode=4663, 4670, 4656"
                }
            ]
        },
        {
            "type": "x-mitre-data-component",
            "spec_version": "2.1",
            "id": "x-mitre-data-component--685f917a-e95e-4ba0-ade1-c7d354dae6e0",
            "created": "2021-10-20T15:05:19.273Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/datacomponents/DC0064",
                    "external_id": "DC0064"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "Command Execution",
            "description": "test desc",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_domains": [
                "ics-attack",
                "mobile-attack",
                "enterprise-attack"
            ],
            "x_mitre_version": "2.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_log_sources": [
                {
                    "name": "Command",
                    "channel": "None"
                },
                {
                    "name": "auditd:SYSCALL",
                    "channel": "execution of realmd, samba-tool, or ldapmodify with user-related arguments"
                },
                {
                    "name": "macos:unifiedlog",
                    "channel": "dsconfigad or dscl with create or append options for AD-bound users"
                }
            ]
        },
        {
            "type": "x-mitre-data-component",
            "spec_version": "2.1",
            "id": "x-mitre-data-component--235b7491-2d2b-4617-9a52-3c0783680f71",
            "created": "2021-10-20T15:05:19.273Z",
            "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "revoked": false,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/datacomponents/DC0055",
                    "external_id": "DC0055"
                }
            ],
            "object_marking_refs": [
                "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
            ],
            "modified": "2025-11-12T22:03:39.105Z",
            "name": "File Access",
            "description": "test desc",
            "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
            "x_mitre_deprecated": false,
            "x_mitre_domains": [
                "ics-attack",
                "enterprise-attack"
            ],
            "x_mitre_version": "2.0",
            "x_mitre_attack_spec_version": "3.3.0",
            "x_mitre_log_sources": [
                {
                    "name": "File",
                    "channel": "None"
                },
                {
                    "name": "m365:unified",
                    "channel": "FileAccessed, MailboxAccessed"
                },
                {
                    "name": "auditd:SYSCALL",
                    "channel": "open, read, or stat of browser config files"
                }
            ]
        }
    ]
}
'''
)

@pytest.fixture
def example_attack_pattern():
    return json.loads('''
    {
        "type": "attack-pattern",
        "spec_version": "2.1",
        "id": "attack-pattern--0042a9f5-f053-4769-b3ef-9ad018dfa298",
        "created": "2020-01-14T17:18:32.126Z",
        "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
        "external_references": [
            {
                "source_name": "mitre-attack",
                "url": "https://attack.mitre.org/techniques/T1055/011",
                "external_id": "T1055.011"
            },
            {
                "source_name": "Microsoft Window Classes",
                "description": "Microsoft. (n.d.). About Window Classes. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms633574.aspx"
            },
            {
                "source_name": "Microsoft GetWindowLong function",
                "description": "Microsoft. (n.d.). GetWindowLong function. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms633584.aspx"
            },
            {
                "source_name": "Microsoft SetWindowLong function",
                "description": "Microsoft. (n.d.). SetWindowLong function. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms633591.aspx"
            },
            {
                "source_name": "Elastic Process Injection July 2017",
                "description": "Hosseini, A. (2017, July 18). Ten Process Injection Techniques: A Technical Survey Of Common And Trending Process Injection Techniques. Retrieved December 7, 2017.",
                "url": "https://www.endgame.com/blog/technical-blog/ten-process-injection-techniques-technical-survey-common-and-trending-process"
            },
            {
                "source_name": "MalwareTech Power Loader Aug 2013",
                "description": "MalwareTech. (2013, August 13). PowerLoader Injection Something truly amazing. Retrieved December 16, 2017.",
                "url": "https://www.malwaretech.com/2013/08/powerloader-injection-something-truly.html"
            },
            {
                "source_name": "WeLiveSecurity Gapz and Redyms Mar 2013",
                "description": "Matrosov, A. (2013, March 19). Gapz and Redyms droppers based on Power Loader code. Retrieved December 16, 2017.",
                "url": "https://www.welivesecurity.com/2013/03/19/gapz-and-redyms-droppers-based-on-power-loader-code/"
            },
            {
                "source_name": "Microsoft SendNotifyMessage function",
                "description": "Microsoft. (n.d.). SendNotifyMessage function. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms644953.aspx"
            }
        ],
        "object_marking_refs": [
            "marking-definition--fa42a846-8d90-4e51-bc29-71d5b4802168"
        ],
        "modified": "2025-04-25T14:45:37.275Z",
        "name": "Extra Window Memory Injection",
        "description": "dummy description",
        "kill_chain_phases": [
            {
                "kill_chain_name": "mitre-attack",
                "phase_name": "defense-evasion"
            },
            {
                "kill_chain_name": "mitre-attack",
                "phase_name": "privilege-escalation"
            }
        ],
        "x_mitre_attack_spec_version": "3.2.0",
        "x_mitre_deprecated": false,
        "x_mitre_detection": "Monitor for API calls related to enumerating and manipulating EWM such as GetWindowLong (Citation: Microsoft GetWindowLong function) and SetWindowLong (Citation: Microsoft SetWindowLong function). Malware associated with this technique have also used SendNotifyMessage (Citation: Microsoft SendNotifyMessage function) to trigger the associated window procedure and eventual malicious injection. (Citation: Elastic Process Injection July 2017)",
        "x_mitre_domains": [
            "enterprise-attack"
        ],
        "x_mitre_is_subtechnique": true,
        "x_mitre_modified_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
        "x_mitre_platforms": [
            "Windows"
        ],
        "x_mitre_version": "1.1",
        "x_mitre_data_sources": [
            "Process: OS API Execution"
        ]
    }
    ''')

@pytest.fixture
def example_attack_pattern_no_tid_ref():
    return json.loads('''
    {
        "type": "attack-pattern",
        "spec_version": "2.1",
        "id": "attack-pattern--0042a9f5-f053-4769-b3ef-9ad018dfa298",
        "created": "2020-01-14T17:18:32.126Z",
        "created_by_ref": "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5",
        "external_references": [
            {
                "source_name": "Microsoft Window Classes",
                "description": "Microsoft. (n.d.). About Window Classes. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms633574.aspx"
            },
            {
                "source_name": "Microsoft GetWindowLong function",
                "description": "Microsoft. (n.d.). GetWindowLong function. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms633584.aspx"
            },
            {
                "source_name": "Microsoft SetWindowLong function",
                "description": "Microsoft. (n.d.). SetWindowLong function. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms633591.aspx"
            },
            {
                "source_name": "Elastic Process Injection July 2017",
                "description": "Hosseini, A. (2017, July 18). Ten Process Injection Techniques: A Technical Survey Of Common And Trending Process Injection Techniques. Retrieved December 7, 2017.",
                "url": "https://www.endgame.com/blog/technical-blog/ten-process-injection-techniques-technical-survey-common-and-trending-process"
            },
            {
                "source_name": "MalwareTech Power Loader Aug 2013",
                "description": "MalwareTech. (2013, August 13). PowerLoader Injection Something truly amazing. Retrieved December 16, 2017.",
                "url": "https://www.malwaretech.com/2013/08/powerloader-injection-something-truly.html"
            },
            {
                "source_name": "WeLiveSecurity Gapz and Redyms Mar 2013",
                "description": "Matrosov, A. (2013, March 19). Gapz and Redyms droppers based on Power Loader code. Retrieved December 16, 2017.",
                "url": "https://www.welivesecurity.com/2013/03/19/gapz-and-redyms-droppers-based-on-power-loader-code/"
            },
            {
                "source_name": "Microsoft SendNotifyMessage function",
                "description": "Microsoft. (n.d.). SendNotifyMessage function. Retrieved December 16, 2017.",
                "url": "https://msdn.microsoft.com/library/windows/desktop/ms644953.aspx"
            }
        ]
    }
    ''')

class TestAttackMapper:
    def test_extract_tid(self, example_attack_pattern, example_attack_pattern_no_tid_ref):
        assert attack_mapper._extract_tid(example_attack_pattern) == 'T1055.011'
        assert attack_mapper._extract_tid(example_attack_pattern_no_tid_ref) is None

    def test_parent_tid(self):
        assert attack_mapper._parent_tid('T1000.123') == 'T1000'
        assert attack_mapper._parent_tid('t1000.123') == 'T1000'
        assert attack_mapper._parent_tid('T1000') == 'T1000'
        assert attack_mapper._parent_tid('t1000') == 'T1000'

    def test_normalize_analytic(self, example_analytic, example_data_comp_by_id):
        want_row = {
            'an_id': 'AN1025',
            'id': 'x-mitre-analytic--2385f397-5d17-4b37-ba07-bb52a52ff66c',
            'name': 'Analytic 1025',
            'platform': 'windows',
            'platforms': ['windows'],
            'statement': 'test analytic description',
            'tunables': [
                {
                    'field': 'TimeWindow',
                    'description': 'Adjustable window to track chained discovery activity (e.g., 5-10 minutes).'
                },
                {
                    'field': 'UserContext',
                    'description': 'Tune to focus on non-admin users or service accounts performing enumeration.'
                },
                {
                    'field': 'ProcessLineageDepth',
                    'description': 'How far back the parent-child process chain is correlated.'
                }
            ]
        }
        want_dc_elements = [
            {
                "name": "WinEventLog:Security",
                "channel": "EventCode=4688",
                "data_component": "Process Creation"
            },
            {
                "name": "WinEventLog:PowerShell",
                "channel": "EventCode=4103, 4104, 4105, 4106",
                "data_component": "Command Execution"
            },
        ]
        row, dc_elements = attack_mapper._normalize_analytic(example_analytic, example_data_comp_by_id)
        assert row == want_row
        assert want_dc_elements == want_dc_elements

    def test_index_bundle_v18(self, example_bundle_v18, example_techniques_by_id, example_strategies_by_tid, example_analytics_by_tid):
        want = {
            'techniques_by_id': example_techniques_by_id,
            'strategies_by_tid': example_strategies_by_tid,
            'analytics_by_tid': example_analytics_by_tid,
        }
        assert attack_mapper.index_bundle(example_bundle_v18) == want

