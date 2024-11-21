<div align="center">
  <a href="https://frappe.io/products/builder">
    <img src=".github/new_logo.svg" height="80" alt="Frappe Builder Logo">
  </a>
  <h2>Frappe Drive</h2>
  <p>100% open source file storage, sharing, and collaboration</p>

![Frappe Drive](https://github.com/user-attachments/assets/8b4b33ad-afb4-4e64-ac10-987076c66d57)

<details>
<summary>More screenshots</summary>

![Image Preview](https://github.com/user-attachments/assets/993cbd87-a96c-4e5c-8737-0c03c9222723)

![File Sharing Dialog](https://github.com/user-attachments/assets/acb1a542-53d1-4d0e-b2e2-6c9b87f04e69)

![Editor](https://github.com/user-attachments/assets/fe87dfd1-3f55-42df-94b9-f7baed03a391)

![Editor with real time editing](https://github.com/user-attachments/assets/f89a2fab-e618-4d7d-90a6-aaa2cf45fa55)

</details>

<div align="center" style="max-height: 55px; margin: 20px 0px">
<a href="https://frappecloud.com/drive/signup">
<picture>

  <source media="(prefers-color-scheme: light)" srcset=".github/try_on_FC_light.svg">

  <source media="(prefers-color-scheme: dark)" srcset=".github/try_on_FC_dark.svg">

  <img height="50" src=".github/try_on_FC_light.svg"  width="50%" title="Try Frappe Drive on Frappe Cloud" >
	
  </picture>
</a>
</div>

[Website](https://frappe.io/drive) <!-- | [Demo](https://www.figma.com/community/file/949266436474872912) --> | [Community](https://t.me/frappedrive) | [Documentation](https://docs.frappe.io/drive/quick-start) | [Forum](https://discuss.frappe.io/)

</div>

### Features

Core — the file manager

- Large file uploads using multi-part uploads
- Folder uploads to maintain your structure in Drive
- Access your files across multiple platforms
- Preview files directly in your browser, [supported file previews](https://docs.frappe.io/drive/previews)
- Stream videos directly from the server
- Search for all your files and files shared shared with you
- View activity logs of a file to glance at the changes in permissions and file metadata
- Manage folders in list or grid view and sort them by preference
- Mark files as favorite and track your recently viewed files
- Tag files and folders for better organization
- Filter by tags or file kind
- Share files and folders with users, groups, everyone on the site or publish publicly
- Make user groups to collaborate quickly
- Invite other users by emailing them directly from Drive
- Work with guest users who have limited and controlled access to your site
- Get an overview of your storage
- Pool storage of all users together or assign a quota of storage to each user

Writer — the document editor

- Quickly write and share an idea directly from Drive
- The WYSIWYG editor supports markdown
- Collaborate with other users or guests in real time
- Annotate, resolve and reply to other users to give suggestions
- Manually version your documents to always be able to go back to a state
- Automatic versioning to make sure you never lose data
- Resize videos and images inside your document
- Import docx documents into the editor
- Export your documents in PDF
- The editor is page-less but you can add page breaks to make sure you get your desired output when printing

> [!WARNING]  
> If you're self hosting Frappe Drive. Do not use the app as the only way to store your files. Always have backup strategy for your files.
>
> Otherwise, consider our managed hosting on [Frappe Cloud](https://frappecloud.com/). It's the same exact code as from the `main` branch here, but with better support tooling and automated backups.

### Installation

To set up the repository locally, follow the steps mentioned below:

### Docker Compose [Recommended]

The quickest way to set up Frappe Drive and take it for a test _drive_.

Frappe framework is multi-tenant and supports multiple apps by default. This docker compose is just a standalone version with Frappe Drive pre-installed. Just put it behind your desired reverse-proxy if needed, and you're good to go.

If you wish to use multiple Frappe apps or need multi-tenancy. I suggest moving over to our production ready self-hosted workflow, or join us on Frappe Cloud to get first party support and hassle-free hosting.

**Step 1**: Setup folder and download the required files

```
mkdir frappe-drive
cd frappe-drive
```

**Step 2**: Download the required files

Docker Compose File:

```
wget -O docker-compose.yml https://raw.githubusercontent.com/frappe/drive/main/docker/docker-compose.yml
```

Frappe Drive Bench Setup Script

```
wget -O init.sh https://raw.githubusercontent.com/frappe/drive/main/docker/init.sh
```

**Step 3**: Run the container and daemonize it

```
docker compose up -d
```

### Normal Bench Install

Install bench and set up a `frappe-bench` directory by following the [installation steps](https://frappeframework.com/docs/user/en/installation).

**Step 1**: [Install Bench.](https://frappeframework.com/docs/user/en/installation)

**Step 2**: Provided bench is all set up you can proceed to install Frappe Drive

```sh
bench get-app drive --branch main
```

**Step 3**: Install some Drive specific system packages

Ubuntu/Debian (apt based distros)

```sh
sudo apt install ffmpeg libmagic
```

MacOs

```sh
brew install libmagic ffmpeg
```

**Step 4**: Install drive once it's downloaded

```
bench install-app drive
```

**Step 5**: Start bench if it's not already running

```
bench start
```

Frappe Drive should be accessible at `localhost:8000` or `sitename:8000`

### Contributions and Community

There are many ways you can contribute even if you don't code:

1. You can start by giving a star to this repository!
1. If you find any issues, even if it is a typo, you can [raise an issue](https://github.com/frappe/drive/issues/new) to inform us.
<!-- If you want to contribute code then you can fork this repo, make changes and raise a PR. ([see how to](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork)) -->

### License

[GNU Affero General Public License v3.0](LICENSE)

<!-- # Docker

This guide provides step-by-step instructions to install the project using Docker via VS Code Remote Containers extension.

## Prerequisites

Before you begin, make sure you have the following prerequisites installed on your system:

1. [Docker](https://docs.docker.com/get-docker/)
2. [Docker Compose](https://docs.docker.com/compose/install/)
3. User added to docker group
   ```shell
   sudo usermod -aG docker $USER
   ```
4. [VS Code Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Step 1: Cloning frappe_docker repo

```shell
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

### Step 2: Copy example devcontainer config from devcontainer-example to .devcontainer

Note:

Feel free to explore the files within devcontainer-example and make changes to the same, be that exposing DB ports or mount desired additional volumes.

```shell
cp -R devcontainer-example .devcontainer
```

### Step 3: Copy example VS Code config for devcontainer from development/vscode-example to development/.vscode.

This will set up basic configuration for debugging.

```shell
cp -R development/vscode-example development/.vscode
```

### Step 4: Open frappe_docker folder in VS Code(After the extensions are installed).

```shell
code .
```

Note:

The development directory is ignored by git.
It is mounted and available inside the container. Create all your benches (installations of bench, the tool that manages frappe) inside this directory.

### Step 5: Setup Bench

Run the following commands in the terminal inside the container. You might need to create a new terminal in VSCode.

```shell
# Use default environments
bench init --skip-redis-config-generation --frappe-branch version-14 frappe-bench
# Or set environment versions explicitly
nvm use v16
PYENV_VERSION=3.10.5 bench init --skip-redis-config-generation --frappe-branch version-14 frappe-bench

cd frappe-bench

```

### Step 6: Setup hosts

We need to tell bench to use the right containers instead of localhost. Run the following commands inside the container:

```shell
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-socketio:6379
```

For any reason the above commands fail, set the values in `common_site_config.json` manually.

```json
{
  "db_host": "mariadb",
  "redis_cache": "redis://redis-cache:6379",
  "redis_queue": "redis://redis-queue:6379",
  "redis_socketio": "redis://redis-socketio:6379"
}
```

### Step 7: Create a new site

Note: `sitename` must end with` .localhost` for trying deployments locally.

for example:

```shell
bench new-site mydrive.localhost --no-mariadb-socket
```

The same command can be run non-interactively as well:

```shell
bench new-site mydrive.localhost --mariadb-root-password 123 --admin-password admin --no-mariadb-socket
```

### Step 8: Set bench in developer mode on the new site

```shell
bench --site mydrive.localhost set-config developer_mode 1
bench --site mydrive.localhost clear-cache
```

### Step 9: Set current site

```shell
bench use mydrive.localhost
```

### Step 10: Install the Drive app onto the site created

```shell
bench get-app https://github.com/frappe/drive

bench --site mydrive.localhost install-app drive
```

### Step 11: Start Bench

Execute the following command from the `frappe-bench` directory.

```shell
bench start
```

### Step 12: Start the frontend development server

You are all set now :)

```shell
cd apps/drive && yarn dev
```

Finally, open the URL http://mydrive.localhost:8000/drive in your browser to see the app running.
 -->
