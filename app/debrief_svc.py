import logging


class DebriefService:
    def __init__(self, services):
        self.services = services
        self.file_svc = services.get('file_svc')
        self.data_svc = services.get('data_svc')
        self.log = logging.getLogger('debrief_svc')

    async def build_agent_d3(self):
        graph_output = dict(nodes=[], links=[])
        id_store = dict(c2=0)
        graph_output['nodes'].append(dict(name="C2", label='server', id=0, img='server'))

        agents = await self.data_svc.locate('agents')
        for agent in agents:
            if agent.unique not in id_store.keys():
                id_store[agent.unique] = max(id_store.values()) + 1
                node = dict(name=agent.display_name,
                            id=id_store[agent.unique],
                            group=agent.group,
                            type='agent',
                            img=agent.platform)
                graph_output['nodes'].append(node)

                link = dict(source=0,
                            target=id_store[agent.unique],
                            type=agent.contact)
                graph_output['links'].append(link)
        return graph_output


