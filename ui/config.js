// Addresses of the two services, read by app.js.
// These are the docker compose ports. The CD pipeline overwrites this file
// with the Azure addresses when it deploys the UI.
window.CONFIG = {
    COURSES_URL: "http://localhost:8001",
    ASSIGNMENTS_URL: "http://localhost:8002"
};
