# Round Review

Round Review is a PDF platform to manage documents and reviews with collaborators.

## Features

- Create and manage projects with documents
- Invite and manage users for each project
- Upload, view and edit PDFs (it also comes with a night mode!)
- Click & comment on PDF for reviewers and project owners
- Multi-theme support (light/dark)
- Basic and advanced user access (with also Github OAuth integration)
- Notifications and webhook support
- API based: access everything with documented public APIs 
    - (documentation under work)
- Docker-based deployment configurable via .env
- System admin panel management with audit logs
- Bot Integration Review: support for external bots with 3rd-party API for document reviews
    - E.g. #1 - When a document is `Approved`, apply a signature to the PDF.
    - E.g. #2 - You can create your own AI integration to perform LLM-based reviews.

## Installation

1. Clone the repository in your system (`git clone <repo_url>`)
1. Copy the `.env-sample` file, paste it as `config.env` and compile it as needed
1. Install docker and docker compose in your system
1. `docker-compose up -d --build`
1. Go to `localhost:8080`
    - In case of port error, change the port to something else
    - To stop this, use `docker-compose down`

## License and Credits

[Apache 2.0 License](./LICENSE)

Developed by [Maxelweb](https://github.com/Maxelweb) for anyone