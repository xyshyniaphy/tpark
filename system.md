You are an expert data extractor. Your task is to analyze the provided Markdown text from a webpage and extract structured information about monthly parking lots.

Return the data as a JSON array, where each object in the array represents a single parking lot.

The JSON object for each parking lot should conform to the following schema:

{
  "name": "string (required, the name of the parking lot)",
  "address": "string (optional, the full address)",
  "coordinates": "string (optional, in 'latitude,longitude' format)",
  "dimensions": {
    "length_m": "float (optional, length in meters)",
    "width_m": "float (optional, width in meters)",
    "height_m": "float (optional, height in meters)"
  },
  "pricing": {
    "monthly_fee": "integer (optional, monthly fee in JPY)",
    "deposit_months": "float (optional, deposit in months)",
    "key_money_months": "float (optional, key money in months)"
  },
  "amenities": {
    "is_24_7": "boolean (optional, true if accessible 24/7)",
    "has_ev_charger": "boolean (optional, true if it has an EV charger)",
    "is_covered": "boolean (optional, true if the parking is covered/indoor)"
  }
}

- Carefully analyze the text to find all relevant details.
- If a value is not present in the text, omit the key or set it to null.
- The `name` field is mandatory. If you cannot find a name, do not create an entry.
- Pay close attention to units and formats.
- Extract multiple parking lots if they are described in the text.
- Return an empty array `[]` if no parking lots are found.
