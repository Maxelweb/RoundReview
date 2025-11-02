# Round Review

![RoundReview Platform](https://private-user-images.githubusercontent.com/34033090/503884354-10e6e314-47d0-4db0-a232-e257e738ad3f.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjIxMTE4MjEsIm5iZiI6MTc2MjExMTUyMSwicGF0aCI6Ii8zNDAzMzA5MC81MDM4ODQzNTQtMTBlNmUzMTQtNDdkMC00ZGIwLWEyMzItZTI1N2U3MzhhZDNmLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMDIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTAyVDE5MjUyMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTZiZmFiMGNhMzAxM2U1MzhhYmEyODdmYmRkYTc0MTc5MzQ5NDkwOTA4NGYzNTg0M2U1MzA2NjJlZmJlY2I2YTQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.eq2QcCd1J9LIbgSCxLLOHhCl00Uw3Z2-nPjbtBf7vr0)

Round Review is a PDF platform to manage documents and reviews with collaborators. More [screenshots](https://github.com/Maxelweb/RoundReview/releases/tag/v0.2.0).

> [!NOTE]
> The project is under active development and the current version is in **beta**

## Features

- 📁 **Create and manage projects** with PDF documents  
- 👥 **Invite and manage users** in each project  
- 📄 **Upload, view, and edit PDFs**  
  - Includes **night mode** for comfortable viewing
- 💬 **Click & comment on PDFs** for reviewers and project owners  
- 🎨 **Multi-theme support** (light/dark)  
- 🔐 **Basic and advanced user access**  
  - Includes **GitHub OAuth integration**  
- 🔔 **Webhook support** for notifications  
- 🔌 **API-based access** to all features  
  - 📚 Documentation is currently under development  
- 🐳 **Docker-based deployment** configurable via `.env`  
- 🛡️ **System admin panel** with audit logs  
- 🤖 **Bot Integration Review**  
  - Supports external bots via 3rd-party API for document reviews  
    - 📝 *Example 1:* When a document is `Approved`, apply a signature to the PDF  
    - 🧠 *Example 2:* Create your own AI integration for LLM-based summaries and reviews  

## Installation and Maintenance

> [!IMPORTANT]
> Follow these instructions to get the app running properly

### First installation (with GIT)

1. Clone the repository in your system (`git clone <repo_url>`)
1. Copy the `envs/template.rr-app.env` into `envs/rr-app.env`
1. Edit the environment file according to your needs (see [envs documentation](./docs/envs.md))
1. Install docker and docker compose in your system
1. Start the container: `docker-compose up roundreview_app -d --build`
1. Go to [localhost:8080](http://localhost:8080)
  - In case of port error, change the first port inside the docker-compose file to something else
  - To stop this, use `docker-compose down roundreview_app`


> [!TIP]
> If you want to enable and start the **PDF Notary Bot** plugin follow also these instructions

1. Create a `./certs/` folder within the docker compose file and move inside it: `mkdir ./certs && cd ./certs`

1. Generate a new SSL certificate: `openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout key.pem -out cert.pem`

1. Copy the `envs/template.rr-pdf-notary-bot.env` into `envs/rr-pdf-notary-bot.env`

1. Edit the environment file according to your needs (see [envs documentation](./docs/envs.md))

1. Start the container: `docker-compose up roundreview_pdf_notary_bot -d --build`
    -  In case of port error, change the first port inside the docker-compose file to something else
    - To stop this, use `docker-compose down roundreview_pdf_notary_bot`

### Docker stack management

1. `docker-compose up -d`: Start all containers in the stack
1. `docker-compose down`: Stop all containers in the stack

> [!TIP]
> Copy `docker-compose.yml` and paste as `docker-compose.custom.yml`. Then customize the stack according to your needs.

1. `docker-compose -f docker-compose.custom.yml up -d`
1. `docker-compose -f docker-compose.custom.yml down`

### Version update (with GIT)

1. `git pull` the last updates from the repo
1. `docker-compose up -d --build`: Start and build all containers; this will automatically update the internal database


## Documentation

Go to [docs/](./docs/README.md) folder for more documentation.


## License and Credits

[Apache 2.0 License](./LICENSE)

Developed by [Maxelweb](https://github.com/Maxelweb) for anyone!