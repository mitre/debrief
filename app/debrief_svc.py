import logging

from app.utility.base_service import BaseService


class DebriefService(BaseService):
    def __init__(self, services):
        self.services = services
        self.app_svc = services.get('app_svc')
        self.file_svc = services.get('file_svc')
        self.data_svc = services.get('data_svc')
        self.log = logging.getLogger('debrief_svc')

    async def build_steps_d3(self, operation_ids):
        graph_output = dict(nodes=[], links=[])
        id_store = dict(c2=0)
        graph_output['nodes'].append(dict(name="C2 Server", type='c2', label='server', id=0, img='server',
                                          attrs={k: v for k, v in self.get_config().items() if k.startswith('app.')}))

        operations = []
        for op_id in operation_ids:
            matches = await self.data_svc.locate('operations', match=dict(id=op_id))
            if matches:
                operations.append(matches[0])

        for operation in operations:
            # Add operation node
            graph_output['nodes'].append(dict(name=operation.name, type='operation', id=operation.id, img='operation',
                                              timestamp=self._format_timestamp(operation.created)))

            # Add agents for this operation
            agents = [x for x in operation.agents if x]
            self._add_agents_to_d3(agents, id_store, graph_output)
            for agent in agents:
                graph_output['links'].append(dict(source=operation.id,
                                                  target=id_store['agent' + agent.unique],
                                                  type='has_agent'))

            # Add steps
            previous_link_graph_id = None
            for link in operation.chain:
                link_graph_id = id_store['link' + link.unique] = max(id_store.values()) + 1
                display_name = link.ability.name + (' (cleanup)' if link.cleanup else '')
                graph_output['nodes'].append(dict(type='link', name='link:'+link.unique, id=link_graph_id,
                                                  status=link.status, operation=operation.id, img=link.ability.tactic,
                                                  attrs=dict(status=link.status, name=display_name),
                                                  timestamp=self._format_timestamp(link.created)))

                if not previous_link_graph_id:
                    graph_output['links'].append(dict(source=operation.id, target=link_graph_id, type='next_link'))
                else:
                    graph_output['links'].append(dict(source=previous_link_graph_id, target=link_graph_id,
                                                      type='next_link'))
                previous_link_graph_id = link_graph_id

                # Link the step to the corresponding agent
                for agent in agents:
                    if agent.paw == link.paw:
                        graph_output['links'].append(dict(source=id_store['agent' + agent.unique], target=link_graph_id,
                                                          type='next_link'))

        return graph_output

    async def build_attackpath_d3(self, operation_ids):
        graph_output = dict(nodes=[], links=[])
        id_store = dict(c2=0)
        graph_output['nodes'].append(dict(name="C2 Server", type='c2', label='server', id=0, img='server',
                                          attrs={config: value for config, value in self.get_config().items() if
                                                 config.startswith('app.')}))

        operations = [op for op_id in operation_ids for op in await self.data_svc.locate('operations',
                                                                                         match=dict(id=op_id))]

        agents = [x for xs in map(lambda o: o.agents, operations) for x in xs]
        self._add_agents_to_d3(agents, id_store, graph_output)

        for agent in agents:
            if agent.origin_link_id:
                operation = await self.app_svc.find_op_with_link(agent.origin_link_id)
                if operation in operations:
                    link = next(lnk for lnk in operation.chain if lnk.id == agent.origin_link_id)
                    link_graph_id = id_store['link' + link.unique] = max(id_store.values()) + 1
                    graph_output['nodes'].append(dict(type='link', name=link.ability.technique_name, id=link_graph_id,
                                                      status=link.status, operation=operation.id,
                                                      img=link.ability.tactic,
                                                      attrs=dict(status=link.status, name=link.ability.name),
                                                      timestamp=self._format_timestamp(link.created)))
                    graph_output['links'].append(dict(source=id_store['agent' + link.paw], target=link_graph_id,
                                                      type='next_link'))
                    graph_output['links'].append(dict(source=link_graph_id, target=id_store['agent' + agent.paw],
                                                      type='next_link'))
        return graph_output

    async def build_fact_d3(self, operation_ids):
        graph_output = dict(nodes=[], links=[])
        id_store = dict(default=0)

        for op_id in operation_ids:
            operation = (await self.data_svc.locate('operations', match=dict(id=op_id)))[0]
            graph_output['nodes'].append(dict(name=operation.name, type='operation', id=op_id, img='operation',
                                              timestamp=self._format_timestamp(operation.created)))
            op_nodes, op_links = [], []
            all_facts = await operation.all_facts()
            for fact in all_facts:
                id_store['fact' + fact.unique] = node_id = max(id_store.values()) + 1
                node = dict(name=fact.trait, id=node_id, type='fact', operation=op_id,
                            attrs=self._get_pub_attrs(fact), img='fact',
                            timestamp=fact.created.strftime('%Y-%m-%dT%H:%M:%S'))
                op_nodes.append(node)

                if fact in operation.source.facts:
                    d3_link = dict(source=op_id, target=node_id, type='relationship')
                    op_links.append(d3_link)

            all_relationships = await operation.all_relationships()
            for relationship in all_relationships:
                if relationship.edge and relationship.target.value:
                    d3_link = dict(source=id_store.get('fact' + relationship.source.unique),
                                   target=id_store.get('fact' + relationship.target.unique),
                                   type='relationship')
                    op_links.append(d3_link)

            self._link_nontargeted_facts(op_nodes, op_links, op_id)

            graph_output['nodes'].extend([n for n in op_nodes if n not in graph_output['nodes']])
            graph_output['links'].extend([lnk for lnk in op_links if lnk not in graph_output['links']])

        return graph_output

    async def build_tactic_d3(self, operation_ids):
        return await self._build_prop_d3(operation_ids, 'tactic')

    async def build_technique_d3(self, operation_ids):
        return await self._build_prop_d3(operation_ids, 'technique_name')

    async def _build_prop_d3(self, operation_ids, prop):
        graph_output = dict(nodes=[], links=[])
        id_store = dict(default=0)

        for op_id in operation_ids:
            operation = (await self.data_svc.locate('operations', match=dict(id=op_id)))[0]
            graph_output['nodes'].append(dict(name=operation.name, type='operation', id=op_id, img='operation',
                                              timestamp=self._format_timestamp(operation.created)))
            previous_prop_graph_id = None
            if len(operation.chain) > 0:
                for p, lnks in self._get_by_prop_order(operation.chain, prop):
                    i = max(id_store.values()) + 1
                    prop_graph_id = id_store[prop + p + str(i)] = i
                    p_attrs = {prop: p}
                    p_attrs.update({lnk.unique: lnk.ability.name for lnk in lnks})
                    graph_output['nodes'].append(dict(type=prop, name=p, id=prop_graph_id, operation=op_id,
                                                      attrs=p_attrs, img=p,
                                                      timestamp=self._format_timestamp(lnks[0].created)))

                    if not previous_prop_graph_id:
                        graph_output['links'].append(dict(source=op_id, target=prop_graph_id, type='next_link'))
                    else:
                        graph_output['links'].append(
                            dict(source=previous_prop_graph_id, target=prop_graph_id, type='next_link'))
                    previous_prop_graph_id = prop_graph_id
        return graph_output

    @staticmethod
    def _add_agents_to_d3(agents, id_store, graph_output):
        for agent in agents:
            if 'agent' + agent.unique not in id_store.keys():
                id_store['agent' + agent.unique] = max(id_store.values()) + 1
                node = dict(name=f'{agent.paw} ({agent.display_name})', id=id_store['agent' + agent.unique], group=agent.group,
                            type='agent', img=agent.platform, timestamp=agent.created.strftime('%Y-%m-%dT%H:%M:%S'),
                            attrs=dict(host=agent.host, group=agent.group, platform=agent.platform, paw=agent.paw))
                graph_output['nodes'].append(node)

                link = dict(source=0, target=id_store['agent' + agent.unique], type='agent_contact')
                graph_output['links'].append(link)

    @staticmethod
    def generate_ttps(operations, key_by_tid=False):
        ttps = dict()
        for op in operations:
            for link in op.chain:
                if not link.cleanup:
                    tactic_name = link.ability.tactic
                    if tactic_name not in ttps.keys():
                        ttps[tactic_name] = DebriefService._generate_new_tactic_entry(op, tactic_name, link, key_by_tid=key_by_tid)
                    else:
                        DebriefService._update_tactic_entry(ttps[tactic_name], op.name, link, key_by_tid=key_by_tid)
        return dict(sorted(ttps.items()))

    @staticmethod
    def _generate_new_tactic_entry(operation, tactic_name, link, key_by_tid=False):
        exact_tid = link.ability.technique_id.strip().upper()
        return dict(
            name=tactic_name,
            techniques={exact_tid: link.ability.technique_name} if key_by_tid else {link.ability.technique_name: exact_tid},
            steps={operation.name: [link.ability.name]}
        )

    @staticmethod
    def _update_tactic_entry(tactic_entry_dict, op_name, link, key_by_tid=False):
        technique_info = tactic_entry_dict['techniques']
        step_info = tactic_entry_dict['steps']
        exact_tid = link.ability.technique_id.strip().upper()
        if not key_by_tid and link.ability.technique_name not in technique_info.keys():
            technique_info[link.ability.technique_name] = exact_tid
        if key_by_tid and exact_tid not in technique_info.keys():
            technique_info[exact_tid] = link.ability.technique_name
        if op_name not in step_info.keys():
            step_info[op_name] = [link.ability.name]
        elif link.ability.name not in step_info[op_name]:
            step_info[op_name].append(link.ability.name)

    @staticmethod
    def _get_pub_attrs(fact):
        filtered_fact = {k: v for k, v in vars(fact).items() if not k.startswith('_')}
        filtered_fact['origin_type'] = filtered_fact['origin_type'].name
        temp = []
        for lnk in filtered_fact['links']:
            temp.append(lnk)
        filtered_fact['links'] = temp
        return filtered_fact

    @staticmethod
    def _get_by_prop_order(chain, prop):
        current = getattr(chain[0].ability, prop)
        ordered = [(current, [chain[0]])]
        for lnk in chain[1:]:
            if getattr(lnk.ability, prop) != current and lnk.cleanup == 0:
                current = getattr(lnk.ability, prop)
                ordered.append((current, [lnk]))
            else:
                next(p for p in ordered if p[0] == current)[1].append(lnk)
        return ordered

    @staticmethod
    def _format_timestamp(timestamp):
        return timestamp.replace(" ", "T")

    @staticmethod
    def _link_nontargeted_facts(op_nodes, op_links, op_id):
        for n in op_nodes:
            target_links = [lnk for lnk in op_links if lnk['target'] == n['id']]
            if not target_links:
                d3_link = dict(source=op_id, target=n['id'], type='relationship')
                op_links.append(d3_link)

    async def build_topology(self, operation_ids):
        """Build network topology data: hosts, subnets, edges, steps grouped by host."""
        operations = []
        for op_id in operation_ids:
            matches = await self.data_svc.locate('operations', match=dict(id=op_id))
            if matches:
                operations.append(matches[0])

        hosts = {}       # keyed by agent paw or discovered-ip
        edges = []
        steps_by_host = {}
        all_ips = {}     # ip -> host_id mapping for subnet grouping

        # --- Compromised hosts (agents) ---
        paw_to_host = {}
        for op in operations:
            for agent in (op.agents or []):
                paw = agent.paw
                if paw in hosts:
                    continue
                ips = list(getattr(agent, 'host_ip_addrs', []) or [])
                hosts[paw] = dict(
                    id=paw,
                    hostname=agent.host,
                    ips=ips,
                    platform=agent.platform,
                    compromised=True,
                    agent_paw=paw,
                    privilege=getattr(agent, 'privilege', ''),
                    username=getattr(agent, 'username', ''),
                    step_count=0,
                    origin_agent=None,
                )
                paw_to_host[paw] = paw
                for ip in ips:
                    all_ips[ip] = paw

        # --- C2 node ---
        c2_config = {k: v for k, v in self.get_config().items() if k.startswith('app.')}
        hosts['c2'] = dict(
            id='c2',
            hostname='C2 Server',
            ips=[c2_config.get('app.contact.http', '')],
            platform='server',
            compromised=True,
            agent_paw=None,
            privilege='',
            username='',
            step_count=0,
            origin_agent=None,
        )

        # --- Steps by host + edges from initial access ---
        for op in operations:
            for agent in (op.agents or []):
                paw = agent.paw
                if paw not in steps_by_host:
                    steps_by_host[paw] = []

                # Initial access edge (C2 → agent)
                if not agent.origin_link_id:
                    edges.append(dict(
                        source='c2', target=paw,
                        type='initial_access', technique='Initial Access',
                    ))

            for link in (op.chain or []):
                if link.cleanup:
                    continue
                paw = link.paw
                if paw not in steps_by_host:
                    steps_by_host[paw] = []
                steps_by_host[paw].append(dict(
                    id=str(link.id),
                    ability_name=link.ability.name,
                    tactic=link.ability.tactic,
                    technique_id=link.ability.technique_id,
                    technique_name=link.ability.technique_name,
                    status=link.status,
                    finish=link.finish or '',
                    facts_count=len([f for f in link.facts if f.score > 0]),
                    command=link.command,
                ))
                if paw in hosts:
                    hosts[paw]['step_count'] = len(steps_by_host[paw])

        # --- Lateral movement edges (origin_link_id) ---
        for op in operations:
            for agent in (op.agents or []):
                if agent.origin_link_id:
                    origin_link = next((lnk for lnk in op.chain if lnk.id == agent.origin_link_id), None)
                    if origin_link:
                        source_paw = origin_link.paw
                        if source_paw in hosts:
                            hosts[agent.paw]['origin_agent'] = source_paw
                            edges.append(dict(
                                source=source_paw, target=agent.paw,
                                type='lateral_movement',
                                technique=f'{origin_link.ability.technique_id} {origin_link.ability.technique_name}',
                            ))

        # --- Discovered hosts (from facts) ---
        discovered_ips = set()
        for op in operations:
            all_facts = await op.all_facts()
            for fact in all_facts:
                trait = getattr(fact, 'trait', '') or ''
                value = str(getattr(fact, 'value', '') or '')
                if not value:
                    continue

                # remote.host.ip or remote.host.fqdn → discovered host
                if trait == 'remote.host.ip' and value not in all_ips and value not in discovered_ips:
                    discovered_ips.add(value)
                    host_id = f'discovered-{value}'
                    hosts[host_id] = dict(
                        id=host_id,
                        hostname=value,
                        ips=[value],
                        platform='unknown',
                        compromised=False,
                        agent_paw=None,
                        privilege='',
                        username='',
                        step_count=0,
                        origin_agent=None,
                        discovered_by=list(getattr(fact, 'collected_by', []) or []),
                        intel=[],
                    )
                    all_ips[value] = host_id

                # Collect intel for discovered hosts
                if trait.startswith('remote.host.') and value in all_ips:
                    hid = all_ips[value]
                    if hid.startswith('discovered-') and 'intel' in hosts.get(hid, {}):
                        hosts[hid]['intel'].append(dict(trait=trait, value=value))

        # --- Build subnets from IPs ---
        subnet_map = {}  # cidr -> set of host_ids
        for host_id, host in hosts.items():
            if host_id == 'c2':
                continue
            for ip in (host.get('ips') or []):
                subnet = self._ip_to_subnet(ip)
                if subnet:
                    subnet_map.setdefault(subnet, set()).add(host_id)

        # Hosts with no IP go to "Unknown" subnet
        hosts_with_subnet = set()
        for hids in subnet_map.values():
            hosts_with_subnet.update(hids)
        ungrouped = [hid for hid in hosts if hid != 'c2' and hid not in hosts_with_subnet]
        if ungrouped:
            subnet_map['Unknown'] = set(ungrouped)

        subnets = [
            dict(cidr=cidr, label=cidr, hosts=sorted(hids))
            for cidr, hids in sorted(subnet_map.items())
        ]

        return dict(
            subnets=subnets,
            hosts=hosts,
            edges=edges,
            steps_by_host=steps_by_host,
        )

    @staticmethod
    def _ip_to_subnet(ip_str):
        """Convert an IP string to a /24 subnet string."""
        try:
            parts = ip_str.strip().split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                return f'{parts[0]}.{parts[1]}.{parts[2]}.0/24'
        except (ValueError, AttributeError):
            pass
        return None
