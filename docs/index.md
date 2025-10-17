# Round-Review - Documentation

> The documentation is under creation and it can be subject to changes

## APIs

- [Integration APIs - v0.1.0](./integration-openapi.yaml)


## Webhook Notification for Document Status Updates

A webhook is a notification that is triggered inside the system when a document status is updated.

### Notification Details

The notification includes the following details:
- **Event type**: "object.updated"
- **Object ID**: The ID of the object that has been updated
- **Project ID**: The ID of the project associated with the object
- **Updated fields**: A dictionary containing the updated status
- **Updated timestamp**: The current timestamp in ISO 8601 format

Each webhook notification is scheduled to be sent with a slight delay, increasing by 2 seconds for each subsequent user to avoid overwhelming the server with simultaneous requests.


### Example JSON Payload

Here is an example of the JSON payload that would be sent in a POST request after triggering a webhook:

```json
POST https://mywebsite.tld/webhook-handler
{
  "event": "object.updated",
  "object_id": "98eb135f-c083-435a-9929-e6f9ad3810fd",
  "project_id": 1,
  "updated_fields": {
    "status": "Pending Review" // Other possibilities: No Review, Pending Review, Under Review, Require Changes, Approved
  },
  "updated_at": "2025-10-12T17:50:16.917017Z"
}
```
