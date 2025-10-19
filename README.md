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
1. Copy the `template.env` file, paste it as `config.env` and compile it as needed
1. Install docker and docker compose in your system
1. `docker-compose up -d --build`
1. Go to `localhost:8080`
    - In case of port error, change the port to something else
    - To stop this, use `docker-compose down`

### Manage containers

1. `docker-compose up -d`: Start all containers
1. `docker-compose down`: Stop all containers

### Version update (with GIT)

1. `git pull` the last updates from the repo
1. `docker-compose up -d --build`: Start and build all containers; this will automatically update the internal database


## Documentation

Go to [docs/](./docs/index.md) folder for more documentation.


## License and Credits

[Apache 2.0 License](./LICENSE)

Developed by [Maxelweb](https://github.com/Maxelweb) for anyone!