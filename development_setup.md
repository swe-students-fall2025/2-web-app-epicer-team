# SETUP INSTRUCTIONS FOR DEVELOPMENT

1. **Clone the repository and navigate to the project root**

2. **Create environment file**
   - Copy `env.example` to `.env` in the project root
   - Update the values in `.env` with your specific configuration
   - Ask in Discord for the production environment variables if needed

3. **Run the setup script**
   ```bash
   pipenv shell
   pipenv install
   ```
   This will:
   - Set up the pipenv virtual environment
   - Install all dependencies

4. **To start the app, run the following commands:**

    ```bash
   python app.py
    ```
Then go to http://127.0.0.1:5000 in your browser.

5. **To stop the app, press Ctrl-C in the flask runtime, go to the root of the project, and run the following commands:**

    ```bash
    deactivate
    ```

## Troubleshooting

- **MongoDB connection issues**: Ensure Docker is running and the MongoDB container is started
- **Environment activation issues**: Make sure you're in the project root directory
- **Permission issues**: You may need to run setup commands with `sudo` on Linux/macOS
- **Port conflicts**: If port 5000 is in use, set `FLASK_PORT` in your `.env` file to a different port
