
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from ucp_sdk.models.schemas.shopping import checkout_create_req, checkout_update_req, payment_create_req
from ucp_sdk.models.schemas.shopping.payment_data import PaymentData
from ucp_sdk.models.schemas.shopping.types import buyer as buyer_model
from ucp_sdk.models.schemas.shopping.types import item_create_req, item_update_req
# from ucp_sdk.models.schemas.shopping.types import item_req, item_update_req
from ucp_sdk.models.schemas.shopping.types import line_item_create_req, line_item_update_req
from ucp_sdk.models.schemas.shopping.types.card_payment_instrument import CardPaymentInstrument
from ucp_sdk.models.schemas.shopping.types.payment_instrument import PaymentInstrument
from ucp_sdk.models.schemas.shopping.types.postal_address import PostalAddress
from ucp_sdk.models.schemas.shopping.types.token_credential_resp import TokenCredentialResponse

from to_a2ui import render_askuserdetails_a2ui, render_catalog_results_a2ui,render_checkout_results_a2ui, render_complete_checkout_a2ui,render_selectacard_a2ui

from constants import (
    ADK_USER_CHECKOUT_ID,
    ADK_PAYMENT_STATE,
    ADK_UCP_METADATA_STATE,
    ADK_EXTENSIONS_STATE_KEY,
    ADK_LATEST_TOOL_RESULT,
    A2A_UCP_EXTENSION_URL,
    UCP_AGENT_HEADER,
    UCP_CHECKOUT_KEY,
    UCP_PAYMENT_DATA_KEY,
    UCP_RISK_SIGNALS_KEY,
)

DEFAULT_SERVER_URL = "http://localhost:8185"
logger = logging.getLogger(__name__)


# If you use the UCP extension gating like your reference
class UcpExtension:
    URI = A2A_UCP_EXTENSION_URL


def _create_error_response(message: str) -> dict:
    return {"message": message, "status": "error"}


def _dump(model_obj: Any) -> Dict[str, Any]:
    return model_obj.model_dump(mode="json", by_alias=True, exclude_none=True)


def _get_headers() -> Dict[str, str]:
    # Hardcoded for now (per your request)
    return {
        UCP_AGENT_HEADER: 'profile="http://localhost:8185/.well-known/ucp"',
        "request-signature": "test",
        "idempotency-key": str(uuid.uuid4()),
        "request-id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


def _get_current_checkout_id(tool_context: ToolContext) -> Optional[str]:
    return tool_context.state.get(ADK_USER_CHECKOUT_ID)


@dataclass
class UcpMetadata:
    server_url: str
    handlers: List[dict]  # from discovery


def _get_or_init_ucp_metadata(tool_context: ToolContext) -> Optional[UcpMetadata]:
    """
    Expects tool_context.state[ADK_UCP_METADATA_STATE] in this shape:
      {"server_url": "...", "handlers": [...]}

    agent_executor.py should set this in state_delta. If not set, we auto-discover.
    """
    raw = tool_context.state.get(ADK_UCP_METADATA_STATE)
    if raw and isinstance(raw, dict) and raw.get("server_url") and raw.get("handlers") is not None:
        return UcpMetadata(server_url=str(raw["server_url"]).rstrip("/"), handlers=list(raw["handlers"]))

    server_url = str(raw.get("server_url") if isinstance(raw, dict) else DEFAULT_SERVER_URL).rstrip("/")
    try:
        with httpx.Client(base_url=server_url, timeout=30.0) as c:
            r = c.get("/.well-known/ucp", headers=_get_headers())
            if r.status_code != 200:
                logger.error("Discovery failed: %s", r.text)
                return None
            data = r.json()
            handlers = data.get("payment", {}).get("handlers", []) or []
            tool_context.state[ADK_UCP_METADATA_STATE] = {"server_url": server_url, "handlers": handlers}
            return UcpMetadata(server_url=server_url, handlers=handlers)
    except Exception:
        logger.exception("Discovery exception")
        return None


# -----------------------------
# REST client wrapper
# -----------------------------
class UcpRestStore:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.server_url, timeout=30.0)

    def get_all_items(self) -> dict:
        with self._client() as c:
            r = c.get("/get-all-items", headers=_get_headers())
            r.raise_for_status()
            return r.json()

    def get_checkout(self, checkout_id: str) -> Optional[dict]:
        with self._client() as c:
            r = c.get(f"/checkout-sessions/{checkout_id}", headers=_get_headers())
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()

    def create_checkout(self, payload: dict) -> dict:
        with self._client() as c:
            r = c.post("/checkout-sessions", json=payload, headers=_get_headers())
            r.raise_for_status()
            return r.json()

    def update_checkout(self, checkout_id: str, payload: dict) -> dict:
        with self._client() as c:
            r = c.put(f"/checkout-sessions/{checkout_id}", json=payload, headers=_get_headers())
            r.raise_for_status()
            print("UPDATED DATA: ", r.json())
            return r.json()

    def complete(self, checkout_id: str, payload: dict) -> dict:
        with self._client() as c:
            r = c.post(f"/checkout-sessions/{checkout_id}/complete", json=payload, headers=_get_headers())
            r.raise_for_status()
            logging.info(f"Complete checkout data: {r.json()}")
            return r.json()


# -----------------------------
# Catalog search
# -----------------------------
def search_shopping_catalog(tool_context: ToolContext, query: str) -> dict:
    """
    Retrieve and return product data from the shopping catalog.

    Args:
        tool_context (ToolContext): Context object containing configuration
            and metadata required to initialize the UCP connection.
        query (str): Search query string provided by the user. The query is
            normalized (trimmed and lowercased). (Note: current implementation
            retrieves all items and does not actively filter results.)
    Returns:
        dict: A response dictionary containing:
            - "a2a.product_results" (list): List of catalog items retrieved
              from the UCP store.
            - "a2ui_part" (Any): Rendered UI component representing the
              catalog results.
            - "status" (str): "success" if the operation completes successfully.
    
    """
    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        catalog = store.get_all_items()
        items = catalog.get("items") if isinstance(catalog, dict) else catalog
        if items is None:
            items = []

        q = (query or "").strip().lower()
        results = []
        for it in items:
            title = str(it.get("title") or it.get("name") or "").lower()
            pid = str(it.get("id") or it.get("sku") or "").lower()
            results.append(it)
        # a2ui_part = render_catalog_results_a2ui(results, str(uuid.uuid4()))
        a2ui_part = render_catalog_results_a2ui(results, str(uuid.uuid4()))
        return {"a2a.product_results": results, "a2ui_part": a2ui_part, "status": "success"}
    except Exception:
        logger.exception("There was an error searching the product catalog.")
        return _create_error_response(
            "Sorry, there was an error searching the product catalog, please try again later."
        )


# -----------------------------
# Checkout helpers (typed payloads)
# -----------------------------
def _build_put_line_items_from_checkout(checkout_json: dict) -> List[line_item_update_req.LineItemUpdateRequest]:
    typed: List[line_item_update_req.LineItemUpdateRequest] = []
    for li in checkout_json.get("line_items", []) or []:
        itm = item_update_req.ItemUpdateRequest(
            id=li.get("item", {}).get("id"),
            title=li.get("item", {}).get("title", ""),
        )
        typed.append(
            line_item_update_req.LineItemUpdateRequest(
                id=li.get("id"),
                quantity=int(li.get("quantity", 0)),
                item=itm,
            )
        )
    return typed


def _checkout_update_payload(
    checkout_id: str,
    checkout_json: dict,
    line_items: List[line_item_update_req.LineItemUpdateRequest],
    fulfillment: Optional[dict] = None,
    discounts: Optional[dict] = None,
) -> dict:
    """
    IMPORTANT: CheckoutUpdateRequest.payment expects a dict (or PaymentUpdateRequest),
    NOT a PaymentCreateRequest instance.
    """
    update_req = checkout_update_req.CheckoutUpdateRequest(
        id=checkout_id,
        currency=checkout_json.get("currency", "INR"),
        line_items=line_items,
        payment=checkout_json.get("payment", {}) or {},  # <- dict
        fulfillment=fulfillment,
    )
    payload = _dump(update_req)
    if discounts is not None:
        payload["discounts"] = discounts
    return payload


def ensure_and_select_shipping_fulfillment(store: UcpRestStore, checkout_id: str, checkout: dict) -> dict:
    """
    Mirrors the reference flow:
      1) Trigger fulfillment methods generation (shipping)
      2) Select destination
      3) Select first option
    Returns updated checkout JSON.
    """
    # Always rebuild typed line_items from the current checkout (strict PUT validators)
    typed_items = _build_put_line_items_from_checkout(checkout)

    # STEP A: Trigger fulfillment generation if missing
    methods = (checkout.get("fulfillment") or {}).get("methods") or []
    if not methods:
        payload = _checkout_update_payload(
            checkout_id,
            checkout,
            typed_items,
            fulfillment={"methods": [{"type": "shipping"}]},
        )
        checkout = store.update_checkout(checkout_id, payload)
        methods = (checkout.get("fulfillment") or {}).get("methods") or []

    if not methods:
        # Nothing we can pick; return what we have.
        return checkout

    method0 = methods[0]
    destinations = method0.get("destinations") or []
    if not destinations:
        return checkout

    dest_id = destinations[0].get("id")
    if not dest_id:
        return checkout

    # STEP B: Select destination (to calculate groups/options)
    payload = _checkout_update_payload(
        checkout_id,
        checkout,
        typed_items,
        fulfillment={"methods": [{"type": "shipping", "selected_destination_id": dest_id}]},
    )
    checkout = store.update_checkout(checkout_id, payload)

    # STEP C: Select first option (if available)
    methods = (checkout.get("fulfillment") or {}).get("methods") or []
    if not methods:
        return checkout

    method0 = methods[0]
    groups = method0.get("groups") or []
    if not groups:
        return checkout

    options = (groups[0] or {}).get("options") or []
    if not options:
        return checkout

    option_id = options[0].get("id")
    if not option_id:
        return checkout

    payload = _checkout_update_payload(
        checkout_id,
        checkout,
        typed_items,
        fulfillment={
            "methods": [
                {
                    "type": "shipping",
                    "selected_destination_id": dest_id,
                    "groups": [{"selected_option_id": option_id}],
                }
            ]
        },
    )
    checkout = store.update_checkout(checkout_id, payload)
    return checkout


# -----------------------------
# Tools: checkout lifecycle
# -----------------------------
def add_to_checkout(tool_context: ToolContext, product_id: str, quantity: int = 1) -> dict:
    """
    Add a product to the user's checkout.

    Creates a new checkout if none exists; otherwise updates the existing
    checkout by increasing the quantity or adding a new line item.

    Args:
        tool_context: Agent tool context with session state and UCP metadata.
        product_id: Product ID to add.
        quantity: Number of units to add (default: 1).

    Returns:
        dict:
            On success:
                {
                    UCP_CHECKOUT_KEY: <checkout_data>,
                    "a2ui_part": <ui_payload>,
                    "status": "success"
                }

            On error:
                {
                    "status": "error",
                    "message": <error_message>
                }
    """
    checkout_id = _get_current_checkout_id(tool_context)
    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        if not checkout_id:
            # CREATE checkout using typed create request
            item1 = item_create_req.ItemCreateRequest(id=product_id, title=product_id)
            li1 = line_item_create_req.LineItemCreateRequest(quantity=int(quantity), item=item1)

            payment_req = payment_create_req.PaymentCreateRequest(
                instruments=[],
                selected_instrument_id=None,
                handlers=md.handlers,
            )
            buyer_req = buyer_model.Buyer()

            create_req = checkout_create_req.CheckoutCreateRequest(
                currency="INR",
                line_items=[li1],
                payment=payment_req,
                buyer=buyer_req,
            )
            created = store.create_checkout(_dump(create_req))
            tool_context.state[ADK_USER_CHECKOUT_ID] = created.get("id")
            a2ui_part = render_checkout_results_a2ui(created, str(uuid.uuid4()))
            return {UCP_CHECKOUT_KEY: created, "a2ui_part":a2ui_part ,"status": "success"}

        checkout = store.get_checkout(checkout_id)
        if checkout is None:
            tool_context.state[ADK_USER_CHECKOUT_ID] = None
            return _create_error_response("Checkout not found for the current session.")

        typed_items = _build_put_line_items_from_checkout(checkout)

        found = False
        for li in typed_items:
            if li.item.id == product_id:
                li.quantity = int(li.quantity or 0) + int(quantity)
                found = True
                break

        if not found:
            typed_items.append(
                line_item_update_req.LineItemUpdateRequest(
                    id=None,
                    quantity=int(quantity),
                    item=item_update_req.ItemUpdateRequest(id=product_id, title=product_id),
                )
            )

        payload = _checkout_update_payload(checkout_id, checkout, typed_items)
        updated = store.update_checkout(checkout_id, payload)
        a2ui_part = render_checkout_results_a2ui(updated, str(uuid.uuid4()))
        return {UCP_CHECKOUT_KEY: updated, "a2ui_part":a2ui_part,"status": "success"}

    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error in add_to_checkout")
        return _create_error_response(f"There was an error adding item to checkout: {e.response.text}")
    except Exception:
        logger.exception("There was an error adding item to checkout, please retry later.")
        return _create_error_response("There was an error adding item to checkout, please retry later.")


def remove_from_checkout(tool_context: ToolContext, product_id: str) -> dict:
    """
    Remove a product from the user's checkout.

    Loads the current checkout, removes any line item matching `product_id`,
    and updates the checkout. If removal would result in an empty cart, an
    error is returned (cart cannot be left empty).

    Args:
        tool_context: Agent tool context with session state and UCP metadata.
        product_id: Product ID to remove from the checkout.

    Returns:
        dict:
            On success:
                {
                    UCP_CHECKOUT_KEY: <checkout_data>,
                    "a2ui_part": <ui_payload>,
                    "status": "success"
                }

            On error:
                {
                    "status": "error",
                    "message": <error_message>
                }
    """
    checkout_id = _get_current_checkout_id(tool_context)
    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        checkout = store.get_checkout(checkout_id)
        if checkout is None:
            return _create_error_response("Checkout not found with the given ID.")

        typed_items = _build_put_line_items_from_checkout(checkout)
        typed_items = [li for li in typed_items if li.item.id != product_id]

        if not typed_items:
            return _create_error_response("Cart would be empty; add an item first.")

        payload = _checkout_update_payload(checkout_id, checkout, typed_items)
        updated = store.update_checkout(checkout_id, payload)
        a2ui_part = render_checkout_results_a2ui(updated, str(uuid.uuid4()))
        return {UCP_CHECKOUT_KEY: updated, "a2ui_part":a2ui_part, "status": "success"}

    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error in remove_from_checkout")
        return _create_error_response(f"There was an error removing item from checkout: {e.response.text}")
    except Exception:
        logger.exception("There was an error removing item from checkout, please retry later.")
        return _create_error_response("There was an error removing item from checkout, please retry later.")


def update_checkout(tool_context: ToolContext, product_id: str, quantity: int) -> dict:
    """
    Update the quantity of a product in the user's checkout.

    Retrieves the current checkout and sets the quantity for the given
    `product_id`. If `quantity` is 0 or less, the item is removed.
    If the update would leave the cart empty, an error is returned.

    Args:
        tool_context: Agent tool context with session state and UCP metadata.
        product_id: Product ID to update.
        quantity: New quantity to set for the product.

    Returns:
        dict:
            On success:
                {
                    UCP_CHECKOUT_KEY: <checkout_data>,
                    "a2ui_part": <ui_payload>,
                    "status": "success"
                }

            On error:
                {
                    "status": "error",
                    "message": <error_message>
                }
    """
    checkout_id = _get_current_checkout_id(tool_context)
    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        checkout = store.get_checkout(checkout_id)
        if checkout is None:
            return _create_error_response("Checkout not found with the given ID.")

        typed_items = _build_put_line_items_from_checkout(checkout)

        new_items: List[line_item_update_req.LineItemUpdateRequest] = []
        for li in typed_items:
            if li.item.id == product_id:
                if int(quantity) <= 0:
                    continue
                li.quantity = int(quantity)
            new_items.append(li)

        if not new_items:
            return _create_error_response("Cart would be empty; add an item first.")

        payload = _checkout_update_payload(checkout_id, checkout, new_items)
        updated = store.update_checkout(checkout_id, payload)
        a2ui_part = render_checkout_results_a2ui(updated, str(uuid.uuid4()))
        return {UCP_CHECKOUT_KEY: updated,"a2ui_part":a2ui_part, "status": "success"}

    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error in update_checkout")
        return _create_error_response(f"There was an error updating item in the cart: {e.response.text}")
    except Exception:
        logger.exception("There was an error updating item in the cart, please retry later.")
        return _create_error_response("There was an error updating item in the cart, please retry later.")


def get_checkout(tool_context: ToolContext) -> dict:
    """
    Retrieve the current user's checkout.

    Loads the checkout associated with the current session and returns
    the latest checkout data along with the rendered UI payload.

    Args:
        tool_context: Agent tool context containing session state and UCP metadata.

    Returns:
        dict:
            On success:
                {
                    UCP_CHECKOUT_KEY: <checkout_data>,
                    "a2ui_part": <ui_payload>,
                    "status": "success"
                }

            On error:
                {
                    "status": "error",
                    "message": <error_message>
                }
    """
    checkout_id = _get_current_checkout_id(tool_context)
    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        checkout = store.get_checkout(checkout_id)
        if checkout is None:
            return _create_error_response("Checkout not found with the given ID.")
        a2ui_part = render_checkout_results_a2ui(checkout, str(uuid.uuid4()))
        return {UCP_CHECKOUT_KEY: checkout,"a2ui_part":a2ui_part, "status": "success"}
    except Exception:
        logger.exception("There was an error fetching checkout.")
        return _create_error_response("There was an error fetching the checkout, please retry later.")


def apply_discount(tool_context: ToolContext, code: str) -> dict:
    """
    Apply a discount code to the current user's checkout.

    Retrieves the current checkout and updates it with the provided discount
    code, returning the updated checkout and rendered UI payload.

    Args:
        tool_context: Agent tool context containing session state and UCP metadata.
        code: Discount/promo code to apply.

    Returns:
        dict:
            On success:
                {
                    UCP_CHECKOUT_KEY: <checkout_data>,
                    "a2ui_part": <ui_payload>,
                    "status": "success"
                }

            On error:
                {
                    "status": "error",
                    "message": <error_message>
                }
    """
    checkout_id = _get_current_checkout_id(tool_context)
    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        checkout = store.get_checkout(checkout_id)
        if checkout is None:
            return _create_error_response("Checkout not found with the given ID.")

        typed_items = _build_put_line_items_from_checkout(checkout)
        payload = _checkout_update_payload(
            checkout_id,
            checkout,
            typed_items,
            discounts={"codes": [code]},
        )
        updated = store.update_checkout(checkout_id, payload)
        a2ui_part = render_checkout_results_a2ui(updated, str(uuid.uuid4()))
        return {UCP_CHECKOUT_KEY: updated,"a2ui_part":a2ui_part, "status": "success"}

    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error in apply_discount")
        return _create_error_response(f"There was an error applying discount: {e.response.text}")
    except Exception:
        logger.exception("There was an error applying discount.")
        return _create_error_response("There was an error applying discount, please retry later.")


def update_customer_details(
    tool_context: ToolContext,
    first_name: str,
    last_name: str,
    street_address: str,
    address_locality: str,
    address_region: str,
    postal_code: str,
    address_country: str | None,
    extended_address: str | None = None,
    email: str | None = None,
) -> dict:
    checkout_id = _get_current_checkout_id(tool_context)
    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    if not address_country:
        address_country = "US"

    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        checkout = store.get_checkout(checkout_id)
        if checkout is None:
            return _create_error_response("Checkout not found for the current session.")

        typed_items = _build_put_line_items_from_checkout(checkout)

        full_name = f"{first_name} {last_name}".strip()
        buyer_payload = {"full_name": full_name}
        if email:
            buyer_payload["email"] = email
        # else:
        #     buyer_payload["email"]="jane.smith@example.com"

        _ = PostalAddress(
            street_address=street_address,
            extended_address=extended_address,
            address_locality=address_locality,
            address_region=address_region,
            address_country=address_country,
            postal_code=postal_code,
            first_name=first_name,
            last_name=last_name,
        )

        payload = _checkout_update_payload(checkout_id, checkout, typed_items)
        payload["buyer"] = buyer_payload
        payload["shipping_address"] = {
            "street_address": street_address,
            "extended_address": extended_address,
            "address_locality": address_locality,
            "address_region": address_region,
            "address_country": address_country,
            "postal_code": postal_code,
            "first_name": first_name,
            "last_name": last_name,
        }

        updated = store.update_checkout(checkout_id, payload)

        updated = ensure_and_select_shipping_fulfillment(store, checkout_id, updated)

        # After details are in, proceed to start payment
        tool_context.state[UCP_CHECKOUT_KEY] = updated
        return start_payment(tool_context)

    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error in update_customer_details")
        return _create_error_response(f"There was an error updating customer details: {e.response.text}")
    except Exception:
        logger.exception("There was an error updating customer details.")
        return _create_error_response("There was an error updating customer details, please retry later.")

def ask_user_details() -> dict:
    """
    Use this function for Ask user details form query.
    """
    a2ui_part = render_askuserdetails_a2ui(datetime_stamp=str(uuid.uuid4()))
    return {"a2ui_part": a2ui_part}

def start_payment(tool_context: ToolContext) -> dict:
    checkout_id = _get_current_checkout_id(tool_context)
    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    try:
        checkout = store.get_checkout(checkout_id)
        if checkout is None:
            return _create_error_response("Checkout not found for the current session.")

        tool_context.actions.skip_summarization = True
        # a2ui_part = render_checkout_results_a2ui(checkout, str(uuid.uuid4()))
        a2ui_part = render_selectacard_a2ui(str(uuid.uuid4()))
        return {UCP_CHECKOUT_KEY: checkout,"a2ui_part":a2ui_part, "status": "success"}
        # return {UCP_CHECKOUT_KEY: checkout, "status": "success"}

    except Exception:
        logger.exception("There was an error starting payment.")
        return _create_error_response("There was an error starting payment, please retry later.")


async def complete_checkout(tool_context: ToolContext, card_brand: str, card_lastdigits: str) -> dict:
    """
    Expects tool_context.state[ADK_PAYMENT_STATE] to include:
      {
        "a2a.ucp.checkout.payment_data": <PaymentInstrument dump OR raw dict>,
        "a2a.ucp.checkout.risk_signals": {...}
      }
    """
    checkout_id = _get_current_checkout_id(tool_context)
    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    md = _get_or_init_ucp_metadata(tool_context)
    if not md:
        return _create_error_response("There was an error creating UCP metadata")

    store = UcpRestStore(md.server_url)

    # payment_state: Optional[dict[str, Any]] = tool_context.state.get(ADK_PAYMENT_STATE)
    # if payment_state is None:
    #     return {
    #         "message": (
    #             "Payment Data is missing. Click 'Confirm Purchase' to complete the purchase."
    #         ),
    #         "status": "requires_more_info",
    #     }

    try:
        # pi_raw = payment_state.get(UCP_PAYMENT_DATA_KEY)
        # risk = payment_state.get(UCP_RISK_SIGNALS_KEY, {"ip": "127.0.0.1", "browser": "python-httpx"})

        instr = CardPaymentInstrument(
            id="instr_my_card",
            handler_id="mock_payment_handler",
            handler_name="mock_payment_handler",
            type="card",
            brand=card_brand,
            last_digits=card_lastdigits,
            credential=TokenCredentialResponse(type="token", token="success_token"),
            billing_address=PostalAddress(
                street_address="123 Main St",
                address_locality="Anytown",
                address_region="CA",
                address_country="US",
                postal_code="12345",
            ),
        )
        wrapped = PaymentInstrument(root=instr)


        pd = PaymentData(payment_data=wrapped)
        final_payload = _dump(pd)
        final_payload["risk_signals"] = {"ip": "127.0.0.1", "browser": "python-httpx"}

        result = store.complete(checkout_id, final_payload)

        tool_context.state[ADK_USER_CHECKOUT_ID] = None
        a2ui_part = render_complete_checkout_a2ui(result,str(uuid.uuid4()))
        return {UCP_CHECKOUT_KEY: result, "a2ui_part":a2ui_part, "status": "success"}

    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error in complete_checkout")
        return _create_error_response(f"Failed to complete checkout: {e.response.text}")
    except Exception:
        logger.exception("There was an error completing the checkout.")
        return _create_error_response(
            "Sorry, there was an error completing the checkout, please try again."
        )





def after_tool_modifier(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    ucp_response_keys = ["a2ui_part"]
    if any(k in tool_response for k in ucp_response_keys):
        tool_context.state[ADK_LATEST_TOOL_RESULT] = tool_response
    return None


def modify_output_after_agent(callback_context: CallbackContext) -> types.Content | None:
    latest_result = callback_context.state.get(ADK_LATEST_TOOL_RESULT)
    if latest_result and "a2ui_part" in latest_result:
        a2ui_part = latest_result["a2ui_part"]
        logging.info(f"a2ui_part received: {a2ui_part}")
        return types.Content(
            parts=[
                types.Part(
                    text=f"a2ui_part:{a2ui_part}"
                    
                )
            ],
            role="model",
        )
    return