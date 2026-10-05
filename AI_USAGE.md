# AI Usage Log

| Date/commit | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-10-05 | ChatGPT | Help me plan the project over the six days and set up the first basic version of StudyFlow. | Modified | I used the suggested setup but kept the first day simple and only created the basic Flask app. | Flask starts the web app. The `/` route runs the `home()` function, and that function sends the text "StudyFlow is running" to the browser. The app also checks if a PORT value exists and uses 5000 if it does not. |
| 2026-10-05 | ChatGPT | Help me choose between Flask, Django and FastAPI for this assignment. | Accepted | No major changes. | I chose Flask because the project is small and Flask is simple. Django gives a lot more features than I need, and Flask makes it easier for me to understand what each part of the app is doing. |