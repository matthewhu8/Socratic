combined_model_response_schema = {
    "type": "object",
    "properties": {
        "response": {"type": "string"},
        "svgContent": {"type": ["string", "null"]}
    },
    "required": ["response", "svgContent"]
}