# Round Review

Round Review is a PDF platform to manage documents and reviews with collaborators.

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

### First installation (with GIT)

1. Clone the repository in your system (`git clone <repo_url>`)
1. Copy the `envs/template.rr-app.env` into `envs/rr-app.env`
1. Edit the environment file according to your needs
1. Install docker and docker compose in your system
1. Start the container: `docker-compose up roundreview_app -d --build`
1. Go to [localhost:8080](http://localhost:8080)
  - In case of port error, change the first port inside the docker-compose file to something else
  - To stop this, use `docker-compose down roundreview_app`

Extras: if you want to start the **PDF Notary Bot** plugin follow these instructions:

1. Create a `./certs/` folder within the docker compose file and move inside it
  - E.g. `mkdir ./certs && cd ./certs`
1. Generate a new SSL certificate.
  - E.g. `openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout key.pem -out cert.pem`
1. Copy the `envs/template.rr-pdf-notary-bot.env` into `envs/rr-pdf-notary-bot.env`
1. Edit the environment file according to your needs
1. Start the container: `docker-compose up roundreview_pdf_notary_bot -d --build`
  - In case of port error, change the first port inside the docker-compose file to something else
  - To stop this, use `docker-compose down roundreview_pdf_notary_bot`

### Stack management

> Tip: copy `docker-compose.yml` into `docker-compose.custom.yml` to customize the stack

1. `docker-compose up -d`: Start all containers in the stack
1. `docker-compose down`: Stop all containers in the stack

### Version update (with GIT)

1. `git pull` the last updates from the repo
1. `docker-compose up -d --build`: Start and build all containers; this will automatically update the internal database


## Documentation

Go to [docs/](./docs/index.md) folder for more documentation.


## License and Credits

[Apache 2.0 License](./LICENSE)

Developed by [Maxelweb](https://github.com/Maxelweb) for anyone!