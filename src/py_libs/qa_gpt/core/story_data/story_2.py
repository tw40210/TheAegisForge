from pydantic import BaseModel
from src.py_libs.chat.chat import get_chat_gpt_response_structure


class Character:
    def __init__(self, name, location) -> None:
        self.name = name
        self.location = location
        self.observation = ""
        self.items = []
        self.skills = {}
        self.stats = {"strength": 0, "intelligence": 0, "agile": 0, "luck": 0}


class Place:
    def __init__(self, name, description="") -> None:
        self.name = name
        self.description = description


class Land:
    def __init__(
        self,
        name,
        coords,
        description="empty land",
        stats=None,
    ) -> None:
        self.name = name
        self.coords = coords
        self.description = description
        self.stats = (
            stats
            if stats is not None
            else {"fertility": 0, "minerals": 0, "rain": 0, "sun shine": 0}
        )

    def __str__(self):
        split_line = "=" * 20 + "\n"
        return f"""
        {split_line}
        name:{self.name}
        coords:{self.coords}
        description:{self.description}
        stats:{self.stats}
        {split_line}
        """


class Step(BaseModel):
    action: str
    explanation: str
    money: int
    human_power: int


class Plan(BaseModel):
    steps: list[Step]


background = {
    0: "This is a empty planet.",
    1: "This is a empty planet with a human troop.",
}

resources = {"money": 100, "human power": 10}

geo_map = [Land(name=f"{i}-{j}", coords=(i, j)) for i in range(5) for j in range(5)]


def take_action():
    pass


def get_action_cost():
    pass


def get_land_change():
    pass


def get_global_info(geo_map):

    msg_buffer = []
    for land in geo_map:
        msg_buffer.append(str(land))

    return "".join(msg_buffer)


def model_cal_land_change():
    pass


def model_cal_action_cost(plan: str, geo_map):
    prompt = """
You are responsible for estimating the resources required for a planetary development plan. Your goal is to break down the plan into a series of steps or actions that need to be taken in order to implement it. For each action, you will estimate the cost in terms of money and human power and provide a detailed explanation for why this action is necessary.

You must carefully consider all relevant factors when estimating these resources, including:

Features of the target land: Is the land fertile, barren, mountainous, forested, or underwater? What challenges does this specific terrain present? How does this affect the amount of resources required to develop it?
Circumstances of the target land: Are there existing resources (water, minerals, infrastructure) that can be used? Are there natural hazards (volcanoes, storms, extreme temperatures) that must be mitigated?
Overall planetary environment: What is the general climate and atmosphere like? Is the planet’s biosphere suitable for human habitation or agriculture? Is there a need for environmental adaptation, such as atmospheric processing or protection from radiation?
Current development level of the planet: Is there existing infrastructure (roads, buildings, power grids)? Are there established colonies, settlements, or industries? What is the level of technology available on the planet?
You should approach the task step by step, estimating the money (represented as a numeric value) and human power (represented as the number of individuals or work units needed) for each action. Here’s the format you should follow for each step:

{action: '....', cost: {money: 3, human_power: 1}, explanation: '....'}
'money' is measured in million US dollars.
'human_power' is measured in the work of a adult man can do in one day.

Your explanation should detail why this action is needed, how you arrived at the cost estimate, and what factors (e.g., terrain difficulty, resource availability, environmental hazards) influenced your decision.
Example:
{action: 'Conduct a comprehensive survey of the land to assess its suitability for development.',
cost: {money: 5, human_power: 2},
explanation: 'This step is crucial to gather detailed information about the terrain, resources, and hazards present. This includes geological analysis, environmental studies, and mapping of the area. Given the lack of current infrastructure on the planet, this will require deploying advanced surveying equipment and specialized teams, hence the moderate cost.'}

    """

    land_info = f"""
    Target land:
    {str(geo_map[13])}

    Global land information:
    {get_global_info(geo_map)}

    """

    plan_info = f"""
    Plan:
    {plan}

    """

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": plan_info + land_info},
    ]

    response = get_chat_gpt_response_structure(messages, res_obj=Plan)
    print(response)
    return response


def model_cal_score():
    pass
