import json


# TargetActorAttr 사용 예
# try:
#     target = TargetActorAttr.search_actor_to_attr_value("vehicle", target_actor_attr.remote_false)
#     print("danger car info : ", target[0].attributes[target_actor_attr.remote_false])
# except KeyError as e:
#     print(e)
#     pass
class TargetActorAttr(object):
    remote_true = "remote_true"
    remote_false = "remote_false"

    def __init__(self, world):
        self.world = world
        self.target = None

    # role_name 외 다른 속성값 할당 시 에러
    # def return_set_bp(self, bp, attr_name, attr_value):
    #     bp.set_attribute(attr_name, attr_value)
    #     return bp

    def search_actor_to_attr_value(self, actor_type, attr_value):
        """
        속성값으로 찾으려는 액터를 반환
        :param actor_type: carla document의 BlueprintLibrary 참고
        :param attr_value: True인 경우 remote_true, False인 경우 remote_false
        :return: list[carla.Actor...]
        """
        attr_actor = [actor for actor in self.world.get_actors() if actor_type in actor.type_id if
                      actor.attributes["role_name"] == attr_value]

        return attr_actor

    def set_target_bp_attribute(self, actor_type):
        attr_actor = [actor for actor in self.world.get_actors() if actor_type in actor.type_id if
                      actor.attributes["role_name"] == TargetActorAttr.remote_true or actor.attributes[
                          "role_name"] == TargetActorAttr.remote_false]
        print("danger car info4 : ", attr_actor)

    def show_attribute(self):
        data = self.target.attributes
        return data
