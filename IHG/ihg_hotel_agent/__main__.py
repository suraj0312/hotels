# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import sys

import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2ui.a2ui_extension import get_a2ui_agent_extension
# from agent import agent
# from agent_executor import ADKAgentExecutor
from agent_executor_v2 import ShoppingAgentExecutor
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

load_dotenv()


# Handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("app.log", mode="a")

fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
console_handler.setFormatter(fmt)
file_handler.setFormatter(fmt)

# 1) Remove handlers from root (important if basicConfig already ran elsewhere)
root = logging.getLogger()
root.handlers.clear()
root.setLevel(logging.WARNING)  # keep root quiet

# 2) Configure only your target logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 3) Avoid adding duplicates if this code runs more than once
logger.handlers.clear()

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 4) Stop bubbling up to root
logger.propagate = False
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'  # Optional: custom date format
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10003)
def main(host, port):
    try:

        capabilities = AgentCapabilities(
            streaming=True,
            extensions=[get_a2ui_agent_extension()],
        )
        ihg_skill = AgentSkill(
            id="ihg_hotel_booking_assistant",
            name="IHG Hotel Booking Assistant",
            description=(
                "Helps users search IHG hotel inventory (InterContinental, Holiday Inn, "
                "Crowne Plaza, etc.), add hotel stays to a booking cart, update room quantities, "
                "apply promo codes, collect guest details, and complete hotel bookings."
            ),
            tags=[
                "hotels",
                "ihg",
                "hotel-search",
                "booking",
                "rooms",
                "checkout",
                "reservation",
                "payments",
                "travel",
                "intercontinental",
                "holiday-inn",
                "crowne-plaza",
                "kimpton",
                "voco",
                "staybridge-suites",
                "candlewood-suites",
            ],
            examples=[
                "Find IHG hotels in Goa",
                "Show Holiday Inn options near Heathrow under £160/night",
                "Add the Crowne Plaza option to my booking with 1 room",
                "Update my booking to 2 rooms",
                "Remove the InterContinental from my booking",
                "Apply promo code IHG10",
                "Add guest details and complete the booking",
                "Show my booking cart",
            ],
        )
        base_url = f"http://{host}:{port}"
        ihg_agent_card = AgentCard(
            name="IHG Hotels Booking Agent",
            description=(
                "An IHG-only hotel search and booking agent. "
                "Use this agent when the user wants IHG properties specifically "
                "(InterContinental / Holiday Inn / Crowne Plaza / Kimpton / voco, etc.), "
                "or when the orchestrator is routing IHG inventory requests."
            ),
            url=base_url,  # set to IHG agent base_url if different
            version="1.0.0",
            default_input_modes=["text", "text/plain"],
            default_output_modes=["text", "text/plain"],
            capabilities=capabilities,
            skills=[ihg_skill],
        )

        # agent_executor = ADKAgentExecutor(agent)
        agent_executor = ShoppingAgentExecutor(base_url=base_url)

        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=ihg_agent_card, http_handler=request_handler
        )
        import uvicorn

        app = server.build()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


        uvicorn.run(app, host=host, port=port)
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
