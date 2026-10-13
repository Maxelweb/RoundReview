# Round Review - Environment Variables

> [!WARNING]
> The documentation is under creation and it will be subject to frequent changes


## Round Review (app)

> [!NOTE]
> Copy the environment file inside `envs/template.rr-app.env` and create `envs/rr-app.env`

| Variable name | Description | Default | Required to change |
|---|---|---|---|
| `RR_APP_NAME` | Application display name visible in the homepage | "Round Review" | No |
| `RR_ADMIN_NAME` | Default administrator username | "admin" | No - Note that you cannot change the name afterwards |
| `RR_ADMIN_EMAIL` | Default administrator email | "admin@system.com" | No — you can change to a real admin email afterwards |
| `RR_DEFAULT_USER_PASSWORD` | Default password for created users (used when not provided) | Random password (generated at runtime) | No |
| `DEBUG` | Enable debug logging and development mode | None (unset) | No — let empty in production and `1` or `True` in development |


### Github OAuth - Extra Configuration

> [!NOTE]
> You can enable Github Authentication for your users using the environment variables in this section.

| Variable name | Description | Default | Required to change|
|---|---|---|---|
| `GITHUB_OAUTH_ENABLED` | Enable GitHub OAuth login | False | Yes - `True` if you want to enable GitHub login; otherwise keep False |
| `GITHUB_OAUTH_CLIENT_ID` | GitHub OAuth app client ID | None | Yes - if `GITHUB_OAUTH_ENABLED` = True |
| `GITHUB_OAUTH_CLIENT_SECRET` | GitHub OAuth app client secret | None | Yes - if `GITHUB_OAUTH_ENABLED` = True |
| `GITHUB_OAUTH_ACCESS_TOKEN_URL` | OAuth access token endpoint | https://github.com/login/oauth/access_token | No — change only for GitHub enterprise/custom endpoints |
| `GITHUB_OAUTH_AUTHORIZE_URL` | OAuth authorize endpoint | https://github.com/login/oauth/authorize | No — change only for GitHub enterprise/custom endpoints |
| `GITHUB_OAUTH_API_BASE_URL` | GitHub API base URL | https://api.github.com/ | No — change only for GitHub enterprise/custom endpoints |
