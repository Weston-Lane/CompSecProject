# CompSecProject

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
