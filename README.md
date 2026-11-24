# StudyFlow

StudyFlow is a small student planner app I am building for my DevOps assignment.

Note: commits in this repo show two GitHub accounts, Sanaddd and sanadhamadd. Both are mine. The older commits used my personal email.

The idea is to have one simple place where a student can keep track of their courses and the assignments linked to them.

The project has two main parts:

1. Courses
2. Assignments

Each part runs as its own service with its own SQL Server database.

## What it does

For courses, the user can add, view, edit, and delete courses.

For assignments, the user can add an assignment with an optional description, link it to a course, give it a due date and priority, and mark it as completed.

## Tech used

- Python
- Flask
- SQL Server (pymssql)
- HTML/CSS
- pytest
- pytest-cov

## Project structure (Assignment 2)

StudyFlow is split into two services along the seam from ADR-2:

    services/
      courses/        Courses domain: own Flask app, own database, own Dockerfile
      assignments/    Assignments domain: own Flask app, own database, own Dockerfile
    ui/               Static front end (HTML, CSS, JS) that calls both services

Each service has its own `requirements.txt` (runtime, pinned) and
`requirements-dev.txt` (tests). Assignments store only a `course_id`; course
details belong to the courses service.

## Running a single service

Each service needs a SQL Server database, given as `DATABASE_URL`:

    cd services/courses            # or services/assignments
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements-dev.txt
    export DATABASE_URL="mssql://<user>:<password>@localhost:1433/<database>"
    python app.py                  # listens on PORT, default 8000

On startup the service applies any pending migrations from its `migrations/` folder.

Migrations so far: courses `001_init.sql`; assignments `001_init.sql` and `002_add_description.sql`, which adds a description column and gives existing rows an empty one.

## Running a service in Docker

    docker build -t studyflow-courses services/courses
    docker run --rm -p 8001:8000 -e DATABASE_URL="mssql://<user>:<password>@host.docker.internal:1433/<database>" studyflow-courses

## Running the whole system

    cp .env.example .env        # then replace the passwords
    docker compose up --build

This starts SQL Server, creates one database and login per service (`db/init.sql`), then starts both services and the UI:

- courses: http://localhost:8001/courses
- assignments: http://localhost:8002/assignments
- UI: http://localhost:8080

Data is kept between restarts. `docker compose down -v` deletes it.

## Testing

Lint, unit tests and coverage, from inside a service folder. Tests run against a throwaway SQL Server: each run creates its own database and drops it at the end.

    export TEST_SQLSERVER_URL="mssql://sa:<password>@localhost:1433/master"
    ruff check .
    python -m pytest --cov        # fails if coverage is below 70%

Integration test across both services, from the repository root, with the system running:

    docker compose up --build -d
    python -m pytest tests/integration -v

It checks that assignments get course names from the courses service, and that they still load, without names, when the courses service is stopped.

## Configuration

Each service reads:

- PORT - port the service listens on. Default: 8000
- DATABASE_URL - connection string of the service's own database. Secret, no default
- GIT_SHA - commit the image was built from, shown by /health. Default: dev
- CORS_ORIGINS - browser origins allowed to call the service, comma-separated (compose: http://localhost:8080). No default: cross-origin calls are refused
- COURSES_URL (assignments only) - base URL of the courses service. Default: http://courses:8000
- COURSES_TIMEOUT_S (assignments only) - how long to wait for the courses service, in seconds. Default: 2

## Health and logs

- GET /health returns 200 `{"status": "ok", "db": "ok", "version": "<sha>"}` when the service can read and write its own database, and 503 otherwise.
- Every request writes one line to stdout: method, path, status and duration.

## Deploying to Azure

The system runs in my Azure for Students subscription, in polandcentral: https://shamadieu2024ui.z36.web.core.windows.net

On every push to main, `.github/workflows/cd.yml` runs CI, then points both Container Apps at the images tagged with that commit, writes `ui/config.js` with the services' Azure addresses, uploads `ui/` to the storage static website, and waits until `/health` of both services returns 200.

### Initial setup (run once, in bash)

    P=shamad-ieu2024; RG=rg-$P; LOC=polandcentral
    az account set --subscription "Azure for Students"
    az group create -n $RG -l $LOC

    # UI: storage static website
    az storage account create -n shamadieu2024ui -g $RG -l $LOC --sku Standard_LRS --kind StorageV2
    az storage blob service-properties update --account-name shamadieu2024ui --static-website --index-document index.html

    # SQL server and one serverless database per service, on the free offer
    az sql server create -n $P-sql -g $RG -l $LOC --admin-user sfadmin --admin-password <admin password>
    az sql server firewall-rule create -g $RG -s $P-sql -n AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
    az sql db create -g $RG -s $P-sql -n $P-courses-db --edition GeneralPurpose --compute-model Serverless --family Gen5 --min-capacity 0.5 --capacity 1 --backup-storage-redundancy Local --use-free-limit true --free-limit-exhaustion-behavior AutoPause
    (the same for $P-assignments-db)

    # One contained user per database, run with sqlcmd as the admin (firewall opened to my IP for this, then closed):
    CREATE USER courses_user WITH PASSWORD = '<courses password>';
    ALTER ROLE db_ddladmin ADD MEMBER courses_user;
    ALTER ROLE db_datareader ADD MEMBER courses_user;
    ALTER ROLE db_datawriter ADD MEMBER courses_user;
    (the same for assignments_user in the assignments database)

    # Container Apps
    az containerapp env create -n $P-env -g $RG -l $LOC
    az containerapp create -n $P-courses -g $RG --environment $P-env --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 8000 --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi --secrets database-url=<courses connection string> --env-vars PORT=8000 DATABASE_URL=secretref:database-url CORS_ORIGINS=https://shamadieu2024ui.z36.web.core.windows.net
    az containerapp create -n $P-assignments ... (the same, plus COURSES_URL=https://<courses address> COURSES_TIMEOUT_S=2)

    # Identity the pipeline signs in as (OIDC, no stored Azure password)
    az identity create -n $P-github -g $RG -l $LOC
    az role assignment create --assignee-object-id <identity principal id> --assignee-principal-type ServicePrincipal --role Contributor --scope <resource group id>
    az identity federated-credential create --identity-name $P-github -g $RG -n github-main --issuer https://token.actions.githubusercontent.com --audiences api://AzureADTokenExchange --subject "repo:Sanaddd/studyflow-devops:ref:refs/heads/main"
    (and github-main-ids with the numeric form repo:Sanaddd@145849499/studyflow-devops@1406333785:ref:refs/heads/main)

    # GitHub: secrets AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, COURSES_DB_PASSWORD, ASSIGNMENTS_DB_PASSWORD
    #         variables PREFIX, RESOURCE_GROUP, UI_STORAGE
    # Reader on the resource group for amartini@faculty.ie.edu and bserra@faculty.ie.edu

After this, only the pipeline changes anything. The first request after an idle period can take about a minute while the container starts and the database resumes; the UI shows "starting up" and retries.
