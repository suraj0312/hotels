
# # agent.py
# # A conversational shopping assistant agent built from the same UCP calls
# # used in simple_happy_path_client.py.

# import os
# import uuid
# from typing import Any, Dict, List, Optional

# import httpx
# from google.adk.agents import Agent
# import litellm

# litellm.ssl_verify = False
# from ucp_sdk.models.schemas.shopping import checkout_create_req
# from ucp_sdk.models.schemas.shopping import checkout_update_req
# from ucp_sdk.models.schemas.shopping import payment_create_req
# from ucp_sdk.models.schemas.shopping.payment_data import PaymentData
# from ucp_sdk.models.schemas.shopping.types import buyer
# from ucp_sdk.models.schemas.shopping.types import item_create_req
# from ucp_sdk.models.schemas.shopping.types import item_update_req
# from ucp_sdk.models.schemas.shopping.types import line_item_create_req
# from ucp_sdk.models.schemas.shopping.types import line_item_update_req
# from ucp_sdk.models.schemas.shopping.types.card_payment_instrument import CardPaymentInstrument
# from ucp_sdk.models.schemas.shopping.types.payment_instrument import PaymentInstrument
# from ucp_sdk.models.schemas.shopping.types.postal_address import PostalAddress
# from ucp_sdk.models.schemas.shopping.types.token_credential_resp import TokenCredentialResponse



# DEFAULT_SERVER_URL = os.getenv("UCP_SERVER_URL", "http://localhost:8182")



# SESSION: Dict[str, Any] = {
#     "server_url": DEFAULT_SERVER_URL,
#     "handlers": None,      
#     "checkout": None,       
#     "checkout_id": None,    
# }


# def _get_headers() -> Dict[str, str]:
#     return {
#         "UCP-Agent": 'profile="https://agent.example/profile"',
#         "request-signature": "test",
#         "idempotency-key": str(uuid.uuid4()),
#         "request-id": str(uuid.uuid4()),
#     }

# def _client(server_url: str) -> httpx.Client:
#     return httpx.Client(base_url=server_url, timeout=30.0)

# def _require_checkout() -> Dict[str, Any]:
#     if not SESSION.get("checkout_id") or not SESSION.get("checkout"):
#         return {
#             "status": "error",
#             "message": "No active checkout yet. Create one first (e.g., 'start a cart with 1 red rose').",
#         }
#     return {"status": "ok"}

# def _line_items_from_session() -> List[Dict[str, Any]]:
#     # Keep line_items in a "PUT-friendly" shape (id optional for new lines).
#     checkout = SESSION["checkout"] or {}
#     return checkout.get("line_items", [])

# def _payment_from_session() -> Dict[str, Any]:
#     checkout = SESSION["checkout"] or {}
#     return checkout.get("payment", {})

# def _currency_from_session() -> str:
#     checkout = SESSION["checkout"] or {}
#     return checkout.get("currency", "USD")

# def _update_session_from_checkout(checkout_json: Dict[str, Any]) -> None:
#     SESSION["checkout"] = checkout_json
#     SESSION["checkout_id"] = checkout_json.get("id")

# def _find_line_item_by_item_id(item_id: str) -> Optional[Dict[str, Any]]:
#     for li in SESSION["checkout"].get("line_items", []):
#         if li.get("item", {}).get("id") == item_id:
#             return li
#     return None

# def _compact_cart_summary(checkout: Dict[str, Any]) -> Dict[str, Any]:
#     line_items = []
#     for li in checkout.get("line_items", []):
#         line_items.append({
#             "line_item_id": li.get("id"),
#             "item_id": li.get("item", {}).get("id"),
#             "title": li.get("item", {}).get("title"),
#             "quantity": li.get("quantity"),
#         })

#     totals = checkout.get("totals", [])
#     total_amount = totals[-1]["amount"] if totals else None

#     discounts_applied = checkout.get("discounts", {}).get("applied", [])
#     discounts = [d.get("code") for d in discounts_applied] if discounts_applied else []

#     return {
#         "checkout_id": checkout.get("id"),
#         "currency": checkout.get("currency"),
#         "items": line_items,
#         "total_cents": total_amount,
#         "discounts_applied": discounts,
#         "has_fulfillment": bool(checkout.get("fulfillment")),
#     }

# # Tools
# def discover_merchant() -> Dict[str, Any]:
#     """Discovery: what services / payment handlers does the merchant support?"""
#     server_url = SESSION["server_url"]
#     with _client(server_url) as c:
#         r = c.get("/.well-known/ucp") # API call
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}

#         data = r.json()
#         handlers = data.get("payment", {}).get("handlers", [])
#         SESSION["handlers"] = handlers
#         return {
#             "status": "success",
#             "server_url": server_url,
#             "payment_handlers": handlers,
#             "raw": data,
#         }
    
# def list_all_items() -> Dict[str, Any]:
#     """
#     Return all the items available in the inventory.
#     """
#     server_url = SESSION["server_url"]
#     with _client(server_url) as c:
#         r = c.get("/get-all-items", headers=_get_headers())
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}
 
#         return {"status": "success", "result": r.json()}

# def start_checkout(
#     currency: str = "USD",
#     buyer_full_name: str = "John Doe",
#     buyer_email: str = "john.doe@example.com",
#     # optional initial item:
#     item_id: str = "bouquet_roses",
#     title: str = "Red Rose",
#     quantity: int = 1,
# ) -> Dict[str, Any]:
#     """
#     Create a new checkout session.
#     """
#     server_url = SESSION["server_url"]

#     if SESSION.get("handlers") is None:
#         # auto-discover for convenience
#         disc = discover_merchant()
#         if disc.get("status") != "success":
#             return disc

#     handlers = SESSION["handlers"] or []

#     payload = {
#         "currency": currency,
#         "line_items": [{"quantity": quantity, "item": {"id": item_id, "title": title}}],
#         "payment": {"instruments": [], "selected_instrument_id": None, "handlers": handlers},
#         "buyer": {"full_name": buyer_full_name, "email": buyer_email},
#     }

#     with _client(server_url) as c:
#         r = c.post("/checkout-sessions", json=payload, headers=_get_headers()) # API call
#         if r.status_code not in (200, 201):
#             return {"status": "error", "code": r.status_code, "body": r.text}

#         data = r.json()
#         _update_session_from_checkout(data)
#         return {"status": "success", "cart": _compact_cart_summary(data)}

# def show_cart() -> Dict[str, Any]:
#     """Show current cart summary (items, totals, discounts)."""
#     chk = _require_checkout()
#     if chk["status"] != "ok":
#         return chk
#     return {"status": "success", "cart": _compact_cart_summary(SESSION["checkout"])}

# def add_item(item_id: str, title: str, quantity: int = 1) -> Dict[str, Any]:
#     """
#     Add an item to the checkout (PUT update). If item already exists, increases quantity.
#     """
#     chk = _require_checkout()
#     if chk["status"] != "ok":
#         return chk

#     server_url = SESSION["server_url"]
#     checkout_id = SESSION["checkout_id"]

#     # extract existing items from session checkout
#     existing_line_items = SESSION["checkout"].get("line_items", [])

#     # Convert existing to update-friendly line items
#     put_line_items: List[Dict[str, Any]] = []
#     for li in existing_line_items:
#         put_line_items.append({
#             "id": li.get("id"),
#             "quantity": li.get("quantity"),
#             "item": {"id": li["item"]["id"], "title": li["item"].get("title", "")},
#         })

#     # If same item_id exists, bump quantity; else add a new line
#     found = False
#     for li in put_line_items:
#         if li["item"]["id"] == item_id:
#             li["quantity"] = int(li.get("quantity", 0)) + int(quantity)
#             # keep title updated if user supplied it
#             li["item"]["title"] = title
#             found = True
#             break

#     if not found:
#         put_line_items.append({"quantity": int(quantity), "item": {"id": item_id, "title": title}})

#     payload = {
#         "id": checkout_id,
#         "currency": _currency_from_session(),
#         "payment": _payment_from_session(),
#         "line_items": put_line_items,
#     }

#     with _client(server_url) as c:
#         r = c.put(f"/checkout-sessions/{checkout_id}", json=payload, headers=_get_headers()) # add items API call
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}

#         data = r.json()
#         _update_session_from_checkout(data)
#         return {"status": "success", "cart": _compact_cart_summary(data)}

# def update_item_quantity(item_id: str, quantity: int) -> Dict[str, Any]:
#     """
#     Set an item's quantity (not add). If quantity <= 0, removes the item.
#     """
#     chk = _require_checkout()
#     if chk["status"] != "ok":
#         return chk

#     server_url = SESSION["server_url"]
#     checkout_id = SESSION["checkout_id"]

#     put_line_items: List[Dict[str, Any]] = []
#     removed = False

#     for li in SESSION["checkout"].get("line_items", []):
#         li_item_id = li.get("item", {}).get("id")
#         if li_item_id == item_id:
#             if int(quantity) <= 0:
#                 removed = True
#                 continue
#             put_line_items.append({
#                 "id": li.get("id"),
#                 "quantity": int(quantity),
#                 "item": {"id": item_id, "title": li.get("item", {}).get("title", "")},
#             })
#         else:
#             put_line_items.append({
#                 "id": li.get("id"),
#                 "quantity": li.get("quantity"),
#                 "item": {"id": li["item"]["id"], "title": li["item"].get("title", "")},
#             })

#     if not put_line_items:
#         return {"status": "error", "message": "Cart would be empty; add an item first."}

#     payload = {
#         "id": checkout_id,
#         "currency": _currency_from_session(),
#         "payment": _payment_from_session(),
#         "line_items": put_line_items,
#     }

#     with _client(server_url) as c:
#         r = c.put(f"/checkout-sessions/{checkout_id}", json=payload, headers=_get_headers())
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}

#         data = r.json()
#         _update_session_from_checkout(data)
#         return {
#             "status": "success",
#             "message": "Removed item." if removed else "Updated quantity.",
#             "cart": _compact_cart_summary(data),
#         }

# def apply_discount(code: str) -> Dict[str, Any]:
#     """
#     Apply a discount code.
#     """
#     chk = _require_checkout()
#     if chk["status"] != "ok":
#         return chk

#     server_url = SESSION["server_url"]
#     checkout_id = SESSION["checkout_id"]

#     # Rebuild full line_items (strict validation friendly, like your script)
#     put_line_items: List[Dict[str, Any]] = []
#     for li in SESSION["checkout"].get("line_items", []):
#         put_line_items.append({
#             "id": li.get("id"),
#             "quantity": li.get("quantity"),
#             "item": {"id": li["item"]["id"], "title": li["item"].get("title", "")},
#         })

#     payload = {
#         "id": checkout_id,
#         "currency": _currency_from_session(),
#         "payment": _payment_from_session(),
#         "line_items": put_line_items,
#         "discounts": {"codes": [code]},
#     }

#     with _client(server_url) as c:
#         r = c.put(f"/checkout-sessions/{checkout_id}", json=payload, headers=_get_headers()) # API call
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}

#         data = r.json()
#         _update_session_from_checkout(data)
#         return {"status": "success", "cart": _compact_cart_summary(data)}

# def start_shipping_and_choose_first_option() -> Dict[str, Any]:
#     """
#     Trigger fulfillment generation and select first destination + first option
#     """
#     chk = _require_checkout()
#     if chk["status"] != "ok":
#         return chk

#     server_url = SESSION["server_url"]
#     checkout_id = SESSION["checkout_id"]

#     # Full line_items
#     put_line_items: List[Dict[str, Any]] = []
#     for li in SESSION["checkout"].get("line_items", []):
#         put_line_items.append({
#             "id": li.get("id"),
#             "quantity": li.get("quantity"),
#             "item": {"id": li["item"]["id"], "title": li["item"].get("title", "")},
#         })

#     with _client(server_url) as c:
#         # trigger
#         payload = {
#             "id": checkout_id,
#             "currency": _currency_from_session(),
#             "payment": _payment_from_session(),
#             "line_items": put_line_items,
#             "fulfillment": {"methods": [{"type": "shipping"}]},
#         }
#         r = c.put(f"/checkout-sessions/{checkout_id}", json=payload, headers=_get_headers()) # API call
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}
#         data = r.json()

#         methods = data.get("fulfillment", {}).get("methods", [])
#         if not methods or not methods[0].get("destinations"):
#             _update_session_from_checkout(data)
#             return {"status": "error", "message": "No shipping destinations returned.", "checkout": data}

#         dest_id = methods[0]["destinations"][0]["id"]

#         # select destination
#         payload["fulfillment"] = {"methods": [{"type": "shipping", "selected_destination_id": dest_id}]}
#         r = c.put(f"/checkout-sessions/{checkout_id}", json=payload, headers=_get_headers())
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}
#         data = r.json()

#         method0 = data.get("fulfillment", {}).get("methods", [{}])[0]
#         groups = method0.get("groups", [])
#         options = groups[0].get("options", []) if groups else []
#         if not options:
#             _update_session_from_checkout(data)
#             return {"status": "error", "message": "No shipping options returned after selecting destination.", "checkout": data}

#         option_id = options[0]["id"]

#         # select option
#         payload["fulfillment"] = {
#             "methods": [{
#                 "type": "shipping",
#                 "selected_destination_id": dest_id,
#                 "groups": [{"selected_option_id": option_id}],
#             }]
#         }
#         r = c.put(f"/checkout-sessions/{checkout_id}", json=payload, headers=_get_headers())
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}
#         data = r.json()
#         _update_session_from_checkout(data)

#         return {
#             "status": "success",
#             "selected_destination_id": dest_id,
#             "selected_option_id": option_id,
#             "cart": _compact_cart_summary(data),
#         }

# def list_payment_handlers() -> Dict[str, Any]:
#     """
#     Return payment handlers the merchant supports (from discovery).
#     If not discovered yet, it will auto-discover.
#     """
#     if SESSION.get("handlers") is None:
#         disc = discover_merchant()
#         if disc.get("status") != "success":
#             return disc
#     return {"status": "success", "payment_handlers": SESSION.get("handlers", [])}

# def complete_payment(handler_id: str = "mock_payment_handler") -> Dict[str, Any]:
#     """
#     Complete checkout payment. Uses a token 'success_token'.
#     """
#     chk = _require_checkout()
#     if chk["status"] != "ok":
#         return chk

#     server_url = SESSION["server_url"]
#     checkout_id = SESSION["checkout_id"]

#     final_payload = {
#         "payment_data": {
#             "id": "instr_my_card",
#             "handler_id": handler_id,
#             "handler_name": handler_id,
#             "type": "card",
#             "brand": "Visa",
#             "last_digits": "4242",
#             "credential": {"type": "token", "token": "success_token"},
#             "billing_address": {
#                 "street_address": "123 Main St",
#                 "address_locality": "Anytown",
#                 "address_region": "CA",
#                 "address_country": "US",
#                 "postal_code": "12345",
#             },
#         },
#         "risk_signals": {"ip": "127.0.0.1", "browser": "python-httpx"},
#     }

#     with _client(server_url) as c:
#         r = c.post(
#             f"/checkout-sessions/{checkout_id}/complete",
#             json=final_payload,
#             headers=_get_headers(),
#         )
#         if r.status_code != 200:
#             return {"status": "error", "code": r.status_code, "body": r.text}

#         return {"status": "success", "result": r.json()}
    


import os
import uuid
from typing import Any, Dict, List, Optional, Callable

import httpx
from google.adk.agents import Agent  # noqa: F401  (kept for your agent wiring)
import litellm

from ucp_sdk.models.schemas.shopping import checkout_create_req
from ucp_sdk.models.schemas.shopping import checkout_update_req
from ucp_sdk.models.schemas.shopping import payment_create_req
from ucp_sdk.models.schemas.shopping.payment_data import PaymentData
from ucp_sdk.models.schemas.shopping.types import buyer
from ucp_sdk.models.schemas.shopping.types import item_create_req
from ucp_sdk.models.schemas.shopping.types import item_update_req
from ucp_sdk.models.schemas.shopping.types import line_item_create_req
from ucp_sdk.models.schemas.shopping.types import line_item_update_req
from ucp_sdk.models.schemas.shopping.types.card_payment_instrument import (
    CardPaymentInstrument,
)
from ucp_sdk.models.schemas.shopping.types.payment_instrument import (
    PaymentInstrument,
)
from ucp_sdk.models.schemas.shopping.types.postal_address import PostalAddress
from ucp_sdk.models.schemas.shopping.types.token_credential_resp import (
    TokenCredentialResponse,
)

litellm.ssl_verify = False

DEFAULT_SERVER_URL = os.getenv("UCP_SERVER_URL", "http://localhost:8182")

SESSION: Dict[str, Any] = {
    "server_url": DEFAULT_SERVER_URL,
    "handlers": None,
    "checkout": None,
    "checkout_id": None,
}


# -----------------------------
# Low-level helpers
# -----------------------------
def _get_headers() -> Dict[str, str]:
    return {
        "UCP-Agent": 'profile="https://agent.example/profile"',
        "request-signature": "test",
        "idempotency-key": str(uuid.uuid4()),
        "request-id": str(uuid.uuid4()),
    }


def _client(server_url: str) -> httpx.Client:
    return httpx.Client(base_url=server_url, timeout=30.0)


def _dump(model_obj: Any) -> Dict[str, Any]:
    # Same behavior as the "correct script"
    return model_obj.model_dump(mode="json", by_alias=True, exclude_none=True)


def _require_checkout() -> Dict[str, Any]:
    if not SESSION.get("checkout_id") or not SESSION.get("checkout"):
        return {
            "status": "error",
            "message": "No active checkout yet. Create one first (e.g., 'start a cart with 1 red rose').",
        }
    return {"status": "ok"}


def _update_session_from_checkout(checkout_json: Dict[str, Any]) -> None:
    SESSION["checkout"] = checkout_json
    SESSION["checkout_id"] = checkout_json.get("id")


def _currency_from_session() -> str:
    checkout = SESSION["checkout"] or {}
    return checkout.get("currency", "USD")


def _payment_from_session() -> Dict[str, Any]:
    checkout = SESSION["checkout"] or {}
    return checkout.get("payment", {}) or {}


def _payment_model_from_session() -> Any:
    """
    CheckoutUpdateRequest.payment type can vary depending on SDK generation.
    We'll try to validate into PaymentCreateRequest; if it fails, we fall back
    to raw dict (most schemas accept it, or allow extra).
    """
    raw = _payment_from_session()
    try:
        # pydantic v2 style
        return payment_create_req.PaymentCreateRequest.model_validate(raw)
    except Exception:
        return raw


def _build_update_line_items(
    existing_line_items: List[Dict[str, Any]],
    mutate_fn: Callable[[List[Dict[str, Any]]], None],
) -> List[line_item_update_req.LineItemUpdateRequest]:
    """
    Convert session line_items (dicts) into typed LineItemUpdateRequest list
    after applying a caller-supplied mutation.
    """
    working: List[Dict[str, Any]] = []
    for li in existing_line_items:
        working.append(
            {
                "id": li.get("id"),
                "quantity": li.get("quantity"),
                "item": {
                    "id": li["item"]["id"],
                    "title": li["item"].get("title", ""),
                },
            }
        )

    mutate_fn(working)

    typed: List[line_item_update_req.LineItemUpdateRequest] = []
    for li in working:
        itm = item_update_req.ItemUpdateRequest(
            id=li["item"]["id"],
            title=li["item"].get("title", ""),
        )
        typed.append(
            line_item_update_req.LineItemUpdateRequest(
                id=li.get("id"),  # may be None for new line items
                quantity=int(li.get("quantity", 0)),
                item=itm,
            )
        )
    return typed


def _compact_cart_summary(checkout: Dict[str, Any]) -> Dict[str, Any]:
    line_items = []
    for li in checkout.get("line_items", []):
        line_items.append(
            {
                "line_item_id": li.get("id"),
                "item_id": li.get("item", {}).get("id"),
                "title": li.get("item", {}).get("title"),
                "quantity": li.get("quantity"),
            }
        )

    totals = checkout.get("totals", [])
    total_amount = totals[-1]["amount"] if totals else None

    discounts_applied = checkout.get("discounts", {}).get("applied", [])
    discounts = [d.get("code") for d in discounts_applied] if discounts_applied else []

    return {
        "checkout_id": checkout.get("id"),
        "currency": checkout.get("currency"),
        "items": line_items,
        "total_cents": total_amount,
        "discounts_applied": discounts,
        "has_fulfillment": bool(checkout.get("fulfillment")),
    }


# -----------------------------
# Tools (UCP-backed)
# -----------------------------
def discover_merchant() -> Dict[str, Any]:
    """Discovery: what services / payment handlers does the merchant support?"""
    server_url = SESSION["server_url"]
    with _client(server_url) as c:
        r = c.get("/.well-known/ucp")  # API call
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        handlers = data.get("payment", {}).get("handlers", [])
        SESSION["handlers"] = handlers
        return {
            "status": "success",
            "server_url": server_url,
            "payment_handlers": handlers,
            "raw": data,
        }


def list_all_items() -> Dict[str, Any]:
    """Return all the items available in the inventory."""
    server_url = SESSION["server_url"]
    with _client(server_url) as c:
        r = c.get("/get-all-items", headers=_get_headers())
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        return {"status": "success", "result": r.json()}


def start_checkout(
    currency: str = "USD",
    buyer_full_name: str = "John Doe",
    buyer_email: str = "john.doe@example.com",
    item_id: str = "bouquet_roses",
    title: str = "Red Rose",
    quantity: int = 1,
) -> Dict[str, Any]:
    """Create a new checkout session."""
    server_url = SESSION["server_url"]

    if SESSION.get("handlers") is None:
        disc = discover_merchant()
        if disc.get("status") != "success":
            return disc

    handlers = SESSION["handlers"] or []

    # Typed line item
    item1 = item_create_req.ItemCreateRequest(id=item_id, title=title)
    line_item1 = line_item_create_req.LineItemCreateRequest(
        quantity=int(quantity), item=item1
    )

    # Typed payment
    payment_req = payment_create_req.PaymentCreateRequest(
        instruments=[],
        selected_instrument_id=None,
        handlers=handlers,
    )

    # Typed buyer
    buyer_req = buyer.Buyer(full_name=buyer_full_name, email=buyer_email)

    create_payload = checkout_create_req.CheckoutCreateRequest(
        currency=currency,
        line_items=[line_item1],
        payment=payment_req,
        buyer=buyer_req,
    )

    payload = _dump(create_payload)

    with _client(server_url) as c:
        r = c.post(
            "/checkout-sessions",
            json=payload,
            headers=_get_headers(),
        )
        if r.status_code not in (200, 201):
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        _update_session_from_checkout(data)
        return {"status": "success", "cart": _compact_cart_summary(data)}


def show_cart() -> Dict[str, Any]:
    """Show current cart summary (items, totals, discounts)."""
    chk = _require_checkout()
    if chk["status"] != "ok":
        return chk
    return {"status": "success", "cart": _compact_cart_summary(SESSION["checkout"])}


def add_item(item_id: str, title: str, quantity: int = 1) -> Dict[str, Any]:
    """Add an item to the checkout (PUT update). If item already exists, increases quantity."""
    chk = _require_checkout()
    if chk["status"] != "ok":
        return chk

    server_url = SESSION["server_url"]
    checkout_id = SESSION["checkout_id"]

    existing = SESSION["checkout"].get("line_items", [])

    def mutate(lines: List[Dict[str, Any]]) -> None:
        found = False
        for li in lines:
            if li["item"]["id"] == item_id:
                li["quantity"] = int(li.get("quantity", 0)) + int(quantity)
                li["item"]["title"] = title
                found = True
                break
        if not found:
            lines.append(
                {
                    "id": None,
                    "quantity": int(quantity),
                    "item": {"id": item_id, "title": title},
                }
            )

    typed_line_items = _build_update_line_items(existing, mutate)

    update_payload = checkout_update_req.CheckoutUpdateRequest(
        id=checkout_id,
        line_items=typed_line_items,
        currency=_currency_from_session(),
        payment=_payment_model_from_session(),
    )

    payload = _dump(update_payload)

    with _client(server_url) as c:
        r = c.put(
            f"/checkout-sessions/{checkout_id}",
            json=payload,
            headers=_get_headers(),
        )
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        _update_session_from_checkout(data)
        return {"status": "success", "cart": _compact_cart_summary(data)}


def update_item_quantity(item_id: str, quantity: int) -> Dict[str, Any]:
    """Set an item's quantity. If quantity <= 0, removes the item."""
    chk = _require_checkout()
    if chk["status"] != "ok":
        return chk

    server_url = SESSION["server_url"]
    checkout_id = SESSION["checkout_id"]

    existing = SESSION["checkout"].get("line_items", [])
    removed = int(quantity) <= 0

    def mutate(lines: List[Dict[str, Any]]) -> None:
        keep: List[Dict[str, Any]] = []
        for li in lines:
            if li["item"]["id"] == item_id:
                if int(quantity) <= 0:
                    continue
                li["quantity"] = int(quantity)
            keep.append(li)
        lines[:] = keep

    typed_line_items = _build_update_line_items(existing, mutate)

    if not typed_line_items:
        return {"status": "error", "message": "Cart would be empty; add an item first."}

    update_payload = checkout_update_req.CheckoutUpdateRequest(
        id=checkout_id,
        line_items=typed_line_items,
        currency=_currency_from_session(),
        payment=_payment_model_from_session(),
    )

    payload = _dump(update_payload)

    with _client(server_url) as c:
        r = c.put(
            f"/checkout-sessions/{checkout_id}",
            json=payload,
            headers=_get_headers(),
        )
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        _update_session_from_checkout(data)
        return {
            "status": "success",
            "message": "Removed item." if removed else "Updated quantity.",
            "cart": _compact_cart_summary(data),
        }


def apply_discount(code: str) -> Dict[str, Any]:
    """Apply a discount code."""
    chk = _require_checkout()
    if chk["status"] != "ok":
        return chk

    server_url = SESSION["server_url"]
    checkout_id = SESSION["checkout_id"]

    existing = SESSION["checkout"].get("line_items", [])

    def mutate(lines: List[Dict[str, Any]]) -> None:
        # no-op: keep items as-is (strict-validation friendly payload)
        return

    typed_line_items = _build_update_line_items(existing, mutate)

    update_payload = checkout_update_req.CheckoutUpdateRequest(
        id=checkout_id,
        line_items=typed_line_items,
        currency=_currency_from_session(),
        payment=_payment_model_from_session(),
    )

    payload = _dump(update_payload)
    payload["discounts"] = {"codes": [code]}

    with _client(server_url) as c:
        r = c.put(
            f"/checkout-sessions/{checkout_id}",
            json=payload,
            headers=_get_headers(),
        )
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        _update_session_from_checkout(data)
        return {"status": "success", "cart": _compact_cart_summary(data)}


def start_shipping_and_choose_first_option() -> Dict[str, Any]:
    """Trigger fulfillment generation and select first destination + first option."""
    chk = _require_checkout()
    if chk["status"] != "ok":
        return chk

    server_url = SESSION["server_url"]
    checkout_id = SESSION["checkout_id"]

    existing = SESSION["checkout"].get("line_items", [])

    def mutate(lines: List[Dict[str, Any]]) -> None:
        return

    typed_line_items = _build_update_line_items(existing, mutate)

    with _client(server_url) as c:
        # Trigger fulfillment generation
        trigger_req = checkout_update_req.CheckoutUpdateRequest(
            id=checkout_id,
            line_items=typed_line_items,
            currency=_currency_from_session(),
            payment=_payment_model_from_session(),
            fulfillment={"methods": [{"type": "shipping"}]},
        )

        payload = _dump(trigger_req)
        r = c.put(
            f"/checkout-sessions/{checkout_id}",
            json=payload,
            headers=_get_headers(),
        )
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        methods = data.get("fulfillment", {}).get("methods", [])

        if not methods or not methods[0].get("destinations"):
            _update_session_from_checkout(data)
            return {
                "status": "error",
                "message": "No shipping destinations returned.",
                "checkout": data,
            }

        dest_id = methods[0]["destinations"][0]["id"]

        # Select destination
        trigger_req.fulfillment = {
            "methods": [{"type": "shipping", "selected_destination_id": dest_id}]
        }
        payload = _dump(trigger_req)

        r = c.put(
            f"/checkout-sessions/{checkout_id}",
            json=payload,
            headers=_get_headers(),
        )
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        method0 = data.get("fulfillment", {}).get("methods", [{}])[0]
        groups = method0.get("groups", [])
        options = groups[0].get("options", []) if groups else []

        if not options:
            _update_session_from_checkout(data)
            return {
                "status": "error",
                "message": "No shipping options returned after selecting destination.",
                "checkout": data,
            }

        option_id = options[0]["id"]

        # Select option
        trigger_req.fulfillment = {
            "methods": [
                {
                    "type": "shipping",
                    "selected_destination_id": dest_id,
                    "groups": [{"selected_option_id": option_id}],
                }
            ]
        }
        payload = _dump(trigger_req)

        r = c.put(
            f"/checkout-sessions/{checkout_id}",
            json=payload,
            headers=_get_headers(),
        )
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        data = r.json()
        _update_session_from_checkout(data)

        return {
            "status": "success",
            "selected_destination_id": dest_id,
            "selected_option_id": option_id,
            "cart": _compact_cart_summary(data),
        }


def list_payment_handlers() -> Dict[str, Any]:
    """
    Return payment handlers the merchant supports (from discovery).
    If not discovered yet, it will auto-discover.
    """
    if SESSION.get("handlers") is None:
        disc = discover_merchant()
        if disc.get("status") != "success":
            return disc
    return {"status": "success", "payment_handlers": SESSION.get("handlers", [])}


def complete_payment(handler_id: str = "mock_payment_handler") -> Dict[str, Any]:
    """Complete checkout payment. Uses a token 'success_token'."""
    chk = _require_checkout()
    if chk["status"] != "ok":
        return chk

    server_url = SESSION["server_url"]
    checkout_id = SESSION["checkout_id"]

    billing_address = PostalAddress(
        street_address="123 Main St",
        address_locality="Anytown",
        address_region="CA",
        address_country="US",
        postal_code="12345",
    )

    credential = TokenCredentialResponse(type="token", token="success_token")

    instr = CardPaymentInstrument(
        id="instr_my_card",
        handler_id=handler_id,
        handler_name=handler_id,
        type="card",
        brand="Visa",
        last_digits="4242",
        credential=credential,
        billing_address=billing_address,
    )

    wrapped_instr = PaymentInstrument(root=instr)
    final_req = PaymentData(payment_data=wrapped_instr)

    final_payload = _dump(final_req)
    final_payload["risk_signals"] = {"ip": "127.0.0.1", "browser": "python-httpx"}

    with _client(server_url) as c:
        r = c.post(
            f"/checkout-sessions/{checkout_id}/complete",
            json=final_payload,
            headers=_get_headers(),
        )
        if r.status_code != 200:
            return {"status": "error", "code": r.status_code, "body": r.text}

        return {"status": "success", "result": r.json()}


