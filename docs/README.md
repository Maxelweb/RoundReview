# Round Review - Extensive Documentation

> [!WARNING]
> The documentation is under creation and it will be subject to frequent changes

## APIs

- [Integration APIs - v0.1.0](./integration-openapi.yaml)

## Environment Variables

Checkout the environment variables for the app and the plugin [in this page](./envs.md).

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
    "status": "Pending Review"
  },
  "updated_at": "2025-10-12T17:50:16.917017Z"
}
```

#### Possible values

- Event can be: `object.updated`
- Status can be: `No Review`, `Pending Review`, `Under Review`, `Require Changes`, `Approved`


## Development Notes

### Logs and Auditing

All the logs are collected inside a `log` table. 
Every **System Operation** (e.g. db update, first admin creation) is logged for the **System User**.

All the API KEYs created by the user are available to admins for security reasons.

### Database

For portability reasons, the database is a SQLite that lives within the main container. 
All files are saved as blobs for performance reasons.

The database has a table called `rr_db_version` which contains the current db schema and the info of when the db has been updated.

> In future releases, it will be possible to choose between SQLite or MySQL to gain more reading performance.

### Github integration 

The Github Integration works as follows:

1. First, create a new [OAuth Apps](https://github.com/settings/developers) in Github > Settings > Developer Settings
1. Copy the client ID (e.g. `Ov2xxxxxx`) and client Secret (e.g. `xxxxxxxxxxdf21c24f`) from the OAuth Apps.
1. Add the information in your `.env` config file and enable `GITHUB_OAUTH_ENABLED=True`
1. Restart the container (`docker compose up -d`) and login into your app as admin
1. Add (or update) a user and insert its Github Username (e.g. `Maxelweb`)
  - The username is case folded, no worries about UPPER / lower cases.
  - If the user change its username in Github it needs to be updated.
1. Done!

### Permissions

- A member of a project can write/read resources, edit documents (name, description, path, version), remove the documents if is the author and view comments / reviews on documents.
- A reviwer of a project can do everything as the member, and can also add / check / delete comments. It can also remove reviews.
- A owner of a project can do everything as the reviewer, and can also manage users.

At the moment, projects cannot be deleted.

> In future release, there might be possible to make in-depth permissions per-user or per-group according to project owner.
