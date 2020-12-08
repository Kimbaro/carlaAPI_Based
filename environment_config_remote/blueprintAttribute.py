import json


class ActorData_Manager(object):
    remote_true = "remote_true"
    remote_false = "remote_false"

    def __init__(self, world):
        self.world = world
        self.target = None
        self.actors = self.world.get_actors()
        self.blueprints = self.world.get_blueprint_library().filter("vehicle.*")

    # role_name 외 다른 속성값 할당 시 에러
    # def return_set_bp(self, bp, attr_name, attr_value):
    #     bp.set_attribute(attr_name, attr_value)
    #     return bp
    def tick(self):
        self.actors = self.world.get_actors()
        self.blueprints = self.world.get_blueprint_library().filter("vehicle.*")

    def split(self):
        """
        속성값으로 찾으려는 액터를 반환
        :param attr_value: True인 경우 remote_true, False인 경우 remote_false
        :return: list[carla.Actor...]
        """
        vehicles = []
        traffic_lights = []
        speed_limits = []
        walkers = []
        stops = []
        static_obstacles = []
        for actor in self.world.get_actors():
            if 'vehicle' in actor.type_id:
                vehicles.append(actor)
            elif 'traffic_light' in actor.type_id:
                traffic_lights.append(actor)
            elif 'speed_limit' in actor.type_id:
                speed_limits.append(actor)
            elif 'walker' in actor.type_id:
                walkers.append(actor)
            elif 'stop' in actor.type_id:
                stops.append(actor)
            elif 'static.prop' in actor.type_id:
                static_obstacles.append(actor)

        attr_actor = [actor for actor in vehicles if actor.attributes["role_name"] == "target"]
        print("ttttttt : ", attr_actor)
        return attr_actor[0]

    def show_attribute(self):
        data = self.target.attributes
        return data
