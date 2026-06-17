#!/bin/bash
# OCM authentication utilities
# Handles OCM login using token or client credentials

# Authenticate to OCM environment using available credentials
# Checks credentials in order: OCM_TOKEN, OCM_CLIENT_ID+OCM_CLIENT_SECRET
# Returns: 0 on successful login or no credentials available, 1 on error
ocm_authenticate() {
    if [[ -n "${OCM_TOKEN:-}" ]]; then
        log_info "Logging in to the ocm environemnt using OCM_TOKEN"
        ocm login --token "${OCM_TOKEN}"
    else
        if [[ -n "${OCM_CLIENT_ID:-}" &&  -n "${OCM_CLIENT_SECRET:-}" ]]; then
            log_info "Logging in to the ocm environemnt using client_id and secret"
            ocm login --client-id "${OCM_CLIENT_ID}" --client-secret "${OCM_CLIENT_SECRET}"
        else
            log_info "Can not log in to the ocm environemnt due to missing credentials"
        fi
    fi
}
