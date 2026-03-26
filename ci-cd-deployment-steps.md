# CI/CD Deployment Process

## 1. Pushing Code & Triggering CI
*   **Push:** Developer pushes code to GitHub.
*   **CI Triggers:** GitHub detects the push and spins up a temporary Ubuntu server to run `.github/workflows/ci.yaml` and execute `pytest` unit tests.

## 2. GitHub Triggers CD (`aws.yaml`)
*   **The Check:** As soon as `ci.yaml` finishes with a green checkmark, GitHub checks if the tests passed AND the code is on the `main` branch.
*   **The Trigger:** If true, the deployment process begins.

## 3. Login to AWS
*   **The Action:** GitHub securely connects to your AWS account.
*   **How it works:** It uses `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to prove it is authorized to make changes.
*   **Where to get these keys:** Go to your AWS Account **IAM -> Users -> Create Access Key**.
*   **Where to store them:** Save these securely in your GitHub repository underneath **Settings -> Secrets and variables -> Actions**.

## 4. Build Docker Image
*   **The Action:** It prepares your application to be run anywhere.
*   **How it works:** It reads your `Dockerfile`, installs the dependencies, and bundles everything into an isolated Docker Image tagged with the unique GitHub commit ID.

## 5. Push to ECR (Elastic Container Registry)
*   **The Action:** It uploads your newly built application to AWS.
*   **How it works:** The pipeline logs into your ECR repository (`documentportalliveclass`) and uploads the Docker image it just built.

## 6. Update Task Definition
*   **The Action:** AWS needs to know what to run via a blueprint (`task_definition.json`).
*   **How it works:** The pipeline dynamically mathematically updates this blueprint to say: "Instead of the old Image version, use the brand new Image version we just pushed to ECR."

## 7. Deploy to Amazon ECS (Elastic Container Service)
*   **The Action:** The final step where your application goes "live" to the internet.
*   **How it works:** Amazon ECS (Fargate engine) reads the updated blueprint, provisions new server space, downloads the new Docker image, and starts it on port 8080. 
*   **Safety Check:** ECS ensures the new container is healthy before gracefully shutting down the old ones, meaning zero downtime for users.
