from metagpt.actions import Action
from examples.werewolf_game.actions.common_actions import Speak, NighttimeWhispers


class Hunt(NighttimeWhispers):
    ACTION = "KILL"

class Impersonate(Speak):
    """Action: werewolf impersonating a good guy in daytime speak"""

    STRATEGY = """
    Try continuously impersonating a role with special ability, such as a Seer or a Witch, in order to mislead
    other players, make them trust you, and thus hiding your werewolf identity. However, pay attention to what your werewolf partner said, 
    if your werewolf partner has claimed to be a Seer or Witch, DONT claim to be the same role. Remmber NOT to reveal your real identity as a werewolf!
    """

    def __init__(self, name="Impersonate", context=None, llm=None):
        super().__init__(name, context, llm)
