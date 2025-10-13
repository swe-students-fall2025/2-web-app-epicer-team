<!-- TODO: REMOVE THIS WHEN DONE -->
# SETUP INSTRUCTIONS FOR DEVELOPMENT
- These instructions are meant for linux and macOS devices. To setup the app on Windows, please use WSL, Cygwin, or any other method of running a \*nix like environment on Windows

1. Install docker and python3 on your local machine. You **must** at least have the docker cli and you must have python3.

2. Add the .env file to the root of the project (ask in discord for this)

3. Go to the root of the project, run the following command, and enter your computer password if prompted:

    ```bash
    sudo chmod +x setup.sh
    ./setup.sh
    ```

4. To start the app, run the following commands:

    ```bash
    source dev_env/bin/activate
    flask run
    ```
Then go to http://127.0.0.1:5000 in your browser.

5. To stop the app, press Ctrl-C in the flask runtime, go to the root of the project, and run the following commands:

    ```bash
    ./demo_scripts/demo_stop.sh
    deactivate
    ```
