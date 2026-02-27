import json
import logging
import os
import uuid
import requests
from collections.abc import AsyncIterable
from typing import Any, Dict, List, Optional
from google.adk.tools import ToolContext
from datetime import datetime
import jsonschema
from json_repair import repair_json
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools import agent_tool
from google.genai import types
from google.adk.tools.base_tool import BaseTool
from google.adk.agents.callback_context import CallbackContext
from tools import (
    search_shopping_catalog,
    add_to_checkout,
    remove_from_checkout,
    update_checkout,
    get_checkout,
    apply_discount,
    update_customer_details,
    start_payment,
    ask_user_details,
    complete_checkout,
    after_tool_modifier,
    modify_output_after_agent
                )
import litellm
from constants import UCP_CHECKOUT_KEY,ADK_LATEST_TOOL_RESULT
litellm.ssl_verify = False
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'  # Optional: custom date format
)
logger = logging.getLogger(__name__)

# AGENT_INSTRUCTION = """
#                     You are a helpful shopping assistant. You have tools to generate response.
#                     To generate the response, you MUST follow these rules:
#                     1.  Call the appropriate tool
#                     2.  If the tool response contain a valid json and `a2ui_response` key, return a valid json as output with key `a2ui_response` and its value to be the EXACT value of `a2ui_response` key from the tool response. If a2ui_response is not present, return the response as it is.
#                     """
 
AGENT_INSTRUCTION = """
You are a helpful **hotel search and booking agent**. You assist users to **find hotels**, **select room quantities**, **add/remove/update hotel reservations in a checkout session**, **apply discounts**, **collect guest details**, and **complete booking**.

### Tool mapping (keep tools unchanged, reinterpret meaning)

Treat the existing shopping tools as hotel-booking actions:

* `search_shopping_catalog` = search hotels and available room options in the hotel catalog
* `add_to_checkout` = add a hotel reservation to the booking cart
* `remove_from_checkout` = remove a hotel reservation from the booking cart
* `update_checkout` = update reservation parameters in the booking cart (especially room quantity)
* `get_checkout` = view current booking cart / reservation summary
* `apply_discount` = apply coupon / promo code to booking
* `update_customer_details` = add/update guest & details for booking
* `complete_checkout` = finalize booking (place reservation)

### Data model reinterpretation (fields stay the same)

* `product_id` **contains a hotel id** (treat it as `hotel_id`)
* `quantity` **means number of rooms to book** (room count)
* Any “price/product” fields represent hotel pricing
* Any “product name/title” represent hotel name / room/package name

### Core behavior

1. **Understand hotel intent**

   * Identify: destination/location, number of guests/rooms, budget and any special needs.
   * If the user does not provide guests, proceed with search using available info, and then ask for missing booking-critical details before completing checkout.

2. **Search first, then act**

   * When the user asks to book/add/select a hotel, always:

     1. call `search_shopping_catalog` using their constraints
     2. present the best matches
     3. add the chosen option to checkout using `add_to_checkout`

3. **Cart language mapping**

   * If the user says **“add to my list/cart”**, treat it as adding a hotel reservation to checkout.
   * If the user says **“remove from my list/cart”**, treat it as removing that hotel reservation from checkout.
   * If the user says **“change/adjust rooms”**, use `update_checkout` to set `quantity` to the new number of rooms.

4. **Replacing hotels**

   * If the user says “replace X with Y”:

     * use `remove_from_checkout` for X
     * then `search_shopping_catalog` for Y
     * then `add_to_checkout` for Y with correct room quantity

5. **Always confirm booking-critical details before finalizing**
   Before calling `complete_checkout`, ensure you have:

   * correct hotel selection(s)
   * correct room quantity (`quantity`)
   * guest name + email details + address via `update_customer_details`

6. **Discounts**

   * If the user provides a promo code, apply it with `apply_discount` and then show updated totals via `get_checkout`.

7. **Checkout summary + confirmation**

   * After any add/remove/update, call `get_checkout` and summarize:

     * hotel(s) selected (product id/hotel id/name)
     * number of rooms (quantity)
     * price/total (if available)
     * applied discounts (if any)
   * Before finalizing, ask a confirmation question **only if** something is ambiguous or missing; otherwise proceed to complete booking.

8. **Completion**

   * When the user says “book”, “confirm”, “pay”, or “complete booking”, and all required details are present:

     * call `complete_checkout`
     * respond with confirmation details (booking/order id, hotel name, rooms, total) based on tool output
   * If tool returns an “order placed event”, treat it as “booking confirmed” and communicate it clearly to the user.

### Communication style

* Be concise and action-oriented.

### Safety/accuracy rules

* Do not invent availability, prices, ratings, or amenities; only use catalog/tool results.
* If the user asks for something the tools/catalog cannot represent, explain the limitation and offer the closest supported alternative using the available fields.
If the tool response contain a valid json and `a2ui_part` key, return a valid json as output with key `a2ui_part` and its value to be the EXACT value of `a2ui_part` key from the tool response
"""
 


class ShoppingAgent:
    """An agent that helps in shopping based on user criteria."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self, base_url: str, use_ui: bool = False):
        self.base_url = base_url
        self.use_ui = use_ui
        self.date_time_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.remote_agent_data = {}
        self._agent = self._build_agent(use_ui)
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return "Working on your query..."

    def _build_agent(self, use_ui: bool) -> LlmAgent:
        """Builds the LLM agent for the shopping agent."""
        # LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gemini/gemini-2.5-flash")
        # LITELLM_MODEL = os.getenv("OPENAI_MODEL_NAME", "openai/gpt-5-mini")

        ucp_agent = LlmAgent(
                    name="ucp_shopping_assistant",
                    description="Conversational shopping assistant for UCP checkout sessions.",
                    model=LiteLlm(model=f"openai/{os.getenv("OPENAI_MODEL_NAME")}", api_key=os.getenv("OPENAI_API_KEY")),
                    instruction=AGENT_INSTRUCTION,
                    tools=[
                            search_shopping_catalog,
                            add_to_checkout,
                            remove_from_checkout,
                            update_checkout,
                            get_checkout,
                            apply_discount,
                            update_customer_details,
                            # start_payment,
                            ask_user_details,
                            complete_checkout,
                    ],
                    after_tool_callback=after_tool_modifier,
                    after_agent_callback=modify_output_after_agent
                )
        return ucp_agent

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        session_state = {"base_url": self.base_url}

        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state=session_state,
                session_id=session_id,
            )
        else:
            # Ensure base_url exists
            session.state.setdefault("base_url", self.base_url)

        current_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)],
        )

        final_response_content: Optional[str] = None
        agent_text_part = None

        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=current_message,
        ):
            logger.info(f"Event from runner: {event}")
            if event.is_final_response():
                if event.content and event.content.parts:
                    texts = [p.text for p in event.content.parts if getattr(p, "text", None)]
                    if texts:
                        final_response_content = "\n".join(texts)
                # break
                        if agent_text_part is None:
                            agent_text_part = final_response_content
                            logging.info (f"Agent final response text part: {agent_text_part}")

            # Intermediate event
            logger.info(f"Intermediate event: {event}")
            yield {
                "is_task_complete": False,
                "updates": self.get_processing_message(),
            }

        # If we never got any final text, return a safe terminal response
        if not final_response_content:
            logger.warning(
                "--- ShoppingAgent.stream: Received no final response content from runner. ---"
            )
            yield {
                "is_task_complete": True,
                "content": None,
                "error": "No final response content received.",
            }
            return

        # Validate / parse final response
        if self.use_ui:
            try:
                if "a2ui_part" in final_response_content:
                    a2ui_part = final_response_content.split("a2ui_part:")[1]
                    # json_data = repair_json(final_response_content, return_objects=True)
                    json_data = repair_json(a2ui_part, return_objects=True)
                    yield {
                        "is_task_complete": True,
                        # "content": json_data,
                        "content": {'a2ui_part':json_data, 'agent_text_part':agent_text_part},
                    }
                    return

                # UI mode but marker not found -> fall back to raw text (or treat as error)
                yield {
                    "is_task_complete": True,
                    "content": final_response_content,
                }
                return

            except Exception as e:
                logger.exception("Validation/parsing failed.")
                yield {
                    "is_task_complete": True,
                    "content": final_response_content,
                    "error": f"Validation failed: {e}",
                }
                return

        # Not using UI => always return text
        yield {
            "is_task_complete": True,
            "content": final_response_content,
        }