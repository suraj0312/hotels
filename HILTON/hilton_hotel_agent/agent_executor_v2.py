import json
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from a2ui.a2ui_extension import create_a2ui_part, try_activate_a2ui_extension
from agent_v2 import ShoppingAgent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'  # Optional: custom date format
)
logger = logging.getLogger(__name__)


class ShoppingAgentExecutor(AgentExecutor):
    """Shopping AgentExecutor Example."""

    def __init__(self, base_url: str):
        # Instantiate two agents: one for UI and one for text-only.
        # The appropriate one will be chosen at execution time.
        self.ui_agent = ShoppingAgent(base_url=base_url, use_ui=True)
        self.text_agent = ShoppingAgent(base_url=base_url, use_ui=False)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = ""
        ui_event_part = None
        action = None

        logger.info(
            f"--- Client requested extensions: {context.requested_extensions} ---"
        )
        use_ui = try_activate_a2ui_extension(context)

        # Determine which agent to use based on whether the a2ui extension is active.
        # if use_ui:
        agent = self.ui_agent
        logger.info(
            "--- AGENT_EXECUTOR: A2UI extension is active. Using UI agent. ---"
        )
        if context.message and context.message.parts:
            logger.info(
                f"--- AGENT_EXECUTOR: Processing {len(context.message.parts)} message parts ---"
            )
            for i, part in enumerate(context.message.parts):
                if isinstance(part.root, DataPart):
                    if "userAction" in part.root.data:
                        logger.info(f"  Part {i}: Found a2ui UI ClientEvent payload.")
                        ui_event_part = part.root.data["userAction"]
                    else:
                        logger.info(f"  Part {i}: DataPart (data: {part.root.data})")
                elif isinstance(part.root, TextPart):
                    logger.info(f"  Part {i}: TextPart (text: {part.root.text})")
                else:
                    logger.info(f"  Part {i}: Unknown part type ({type(part.root)})")

        if ui_event_part:
            logger.info(f"Received a2ui ClientEvent: {ui_event_part}")
            action = ui_event_part.get("name")
            ctx = ui_event_part.get("context", {})

            
            # if action == "addToCheckout":
            #     item_id = ctx.get("productId", "Unknown Item")
            #     name = ctx.get("name", "title not provided")
            #     image_url = ctx.get("imageUrl", "")
            #     quantity = ctx.get("quantity", "1")
            #     query = f"USER_WANTS_TO_ADD_ITEM_TO_CART: id: {item_id}, name: {name}, ImageURL: {image_url},quantity:{quantity}"

            # elif action == "completeCheckout":
            #     query = "USER want to complete checkout."
            # elif action == "submit_add_item_form":
            #     item_id = ctx.get("item_id", "Unknown ID")
            #     title = ctx.get("title", "Unknown Item")
            #     quantity = ctx.get("quantity", "Unknown Quantity")
            #     query = f"User submitted the form to add item to cart for id: {item_id}, title: {title} and quantity: {quantity}"



            if action == "addToCheckout":
                item_id = ctx.get("productId", "Unknown Item")
                name = ctx.get("name", "title not provided")
                image_url = ctx.get("imageUrl", "")
                quantity = ctx.get("quantity", "1")

                query = f"Add the following item:\n id: {item_id}, name: {name}, ImageURL: {image_url}, quantity:{quantity}"

            elif action == "startCheckout":

                query = "Ask user details form."

            elif action == "submitForm":
                firstName = ctx.get("firstName", "Unknown firstName")
                lastName = ctx.get("lastName", "Unknown LastName")
                email = ctx.get("email", "Unknown Email")
                address = ctx.get("address", "Unknown Address")
                pinCode = ctx.get("pinCode", "Unknown PinCode")
                country = ctx.get("country", "Unknown Country")

                query = f"Update these customer details:\n first_name: {firstName}, last_name: {lastName}, email: {email}, complete_address: {address}, postal_code: {pinCode} and address_country: {country}"
            elif action == "payWithCard":
                cardType = ctx.get("cardType", "Unknown cardType")
                cardNumber = ctx.get("cardNumber", "Unknown cardNumber")
                query = f"Complete the checkout:\n card_brand: {cardType}, card_LastDigits: {cardNumber[-4]}"




            else:
                query = f"User submitted an event: {action} with data: {ctx}"
        else:
            logger.info("No a2ui UI event part found. Falling back to text input.")
            query = context.get_user_input()

        logger.info(f"--- AGENT_EXECUTOR: Final query for LLM: '{query}' ---")

        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        async for item in agent.stream(query, task.context_id):
            is_task_complete = item["is_task_complete"]
            if not is_task_complete:
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(item["updates"], task.context_id, task.id),
                )
                continue

            final_state = (
                TaskState.completed
                if action == "submit_booking"
                else TaskState.input_required
            )

            content = item["content"]
            final_parts = []
            if 'agent_text_part' in content:
                            final_parts.append(Part(root=TextPart(text = content['agent_text_part'])))
            if "a2ui_part" in content:
                        if isinstance(content["a2ui_part"], list):
                            logger.info(
                                f"Found {len("a2ui_part")} messages. Creating individual DataParts."
                            )
                            for message in content["a2ui_part"]:
                                final_parts.append(create_a2ui_part(message))
                        else:
                            # Handle the case where a single JSON object is returned
                            logger.info(
                                "Received a single JSON object. Creating a DataPart."
                            )
                            final_parts.append(create_a2ui_part(content["a2ui_part"]))                     

            else:
                final_parts.append(Part(root=TextPart(text=content.strip())))

            logger.info("--- FINAL PARTS TO BE SENT ---")
            for i, part in enumerate(final_parts):
                logger.info(f"  - Part {i}: Type = {type(part.root)}")
                if isinstance(part.root, TextPart):
                    logger.info(f"    - Text: {part.root.text[:200]}...")
                elif isinstance(part.root, DataPart):
                    logger.info(f"    - Data: {str(part.root.data)[:200]}...")
            logger.info("-----------------------------")

            await updater.update_status(
                final_state,
                new_agent_parts_message(final_parts, task.context_id, task.id),
                final=(final_state == TaskState.completed),
            )
            break

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
