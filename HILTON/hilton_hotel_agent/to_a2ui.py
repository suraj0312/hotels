
from typing import List, Any,Dict
def format_price_cents(amount: int, currency: str = "INR") -> str:
    # simple formatter; adapt for INR etc.
    symbol = "₹"
    return f"{symbol}{amount:,.2f}"

items_image_data={
    "bouquet_roses":"http://localhost:10002/static/bouquetroses.png",
    "pot_ceramic":"http://localhost:10002/static/potceramic.png",
    "bouquet_sunflowers":"http://localhost:10002/static/bouquetsunflowers.png",
    "bouquet_tulips":"http://localhost:10002/static/bouquettulips.png",
    "orchid_white":"http://localhost:10002/static/whiteorchid.png", 
    "gardenias":"http://localhost:10002/static/gardenias.png",
    "royal":"https://www.google.com/imgres?q=hotel%20image&imgurl=https%3A%2F%2Fcf.bstatic.com%2Fxdata%2Fimages%2Fhotel%2Fmax1024x768%2F640278495.jpg%3Fk%3Dd01b304a29089108ae381173be12460b5524ea2ce71cf3203fa2dcea36d370a8%26o%3D&imgrefurl=https%3A%2F%2Fwww.booking.com%2Fhotel%2Fae%2Fcopthorne-dubai.html&docid=SmixXHR4jkcACM&tbnid=g8zSZISci39fSM&vet=12ahUKEwjRobrV-PaSAxXBUWcHHSRkOEQQnPAOegQIJxAB..i&w=1024&h=683&hcb=2&ved=2ahUKEwjRobrV-PaSAxXBUWcHHSRkOEQQnPAOegQIJxAB"
}


def render_catalog_results_a2ui(
    products: List[Dict[str, Any]],
    datetime_stamp: str,
    currency: str = "INR",
) -> List[Dict[str, Any]]:
    """
    Use this to render UI. in A2UI formatt.
    """
    surface_id = f"catalog-{datetime_stamp}"

    # Components
    components = [
                    {
                        "id": "catalog_root",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "heading",
                                "productList"
                            ]
                            },
                            "alignment": "center",
                            "distribution": "start"
                        }
                        }
                    },
                    {
                        "id": "heading",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Product Catalog"
                            },
                            "usageHint": "h2"
                        }
                        }
                    },
                    {
                        "id": "productList",
                        "component": {
                        "List": {
                            "children": {
                            "template": {
                                "componentId": "productCard",
                                "dataBinding": "/products"
                            }
                            },
                            "direction": "vertical",
                            "alignment": "stretch"
                        }
                        }
                    },
                    {
                        "id": "productCard",
                        "component": {
                        "Card": {
                            "child": "productCardContent"
                        }
                        }
                    },
                    {
                        "id": "productCardContent",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "productImage",
                                "productDetails",
                                "productInputs",
                            ]
                            },
                            "alignment": "center",
                            "distribution": "start"
                        }
                        }
                    },
                    {
                        "id": "productImage",
                        "component": {
                        "Image": {
                            "url": {
                            "path": "/imageUrl"
                            },
                            "fit": "contain",
                            "usageHint": "mediumFeature"
                        }
                        }
                    },
                    {
                        "id": "productDetails",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "productName",
                                "productPrice"
                            ]
                            },
                            "gap": "large",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "productName",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/name"
                            },
                            "usageHint": "h4"
                        }
                        }
                    },
                    {
                        "id": "productPrice",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/price_cents"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "productInputs",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "quantityInput",
                                "addToCheckoutButton"
                            ]
                            },
                            "gap": "small",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "quantityInput",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "quantityLabel",
                                "quantityField"
                            ]
                            },
                            "gap": "small",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "quantityLabel",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Number of Room"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "quantityField",
                        "component": {
                        "TextField": {
                            "label": {
                            "literalString": ""
                            },
                            "text": {
                            "path": "/quantity"
                            },
                            "textFieldType": "number"
                        }
                        }
                    },
                    {
                        "id": "addToCheckoutButton",
                        "weight": 2,
                        "component": {
                        "Button": {
                            "child": "addToCheckoutButtonText",
                            "action": {
                            "name": "addToCheckout",
                            "context": [
                                {
                                "key": "productId",
                                "value": {
                                    "path": "/id"
                                }
                                },
                                {
                                "key": "name",
                                "value": {
                                    "path": "/name"
                                }
                                },
                                {
                                "key": "quantity",
                                "value": {
                                    "path": "/quantity"
                                }
                                },
                                {
                                "key": "price",
                                "value": {
                                    "path": "/price_cents"
                                }
                                },
                                {
                                "key": "imageUrl",
                                "value": {
                                    "path": "/imageUrl"
                                }
                                },
                            ]
                            },
                            "primary": True
                        }
                        }
                    },
                    {
                        "id": "addToCheckoutButtonText",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Proceed"
                            }
                        }
                        }
                    }
                ]

    # Data model: convert your list into the map-ish structure your example uses
    # Your example uses: valueMap: [{key:"item_0", valueMap:[...]}]
    product_maps = []
    for i, p in enumerate(products):
        product_maps.append(
            {
                "key": f"product_{i}",
                "valueMap": [
                    {"key": "id", "valueString": str(p.get("id", ""))},
                    {"key": "name", "valueString": str(p.get("name", ""))},
                    {"key": "price_cents", "valueString": format_price_cents(int(p.get("price", 0)), currency)},
                    {"key": "imageUrl", "valueString": str(p.get("image_url", ""))},
                    {"key": "quantity", "valueString": "1"}
                ],
            }
        )

    a2ui_messages = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "catalog_root",
                "styles": {"primaryColor": "#FF0000", "font": "Roboto"},
            }
        },
        {"surfaceUpdate": {"surfaceId": surface_id, "components": components}},
        {
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "path": "/",
                "contents": [
                    {"key": "products", "valueMap": product_maps},
                ],
            }
        },
    ]

    return a2ui_messages
 

def render_checkout_results_a2ui(checkout_data:dict,datetime_stamp: str,)->List[Dict[str,any]]:
    surface_id = f"checkoutdetails-{datetime_stamp}"

    components=[
                    {
                        "id": "checkoutdetails_root",
                        "component": {
                        "Card": {
                            "child": "cardContent"
                        }
                        }
                    },
                    {
                        "id": "cardContent",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "header",
                                "checkoutInfo",
                                "itemsList",
                                "divider1",
                                "discountRow",
                                "couponCodeRow",
                                "currencyRow",
                                "totalRow",
                                "startCheckoutBtn"
                            ]
                            },
                            "alignment": "stretch",
                            "gap": "small"
                        }
                        }
                    },
                    {
                        "id": "header",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "headerIcon",
                                "headingText"
                            ]
                            },
                            "gap": "small",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "headerIcon",
                        "component": {
                        "Icon": {
                            "name": {
                            "literalString": "shopping_cart"
                            }
                        }
                        }
                    },
                    {
                        "id": "headingText",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Checkout Details"
                            },
                            "usageHint": "h2"
                        }
                        }
                    },
                    {
                        "id": "checkoutInfo",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": ["checkoutIdLabel","checkoutIdText"]
                            },
                            "distribution": "spaceBetween",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "checkoutIdLabel",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Checkout Id"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "checkoutIdText",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/checkout_id"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "itemsList",
                        "component": {
                        "List": {
                            "children": {
                            "template": {
                                "componentId": "itemTemplate",
                                "dataBinding": "/items"
                            }
                            },
                            "direction": "vertical",
                            "alignment": "stretch"
                        }
                        }
                    },
                    {
                        "id": "itemTemplate",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": ["itemPhoto", "itemName", "itemQuantity", "itemPrice"]
                            },
                            "distribution": "spaceBetween",
                            "alignment": "center",
                            "gap": "large"
                        }
                        }
                    },
                    {
                        "id": "itemPhoto",
                        "weight": 2,
                        "component": {
                        "Image": {
                            "url": {
                            "path": "/image_url"
                            },
                            "fit": "contain",
                            "usageHint": "smallFeature"
                        }
                        }
                    },
                    {
                        "id": "itemName",
                        "weight": 2,
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/name"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "itemQuantity",
                        "weight": 1,
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/quantity"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "itemPrice",
                        "weight": 1,
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/price_cents"
                            },
                            "usageHint": "caption"
                        }
                        }
                    },
                    {
                        "id": "divider1",
                        "component": {
                        "Divider": {
                            "axis": "horizontal"
                        }
                        }
                    },
                    {
                        "id": "discountRow",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": ["discountLabel", "discountValue"]
                            },
                            "distribution": "spaceBetween"
                        }
                        }
                    },
                    {
                        "id": "discountLabel",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Discount"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "discountValue",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/discount"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "couponCodeRow",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": ["couponCodeLabel", "couponCodeValue"]
                            },
                            "distribution": "spaceBetween"
                        }
                        }
                    },
                    {
                        "id": "couponCodeLabel",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Coupon Code"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "couponCodeValue",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/coupon_code"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "currencyRow",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": ["currencyLabel", "currencyValue"]
                            },
                            "distribution": "spaceBetween"
                        }
                        }
                    },
                    {
                        "id": "currencyLabel",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Currency"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "currencyValue",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/currency"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "totalRow",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": ["totalLabel", "totalValue"]
                            },
                            "distribution": "spaceBetween"
                        }
                        }
                    },
                    {
                        "id": "totalLabel",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Total"
                            },
                            "usageHint": "h4"
                        }
                        }
                    },
                    {
                        "id": "totalValue",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/total_cents"
                            },
                            "usageHint": "h4"
                        }
                        }
                    },
                    {
                        "id": "startCheckoutBtn",
                        "component": {
                        "Button": {
                            "child": "startCheckoutBtnText",
                            "primary": True,
                            "action": {
                            "name": "startCheckout"
                            }
                        }
                        }
                    },
                    {
                        "id": "startCheckoutBtnText",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Start Checkout"
                            }
                        }
                        }
                    }
        ]

    currency = checkout_data.get("currency", "INR")
    line_items = checkout_data.get("line_items", [])
    checkout_id = checkout_data.get("id", "")

    # Build items map
    item_maps = []
    for i, item in enumerate(line_items):
        item_data = item.get("item", {})
        quantity = item.get("quantity", 0)

        # Get total amount for this line item
        totals = item.get("totals", [])
        total_amount = next(
            (t.get("amount", 0) for t in totals if t.get("type") == "total"),
            0,
        )

        item_maps.append(
            {
                "key": f"item_{i}",
                "valueMap": [
                    {
                        "key": "image_url",
                        "valueString": str(
                            item_data.get("image_url")
                    
                        ),
                    },
                    {
                        "key": "name",
                        "valueString": str(item_data.get("title", "")),
                    },
                    {
                        "key": "quantity",
                        "valueString": str(quantity),
                    },
                    {
                        "key": "price_cents",
                        "valueString": format_price_cents(
                            int(total_amount), currency
                        ),
                    },
                ],
            }
        )

    # Get checkout total
    checkout_totals = checkout_data.get("totals", [])
    total_amount = next(
        (t.get("amount", 0) for t in checkout_totals if t.get("type") == "total"),
        0,
    )
    discount_amount = next(
        (t.get("amount", 0) for t in checkout_totals if t.get("type") == "discount"),
        0,
    )

   # Gets the first code or None if anything is missing/empty
    # This forces the result of .get() to be a dict/list even if the value found was None
    codes = (checkout_data.get("discounts") or {}).get("codes") or []

    discount_code = next(iter(codes), None)


    a2ui_messages = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "checkoutdetails_root",
                "styles": {"primaryColor": "#FF0000", "font": "Roboto"},
            }
        },
        {"surfaceUpdate": {"surfaceId": surface_id, "components": components}},
        {
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "path": "/",
                "contents": [
                                {"key": "checkout_id", "valueString": str(checkout_id)},
                                {"key": "items", "valueMap": item_maps},
                                {"key": "discount", "valueString": format_price_cents(int(discount_amount), currency)},
                                {"key": "coupon_code", "valueString": str(discount_code)},
                                {"key": "currency", "valueString": str(currency)},
                                {"key": "total_cents", "valueString": format_price_cents(int(total_amount), currency),
                                },
                            ]
            }
        },
    ]
    return a2ui_messages


def render_askuserdetails_a2ui(
    datetime_stamp: str,
) -> List[Dict[str, Any]]:
    """
    Use this to render UI. in A2UI formatt.
    """
    surface_id = f"askuserdetails-{datetime_stamp}"

    # Components
    components =[
                    {
                        "id": "askuserdetails_root",
                        "component": {
                        "Card": {
                            "child": "formColumn"
                        }
                        }
                    },
                    {
                        "id": "formColumn",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "personalDetailsHeading",
                                "firstNameContainer",
                                "lastNameContainer",
                                "emailContainer",
                                "divider1",
                                "addressDetailsHeading",
                                "addressField",
                                "pinCodeCountryRow",
                                "submitButton"
                            ]
                            },
                            "distribution": "start",
                            "alignment": "stretch"
                        }
                        }
                    },
                    {
                        "id": "personalDetailsHeading",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Personal Details"
                            },
                            "usageHint": "h3"
                        }
                        }
                    },
                    {
                        "id": "firstNameContainer",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "firstNameLabel",
                                "firstNameField"
                            ]
                            },
                            "distribution": "spaceBetween",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "firstNameLabel",
                        "weight": 1,
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "First Name"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "firstNameField",
                        "weight": 2,
                        "component": {
                        "TextField": {
                            "label": {
                            "literalString": ""
                            },
                            "text": {
                            "path": "/form/firstName"
                            },
                            "textFieldType": "shortText"
                        }
                        }
                    },
                    {
                        "id": "lastNameContainer",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "lastNameLabel",
                                "lastNameField"
                            ]
                            },
                            "distribution": "spaceBetween",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "lastNameLabel",
                        "weight": 1,
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Last Name"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "lastNameField",
                        "weight": 2,
                        "component": {
                        "TextField": {
                            "label": {
                            "literalString": ""
                            },
                            "text": {
                            "path": "/form/lastName"
                            },
                            "textFieldType": "shortText"
                        }
                        }
                    },
                    {
                        "id": "emailContainer",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "emailLabel",
                                "emailField"
                            ]
                            },
                            "distribution": "spaceBetween",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "emailLabel",
                        "weight": 1,
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Email"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "emailField",
                        "weight": 2,
                        "component": {
                        "TextField": {
                            "label": {
                            "literalString": ""
                            },
                            "text": {
                            "path": "/form/email"
                            },
                            "textFieldType": "longText"
                        }
                        }
                    },
                    {
                        "id": "divider1",
                        "component": {
                        "Divider": {
                            "axis": "horizontal"
                        }
                        }
                    },
                    {
                        "id": "addressDetailsHeading",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Address Details"
                            },
                            "usageHint": "h3"
                        }
                        }
                    },
                    {
                        "id": "addressField",
                        "component": {
                        "TextField": {
                            "label": {
                            "literalString": "Address"
                            },
                            "text": {
                            "path": "/form/address"
                            },
                            "textFieldType": "longText"
                        }
                        }
                    },
                    {
                        "id": "pinCodeCountryRow",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "pinCodeField",
                                "countryField"
                            ]
                            },
                            "distribution": "start",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "pinCodeField",
                        "component": {
                        "TextField": {
                            "label": {
                            "literalString": "Pin Code"
                            },
                            "text": {
                            "path": "/form/pinCode"
                            },
                            "textFieldType": "shortText"
                        }
                        }
                    },
                    {
                        "id": "countryField",
                        "component": {
                        "TextField": {
                            "label": {
                            "literalString": "Country"
                            },
                            "text": {
                            "path": "/form/country"
                            },
                            "textFieldType": "shortText"
                        }
                        }
                    },
                    {
                        "id": "submitButtonText",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Submit"
                            }
                        }
                        }
                    },
                    {
                        "id": "submitButton",
                        "component": {
                        "Button": {
                            "child": "submitButtonText",
                            "primary": True,
                            "action": {
                            "name": "submitForm",
                            "context": [
                                {
                                "key": "firstName",
                                "value": {
                                    "path": "/form/firstName"
                                }
                                },
                                {
                                "key": "lastName",
                                "value": {
                                    "path": "/form/lastName"
                                }
                                },
                                {
                                "key": "email",
                                "value": {
                                    "path": "/form/email"
                                }
                                },
                                {
                                "key": "address",
                                "value": {
                                    "path": "/form/address"
                                }
                                },
                                {
                                "key": "pinCode",
                                "value": {
                                    "path": "/form/pinCode"
                                }
                                },
                                {
                                "key": "country",
                                "value": {
                                    "path": "/form/country"
                                }
                                },
                            ]
                            }
                        }
                        }
                    }
                    ]

    # Data model: convert your list into the map-ish structure your example uses
    # Your example uses: valueMap: [{key:"item_0", valueMap:[...]}]
  
 
    userdetailsform_maps = {
            "key": f"form",
            "valueMap": [
                {"key": "firstName", "valueString": ""},
                {"key": "lastName", "valueString": ""},
                {"key": "email", "valueString": ""},
                {"key": "address", "valueString": ""},
                {"key": "pinCode", "valueString": ""},
                {"key": "country", "valueString": ""},
            ],
        }
    
    a2ui_messages = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "askuserdetails_root",
                "styles": {"primaryColor": "#FF0000", "font": "Roboto"},
            }
        },
        {"surfaceUpdate": {"surfaceId": surface_id, "components": components}},
        {
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "path": "/",
                "contents": [
                    userdetailsform_maps
                ],
            }
        },
    ]

    return a2ui_messages


def render_selectacard_a2ui(
    datetime_stamp: str,
) -> List[Dict[str, Any]]:
    """
    Use this to render UI. in A2UI formatt.
    """
    surface_id = f"selectacard-{datetime_stamp}"

    # Components
    components =[
                    {
                        "id": "selectacard_root",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "header-row",
                                "cards-list"
                            ]
                            },
                            "gap": "large"
                        }
                        }
                    },
                    {
                        "id": "header-row",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "header-text",
                                "header-icon"
                            ]
                            },
                            "distribution": "spaceBetween",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "header-text",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Pay Via Card"
                            },
                            "usageHint": "h3"
                        }
                        }
                    },
                    {
                        "id": "header-icon",
                        "component": {
                        "Icon": {
                            "name": {
                            "literalString": "payment_card"
                            }
                        }
                        }
                    },
                    {
                        "id": "cards-list",
                        "component": {
                        "List": {
                            "children": {
                            "template": {
                                "componentId": "card-item-template",
                                "dataBinding": "/cards"
                            }
                            },
                            "direction": "vertical",
                            "alignment": "stretch"
                        }
                        }
                    },
                    {
                        "id": "card-item-template",
                        "component": {
                        "Card": {
                            "child": "card-main-column"
                        }
                        }
                    },
                    {
                        "id": "card-main-column",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "card-info-column",
                                "pay-button-container"
                            ]
                            },
                            "gap": "medium"
                        }
                        }
                    },
                    {
                        "id": "card-info-column",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "card-type-row",
                                "card-number",
                                "card-details"
                            ]
                            }
                        }
                        }
                    },
                    {
                        "id": "card-type-row",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "card-icon-template",
                                "card-type-template"
                            ]
                            },
                            "distribution": "spaceBetween",
                            "alignment": "center"
                        }
                        }
                    },
                    {
                        "id": "card-icon-template",
                        "component": {
                        "Icon": {
                            "name": {
                            "literalString": "credit_card"
                            }
                        }
                        }
                    },
                    {
                        "id": "card-type-template",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/cardType"
                            },
                            "usageHint": "h4"
                        }
                        }
                    },
                    {
                        "id": "card-number",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/cardNumber"
                            },
                            "usageHint": "h2"
                        }
                        }
                    },
                    {
                        "id": "card-details",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "holder-col",
                                "expiry-col"
                            ]
                            },
                            "distribution": "spaceBetween"
                        }
                        }
                    },
                    {
                        "id": "holder-col",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "holder-label",
                                "holder-name"
                            ]
                            }
                        }
                        }
                    },
                    {
                        "id": "holder-label",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "CARD HOLDER"
                            },
                            "usageHint": "caption"
                        }
                        }
                    },
                    {
                        "id": "holder-name",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/holderName"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "expiry-col",
                        "component": {
                        "Column": {
                            "children": {
                            "explicitList": [
                                "expiry-label",
                                "expiry-date"
                            ]
                            },
                            "alignment": "end"
                        }
                        }
                    },
                    {
                        "id": "expiry-label",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "EXPIRES"
                            },
                            "usageHint": "caption"
                        }
                        }
                    },
                    {
                        "id": "expiry-date",
                        "component": {
                        "Text": {
                            "text": {
                            "path": "/expiryDate"
                            },
                            "usageHint": "body"
                        }
                        }
                    },
                    {
                        "id": "pay-button-container",
                        "component": {
                        "Row": {
                            "children": {
                            "explicitList": [
                                "pay-button"
                            ]
                            },
                            "distribution": "end"
                        }
                        }
                    },
                    {
                        "id": "pay-button",
                        "component": {
                        "Button": {
                            "child": "pay-button-text",
                            "action": {
                            "name": "payWithCard",
                            "context": [
                                {
                                "key": "cardType",
                                "value": {
                                    "path": "/cardType"
                                }
                                },
                                {
                                "key": "cardNumber",
                                "value": {
                                    "path": "/cardNumber"
                                }
                                },
                            ]
                            }
                        }
                        }
                    },
                    {
                        "id": "pay-button-text",
                        "component": {
                        "Text": {
                            "text": {
                            "literalString": "Pay"
                            }
                        }
                        }
                    }
                    ]

    # Data model: convert your list into the map-ish structure your example uses
    # Your example uses: valueMap: [{key:"item_0", valueMap:[...]}]
    cards_data = {
                    "cards": [
                        {
                        "cardType": "Mastercard",
                        "cardNumber": "•••• •••• •••• 5678",
                        "holderName": "UTKARSH ALPURIA",
                        "expiryDate": "09/27"
                        },
                        {
                        "cardType": "Visa",
                        "cardNumber": "•••• •••• •••• 1234",
                        "holderName": "SURAJ KUMAR",
                        "expiryDate": "11/26"
                        }
                    ],
                    "selectedCard": []
                    }
    
    cards_maps = []

    for i, c in enumerate(cards_data["cards"]):
        cards_maps.append(
            {
                "key": f"card_{i}",
                "valueMap": [
                    {"key": "cardType", "valueString": str(c.get("cardType", ""))},
                    {"key": "cardNumber", "valueString": str(c.get("cardNumber", ""))},
                    {"key": "holderName", "valueString": str(c.get("holderName", ""))},
                    {"key": "expiryDate", "valueString": str(c.get("expiryDate", ""))},
                ],
            }
        )

    a2ui_messages = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "selectacard_root",
                "styles": {"primaryColor": "#FF0000", "font": "Roboto"},
            }
        },
        {"surfaceUpdate": {"surfaceId": surface_id, "components": components}},
        {
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "path": "/",
                "contents": [
                    {"key": "cards", "valueMap": cards_maps},
                ],
            }
        },
    ]

    return a2ui_messages
 




def render_complete_checkout_a2ui(checkout_data:dict,datetime_stamp: str,)->List[Dict[str,any]]:
    surface_id = f"completecheckout-{datetime_stamp}"

    components=[
                {
                    "id": "completecheckout_root",
                    "component": {
                    "Card": {
                        "child": "main-column"
                    }
                    }
                },
                {
                    "id": "main-column",
                    "component": {
                    "Column": {
                        "children": {
                        "explicitList": [
                            "success-icon",
                            "title",
                            "product-list",
                            "divider",
                            "details-col",
                            "view-btn"
                        ]
                        },
                        "gap": "medium",
                        "alignment": "center"
                    }
                    }
                },
                {
                    "id": "success-icon",
                    "component": {
                    "Icon": {
                        "name": {
                        "literalString": "check_circle"
                        }
                    }
                    }
                },
                {
                    "id": "title",
                    "component": {
                    "Text": {
                        "text": {
                        "literalString": "Purchase Complete"
                        },
                        "usageHint": "h2"
                    }
                    }
                },
                {
                    "id": "product-list",
                    "component": {
                    "List": {
                        "children": {
                        "template": {
                            "componentId": "product-item-template",
                            "dataBinding": "/products"
                        }
                        },
                        "direction": "vertical",
                        "alignment": "start"
                    }
                    }
                },
                {
                    "id": "product-item-template",
                    "component": {
                    "Row": {
                        "children": {
                        "explicitList": [
                            "product-image",
                            "product-details-row"
                        ]
                        },
                        "gap": "medium",
                        "alignment": "center"
                    }
                    }
                },
                {
                    "id": "product-image",
                    "component": {
                    "Image": {
                        "url": {
                        "path": "/image_url"
                        },
                        "altText": {
                        "path": "/name"
                        },
                        "fit": "contain",
                        "usageHint": "smallFeature"
                    }
                    }
                },
                {
                    "id": "product-details-row",
                    "component": {
                    "Row": {
                        "children": {
                        "explicitList": [
                            "product-name",
                            "product-qty",
                            "product-price"
                        ]
                        },
                        "gap": "medium",
                        "alignment": "center"
                    }
                    }
                },
                {
                    "id": "product-name",
                    "component": {
                    "Text": {
                        "text": {
                        "path": "/name"
                        },
                        "usageHint": "h4"
                    }
                    }
                },
                {
                    "id": "product-qty",
                    "component": {
                    "Text": {
                        "text": {
                        "path": "/quantity"
                        },
                        "usageHint": "body"
                    }
                    }
                },
                {
                    "id": "product-price",
                    "component": {
                    "Text": {
                        "text": {
                        "path": "/price_cents"
                        },
                        "usageHint": "body"
                    }
                    }
                },
                {
                    "id": "divider",
                    "component": {
                    "Divider": {}
                    }
                },
                {
                    "id": "details-col",
                    "component": {
                    "Column": {
                        "children": {
                        "explicitList": [
                            "delivery-row",
                            "total-price",
                            "buyer-row"
                        ]
                        },
                        "gap": "small"
                    }
                    }
                },
                {
                    "id": "delivery-row",
                    "component": {
                    "Row": {
                        "children": {
                        "explicitList": [
                            "delivery-icon",
                            "delivery-text"
                        ]
                        },
                        "gap": "small",
                        "alignment": "center"
                    }
                    }
                },
                {
                    "id": "delivery-icon",
                    "component": {
                    "Icon": {
                        "name": {
                        "literalString": "local_shipping"
                        }
                    }
                    }
                },
                {
                    "id": "delivery-text",
                    "component": {
                    "Text": {
                        "text": {
                        "path": "/deliveryDate"
                        },
                        "usageHint": "body"
                    }
                    }
                },
                {
                    "id": "total-price",
                    "component": {
                    "Text": {
                        "text": {
                        "path": "/totalPrice"
                        },
                        "usageHint": "h4"
                    }
                    }
                },
                {
                    "id": "buyer-row",
                    "component": {
                    "Row": {
                        "children": {
                        "explicitList": [
                            "buyer-label",
                            "buyer-name"
                        ]
                        },
                        "gap": "small"
                    }
                    }
                },
                {
                    "id": "buyer-label",
                    "component": {
                    "Text": {
                        "text": {
                        "literalString": "Purchased by:"
                        },
                        "usageHint": "caption"
                    }
                    }
                },
                {
                    "id": "buyer-name",
                    "component": {
                    "Text": {
                        "text": {
                        "path": "/buyer"
                        },
                        "usageHint": "body"
                    }
                    }
                },
                {
                    "id": "view-btn-text",
                    "component": {
                    "Text": {
                        "text": {
                        "literalString": "View Order Details"
                        }
                    }
                    }
                },
                {
                    "id": "view-btn",
                    "component": {
                    "Button": {
                        "child": "view-btn-text",
                        "action": {
                        "name": "view_details"
                        }
                    }
                    }
                }
                ]
    currency = checkout_data.get("currency", "INR")
    line_items = checkout_data.get("line_items", [])
    checkout_id = checkout_data.get("id", "")

    # Build items map
    item_maps = []
    for i, item in enumerate(line_items):
        item_data = item.get("item", {})
        quantity = item.get("quantity", 0)

        # Get total amount for this line item
        totals = item.get("totals", [])
        total_amount = next(
            (t.get("amount", 0) for t in totals if t.get("type") == "total"),
            0,
        )

        item_maps.append(
            {
                "key": f"item_{i}",
                "valueMap": [
                    {
                        "key": "image_url",
                        "valueString": str(
                            item_data.get("image_url")
                         
                        ),
                    },
                    {
                        "key": "name",
                        "valueString": str(item_data.get("title", "")),
                    },
                    {
                        "key": "quantity",
                        "valueString": str(quantity),
                    },
                    {
                        "key": "price_cents",
                        "valueString": format_price_cents(
                            int(total_amount), currency
                        ),
                    },
                ],
            }
        )

    # Get checkout total
    checkout_totals = checkout_data.get("totals", [])
    total_amount = next(
        (t.get("amount", 0) for t in checkout_totals if t.get("type") == "total"),
        0,
    )
    discount_amount = next(
        (t.get("amount", 0) for t in checkout_totals if t.get("type") == "discount"),
        0,
    )

   # Gets the first code or None if anything is missing/empty
    # This forces the result of .get() to be a dict/list even if the value found was None
    codes = (checkout_data.get("discounts") or {}).get("codes") or []

    discount_code = next(iter(codes), None)

    buyer = checkout_data.get("buyer",{}).get("full_name","Not Available")
    # Returns "Unknown" if the name is missing

    group = checkout_data["fulfillment"]["methods"][0]["groups"][0]

    selected_id = group["selected_option_id"]

    selected_title = None
    selected_amount = None

    for option in group["options"]:
        if option["id"] == selected_id:
            selected_title = option["title"]
            # Access the 'amount' from the last item in the 'totals' list
            selected_amount = option["totals"][-1]["amount"]
            break


    a2ui_messages = [
        {
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "completecheckout_root",
                "styles": {"primaryColor": "#FF0000", "font": "Roboto"},
            }
        },
        {"surfaceUpdate": {"surfaceId": surface_id, "components": components}},
        {
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "path": "/",
                "contents": [
                                {"key": "products", "valueMap": item_maps},
                                {"key": "buyer", "valueString":str(buyer)} ,
                                {"key": "deliveryDate", "valueString": f"{selected_title} - {format_price_cents(int(selected_amount), currency)}"},
                                {"key": "totalPrice", "valueString": f"Total - {format_price_cents(int(total_amount), currency)}"},
                            ]
            }
        },
    ]
    return a2ui_messages

 

