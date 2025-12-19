# API Gateway Design – Music Soulmate Finder

This document describes the HTTP API Gateway configuration used to expose the **taste profile** Lambda function for the Music Soulmate Finder project.

---

## 1. High-level overview

API Gateway provides a public HTTPS endpoint that the frontend can call from the browser.

Architecture:

[Browser / Frontend JS]
        |
        |  HTTPS POST /taste-profile
        v
[Amazon API Gateway HTTP API]
        |
        v
[AWS Lambda: build_taste_profile handler]
        |
        v
[JSON response back to client]

Key points:

- Type: HTTP API (cheaper and simpler than REST API for this use case)
- Region: us-east-1
- Integration: Lambda proxy integration
- Primary route: POST /taste-profile

2. Base URL and route
The deployed API Gateway base URL is:

```text
https://7rn3olmit4.execute-api.us-east-1.amazonaws.com
```

The main route used by the frontend is:

```text
POST /taste-profile
```

Full URL:

```text
https://7rn3olmit4.execute-api.us-east-1.amazonaws.com/taste-profile
```

3. Request/Response contract
Request
The frontend (in backend/static/app.js) sends a JSON body such as:

```json
{
  "items": {
    "user_id": "spotify:user:briana",
    "top_artists": [
      "NCT 127",
      "Lisa",
      "Red Velvet",
      "NewJeans"
    ],
    "top_genres": [
      "k-pop",
      "k-pop",
      "r&b",
      "pop"
    ],
    "top_tracks": [
      "Favorite – NCT 127",
      "Sticker – NCT 127",
      "No Clue – NCT 127",
      "Thunder – Lisa"
    ]
  }
}
```

Headers (simplified):

```http
Content-Type: application/json
```

The HTTP API is configured to proxy this request directly to the Lambda function.

Response
On success (HTTP 200), Lambda returns JSON similar to:

```json
Copy code
{
  "taste_profile": {
    "summary": "You listen to a lot of energetic k-pop with strong vocals.",
    "favorite_genres": ["k-pop", "r&b", "pop"],
    "favorite_artists": ["NCT 127", "Taeyeon"],
    "sample_tracks": [
      { "name": "Favorite – NCT 127", "artist": "NCT 127" },
      { "name": "Sticker – NCT 127", "artist": "NCT 127" }
    ]
  }
}
```

On error, the API may return:

- HTTP 4xx (e.g., bad request)
- HTTP 5xx if the Lambda fails

In the frontend, non-ok responses are handled by showing an error message and logging the raw response body for debugging.

4. CORS configuration
To allow the local frontend (served by Flask) to call API Gateway from the browser, CORS is enabled.

Typical settings:

- Allowed origin:
  - http://127.0.0.1:5000 (local dev frontend)
- Allowed methods:
  - POST
- Allowed headers:
  - Content-Type

This allows JavaScript running in the browser to call the API without being blocked by CORS.

5. Before vs After (frontend perspective)
Before

[Browser JS] --> GET /taste-profile  (local Flask route)
                       |
                       +--> Local Python function only

- The taste profile was computed locally.
- There was no public API endpoint.

After

[Browser JS] --> POST https://7rn3olmit4.execute-api.us-east-1.amazonaws.com/taste-profile
                       |
                       +--> API Gateway HTTP API
                               |
                               +--> AWS Lambda (build_taste_profile)
Now:

- The browser talks directly to API Gateway.
- Lambda runs the taste profile logic.
- This design is cloud-native and can be reused by any client (web, mobile, etc.).

6. Frontend integration (app.js)
The frontend uses a dedicated base URL constant:

```javascript
const AWS_API_BASE_URL = "https://7rn3olmit4.execute-api.us-east-1.amazonaws.com";
```
And calls the endpoint like this:

```javascript
const response = await fetch(`${AWS_API_BASE_URL}/taste-profile`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(body)
});
```

Where body is the JSON payload described above.

On success:

- The frontend parses response.json().
- Displays the taste profile in the “Taste Profile Summary” card.

On failure:

- Shows an error message (e.g. Error from AWS: HTTP 500).
- Optionally renders the raw error text inside a <pre> for debugging.

7. Design goals
The API Gateway design is intentionally minimal:

- Single POST route for now: /taste-profile
- HTTP API for lower cost and simplicity
- Lambda proxy integration to keep all routing logic in the code
- CORS configured for local development

This sets a clean foundation for future expansion, such as:

- Adding more routes (e.g., /health, /users/{id}/taste-profile)
- Adding authentication/authorization in front of API Gateway
- Storing and retrieving profiles from DynamoDB