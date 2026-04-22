# CompSecProject
## ----Documentation is in the Docs/ and docs/ folders----
## Dependencies

* **Create a virtual environment** (if not done already):
    Windows:
    ```bash
        python -m venv venv
    ```
    Mac:
    ```bash
        python3 -m venv venv
    ```

* **Activate the virtual environment**:
    Windows:
    ```bash
        venv\Scripts\activate
    ```
    Mac:
    ```bash
        source venv/bin/activate
    ```
* **Install requirements**:
    ```bash
    pip install -r requirements.txt
    ```
    If youre on python 3.14 use 
    ```bash
    pip install -r requirements2.txt
    ```
* **Generate Local SSL Certs**:
  ### OPEN SSL MUST BE INSTALLED AND IN PATH ENV VARIABLE
    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    ```
* **Generate Data at Rest and App State keys**:
    ```bash
    python setup_keys.py
    ```

* **Run With**
    ```bash
    python app.py
    ```

    # IMPORTANT NOTES:
      * The first user created will be the admin account. This allows for easy testing for the grader.
      * Every subsiquent created account will be a standard user.
      * The only way to get a guest user is to demote through an admin account
