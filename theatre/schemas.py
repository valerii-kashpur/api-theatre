from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse, OpenApiExample
)

play_list_schema = extend_schema(
    parameters=[
        OpenApiParameter(
            "title",
            description="Play title",
        ),
        OpenApiParameter(
            "genres",
            type={"type": "list", "items": {"type": "integer"}},
            description="Play genres",
        ),
        OpenApiParameter(
            "actors",
            type={"type": "list", "items": {"type": "integer"}},
            description="Play actors",
        ),
    ]
)

reservation_pay_schema = extend_schema(
    summary="Create a payment intent for the reservation"
            " using a test payment method",
    description="Initiates a payment intent for the specified reservation"
                " using Stripe in test mode. Requires a"
                " test payment method ID or token in the request body."
                " Use Stripe's test payment method IDs"
                " (e.g., 'pm_card_visa') for simulation."
                " See https://stripe.com/docs/testing for test data."
                " This endpoint is configured to only accept"
                " card payments without redirects.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "payment_method_id": {
                    "type": "string",
                    "description": "The test payment method ID"
                                   " or token from Stripe"
                                   " (e.g., pm_card_visa for"
                                   " a successful test payment)",
                    "example": "pm_card_visa",
                }
            },
            "required": ["payment_method_id"],
        }
    },
    responses={
        200: OpenApiResponse(
            description="Payment intent created successfully"
                        " with attached payment method",
            examples=[
                OpenApiExample(
                    "Example Response",
                    value={
                        "client_secret": "pi_xxxx_secret_xxxx",
                        "reservation_id": 1,
                        "payment_intent_id": "pi_xxxx",
                    },
                    summary="Successful payment intent creation",
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad request (e.g., reservation already processed,"
                        " invalid payment method, or Stripe error)",
            examples=[
                OpenApiExample(
                    "Error Example",
                    value={"error": "Reservation already processed"},
                    summary="Reservation already processed",
                ),
                OpenApiExample(
                    "Stripe Error Example",
                    value={"error": "Invalid payment method"},
                    summary="Invalid payment method ID",
                ),
            ],
        ),
    },
)

reservation_confirm_payment_schema = extend_schema(
    summary="Confirm the payment for the reservation",
    description="Confirms a payment intent for the specified reservation"
                " using Stripe in test mode. Requires the payment intent"
                " ID from the 'pay' endpoint. The 'id' in the URL path"
                " must be the reservation ID (an integer)."
                " Since the payment method is already attached in"
                " the 'pay' endpoint, this step simply verifies"
                " the payment status.",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location="path",
            description="The unique integer ID of the reservation"
                        " to confirm payment for (e.g., 1)",
            required=True,
        ),
    ],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "payment_intent_id": {
                    "type": "string",
                    "description": "The ID of the"
                                   " Payment Intent from Stripe"
                                   " (e.g., pi_3QwMRqEqE7060X0V8SCABXKv)."
                                   " Use the ID returned from the"
                                   ' "pay" endpoint.',
                    "example": "pi_3QwMRqEqE7060X0V8SCABXKv",
                }
            },
            "required": ["payment_intent_id"],
        }
    },
    responses={
        200: OpenApiResponse(
            description="Payment confirmed successfully",
            examples=[
                OpenApiExample(
                    "Example Response",
                    value={
                        "status": "success",
                        "payment_status": "paid",
                        "payment_intent": {
                            "id": "pi_3QwMRqEqE7060X0V8SCABXKv",
                            "status": "succeeded",
                        },
                    },
                    summary="Successful payment confirmation",
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad request (e.g., invalid payment intent ID,"
                        " reservation not found, or Stripe error)",
            examples=[
                OpenApiExample(
                    "Error Example",
                    value={"error": "Payment intent ID is required"},
                    summary="Missing payment intent ID",
                ),
                OpenApiExample(
                    "Stripe Error Example",
                    value={"error": "Payment intent not found"},
                    summary="Invalid payment intent ID",
                ),
            ],
        ),
    },
)
