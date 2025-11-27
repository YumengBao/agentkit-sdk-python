# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from veadk import Agent, Runner
from veadk.a2a.agent_card import get_agent_card
from veadk.tools.demo_tools import get_city_weather

from agentkit.apps import AgentkitA2aApp

logger = logging.getLogger(__name__)


a2a_app = AgentkitA2aApp()

app_name = "weather_reporter"
agent = Agent(tools=[get_city_weather])
runner = Runner(agent=agent)


@a2a_app.agent_executor(runner=runner)
class MyAgentExecutor(A2aAgentExecutor):
    """Use Google ADK A2aAgentExecutor directly."""

    pass


if __name__ == "__main__":
    a2a_app.run(
        agent_card=get_agent_card(agent=agent, url="http://0.0.0.0:8000"),
        host="0.0.0.0",
        port=8000,
    )
