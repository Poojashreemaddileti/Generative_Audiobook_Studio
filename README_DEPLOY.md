# Deployment notes

This project is a Flask application (not a Streamlit app). The included `run.bat` is intended for local Windows use.

For a server/container deployment, install the dependencies in `backend/requirements.txt` plus a compatible PyTorch build, then start the application with:

```bash
cd backend
HOST=0.0.0.0 PORT=5000 FLASK_DEBUG=0 python app.py
```

Persist the project `data/` directory between deployments. The first generation downloads the configured Hugging Face model; make sure the deployment has outbound access to Hugging Face and enough memory/disk for PyTorch and the model. Do not expose an unauthenticated instance publicly: this starter project is designed for local/private use and does not include user authentication, rate limiting, or a production reverse proxy.
