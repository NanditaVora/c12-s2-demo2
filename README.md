# Sprint 2 — Demo 2: Build and Deploy a Containerised Service 
## Purpose

Use the supplied Python application to build a container image, push it to Floci's local registry, deploy it through ECS and verify that it responds.

**Learning outcome:** Build and push a container image to a local registry, deploy it on Floci's ECS, and verify that it responds.

GitHub Actions can run the tests. Image publishing and deployment use local commands.

## Problem statement

Use the supplied Python application to build a container image, push it to Floci’s local 
registry and deploy it through ECS using the execution role created in Demo 1.​

Run the application tests locally, push the source code to GitHub and confirm that GitHub 
Actions tests pass. Use local commands to build the image, tag it with the Git commit SHA, 
publish it and deploy the ECS service.​

Verify that the task is healthy, /health returns the expected version and /chat returns a 
reply. Check the application logs and saved deployment evidence to confirm success.​

## Before starting

**The application and supporting scripts are supplied so learners can focus on building, publishing and deploying the container. Each file includes a brief description of its role; detailed code walkthroughs are outside the scope of this demo.**

- Use **Windows PowerShell** in the supplied Demo 2 project root, containing `app.py`, `Dockerfile`, `requirements.txt` and `scripts`.
- Docker Desktop must be running in **Linux containers** mode.
- Python 3.12, AWS CLI v2 and Git must be installed.
- Demo 1 must be completed on this Windows machine, with its Floci `data` folder retained.
- Profile `floci` must use local credentials `test` / `test`, region `us-east-1`, output `json`.
- Internet access is needed for dependency installation and image downloads.

Keep the same PowerShell window open throughout. Folder variables such as `$Demo1Folder` and environment variables are not automatically retained in a new terminal. Stop at an error and resolve it before continuing.

**Do not copy Demo 1's `data` folder into Demo 2.** The commands below use it directly. Keeping only `execution-role-arn.txt` does not retain the IAM role; the role is stored in Floci's data.

## Supplied files

| File / folder | What the code does |
|---|---|
| `app.py` | Provides `/health` to check the application and `/chat` to return a simple reply. |
| `requirements.txt` | Lists the Python packages and versions required by the application. |
| `Dockerfile` | Builds a container image containing the application and its dependencies, then runs it as a non-root user. |
| `docker-compose.yml` | Runs Floci 2.2.0 with the settings needed for a local registry and real ECS containers. |
| `.github/workflows/ci.yml` | Runs the application tests automatically when code is pushed to `main`. |
| `ecs/task-definition.template.json` | Defines how ECS runs the container: image, execution role, CPU, memory, port, health check and logs. |
| `scripts/__init__.py` | Makes the scripts folder a Python package so commands such as `python -m scripts.publish` work. |
| `scripts/local_cloud.py` | Provides shared helpers for calling local Floci APIs, retrieving the execution role and saving generated files. |
| `scripts/prepare_local.py` | Prepares the image repository, log group, ECS cluster and placement resources; saves their details locally. |
| `scripts/publish.py` | Builds the image, signs in to the registry and pushes it with the Git commit SHA as its tag. |
| `scripts/deploy.py` | Deploys the image through ECS, checks task health and application responses, and saves evidence. |
| `tests/` | Checks application responses, invalid inputs and selected deployment configuration rules. |
| `.gitignore` | Prevents local data, virtual environments, credentials and generated files from being committed. |
| `.dockerignore` — if supplied | Excludes unnecessary local files from the Docker build context. |
| `README.md` | Gives the commands, their purpose and the expected results for completing the demo. |

`/chat` returns a fixed reply. No external model or API key is needed.

## 1. Check the tools

```powershell
docker version
docker compose version
py -3.12 --version
aws --version
git --version
```

**Why:** Checks the tools before deployment.

**Expected:** Docker client/server information, Compose version, Python 3.12, AWS CLI v2 and Git version. If Docker server information is missing, start Docker Desktop. If Python 3.12 is missing, resolve the installation before continuing.

## 2. Set the folder locations and standard Compose filename

In the Demo 2 root:

```powershell
$Demo2Folder = (Get-Location).Path
$Demo1Folder = 'C:\full\path\to\Demo1'
```

**Why:** Records the current Demo 2 folder and the completed Demo 1 folder. Replace the second line's example path with your actual Windows path. Quotes allow spaces in folder names.

For example, a folder under Documents could be:

```powershell
$Demo1Folder = "$env:USERPROFILE\Documents\Course12\Sprint 2\Demo1"
```

This is only an example; use the location that actually contains your Demo 1 files.

```powershell
$Demo2Folder
$Demo1Folder
Get-ChildItem $Demo1Folder
```

**Why:** Checks both saved paths.

**Expected:** Demo 1's file list includes `docker-compose.yml`, `data` and the policy files.

The standard filename for Demo 2 is **`docker-compose.yml`**. If the older supplied folder still has `docker-compose.example.yml`, rename it once:

```powershell
if (!(Test-Path '.\docker-compose.yml')) {
    Rename-Item '.\docker-compose.example.yml' 'docker-compose.yml'
}
```

**Why:** Standardises the filename without replacing an existing Compose file.

### Use the version verified during rehearsal

Open Demo 2's `docker-compose.yml` in your editor. Set its existing image line to:

```yaml
image: floci/floci:2.2.0
```

Keep the other supplied settings. In particular, the file must retain:

```yaml
FLOCI_SERVICES_ECS_MOCK: "false"
FLOCI_SERVICES_ECS_DOCKER_NETWORK: sprint2-local
FLOCI_SERVICES_ECS_PUBLISH_AWSVPC_PORTS_TO_HOST: "true"
FLOCI_SERVICES_ECS_IMAGE_PULL_BEHAVIOR: always
```

**Why:** The Ubuntu rehearsal succeeded with Floci 2.2.0. Version 2.1.0 did not publish the application port or return the health status required by the deployment script. Pinning the verified version avoids silently reusing an older `latest` image. The final classroom files should already contain this version and filename.

## 3. Start Floci using Demo 1's retained data

```powershell
docker compose -f "$Demo1Folder\docker-compose.yml" down
```

**Why:** Stops Demo 1's Floci before starting the deployment configuration. Its bind-mounted data remains in place. If already stopped, continue.

```powershell
docker compose --project-directory "$Demo1Folder" -f "$Demo2Folder\docker-compose.yml" config
```

**Why:** Checks the resolved configuration. `-f` selects Demo 2's file, while `--project-directory` makes `./data` refer to Demo 1's existing data.

**Expected:** The resolved data mount points to **Demo1/data**. Do not continue if it points to an empty or different folder.

```powershell
docker compose --project-directory "$Demo1Folder" -f "$Demo2Folder\docker-compose.yml" pull floci
```

**Why:** Downloads the pinned Floci version.

```powershell
docker compose --project-directory "$Demo1Folder" -f "$Demo2Folder\docker-compose.yml" up -d
docker compose --project-directory "$Demo1Folder" -f "$Demo2Folder\docker-compose.yml" ps
```

**Why:** Starts Floci with ECS execution settings, then checks the service. Compose starts Floci; ECS deploys the application later.

```powershell
Invoke-RestMethod -Uri 'http://localhost:4566/_floci/health' | ConvertTo-Json -Depth 10
```

**Why:** Checks the local endpoint and running version.

**Expected:** Health JSON reports **`version: 2.2.0`**. Retry after a short interval if Floci is still starting.

```powershell
aws iam get-role --role-name application-execution-role --endpoint-url http://localhost:4566 --profile floci
```

**Why:** Confirms Demo 1's execution role remains available.

**Expected:** Role details and its ARN. The actual account ID is part of the ARN; do not substitute a guessed account ID.


## 4. Prepare the deployment targets

```powershell
$env:FLOCI_ENDPOINT = 'http://localhost:4566'
$env:AWS_DEFAULT_REGION = 'us-east-1'
$env:AWS_PROFILE = 'floci'
$env:AWS_PAGER = ''
$env:APP_BASE_URL = 'http://localhost:8080'
Remove-Item Env:GITHUB_SHA, Env:GITHUB_ENV, Env:GITHUB_STEP_SUMMARY -ErrorAction SilentlyContinue
```

**Why:** Gives the scripts the local endpoint, profile, correct region and application address. Clearing GitHub-only variables selects the local execution flow. Setting these values normally produces no output.

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_local
```

**Why:** Reads the existing execution role and creates/reuses the image repository, log group, ECS cluster and local placement resources.

**Expected:** Output includes `execution_role_arn`, `repository_uri` and `subnet_id`. Values are also saved automatically in **`local-config.json`** in Demo 2.

**No manual saving or GitHub subnet variable is required.** The script prints `Configuration saved to local-config.json. Continue with the README's local deployment steps.` Step 8 reads the saved values automatically.

The subnet is supplied placement infrastructure. No EC2 instance is created, and the execution role's permissions are not broadened.

## 5. Record the Git commit and verify GitHub tests

### 1. Create a GitHub Repository

Sign in to GitHub and create a new repository.

Do not add another README, `.gitignore`,if these files already exist in the local project.

---

### 2. Create a Fine-Grained Personal Access Token

GitHub does not accept the normal GitHub account password for Git operations over HTTPS.

Use a **Personal Access Token (PAT)** as the password.

1. Open **Profile picture → Settings**.
2. Open **Developer settings**.
3. Open **Personal access tokens → Fine-grained tokens**.
4. Create a new token.
5. Select the repository created for this demo.

### 3. Configure Repository Permissions

After selecting the repository for the token:

1. Scroll to the **Repository permissions** section.
2. Click **Add permissions**.
3. Select **Contents**.
4. Set **Contents** to **Read and write**.
5. Click **Add permissions** again.
6. Select **Workflows**.
7. Set **Workflows** to **Read and write**.
8. Keep **Metadata** as **Read-only**.
9. Click **Generate token** or **Update**.

Final permissions should be:

```text
Contents   → Read and write
Workflows  → Read and write
Metadata   → Read-only
```

> The token is used only for authentication. Do not add it to source code or commit it to Git.

---

### 4. Use the Token with Git

When Git asks:

```text
Username for 'https://github.com':
```

enter your GitHub username.

When Git asks:

```text
Password for 'https://<username>@github.com':
```

paste the **Personal Access Token**, not your GitHub account password.

---

### 5. Push the Existing Service to GitHub

From the project root:

```bash
git add .
git commit -m "<Commit Message>"
git branch -M main
git remote add origin <repository-url>
git push -u origin main
```

Verify that the pushed Service source code is visible in the GitHub repository.

> If the remote is already configured, do not run `git remote add origin` again.

---
### 6. Check the Actions

Open the repository's **Actions tab on its main page**.
Open **Application CI**, select the latest run, then **Test application**.
Confirm eight tests passed and the workflow is green. This workflow contains only the test job.

The repository Actions tab shows workflow runs. **No runner setup, repository deployment variables or secrets are required.**

### Save the image tag

Back in the same Demo 2 PowerShell terminal:

```powershell
$DemoSha = (git rev-parse HEAD).Trim()
$DemoSha
```

**Why:** Saves the full Git commit SHA used as the image tag.

**Expected:** A 40-character SHA.

**Source push and image push are different:** `git push` sends source code to GitHub. Step 7 pushes a container image to Floci. GitHub test success does not deploy the service in this simplified flow.

## 6. Allow the local HTTP registry, then build and push

### Configure Docker Desktop once

Floci's local registry serves HTTP. Add only its actual registry hostname to Docker Engine's allowed HTTP registries before publishing.

```powershell
$LocalConfig = Get-Content '.\local-config.json' -Raw | ConvertFrom-Json
$RegistryHost = ($LocalConfig.repository_uri -split '/')[0]
$RegistryHost
```

**Why:** Reads the registry hostname from the actual environment, avoiding hard-coded learner account IDs.

Example output:

```text
000000000000.dkr.ecr.us-east-1.localhost:4566
```

1. Open **Docker Desktop → Settings → Docker Engine**.
2. Copy the existing JSON somewhere safe as a backup.
3. Add `insecure-registries` to the existing top-level JSON object, using the hostname printed above. **Keep all existing settings.** If that key already exists, append the hostname to its list instead of adding a duplicate key.

For an otherwise empty configuration, the complete JSON would be:

```json
{
  "insecure-registries": [
    "000000000000.dkr.ecr.us-east-1.localhost:4566"
  ]
}
```

For a configuration with other settings, add this property with the appropriate comma; do not replace those settings. Do not include `http://` or the repository path in the list.

4. Save/apply the change and restart Docker Desktop using its apply/restart control. Restarting may stop running containers. Wait for Docker Engine to be ready.

**Why:** Allows Docker to use HTTP for this specific local registry. This is a Docker Engine setting, not a Floci Compose setting. Without it, some environments report `HTTP response to HTTPS client`.

Restart/check Floci after Docker Desktop restarts:

```powershell
docker compose --project-directory "$Demo1Folder" -f "$Demo2Folder\docker-compose.yml" up -d
Invoke-RestMethod -Uri 'http://localhost:4566/_floci/health' | ConvertTo-Json -Depth 10
```

**Expected:** Floci 2.2.0 responds. The folder and environment variables remain available if the PowerShell window stayed open.

### Publish the image

```powershell
.\.venv\Scripts\python.exe -m scripts.publish
```

**Why:** Builds the multi-stage image, obtains registry authentication, logs in, pushes the SHA-tagged image and verifies registry metadata.

**Expected:** Build succeeds, `Login Succeeded`, image layers are pushed, and output contains **`Published image digest`** and `IMAGE_URI=...`.

The first build can take several minutes. A credential-storage warning is separate from push success; check the final result. Do not continue if the push fails.

## 7. Load the image and subnet values

```powershell
$LocalConfig = Get-Content '.\local-config.json' -Raw | ConvertFrom-Json
$env:IMAGE_URI = "$($LocalConfig.repository_uri):$DemoSha"
$env:FLOCI_SUBNET_ID = $LocalConfig.subnet_id
$env:APP_BASE_URL = 'http://localhost:8080'
$env:IMAGE_URI = "$($LocalConfig.repository_uri):$DemoSha"
$env:FLOCI_SUBNET_ID
```

**Why:** Reads the actual values automatically. No account ID or subnet needs to be typed. The image tag is the commit published in Step 7. Re-setting `APP_BASE_URL` here prevents a missing-address deployment error.

**Expected:** Image URI ending in the full Git SHA and a subnet ID beginning with `subnet-`.

```powershell
aws ecr describe-images --repository-name application-service --image-ids "imageTag=$DemoSha" --endpoint-url http://localhost:4566 --profile floci
```

**Why:** Confirms the SHA-tagged image exists in the registry.

**Expected:** Image metadata with the tag and digest.

## 8. Deploy through ECS

```powershell
.\.venv\Scripts\python.exe -m scripts.deploy
```

**Why:** Registers the task definition, uses Demo 1's execution role, creates/updates the service and verifies task health plus live responses.

**Expected:** JSON containing your image URI, generated task/task-definition ARNs, `ecs_health: HEALTHY`, health status `ok` with the Git SHA, and chat reply `Application received: Hello`.

A repeat deployment may print `Stopping the previous lab task to release port 8080.` The script can wait up to three minutes for the old task to stop and another three minutes for the new task to become healthy. It does not print continuous progress.

Successful deployment evidence is saved automatically in **`.generated/deployment-evidence.json`**. Do not rerun publishing merely to retry deployment of the same image.

## 9. Verify the service and live responses

```powershell
aws ecs describe-services --cluster sprint2-cluster --services application-service --endpoint-url http://localhost:4566 --profile floci
```

**Why:** Checks the service's task counts.

**Expected:** Service `ACTIVE`, `desiredCount: 1`, `runningCount: 1`, `pendingCount: 0`.

```powershell
$Health = Invoke-RestMethod -Uri 'http://localhost:8080/health'
$Health | ConvertTo-Json
```

**Why:** Checks that the ECS-hosted application responds through the Windows host port.

**Expected:** `status: ok` and `version` matching `$DemoSha`, rather than `local`.

```powershell
if ($Health.status -ne 'ok' -or $Health.version -ne $DemoSha) {
    throw 'Wrong deployment status or commit'
}
'Expected commit is running'
```

**Why:** Confirms the response identifies the expected deployed commit.

**Expected:** `Expected commit is running`. Run this block only after the health request succeeds.

```powershell
$ChatBody = @{ message = 'Hello' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8080/chat' -Method Post -ContentType 'application/json' -Body $ChatBody | ConvertTo-Json
```

**Why:** Sends a real POST request to the deployed application.

**Expected:** `{"reply":"Application received: Hello"}`; formatting may differ.

## 10. Check logs and saved evidence

```powershell
aws logs describe-log-streams --log-group-name /ecs/application-service --endpoint-url http://localhost:4566 --profile floci
aws logs filter-log-events --log-group-name /ecs/application-service --endpoint-url http://localhost:4566 --profile floci
```

**Why:** Confirms the application log stream and reads startup/request entries. Allow a short interval for forwarding.

```powershell
Get-Content '.\.generated\deployment-evidence.json'
```

**Why:** Displays the evidence saved by the successful deployment script.

## Completion checklist

- Application tests passed locally and, if the GitHub stage was used, on GitHub.
- The full-SHA-tagged container image is visible in the registry.
- ECS runs the intended image using Demo 1's execution role.
- The task is healthy, and host-side `/health` identifies the expected SHA.
- `/chat` returns the expected response and logs are available.

Keep Demo 1's policy files, `execution-role-arn.txt` and `data` folder locally. Keep Demo 2's generated files for reference. Do not commit Floci data, virtual environments, `local-config.json`, `.generated` or credentials. Learners do not need another GitHub push after deployment.

Successful local execution alone does not prove every AWS IAM permission is enforced by Floci.

## Troubleshooting — run only when needed

| Problem | Action |
|---|---|
| `floci` profile missing | Run `aws configure --profile floci`; enter `test`, `test`, `us-east-1`, `json`. If asked about optional AWS AI skills, enter `n`. |
| Role missing | Check Step 3's data mount; retain Demo 1's original data. |
| Floci reports 2.1.0 | Check the image line is `floci/floci:2.2.0`, then repeat Step 3's pull/up commands. |
| `HTTP response to HTTPS client` | Check Step 7's Docker Engine registry entry and restart Docker Desktop. |
| Missing `APP_BASE_URL` | Repeat Step 8 before retrying deployment. |
| Port 8080 already allocated | Stop an earlier source application or manually started container. |
| Deployment timeout | Check task/container status and logs below; do not repeatedly redeploy without inspecting the failure. |
| Host health request fails | Confirm Floci 2.2.0 and host port publication below. Do not treat a running task alone as success. |

Check actual Docker containers:

```powershell
docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'
```

**Expected:** The application container is healthy and has a published host mapping such as `0.0.0.0:8080->8080/tcp`. `8080/tcp` alone is not host publication.

Read Floci logs:

```powershell
docker compose --project-directory "$Demo1Folder" -f "$Demo2Folder\docker-compose.yml" logs --tail 100 floci
```

Find stopped task identifiers:

```powershell
aws ecs list-tasks --cluster sprint2-cluster --service-name application-service --desired-status STOPPED --endpoint-url http://localhost:4566 --profile floci
```

Use a returned ARN to inspect its failure details:

```powershell
aws ecs describe-tasks --cluster sprint2-cluster --tasks 'PASTE_STOPPED_TASK_ARN_HERE' --endpoint-url http://localhost:4566 --profile floci
```

**Why:** Reads `stoppedReason` and container exit details.

## Stop the demo when finished

```powershell
aws ecs update-service --cluster sprint2-cluster --service application-service --desired-count 0 --endpoint-url http://localhost:4566 --profile floci
```

**Why:** Requests zero application tasks. After they stop, stop Floci if no further local cloud work is required:

```powershell
docker compose --project-directory "$Demo1Folder" -f "$Demo2Folder\docker-compose.yml" down
```

**Why:** Stops Floci while retaining the bind-mounted Demo 1 data.

If a runner was started during the earlier version, stop its terminal process with Ctrl+C. The final `Application CI` workflow does not use a self-hosted runner.



## References

- [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/)
- [Docker registry configuration](https://docs.docker.com/reference/cli/dockerd/#insecure-registries)
- [Floci ECS](https://floci.io/floci/services/ecs/)
- [Floci releases](https://github.com/floci-io/floci/releases)