import html
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
                    # PATCH: escape technique_name before placing in graph node
                    safe_technique_name = html.escape(str(link.ability.technique_name or ''))
                    graph_output['nodes'].append(dict(type='link', name=safe_technique_name, id=link_graph_id,
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
                    # PATCH: escape p before placing into graph node name and attrs
                    p_safe = html.escape(str(p))
                    p_attrs = {prop: p_safe}
                    p_attrs.update({lnk.unique: lnk.ability.name for lnk in lnks})
                    graph_output['nodes'].append(dict(type=prop, name=p_safe, id=prop_graph_id, operation=op_id,
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
                    contact=getattr(agent, 'contact', 'HTTP'),
                    is_pivot=bool(getattr(agent, 'proxy_receivers', None)),
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
        
        # --- Steps by host ---
        # Also build an ordered list of (step_index, paw, step_data) for replay sequencing
        replay_sequence = []  # ordered list of {paw, step, index}
        for op in operations:
            for agent in (op.agents or []):
                paw = agent.paw
                if paw not in steps_by_host:
                    steps_by_host[paw] = []
            step_idx = 0
            for link in (op.chain or []):
                if link.cleanup:
                    continue
                paw = link.paw
                if paw not in steps_by_host:
                    steps_by_host[paw] = []
                step_data = dict(
                    id=str(link.id),
                    ability_name=link.ability.name,
                    tactic=link.ability.tactic,
                    technique_id=link.ability.technique_id,
                    technique_name=link.ability.technique_name,
                    status=link.status,
                    finish=link.finish or '',
                    facts_count=len([f for f in link.facts if f.score > 0]),
                    command=link.command,
                )
                steps_by_host[paw].append(step_data)
                replay_sequence.append(dict(paw=paw, step=step_data, index=step_idx))
                step_idx += 1
                if paw in hosts:
                    hosts[paw]['step_count'] = len(steps_by_host[paw])
        # --- Build edges from chain order + origin_link_id ---
        # First: explicit lateral movement via origin_link_id
        agents_with_origin = set()
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
                            agents_with_origin.add(agent.paw)
        # Second: agents without origin_link_id connect directly to C2
        # Only agents with an explicit origin_link_id (lateral movement) get
        # agent-to-agent edges (handled above). All others beacon to C2 directly.
        seen_paws = set()
        edge_pairs = set()
        for item in replay_sequence:
            paw = item['paw']
            if paw not in seen_paws:
                if paw not in agents_with_origin:
                    edge_pair = ('c2', paw)
                    if edge_pair not in edge_pairs:
                        edges.append(dict(source='c2', target=paw,
                                          type='initial_access', technique='Initial Access'))
                        edge_pairs.add(edge_pair)
                seen_paws.add(paw)
        # Third: fallback — if no chain at all, create edges from agent order
        # This handles fabricated operations where agents exist but no steps ran
        if not replay_sequence and not edges:
            agent_paws = [paw for paw in hosts if paw != 'c2']
            if agent_paws:
                # C2 → first agent
                edges.append(dict(source='c2', target=agent_paws[0],
                                  type='initial_access', technique='Initial Access'))
                # Chain remaining agents sequentially
                for i in range(1, len(agent_paws)):
                    edges.append(dict(source=agent_paws[i-1], target=agent_paws[i],
                                      type='lateral_movement', technique='Inferred from agent order'))
                # Also generate a synthetic replay_sequence so play button works
                for i, paw in enumerate(agent_paws):
                    replay_sequence.append(dict(
                        paw=paw,
                        step=dict(
                            id=f'synthetic-{i}',
                            ability_name=f'Agent on {hosts[paw]["hostname"]}',
                            tactic='initial-access' if i == 0 else 'lateral-movement',
                            technique_id='',
                            technique_name='',
                            status=0,
                            finish='',
                            facts_count=0,
                            command='',
                        ),
                        index=i,
                    ))
        # --- Discovered hosts (from operation facts + knowledge svc) ---
        discovered_ips = set()
        knowledge_svc = self.services.get('knowledge_svc')
        for op in operations:
            all_facts = list(await op.all_facts())
            # Also query knowledge_svc for facts in the operation's source
            source = getattr(op, 'source', None)
            source_id = str(getattr(source, 'id', '')) if source else ''
            if knowledge_svc and source_id:
                try:
                    kb_facts = await knowledge_svc.get_facts(
                        criteria=dict(source=source_id, trait='remote.host.ip')
                    )
                    for kf in (kb_facts or []):
                        all_facts.append(kf)
                    kb_fqdn = await knowledge_svc.get_facts(
                        criteria=dict(source=source_id, trait='remote.host.fqdn')
                    )
                    for kf in (kb_fqdn or []):
                        all_facts.append(kf)
                except Exception:
                    pass
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
        # Each host goes in ONE subnet only (its primary/first non-docker IP).
        # Docker bridge IPs (172.17-31.x.x) are deprioritized.
        subnet_map = {}  # cidr -> set of host_ids
        assigned_hosts = set()
        for host_id, host in hosts.items():
            if host_id == 'c2':
                continue
            ips = host.get('ips') or []
            # Pick best IP: prefer non-172.1x (non-Docker bridge) IPs
            primary_ip = None
            for ip in ips:
                subnet = self._ip_to_subnet(ip)
                if subnet and not ip.startswith('172.'):
                    primary_ip = ip
                    break
            if not primary_ip:
                for ip in ips:
                    subnet = self._ip_to_subnet(ip)
                    if subnet:
                        primary_ip = ip
                        break
            if primary_ip:
                subnet_cidr = self._ip_to_subnet(primary_ip)
                subnet_map.setdefault(subnet_cidr, set()).add(host_id)
                assigned_hosts.add(host_id)
                # Store primary IP on host for display
                host['primary_ip'] = primary_ip
        # Hosts with no valid IP go to "Unknown" subnet
        ungrouped = [hid for hid in hosts if hid != 'c2' and hid not in assigned_hosts]
        if ungrouped:
            subnet_map['Unknown'] = set(ungrouped)
        # Also include empty subnets from agent secondary IPs (networks the agent can see)
        for host_id, host in hosts.items():
            if host_id == 'c2':
                continue
            for ip in (host.get('ips') or []):
                subnet_cidr = self._ip_to_subnet(ip)
                if subnet_cidr and subnet_cidr not in subnet_map:
                    subnet_map[subnet_cidr] = set()  # empty subnet — visible but no hosts
        # Order subnets by chain appearance (first agent in each subnet determines position)
        subnet_order = []
        seen_subnets = set()
        # First pass: order by replay_sequence (chain order)
        for item in replay_sequence:
            paw = item['paw']
            host = hosts.get(paw)
            if host and host.get('primary_ip'):
                cidr = self._ip_to_subnet(host['primary_ip'])
                if cidr and cidr not in seen_subnets:
                    subnet_order.append(cidr)
                    seen_subnets.add(cidr)
        # Add any remaining subnets (empty ones, etc.) alphabetically
        for cidr in sorted(subnet_map.keys()):
            if cidr not in seen_subnets:
                subnet_order.append(cidr)
                seen_subnets.add(cidr)
        subnets = [
            dict(cidr=cidr, label=cidr, hosts=sorted(subnet_map.get(cidr, set())))
            for cidr in subnet_order
        ]
        # --- Compute path_to_c2 for each host (for beacon animation) ---
        # Build parent map from edges: target → source
        parent_map = {}
        for e in edges:
            if e['target'] != 'c2':
                parent_map[e['target']] = e['source']
        path_to_c2 = {}
        for host_id in hosts:
            if host_id == 'c2':
                continue
            path = [host_id]
            current = host_id
            visited = set()
            while current in parent_map and current not in visited:
                visited.add(current)
                current = parent_map[current]
                path.append(current)
            path_to_c2[host_id] = path  # e.g. ['db01', 'dc01', 'proxy01', 'web01', 'c2']
        return dict(
            subnets=subnets,
            hosts=hosts,
            edges=edges,
            steps_by_host=steps_by_host,
            replay_sequence=replay_sequence,
            path_to_c2=path_to_c2,
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