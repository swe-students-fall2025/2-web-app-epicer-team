# SETUP INSTRUCTIONS

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

## Inside the app

- **login**: please use the following login with a preset location.
```
username:
Test_User
email:
test@example.com
password:
SecretTest1
```
 Optionally, if you register your own account, you can set your location during registration, but please do make sure it is a real address to take advantage of the distance features. Additionally, please do not change your location too rapidly so as not to abuse the map api endpoint.
 
- **search**: 
The products you can search for are the following
```
Organic Spinach
Organic Bananas
Almond Milk
Free-Range Eggs
Coffee
```
The stores you can search for are the following
```
Trader Joe's
Whole Foods Market
Costco
Organic Spinach
Almond Store
```
- **filter**: 
To test our filter first search for:
almond

You should see an almond product and an almond store. 
Now you can use the filter. 
-