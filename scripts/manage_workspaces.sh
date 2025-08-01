#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

disable_workspaces() {
    echo "Disabling workspaces..."

    echo "Renaming pnpm-workspace.yaml to pnpm-workspace.yaml.disabled..."
    if [ -f pnpm-workspace.yaml ]; then
        mv pnpm-workspace.yaml pnpm-workspace.yaml.disabled
        echo "pnpm-workspace.yaml renamed to pnpm-workspace.yaml.disabled"
    else
        echo "pnpm-workspace.yaml not found. Skipping rename."
    fi

    echo "Setting root postinstall script to 'npm run frontend:pnpm_install'..."
    pnpm pkg set scripts.postinstall="npm run frontend:pnpm_install"

    echo "Setting frappe-ui to explicit version in frontend..."
    (cd frontend && pnpm pkg set "dependencies.frappe-ui"="^0.1.140")

    echo "Removing old node_modules to ensure clean install..."
    rm -rf node_modules ./frontend/node_modules/ ./frappe-ui/node_modules/

    echo "Updating frontend to use latest frappe-ui from registry..."
    (cd frontend && pnpm add frappe-ui@latest)

    echo "Workspaces disabled. Frontend will use the latest published frappe-ui."
}

enable_workspaces() {
    echo "Enabling workspaces..."

    echo "Renaming pnpm-workspace.yaml.disabled to pnpm-workspace.yaml..."
    if [ -f pnpm-workspace.yaml.disabled ]; then
        mv pnpm-workspace.yaml.disabled pnpm-workspace.yaml
        echo "pnpm-workspace.yaml.disabled renamed to pnpm-workspace.yaml"
    else
        echo "pnpm-workspace.yaml.disabled not found. Assuming pnpm-workspace.yaml already exists or is not needed."
    fi

    echo "Setting root postinstall script to no-op for active workspaces..."
    pnpm pkg set scripts.postinstall="echo 'Root postinstall disabled as workspaces are active'"

    echo "Updating frontend to use local frappe-ui (workspace:*)..."
    (cd frontend && pnpm pkg set "dependencies.frappe-ui"="workspace:*")

    echo "Removing old node_modules to ensure clean install..."
    rm -rf node_modules ./frontend/node_modules/ ./frappe-ui/node_modules/

    echo "Running pnpm install to link workspaces and install dependencies..."
    pnpm install

    echo "Workspaces enabled. Frontend will use local frappe-ui."
}


ACTION=$1
if [ "$ACTION" == "enable" ]; then
    enable_workspaces
elif [ "$ACTION" == "disable" ]; then
    disable_workspaces
else
    echo "Usage: $0 <enable|disable>"
    exit 1
fi