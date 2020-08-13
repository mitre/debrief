import logging


class DebriefService:
    def __init__(self, services):
        self.services = services
        self.file_svc = services.get('file_svc')
        self.data_svc = services.get('data_svc')
        self.log = logging.getLogger('debrief_svc')

    async def build_operation_d3(self, operation_ids):
        print(operation_ids)
        graph_output = dict(nodes=[], links=[])
        id_store = dict(c2=0)
        graph_output['nodes'].append(dict(name="C2", type='c2', label='server', id=0, img='server'))

        agents = await self.data_svc.locate('agents')
        for agent in agents:
            if 'agent' + agent.unique not in id_store.keys():
                id_store['agent' + agent.unique] = max(id_store.values()) + 1
                node = dict(name=agent.display_name,
                            id=id_store['agent' + agent.unique],
                            group=agent.group,
                            type='agent',
                            img=agent.platform)
                graph_output['nodes'].append(node)

                link = dict(source=0,
                            target=id_store['agent' + agent.unique],
                            type=agent.contact)
                graph_output['links'].append(link)

        for op_id in operation_ids:
            operation = (await self.data_svc.locate('operations', match=dict(id=int(op_id))))[0]
            graph_output['nodes'].append(dict(name=operation.name, type='operation', id=op_id))
            previous_link_graph_id = None
            for link in operation.chain:
                link_graph_id = id_store['link' + link.unique] = max(id_store.values()) + 1
                graph_output['nodes'].append(dict(type='link', name='link:'+link.unique, id=link_graph_id))

                if not previous_link_graph_id:
                    graph_output['links'].append(dict(source=op_id, target=link_graph_id, type='next_link'))
                else:
                    graph_output['links'].append(dict(source=previous_link_graph_id, target=link_graph_id, type='next_link'))
                previous_link_graph_id = link_graph_id

                # link to agent
                try:
                    agent = (await self.data_svc.locate('agents', dict(paw=link.paw)))[0]
                    if 'agent' + agent.unique not in id_store.keys():
                        id_store['agent' + agent.unique] = max(id_store.values()) + 1
                    graph_output['links'].append(dict(source=link_graph_id, target=id_store['agent' + agent.unique], type='next_link'))
                except:
                    continue
        return graph_output

    async def build_fact_d3(self, operation_ids):
        graph_output = dict(nodes=[], links=[])
        id_store = dict(default=0)

        for op_id in operation_ids:
            operation = (await self.data_svc.locate('operations', match=dict(id=int(op_id))))[0]
            graph_output['nodes'].append(dict(name=operation.name, type='operation', id=op_id))
            for fact in operation.all_facts():
                if 'fact' + fact.unique + operation.source.id not in id_store.keys():
                    id_store['fact' + fact.unique + operation.source.id] = node_id = max(id_store.values()) + 1
                    node = dict(name=fact.value, id=node_id, type=fact.trait, attrs=self.get_pub_attrs(fact))
                    graph_output['nodes'].append(node)

            for relationship in operation.all_relationships():
                if relationship.edge:
                    link = dict(source=id_store.get('fact' + relationship.source.unique + operation.source.id),
                                target=id_store.get('fact' + relationship.target.unique + operation.source.id),
                                type=relationship.edge)
                    graph_output['links'].append(link)

            for n in graph_output['nodes']:
                if not next((lnk for lnk in graph_output['links'] if lnk['target'] == n['id']), None):
                    link = dict(source=op_id, target=n['id'], type='has_fact')
                    graph_output['links'].append(link)

        return graph_output

    async def build_tactic_d3(self, operation_ids):
        return await self._build_prop_d3(operation_ids, 'tactic')

    async def build_technique_d3(self, operation_ids):
        return await self._build_prop_d3(operation_ids, 'technique_name')

    async def _build_prop_d3(self, operation_ids, prop):
        graph_output = dict(nodes=[], links=[])
        id_store = dict(default=0)

        for op_id in operation_ids:
            operation = (await self.data_svc.locate('operations', match=dict(id=int(op_id))))[0]
            graph_output['nodes'].append(dict(name=operation.name, type='operation', id=op_id))
            previous_prop_graph_id = None
            for p in self._get_by_prop_order(operation.chain, prop):
                i = max(id_store.values()) + 1
                prop_graph_id = id_store[prop + p + str(i)] = i
                graph_output['nodes'].append(dict(type=prop, name=p, id=prop_graph_id))

                if not previous_prop_graph_id:
                    graph_output['links'].append(dict(source=op_id, target=prop_graph_id, type='next_link'))
                else:
                    graph_output['links'].append(
                        dict(source=previous_prop_graph_id, target=prop_graph_id, type='next_link'))
                previous_prop_graph_id = prop_graph_id
        return graph_output

    @staticmethod
    def get_pub_attrs(fact):
        return {k: v for k, v in vars(fact).items() if not k.startswith('_')}

    @staticmethod
    def _get_by_prop_order(chain, prop):
        current = getattr(chain[0].ability, prop)
        ordered = [current]
        for lnk in chain:
            if getattr(lnk.ability, prop) != current and lnk.cleanup == 0:
                current = getattr(lnk.ability, prop)
                ordered.append(current)
        return ordered
